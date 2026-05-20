"""
复习记录页面 — 查看所有复习历史。
"""

import streamlit as st
from datetime import date, timedelta

from src.db import init_db
from src.services import get_all_subjects, get_review_records_by_date_range

init_db()


def main():
    st.title("📋 复习记录")

    subjects = get_all_subjects()
    subj_opts = {"全部科目": None}
    subj_opts.update({s["name"]: s["id"] for s in subjects})

    col1, col2 = st.columns(2)
    with col1:
        subj_name = st.selectbox("科目", list(subj_opts.keys()), key="rr_subj")
        subject_id = subj_opts[subj_name]
    with col2:
        range_opt = st.selectbox("时间范围", ["最近 7 天", "最近 30 天", "最近 90 天", "自定义"], key="rr_range")

    today = date.today()
    if range_opt == "最近 7 天":
        start = (today - timedelta(days=6)).isoformat()
        end = today.isoformat()
    elif range_opt == "最近 30 天":
        start = (today - timedelta(days=29)).isoformat()
        end = today.isoformat()
    elif range_opt == "最近 90 天":
        start = (today - timedelta(days=89)).isoformat()
        end = today.isoformat()
    else:
        sc1, sc2 = st.columns(2)
        with sc1:
            start = st.date_input("开始日期", value=today - timedelta(days=30)).isoformat()
        with sc2:
            end = st.date_input("结束日期", value=today).isoformat()

    records = get_review_records_by_date_range(start, end, subject_id)

    st.caption(f"共 {len(records)} 条复习记录")

    if not records:
        st.info("暂无复习记录。")
        return

    # 摘要统计
    completed = sum(1 for r in records if r["is_completed"])
    correct = sum(1 for r in records if r["is_correct"])
    mastered = sum(1 for r in records if r["marked_mastered"])
    ca, cb, cc = st.columns(3)
    ca.metric("完成", completed)
    cb.metric("答对", correct)
    cc.metric("已掌握", mastered)

    st.divider()

    for r in records:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            with c1:
                st.markdown(f"**{r['title']}**")
                st.caption(f"{r['subject_name']}")
            with c2:
                st.caption(f"📅 {r['review_date']}")
            with c3:
                status = "✅" if r["is_completed"] else "❌"
                st.markdown(status)
            with c4:
                extra = []
                if r["is_correct"]:
                    extra.append("答对")
                else:
                    extra.append("错误")
                if r["marked_mastered"]:
                    extra.append("🎯已掌握")
                if r["note"]:
                    extra.append(f"💬{r['note']}")
                st.caption(" ".join(extra))


if __name__ == "__main__":
    main()
