"""
考研错题复习提醒系统 — 主入口 + 首页 Dashboard
"""

import streamlit as st
from datetime import date

from src.db import init_db
from src.statistics import get_total_statistics, get_subject_statistics
from src.task_scheduler import generate_daily_tasks, regenerate_daily_tasks
from src.services import task_exists_for_date
from src.utils import get_today_str

st.set_page_config(
    page_title="考研错题复习提醒系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.title("📚 考研错题复习提醒系统")
    today = get_today_str()
    st.caption(f"📅 今天：{today}")

    # ===== 初始化数据库 =====
    init_db()

    # ===== 侧边栏操作按钮 =====
    with st.sidebar:
        st.subheader("⚡ 快捷操作")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 生成今日任务", use_container_width=True):
                if task_exists_for_date(today):
                    st.warning("今日任务已存在！如需重新生成，请使用下方按钮。")
                else:
                    result = generate_daily_tasks(today)
                    total = sum(len(v) for v in result.values())
                    if total > 0:
                        st.success(f"已生成 {total} 道今日复习题！")
                    else:
                        st.info("暂无可生成的任务。请先录入错题。")
                    st.rerun()

        with col_b:
            if st.button("🔁 重新生成", use_container_width=True):
                result = regenerate_daily_tasks(today)
                total = sum(len(v) for v in result.values())
                st.success(f"已重新生成 {total} 道今日复习题（已完成的任务已保留）")
                st.rerun()

        st.divider()
        st.caption("页面导航请使用左侧菜单")

    # ===== 获取统计数据 =====
    stats = get_total_statistics()
    subj_stats = get_subject_statistics()

    # ===== 总览卡片 =====
    st.subheader("📊 总览")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("总错题数", stats["total"])
    col2.metric("需复习", stats["need_review"], delta=None)
    col3.metric("已复习", stats["reviewed"])
    col4.metric("已熟练", stats["mastered"])
    col5.metric("今日待完成", stats["today_pending"])
    col6.metric("今日已完成", stats["today_done"])

    st.divider()

    # ===== 各科目进度 =====
    st.subheader("📋 各科目进度")
    if subj_stats:
        cols = st.columns(len(subj_stats))
        for i, ss in enumerate(subj_stats):
            with cols[i]:
                st.markdown(f"**{ss['subject_name']}** ({ss['category']})")
                st.caption(f"总错题：{ss['total']}  |  熟练：{ss['mastered']}")
                st.caption(f"今日任务：{ss['today_tasks']}  |  已完成：{ss['today_done']}")
                if ss["total"] > 0:
                    progress = ss["today_done"] / max(ss["today_tasks"], 1)
                    st.progress(min(progress, 1.0), text=f"今日进度 {ss['today_done']}/{ss['today_tasks']}")
                else:
                    st.progress(0, text="暂无错题")
    else:
        st.info("暂无科目数据。")

    st.divider()

    # ===== 快捷操作卡片 =====
    st.subheader("📌 常用入口")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.markdown("#### 📝 今日复习")
            st.write(f"待完成：**{stats['today_pending']}** 题")
            st.write(f"已完成：**{stats['today_done']}** 题")
            st.page_link("pages/1_今日复习.py", label="进入今日复习 →")
    with c2:
        with st.container(border=True):
            st.markdown("#### ➕ 录入错题")
            st.write("记录今日新错题")
            st.write("或批量导入历史错题")
            st.page_link("pages/2_新增错题.py", label="录入新错题 →")
    with c3:
        with st.container(border=True):
            st.markdown("#### 📚 错题库")
            st.write(f"总错题：**{stats['total']}** 题")
            st.write(f"收藏：**{stats['favorite']}**  |  熟练：**{stats['mastered']}**")
            st.page_link("pages/3_错题库.py", label="查看错题库 →")
    with c4:
        with st.container(border=True):
            st.markdown("#### 📊 数据统计")
            st.write(f"待复习：**{stats['need_review']}** 题")
            st.write(f"延期题：**{stats['postponed']}** 题")
            st.page_link("pages/6_数据统计.py", label="查看详细统计 →")


if __name__ == "__main__":
    main()
