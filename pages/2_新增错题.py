"""
新增错题页面 — 支持录入单道错题和批量历史错题导入，支持上传题目图片。
"""

import os
import streamlit as st
from datetime import date

from src.db import init_db, DB_DIR
from src.services import (
    get_all_subjects, get_chapters_by_subject, create_mistake, update_mistake,
    get_mistake_by_id, query_mistakes,
)
from src.statistics import get_mistakes_by_filter
from src.utils import save_uploaded_image, extract_chapter_number, generate_quick_title

init_db()

SOURCES = ["真题", "模拟题", "习题册", "课后习题", "教材例题", "思考题", "课堂", "自己整理"]
DIFFICULTIES = ["简单", "中等", "困难"]


def main():
    st.title("➕ 新增错题")

    tab1, tab2, tab3, tab4 = st.tabs(["📝 逐题录入", "⚡ 快捷录入", "📋 批量历史录入", "✏️ 编辑错题"])

    with tab1:
        _single_entry_form()

    with tab2:
        _quick_entry_form()

    with tab3:
        _batch_entry_form()

    with tab4:
        _edit_form()


def _single_entry_form():
    """逐题录入表单。"""
    st.subheader("录入单道错题")

    subjects = get_all_subjects()
    subj_opts = {s["name"]: s["id"] for s in subjects}

    col1, col2 = st.columns(2)
    with col1:
        subj_name = st.selectbox("科目 *", list(subj_opts.keys()), key="s_subj")
        subj_id = subj_opts[subj_name]
    with col2:
        chapters = get_chapters_by_subject(subj_id)
        ch_opts = {c["name"]: c["id"] for c in chapters}
        ch_opts["（无章节）"] = None
        ch_name = st.selectbox("章节", list(ch_opts.keys()), key="s_ch")
        chapter_id = ch_opts[ch_name]

    title = st.text_input("题目标题 *", key="s_title", placeholder="例如：求极限 lim(x→0) sin(x)/x")

    col3, col4, col5 = st.columns(3)
    with col3:
        difficulty = st.selectbox("难度", DIFFICULTIES, index=1, key="s_diff")
    with col4:
        source = st.selectbox("来源", SOURCES, key="s_src")
    with col5:
        st.caption(f"📅 首次复习日期：{date.today().isoformat()}（系统自动设定）")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        content = st.text_area("题目内容", height=120, key="s_content",
                               placeholder="粘贴或输入题目描述...")
        wrong_reason = st.text_area("我的错误原因", height=100, key="s_wrong",
                                    placeholder="分析自己为什么错...")
    with col_b:
        solution = st.text_area("正确解法 / 解析", height=120, key="s_sol",
                                placeholder="正确的解题步骤...")
        knowledge = st.text_area("关键知识点", height=100, key="s_kp",
                                 placeholder="涉及的知识点，用逗号分隔...")

    note = st.text_area("备注", height=60, key="s_note")

    col_status, col_img = st.columns([1, 1])
    with col_status:
        status = st.radio("状态", ["普通", "⭐ 收藏", "🎯 熟练"], horizontal=True, key="s_status")
    with col_img:
        uploaded = st.file_uploader("📷 题目图片（可选）", type=["png", "jpg", "jpeg", "gif", "bmp"], key="s_img")

    if uploaded:
        st.caption(f"已选择：{uploaded.name}")

    if st.button("💾 保存错题", type="primary", use_container_width=True):
        if not title.strip():
            st.error("题目标题不能为空！")
            return
        # 先保存图片
        image_path = save_uploaded_image(uploaded, DB_DIR) if uploaded else ""
        is_fav = 1 if status == "⭐ 收藏" else 0
        is_mas = 1 if status == "🎯 熟练" else 0
        data = {
            "subject_id": subj_id,
            "chapter_id": chapter_id,
            "title": title.strip(),
            "content": content.strip(),
            "wrong_reason": wrong_reason.strip(),
            "solution": solution.strip(),
            "knowledge_points": knowledge.strip(),
            "source": source,
            "difficulty": difficulty,
            "is_favorite": is_fav,
            "is_mastered": is_mas,
            "note": note.strip(),
            "next_review_date": date.today().isoformat(),
            "image_path": image_path,
        }
        mid = create_mistake(data)
        st.success(f"错题已保存！ID: {mid}")
        st.balloons()


