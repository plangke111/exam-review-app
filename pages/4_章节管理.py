"""
章节管理页面 — 按科目分组查看、新增、删除章节。
预置 42 个标准章节（来自 目录章节整理.md），开箱即用。
"""

import streamlit as st

from src.db import init_db
from src.services import (
    get_all_subjects, get_all_chapters, create_chapter, delete_chapter,
    get_chapters_by_subject,
)
from src.statistics import get_chapter_statistics

init_db()


def main():
    st.title("📂 章节管理")

    subjects = get_all_subjects()

    # 章节总数统计
    all_chapters = get_all_chapters()
    st.caption(f"📊 共 {len(all_chapters)} 个章节，覆盖 {len(subjects)} 个科目")

    tab1, tab2 = st.tabs(["📋 章节列表", "➕ 新增章节"])

    with tab1:
        _chapter_list(subjects, all_chapters)

    with tab2:
        _add_chapter(subjects)


def _chapter_list(subjects, all_chapters):
    """按科目分组展示章节，显示每章错题数。"""

    # 科目筛选
    subj_names = ["全部科目"] + [s["name"] for s in subjects]
    filter_name = st.selectbox("按科目筛选", subj_names, key="ch_filter")

    # 获取章节统计数据（含错题数）
    ch_stats = get_chapter_statistics()
    stats_map = {s["chapter_id"]: s for s in ch_stats}

    if filter_name == "全部科目":
        target_subjects = subjects
    else:
        target_subjects = [s for s in subjects if s["name"] == filter_name]

    for subj in target_subjects:
        subj_chapters = [c for c in all_chapters if c["subject_id"] == subj["id"]]
        _render_subject_section(subj["name"], subj_chapters, stats_map)


def _render_subject_section(subject_name, chapters, stats_map):
    """渲染一个科目下的所有章节。"""
    done_count = sum(1 for c in chapters if stats_map.get(c["id"], {}).get("total", 0) > 0)
    total_count = len(chapters)

    with st.expander(
        f"📐 {subject_name}  ({total_count} 个章节，{done_count} 个有错题)",
        expanded=False,
    ):
        if not chapters:
            st.caption("暂无章节。")
            return

        # 表头
        header_cols = st.columns([4, 1, 1, 1, 1, 0.8])
        header_cols[0].markdown("**章节名**")
        header_cols[1].markdown("**错题**")
        header_cols[2].markdown("**已复习**")
        header_cols[3].markdown("**未复习**")
        header_cols[4].markdown("**熟练**")
        header_cols[5].markdown("**操作**")

        st.divider()

        for ch in chapters:
            stats = stats_map.get(ch["id"], {})
            _render_chapter_row(ch, stats)


def _render_chapter_row(ch, stats):
    """渲染单个章节行。"""
    row_cols = st.columns([4, 1, 1, 1, 1, 0.8])

    with row_cols[0]:
        st.markdown(f"{ch['name']}")

    with row_cols[1]:
        total = stats.get("total", 0) or 0
        st.caption(f"{total}")

    with row_cols[2]:
        reviewed = stats.get("reviewed", 0) or 0
        st.caption(f"{reviewed}")

    with row_cols[3]:
        unreviewed = stats.get("unreviewed", 0) or 0
        st.caption(f"{unreviewed}")

    with row_cols[4]:
        mastered = stats.get("mastered", 0) or 0
        st.caption(f"{mastered}")

    with row_cols[5]:
        if st.button("🗑️", key=f"ch_del_{ch['id']}", help="删除此章节"):
            st.session_state[f"ch_del_confirm_{ch['id']}"] = True

    # 删除确认
    if st.session_state.get(f"ch_del_confirm_{ch['id']}"):
        _confirm_delete_chapter(ch)


def _confirm_delete_chapter(ch):
    """删除章节确认对话框。"""
    st.warning(f"确定删除「{ch['name']}」吗？")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("确认删除", key=f"ch_del_yes_{ch['id']}"):
            ok, msg = delete_chapter(ch["id"])
            if ok:
                st.success(msg)
            else:
                st.error(msg)
            st.session_state[f"ch_del_confirm_{ch['id']}"] = False
            st.rerun()
    with c2:
        if st.button("取消", key=f"ch_del_no_{ch['id']}"):
            st.session_state[f"ch_del_confirm_{ch['id']}"] = False
            st.rerun()


def _add_chapter(subjects):
    """新增章节表单，含重复检测。"""
    st.subheader("➕ 新增章节")

    subj_opts = {s["name"]: s["id"] for s in subjects}
    subj_name = st.selectbox("所属科目 *", list(subj_opts.keys()), key="add_ch_subj")
    subject_id = subj_opts[subj_name]

    # 已有章节列表
    existing = get_chapters_by_subject(subject_id)
    existing_names = {c["name"] for c in existing}

    name = st.text_input("章节名称 *", key="add_ch_name",
                         placeholder="例如：极限、矩阵、组合逻辑电路...")

    # 重复检测
    if name.strip() and name.strip() in existing_names:
        st.warning(f"⚠️ 「{name.strip()}」已存在于 {subj_name} 中，无需重复创建。")

    description = st.text_area("章节描述（可选）", key="add_ch_desc",
                               placeholder="简要描述章节内容...")

    # 显示当前科目已有章节
    if existing:
        st.markdown("**当前科目已有章节：**")
        st.caption("、".join([c["name"] for c in existing[:10]]))
        if len(existing) > 10:
            st.caption(f"…还有 {len(existing) - 10} 个")

    if st.button("💾 新增章节", type="primary", use_container_width=True):
        if not name.strip():
            st.error("章节名称不能为空！")
        elif name.strip() in existing_names:
            st.error(f"「{name.strip()}」已存在，请使用其他名称。")
        else:
            create_chapter(subject_id, name.strip(), description.strip())
            st.success(f"章节「{name.strip()}」已创建！")
            st.rerun()


if __name__ == "__main__":
    main()
