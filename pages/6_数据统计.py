"""
数据统计页面 — 总览统计、按科目/章节下钻、筛选与题目列表展开。
"""

import streamlit as st
import pandas as pd

from src.db import init_db
from src.statistics import (
    get_total_statistics, get_subject_statistics, get_chapter_statistics,
    get_mistakes_by_filter,
)
from src.services import get_all_subjects, get_chapters_by_subject

init_db()


def main():
    st.title("📊 数据统计")

    # ===== 总览统计卡片 =====
    stats = get_total_statistics()
    st.subheader("📈 总览统计")
    r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
    r1c1.metric("总错题数", stats["total"])
    r1c2.metric("需复习", stats["need_review"])
    r1c3.metric("已复习", stats["reviewed"])
    r1c4.metric("从未复习", stats["unreviewed"])
    r1c5.metric("已熟练", stats["mastered"])
    r1c6.metric("收藏数", stats["favorite"])

    r2c1, r2c2, r2c3 = st.columns(3)
    r2c1.metric("今日待复习", stats["today_pending"])
    r2c2.metric("今日已完成", stats["today_done"])
    r2c3.metric("延期题数", stats["postponed"])

    st.divider()

    # ===== 各科目统计表格 =====
    st.subheader("📋 各科目复习进度")
    subj_stats = get_subject_statistics()
    if subj_stats:
        df = pd.DataFrame(subj_stats)
        df_display = df.rename(columns={
            "subject_name": "科目", "category": "分类", "total": "总错题",
            "need_review": "需复习", "reviewed": "已复习", "mastered": "已熟练",
            "favorite": "收藏", "today_tasks": "今日任务", "today_done": "今日完成",
        })
        st.dataframe(
            df_display[["科目", "分类", "总错题", "需复习", "已复习", "已熟练", "收藏", "今日任务", "今日完成"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("暂无科目数据。")

    st.divider()

    # ===== 各章节统计表格 =====
    st.subheader("📂 各章节复习进度")

    subjects = get_all_subjects()
    subj_opts = {"全部科目": None}
    subj_opts.update({s["name"]: s["id"] for s in subjects})
    filter_subj = st.selectbox("按科目筛选", list(subj_opts.keys()), key="stat_ch_filter")
    sid = subj_opts[filter_subj]

    ch_stats = get_chapter_statistics(subject_id=sid)
    if ch_stats:
        df_ch = pd.DataFrame(ch_stats)
        df_ch_d = df_ch.rename(columns={
            "subject_name": "科目", "chapter_name": "章节", "total": "总错题",
            "reviewed": "已复习", "unreviewed": "未复习", "mastered": "已熟练",
            "favorite": "收藏", "need_review": "待复习",
        })
        st.dataframe(
            df_ch_d[["科目", "章节", "总错题", "已复习", "未复习", "已熟练", "收藏", "待复习"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("暂无章节数据。")

    st.divider()

    # ===== 筛选查看题目列表 =====
    st.subheader("🔍 筛选查看题目列表")

    c1, c2, c3 = st.columns(3)
    with c1:
        fs_name = st.selectbox("科目", list(subj_opts.keys()), key="ml_subj")
        fsid = subj_opts[fs_name]
    with c2:
        ch_opts = {"全部章节": None}
        if fsid:
            for c in get_chapters_by_subject(fsid):
                ch_opts[c["name"]] = c["id"]
        fc_name = st.selectbox("章节", list(ch_opts.keys()), key="ml_ch")
        fcid = ch_opts.get(fc_name)
    with c3:
        list_type = st.selectbox(
            "题目类型",
            ["全部", "需复习题目", "已复习题目", "从未复习题目", "已熟练题目", "收藏题目"],
            key="ml_type",
        )

    is_fav = {"收藏题目": 1}.get(list_type, None)
    is_mas = {"已熟练题目": 1}.get(list_type, None)
    is_due = {"需复习题目": True}.get(list_type, None)
    is_rev = {"已复习题目": True, "从未复习题目": False}.get(list_type, None)

    mistake_list = get_mistakes_by_filter(
        subject_id=fsid, chapter_id=fcid,
        is_favorite=is_fav, is_mastered=is_mas,
        is_due=is_due, is_reviewed=is_rev,
    )

    st.caption(f"共 {len(mistake_list)} 道题")

    if mistake_list:
        for m in mistake_list:
            fav_str = "⭐" if m["is_favorite"] else ""
            mas_str = "🎯" if m["is_mastered"] else ""
            diff_str = {"简单": "🟢", "中等": "🟡", "困难": "🔴"}.get(m["difficulty"], "")
            tags = " ".join(filter(None, [fav_str, mas_str, diff_str]))

            with st.expander(
                f"{tags}  [{m['subject_name']} / {m['chapter_name'] or '未分章'}] {m['title']}",
                expanded=False,
            ):
                c_a, c_b = st.columns(2)
                with c_a:
                    st.markdown(f"**难度：** {m['difficulty']}  |  **来源：** {m['source']}")
                    st.markdown(f"**复习次数：** {m['review_count']}  |  **错误次数：** {m['wrong_count']}")
                    st.markdown(f"**最近复习：** {m['last_review_date'] or '无'}  |  **下次复习：** {m['next_review_date'] or '无'}")
                with c_b:
                    st.markdown(f"**收藏：** {'是' if m['is_favorite'] else '否'}  |  **熟练：** {'是' if m['is_mastered'] else '否'}")
                    st.markdown(f"**创建日期：** {m['created_at']}")
    else:
        st.info("没有符合条件的题目。")


if __name__ == "__main__":
    main()