def _quick_entry_form():
    """快捷录入面板：只选题号，不写题目内容，用户翻书复习。"""
    st.subheader("⚡ 快捷录入")
    st.caption("直接输入题号即可记录错题，无需填写题目内容。用户翻书查阅原题。")

    subjects = get_all_subjects()
    subj_opts = {s["name"]: s["id"] for s in subjects}

    col_s, col_c = st.columns(2)
    with col_s:
        subj_name = st.selectbox("科目", list(subj_opts.keys()), key="q_subj")
        subj_id = subj_opts[subj_name]
    with col_c:
        chapters = get_chapters_by_subject(subj_id)
        if not chapters:
            st.info("该科目暂无章节，请先到「章节管理」创建章节。")
            return
        ch_opts = {c["name"]: c["id"] for c in chapters}
        ch_name = st.selectbox("章节", list(ch_opts.keys()), key="q_ch")
        chapter_id = ch_opts[ch_name]
        selected_chapter = next((c for c in chapters if c["id"] == chapter_id), None)
        chapter_num = extract_chapter_number(selected_chapter["name"] if selected_chapter else "")

    if chapter_num is None:
        # 解析不到编号时用数据库 id 替代
        chapter_num = chapter_id or 0

    # 题型配置：类型 → (标题, 容量, 来源, 前缀)
    question_types = [
        ("例题", 40, "教材例题", f"例题{chapter_num}."),
        ("习题", 30, "课后习题", f"习题{chapter_num}."),
        ("练习册", 40, "习题册",   f"练习册{chapter_num}."),
    ]

    # 已存在的错题编号（用于标记已录入）
    existing = _get_existing_quick_numbers(subj_id, chapter_id)

    with st.form("quick_form", clear_on_submit=False):

        for qtype, capacity, source_name, prefix in question_types:
            st.markdown(f"**📌 {qtype}（共 {capacity} 题）**")
            cols = st.columns(5)
            for i in range(1, capacity + 1):
                key = f"qc_{chapter_id}_{qtype}_{i}"
                already = f"{prefix}{i}" in existing
                with cols[(i - 1) % 5]:
                    checked = st.checkbox(
                        f"{prefix}{i}",
                        key=key,
                        # 灰色标记已录入的题目
                        disabled=already,
                    )
                    if already and i == 1:
                        st.caption("（已录入）")

        st.divider()
        submitted = st.form_submit_button("💾 保存选中的错题", type="primary", use_container_width=True)

    if submitted:
        count = 0
        for qtype, capacity, source_name, prefix in question_types:
            for i in range(1, capacity + 1):
                key = f"qc_{chapter_id}_{qtype}_{i}"
                if st.session_state.get(key, False):
                    title = generate_quick_title(qtype, chapter_num, i)
                    # 跳过已存在的
                    if title in existing:
                        continue
                    data = {
                        "subject_id": subj_id,
                        "chapter_id": chapter_id,
                        "title": title,
                        "content": "",
                        "wrong_reason": "",
                        "solution": "",
                        "knowledge_points": "",
                        "source": source_name,
                        "difficulty": "中等",
                        "is_favorite": 0,
                        "is_mastered": 0,
                        "note": "",
                        "next_review_date": date.today().isoformat(),
                        "question_type": qtype,
                        "question_number": i,
                    }
                    create_mistake(data)
                    count += 1
        if count > 0:
            st.success(f"成功录入 {count} 道错题！")
        else:
            st.info("未选中任何新错题。")
        st.rerun()


def _get_existing_quick_numbers(subject_id, chapter_id):
    """获取已有快捷录入的题号集合，用于标记已录入。"""
    rows = get_mistakes_by_filter(subject_id=subject_id, chapter_id=chapter_id)
    result = set()
    for r in rows:
        title = r["title"] if r["title"] else ""
        if title.startswith(("例题", "习题", "练习册")):
            result.add(title)
    return result


