"""
今日复习页面 — 按科目分组展示今日任务，支持标记完成/错误/掌握/收藏/熟练。
"""

import streamlit as st
from datetime import date

from src.db import init_db
from src.services import (
    get_today_tasks, mark_task_done, mark_task_wrong, postpone_task,
    toggle_favorite, toggle_mastered, get_task_by_id, create_review_record,
)
from src.utils import difficulty_color, get_today_str

init_db()


def main():
    st.title("📝 今日复习")
    today = get_today_str()
    st.caption(f"📅 {today}")

    tasks = get_today_tasks()
    if not tasks:
        st.info("今日暂无复习任务。请先到首页「生成今日任务」。")
        return

    # 按科目分组
    grouped = {}
    for t in tasks:
        subj = t["subject_name"]
        grouped.setdefault(subj, []).append(t)

    for subj_name, subj_tasks in grouped.items():
        done_count = sum(1 for t in subj_tasks if t["status"] == "done")
        pending_count = len(subj_tasks) - done_count
        st.subheader(f"📐 {subj_name}  ({done_count}/{len(subj_tasks)} 已完成)")

        for task in subj_tasks:
            _render_task_card(task)

        st.divider()


def _render_task_card(task):
    """渲染单个复习任务卡片。"""
    status_icon = {"pending": "⬜", "done": "✅", "postponed": "⏳"}.get(task["status"], "⬜")
    fav_icon = "⭐" if task["is_favorite"] else ""
    master_icon = "🎯" if task["is_mastered"] else ""
    diff_icon = {"简单": "🟢", "中等": "🟡", "困难": "🔴"}.get(task["difficulty"], "")

    with st.expander(
        f"{status_icon} {fav_icon}{master_icon} {diff_icon} [{task['chapter_name'] or '未分章'}] {task['title']}",
        expanded=False,
    ):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**科目：** {task['subject_name']}")
            st.markdown(f"**章节：** {task['chapter_name'] or '未分章'}")
            st.markdown(f"**难度：** {task['difficulty']}")

            st.markdown("---")
            st.markdown("**📄 题目内容**")
            st.text(task["content"] or "（无）")

            st.markdown("**❌ 错误原因**")
            st.text(task["wrong_reason"] or "（无）")

            st.markdown("**✅ 正确解法**")
            st.text(task["solution"] or "（无）")

            st.markdown("**💡 关键知识点**")
            st.text(task["knowledge_points"] or "（无）")

            st.caption(f"状态：{task['status']} | 收藏：{'是' if task['is_favorite'] else '否'} | 熟练：{'是' if task['is_mastered'] else '否'}")

        with col2:
            st.markdown("**操作**")

            if task["status"] != "done":
                if st.button("✅ 标记完成", key=f"done_{task['id']}", use_container_width=True):
                    mark_task_done(task["id"])
                    create_review_record(task["mistake_id"], get_today_str(), is_completed=1, is_correct=1)
                    st.rerun()

                if st.button("❌ 仍然错误", key=f"wrong_{task['id']}", use_container_width=True):
                    mark_task_wrong(task["id"])
                    create_review_record(task["mistake_id"], get_today_str(), is_completed=1, is_correct=0)
                    st.rerun()

                if st.button("⏳ 标记未完成", key=f"postpone_{task['id']}", use_container_width=True):
                    postpone_task(task["id"])
                    create_review_record(task["mistake_id"], get_today_str(), is_completed=0, is_correct=1)
                    st.rerun()

                if st.button("🎯 已经掌握", key=f"master_{task['id']}", use_container_width=True):
                    mark_task_done(task["id"])
                    toggle_mastered(task["mistake_id"])
                    create_review_record(task["mistake_id"], get_today_str(), is_completed=1, is_correct=1, marked_mastered=1)
                    st.rerun()

            st.markdown("---")

            # 收藏切换
            fav_label = "💛 取消收藏" if task["is_favorite"] else "⭐ 收藏"
            if st.button(fav_label, key=f"fav_{task['id']}", use_container_width=True):
                toggle_favorite(task["mistake_id"])
                st.rerun()

            # 熟练切换
            m_label = "🔓 取消熟练" if task["is_mastered"] else "🎯 熟练"
            if st.button(m_label, key=f"tog_master_{task['id']}", use_container_width=True):
                toggle_mastered(task["mistake_id"])
                st.rerun()


if __name__ == "__main__":
    main()
