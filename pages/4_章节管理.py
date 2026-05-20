"""
章节管理页面 — 新增、查看、删除章节。
"""

import streamlit as st

from src.db import init_db
from src.services import (
    get_all_subjects, get_all_chapters, create_chapter, delete_chapter,
)

init_db()


def main():
    st.title("📂 章节管理")

    tab1, tab2 = st.tabs(["📋 章节列表", "➕ 新增章节"])

    with tab1:
        _chapter_list()

    with tab2:
        _add_chapter()


def _chapter_list():
    """显示所有章节列表。"""
    subjects = get_all_subjects()
    subj_opts = {"全部科目": None}
    subj_opts.update({s["name"]: s["id"] for s in subjects})
    filter_subj = st.selectbox("按科目筛选", list(subj_opts.keys()), key="ch_filter")

    chapters = get_all_chapters()
    if filter_subj != "全部科目":
        sid = subj_opts[filter_subj]
        chapters = [c for c in chapters if c["subject_id"] == sid]

    if not chapters:
        st.info("暂无章节数据。请先新增章节。")
        return

    st.caption(f"共 {len(chapters)} 个章节")

    for ch in chapters:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 4, 1])
            with col1:
                st.markdown(f"**{ch['name']}**")
                st.caption(f"科目：{ch['subject_name']}")
            with col2:
                st.caption(f"描述：{ch['description'] or '（无）'}")
                st.caption(f"创建时间：{ch['created_at']}")
            with col3:
                if st.button("🗑️ 删除", key=f"ch_del_{ch['id']}", use_container_width=True):
                    st.session_state[f"ch_del_confirm_{ch['id']}"] = True

            if st.session_state.get(f"ch_del_confirm_{ch['id']}"):
                ok, msg = delete_chapter(ch["id"])
                if ok:
                    st.success(msg)
                    st.session_state[f"ch_del_confirm_{ch['id']}"] = False
                    st.rerun()
                else:
                    st.error(msg)
                    if st.button("知道了", key=f"ch_del_ok_{ch['id']}"):
                        st.session_state[f"ch_del_confirm_{ch['id']}"] = False
                        st.rerun()


def _add_chapter():
    """新增章节表单。"""
    st.subheader("新增章节")

    subjects = get_all_subjects()
    subj_opts = {s["name"]: s["id"] for s in subjects}
    subj_name = st.selectbox("所属科目 *", list(subj_opts.keys()), key="add_ch_subj")
    subject_id = subj_opts[subj_name]

    name = st.text_input("章节名称 *", key="add_ch_name", placeholder="例如：极限、矩阵、组合逻辑电路...")
    description = st.text_area("章节描述（可选）", key="add_ch_desc", placeholder="简要描述章节内容...")

    if st.button("💾 新增章节", type="primary", use_container_width=True):
        if not name.strip():
            st.error("章节名称不能为空！")
            return
        create_chapter(subject_id, name.strip(), description.strip())
        st.success(f"章节「{name.strip()}」已创建！")


if __name__ == "__main__":
    main()