def _batch_entry_form():
    """批量录入历史错题。"""
    st.subheader("批量录入历史错题")
    st.caption("一次性录入多道同一科目/章节的错题。")

    subjects = get_all_subjects()
    subj_opts = {s["name"]: s["id"] for s in subjects}
    subj_name = st.selectbox("科目 *", list(subj_opts.keys()), key="b_subj")
    subj_id = subj_opts[subj_name]
    chapters = get_chapters_by_subject(subj_id)
    ch_opts = {c["name"]: c["id"] for c in chapters}
    ch_opts["（无章节）"] = None
    ch_name = st.selectbox("章节", list(ch_opts.keys()), key="b_ch")
    chapter_id = ch_opts[ch_name]

    source = st.selectbox("来源", SOURCES, key="b_src")
    difficulty = st.selectbox("默认难度", DIFFICULTIES, index=1, key="b_diff")

    st.markdown("---")
    batch_text = st.text_area(
        "批量粘贴错题",
        height=250,
        key="b_text",
        placeholder="每道题用「---」分隔，格式如下：\n\n题目标题：求极限\n"
                    "题目内容：lim(x→0) sin(x)/x = ?\n错误原因：洛必达法则使用条件没判断\n"
                    "正确解法：用等价无穷小替换\n关键知识点：等价无穷小、极限运算法则\n\n---\n\n题目标题：求导数\n...",
    )
    st.caption("使用「---」分隔每道题。每道题内部：题目标题、题目内容、错误原因、正确解法、关键知识点各占一行，以「字段名：」开头。")

    if st.button("📥 批量保存", type="primary", use_container_width=True):
        if not batch_text.strip():
            st.warning("请输入错题内容！")
            return

        items = batch_text.split("---")
        count = 0
        errors = []
        for idx, item in enumerate(items, 1):
            item = item.strip()
            if not item:
                continue
            fields = _parse_batch_item(item)
            if not fields.get("title"):
                errors.append(f"第 {idx} 道：标题为空，已跳过")
                continue
            data = {
                "subject_id": subj_id,
                "chapter_id": chapter_id,
                "title": fields.get("title", ""),
                "content": fields.get("content", ""),
                "wrong_reason": fields.get("wrong_reason", ""),
                "solution": fields.get("solution", ""),
                "knowledge_points": fields.get("knowledge_points", ""),
                "source": source,
                "difficulty": difficulty,
                "is_favorite": 0,
                "is_mastered": 0,
                "next_review_date": date.today().isoformat(),
            }
            try:
                create_mistake(data)
                count += 1
            except Exception as e:
                errors.append(f"第 {idx} 道：{str(e)}")

        if count > 0:
            st.success(f"成功录入 {count} 道错题！")
        if errors:
            for e in errors:
                st.warning(e)


def _parse_batch_item(text: str) -> dict:
    """解析单条批量录入文本。"""
    fields = {}
    lines = text.strip().split("\n")
    current_key = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 尝试匹配 "字段名：内容" 或 "字段名:内容"
        found = False
        for key in ["题目标题", "题目内容", "错误原因", "正确解法", "关键知识点", "备注"]:
            if line.startswith(f"{key}：") or line.startswith(f"{key}:"):
                current_key = key
                value = line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1]
                fields[key] = value.strip()
                found = True
                break
        if not found and current_key:
            # 续行
            fields[current_key] = fields.get(current_key, "") + "\n" + line
    # 映射到英文字段
    result = {
        "title": fields.get("题目标题", ""),
        "content": fields.get("题目内容", ""),
        "wrong_reason": fields.get("错误原因", ""),
        "solution": fields.get("正确解法", ""),
        "knowledge_points": fields.get("关键知识点", ""),
    }
    return result


def _edit_form():
    """编辑已有错题。"""
    st.subheader("✏️ 编辑错题")
    st.caption("搜索并选择要编辑的错题。")

    search_kw = st.text_input("搜索关键词", key="edit_search", placeholder="输入题目标题关键词...")

    mistakes = []
    if search_kw:
        mistakes = query_mistakes(keyword=search_kw)

    if mistakes:
        m_opts = {f"[{m['id']}] {m['title']} ({m['subject_name']} / {m['chapter_name'] or '未分章'})": m["id"]
                  for m in mistakes}
        selected = st.selectbox("选择要编辑的错题", list(m_opts.keys()), key="edit_sel")
        if selected:
            m_id = m_opts[selected]
            _show_edit_form(m_id)
    elif search_kw:
        st.info("未找到匹配的错题。")


