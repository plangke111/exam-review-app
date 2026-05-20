"""
错题库页面 — 多条件筛选、搜索、查看详情、编辑、删除。
"""

import streamlit as st
import os

from src.db import init_db
from src.services import (
    get_all_subjects, get_chapters_by_subject, query_mistakes,
    get_mistake_by_id, toggle_favorite, toggle_mastered, delete_mistake,
    get_review_records_by_mistake,
)

init_db()


def main():
    st.title("📚 错题库")

    # ===== 筛选区 =====
    with st.container(border=True):
        st.markdown("**筛选条件**")
        col1, col2, col3, col4, col5 = st.columns(5)

        subjects = get_all_subjects()
        subj_opts = {"全部科目": None}
        subj_opts.update({s["name"]: s["id"] for s in subjects})
        with col1:
            subj_name = st.selectbox("科目", list(subj_opts.keys()), key="qb_subj")
            subject_id = subj_opts[subj_name]

        with col2:
            ch_opts = {"全部章节": None}
            if subject_id:
                for c in get_chapters_by_subject(subject_id):
                    ch_opts[c["name"]] = c["id"]
            ch_name = st.selectbox("章节", list(ch_opts.keys()), key="qb_ch")
            chapter_id = ch_opts.get(ch_name)

        with col3:
            fav_filter = st.selectbox("收藏", ["全部", "已收藏", "未收藏"], key="qb_fav")
            is_favorite = {"全部": None, "已收藏": 1, "未收藏": 0}[fav_filter]

        with col4:
            mas_filter = st.selectbox("熟练", ["全部", "已熟练", "未熟练"], key="qb_mas")
            is_mastered = {"全部": None, "已熟练": 1, "未熟练": 0}[mas_filter]

        with col5:
            diff_filter = st.selectbox("难度", ["全部", "简单", "中等", "困难"], key="qb_diff")
            difficulty = None if diff_filter == "全部" else diff_filter

        keyword = st.text_input("🔍 关键词搜索", placeholder="搜索标题、内容、知识点...")

    # ===== 结果列表 =====
    mistakes = query_mistakes(
        subject_id=subject_id, chapter_id=chapter_id,
        is_favorite=is_favorite, is_mastered=is_mastered,
        difficulty=difficulty,
        keyword=keyword.strip() if keyword else None,
    )

    st.caption(f"共找到 {len(mistakes)} 道错题")

    if not mistakes:
        st.info("暂无错题记录。去「新增错题」页面录入吧！")
        return

    for m in mistakes:
        _render_mistake_card(m)


def _render_mistake_card(m):
    """渲染错题卡片，支持展开详情和操作。"""
    fav_icon = "⭐" if m["is_favorite"] else ""
    master_icon = "🎯" if m["is_mastered"] else ""
    diff_icon = {"简单": "🟢", "中等": "🟡", "困难": "🔴"}.get(m["difficulty"], "")

    status_tags = " ".join(filter(None, [fav_icon, master_icon, diff_icon]))
    title_line = f"[{m['subject_name']} / {m['chapter_name'] or '未分章'}] {m['title']}"
    if status_tags:
        title_line = f"{status_tags}  {title_line}"

    with st.expander(title_line, expanded=False):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**科目：** {m['subject_name']}  |  **章节：** {m['chapter_name'] or '未分章'}")
            st.markdown(f"**难度：** {m['difficulty']}  |  **来源：** {m['source']}")
            st.markdown(
                f"**创建：** {m['created_at']}  |  **复习次数：** {m['review_count']}  |  **错误次数：** {m['wrong_count']}"
            )
            if m["last_review_date"]:
                st.caption(f"最近复习：{m['last_review_date']}  |  下次计划：{m['next_review_date'] or '未设定'}")

            st.markdown("---")
            if m.get("image_path"):
                _show_mistake_image(m["image_path"])
            st.markdown("**📄 题目内容**")
            st.text(m["content"] or "（无）")
            st.markdown("**❌ 错误原因**")
            st.text(m["wrong_reason"] or "（无）")
            st.markdown("**✅ 正确解法**")
            st.text(m["solution"] or "（无）")
            st.markdown("**💡 关键知识点**")
            st.text(m["knowledge_points"] or "（无）")
            if m["note"]:
                st.markdown("**📝 备注**")
                st.text(m["note"])

        with col2:
            st.markdown("**操作**")
            fav_label = "💛 取消收藏" if m["is_favorite"] else "⭐ 收藏"
            if st.button(fav_label, key=f"qb_fav_{m['id']}", use_container_width=True):
                toggle_favorite(m["id"])
                st.rerun()

            mas_label = "🔓 取消熟练" if m["is_mastered"] else "🎯 熟练"
            if st.button(mas_label, key=f"qb_mas_{m['id']}", use_container_width=True):
                toggle_mastered(m["id"])
                st.rerun()

            st.markdown("---")
            if st.button("📋 复习记录", key=f"qb_rec_{m['id']}", use_container_width=True):
                st.session_state[f"show_rec_{m['id']}"] = not st.session_state.get(f"show_rec_{m['id']}", False)

            if st.session_state.get(f"show_rec_{m['id']}"):
                records = get_review_records_by_mistake(m["id"])
                if records:
                    for r in records[:10]:
                        st.caption(
                            f"{r['review_date']} | {'✅' if r['is_completed'] else '❌'} | "
                            f"{'答对' if r['is_correct'] else '错误'} | {'🎯已掌握' if r['marked_mastered'] else ''}"
                        )
                else:
                    st.caption("暂无复习记录。")

            st.markdown("---")
            if st.button("🗑️ 删除", key=f"qb_del_{m['id']}", type="secondary", use_container_width=True):
                st.session_state[f"qb_confirm_{m['id']}"] = True

            if st.session_state.get(f"qb_confirm_{m['id']}"):
                st.error("确认删除？此操作不可恢复！")
                cy, cn = st.columns(2)
                with cy:
                    if st.button("确认删除", key=f"qb_dy_{m['id']}", use_container_width=True):
                        delete_mistake(m["id"])
                        st.session_state[f"qb_confirm_{m['id']}"] = False
                        st.rerun()
                with cn:
                    if st.button("取消", key=f"qb_dn_{m['id']}", use_container_width=True):
                        st.session_state[f"qb_confirm_{m['id']}"] = False
                        st.rerun()


def _show_mistake_image(image_path):
    """显示错题图片。"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base, "data", image_path)
    if os.path.exists(full_path):
        st.image(full_path, width=400)
    else:
        st.caption("（图片已丢失）")


if __name__ == "__main__":
    main()