def _show_edit_form(mistake_id):
    """显示编辑表单。"""
    m = get_mistake_by_id(mistake_id)
    if not m:
        st.error("错题不存在。")
        return

    subjects = get_all_subjects()
    subj_opts = {s["name"]: s["id"] for s in subjects}
    inv_subj = {v: k for k, v in subj_opts.items()}

    subj_name = st.selectbox("科目 *", list(subj_opts.keys()),
                             index=list(subj_opts.values()).index(m["subject_id"]) if m["subject_id"] in subj_opts.values() else 0,
                             key="edit_subj")
    subj_id = subj_opts[subj_name]
    chapters = get_chapters_by_subject(subj_id)
    ch_opts = {c["name"]: c["id"] for c in chapters}
    ch_opts["（无章节）"] = None
    current_ch = next((k for k, v in ch_opts.items() if v == m["chapter_id"]), "（无章节）")

    ch_name = st.selectbox("章节", list(ch_opts.keys()),
                           index=list(ch_opts.keys()).index(current_ch) if current_ch in ch_opts else 0,
                           key="edit_ch")
    chapter_id = ch_opts[ch_name]

    title = st.text_input("题目标题 *", value=m["title"], key="edit_title")

    col1, col2, col3 = st.columns(3)
    with col1:
        diff_opts = ["简单", "中等", "困难"]
        diff_idx = diff_opts.index(m["difficulty"]) if m["difficulty"] in diff_opts else 1
        difficulty = st.selectbox("难度", diff_opts, index=diff_idx, key="edit_diff")
    with col2:
        src_opts = SOURCES
        src_idx = src_opts.index(m["source"]) if m["source"] in src_opts else 0
        source = st.selectbox("来源", src_opts, index=src_idx, key="edit_src")
    with col3:
        next_str = m["next_review_date"] or "未设定"
        st.caption(f"📅 下次复习日期：{next_str}（系统管理）")

    col_a, col_b = st.columns(2)
    with col_a:
        content = st.text_area("题目内容", value=m["content"] or "", height=120, key="edit_content")
        wrong_reason = st.text_area("错误原因", value=m["wrong_reason"] or "", height=100, key="edit_wrong")
    with col_b:
        solution = st.text_area("正确解法", value=m["solution"] or "", height=120, key="edit_sol")
        knowledge = st.text_area("关键知识点", value=m["knowledge_points"] or "", height=100, key="edit_kp")

    # 互斥状态：收藏和熟练二选一
    current_status = "🎯 熟练" if m["is_mastered"] else ("⭐ 收藏" if m["is_favorite"] else "普通")
    status = st.radio("状态", ["普通", "⭐ 收藏", "🎯 熟练"],
                      index=["普通", "⭐ 收藏", "🎯 熟练"].index(current_status),
                      horizontal=True, key="edit_status")
    is_fav = 1 if status == "⭐ 收藏" else 0
    is_mas = 1 if status == "🎯 熟练" else 0

    note = st.text_area("备注", value=m["note"] or "", height=60, key="edit_note")

    # 当前图片展示
    if m["image_path"]:
        img_full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", m["image_path"])
        if os.path.exists(img_full):
            st.caption("📷 当前图片：")
            st.image(img_full, width=400)

    edit_uploaded = st.file_uploader("📷 替换图片（可选，留空则保留原图）", type=["png", "jpg", "jpeg", "gif", "bmp"], key="edit_img")
    if edit_uploaded:
        st.caption(f"新图片：{edit_uploaded.name}")

    col_save, col_del = st.columns([3, 1])
    with col_save:
        if st.button("💾 保存修改", type="primary", use_container_width=True):
            data = {
                "subject_id": subj_id, "chapter_id": chapter_id,
                "title": title.strip(), "content": content.strip(),
                "wrong_reason": wrong_reason.strip(), "solution": solution.strip(),
                "knowledge_points": knowledge.strip(), "source": source,
                "difficulty": difficulty, "is_favorite": is_fav,
                "is_mastered": is_mas, "note": note.strip(),
            }
            # 上传了新图片则替换
            if edit_uploaded:
                new_path = save_uploaded_image(edit_uploaded, DB_DIR)
                if new_path:
                    # 删除旧图片
                    if m["image_path"]:
                        old_img = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", m["image_path"])
                        if os.path.exists(old_img):
                            os.remove(old_img)
                    data["image_path"] = new_path
            update_mistake(mistake_id, data)
            st.success("错题已更新！")
            st.rerun()
    with col_del:
        if st.button("🗑️ 删除", type="secondary", use_container_width=True):
            st.session_state[f"confirm_del_{mistake_id}"] = True

        if st.session_state.get(f"confirm_del_{mistake_id}"):
            st.error("确认删除？此操作不可恢复！")
            col_y, col_n = st.columns(2)
            with col_y:
                if st.button("确认删除", key=f"del_yes_{mistake_id}", use_container_width=True):
                    from src.services import delete_mistake
                    delete_mistake(mistake_id)
                    st.success("已删除。")
                    st.session_state[f"confirm_del_{mistake_id}"] = False
                    st.rerun()
            with col_n:
                if st.button("取消", key=f"del_no_{mistake_id}", use_container_width=True):
                    st.session_state[f"confirm_del_{mistake_id}"] = False
                    st.rerun()


if __name__ == "__main__":
    main()
