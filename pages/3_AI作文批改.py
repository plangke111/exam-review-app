"""AI 作文 + 政治主观题批改页面"""

import streamlit as st
from src.essay_grader import EnglishGrader, PoliticsGrader, list_available_prompts, list_prompt_files

st.set_page_config(page_title="AI 作文批改", page_icon="🤖", layout="wide")

# ── 初始化 ──────────────────────────
if "grade_result" not in st.session_state:
    st.session_state.grade_result = None
if "grading" not in st.session_state:
    st.session_state.grading = False


def check_prompts():
    """检查提示词是否就绪"""
    return list_available_prompts()


def render_result_english(result: dict):
    """渲染英语作文批改结果"""
    dims = result.get("dimension_diagnosis", {}) or {}
    labels = {
        "task_fulfillment": "任务完成", "content_development": "内容发展",
        "organization_coherence": "组织连贯", "language_accuracy": "语言准确",
        "language_range": "语言多样", "register_effect": "语域效果",
    }

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总分", f"{result.get('score','?')}/{result.get('max_score',20)}")
    col2.metric("档次", result.get("band", "?"))
    col3.metric("置信度", f"{(result.get('confidence',0) or 0)*100:.0f}%")
    col4.metric("词数", result.get("word_count", "?"))

    st.caption(f"score_range: {result.get('score_range','?')}")

    # 六维度
    if dims:
        st.subheader("六维度诊断")
        cols = st.columns(6)
        for i, (k, cn) in enumerate(labels.items()):
            d = dims.get(k, {}) or {}
            level = d.get("level", "?")
            cols[i].metric(cn, level, help="; ".join(d.get("evidence", []) or []))

    # 优缺点
    c1, c2 = st.columns(2)
    with c1:
        if result.get("major_strengths"):
            st.success("\n\n".join(f"✓ {s}" for s in result["major_strengths"]))
    with c2:
        if result.get("major_weaknesses"):
            st.error("\n\n".join(f"✗ {w}" for w in result["major_weaknesses"]))

    # 错误标注
    errors = result.get("errors") or []
    if errors:
        st.subheader(f"语言错误 ({len(errors)}处)")
        for e in errors:
            sev_color = {"major": "red", "moderate": "orange", "minor": "blue"}
            color = sev_color.get(e.get("severity"), "gray")
            st.markdown(
                f":{color}[**{e.get('severity','')}**] "
                f"~~{e.get('original','')}~~ → **{e.get('corrected','')}**  "
                f"`{e.get('category','')}`  "
                f"*{e.get('explanation_cn','')}*  "
                f"[扣分影响: {e.get('score_impact','')}]"
            )

    # 评分依据
    if result.get("score_rationale"):
        st.subheader("评分依据")
        for s in result["score_rationale"]:
            st.caption(f"• {s}")

    # 阅卷评语
    if result.get("examiner_comment_cn"):
        st.info(result["examiner_comment_cn"])

    # 优先行动
    pa = result.get("priority_actions") or []
    if pa:
        st.subheader("提分优先级")
        for a in pa:
            st.markdown(f"**P{a.get('priority','?')}** [{a.get('expected_gain','?')}] {a.get('action','')}")

    # 修改稿
    r1, r2 = st.columns(2)
    with r1:
        st.subheader("Minimal Revision")
        st.text_area("minimal", result.get("minimal_revision", ""), height=250, label_visibility="collapsed")
    with r2:
        st.subheader("High-Score Revision")
        st.text_area("high", result.get("high_score_revision", ""), height=250, label_visibility="collapsed")


def render_result_small(result: dict):
    """渲染英语小作文批改结果"""
    ta = result.get("task_analysis", {}) or {}

    col1, col2, col3 = st.columns(3)
    col1.metric("总分", f"{result.get('score','?')}/10")
    col2.metric("档次", result.get("band", "?"))
    col3.metric("置信度", f"{(result.get('confidence',0) or 0)*100:.0f}%")

    st.caption(f"作者: {ta.get('writer_role','?')} → 读者: {ta.get('reader_role','?')} | 目的: {ta.get('communicative_purpose','?')} | 语域: {ta.get('expected_register','?')}")

    # 信息点覆盖
    rps = ta.get("required_points") or []
    if rps:
        st.subheader("信息点覆盖")
        for rp in rps:
            icon = {"covered": "✅", "partly_covered": "⚠️", "missing": "❌"}.get(rp.get("status", ""), "?")
            st.markdown(f"{icon} [{rp.get('importance','')}] {rp.get('point','')}  _{rp.get('evidence','')}_")

    # 组织语言
    org = result.get("organization", {}) or {}
    lang = result.get("language_summary", {}) or {}
    st.caption(f"组织: {org.get('status','?')} | 准确: {lang.get('accuracy','?')} | 多样: {lang.get('range','?')} | 交际: {lang.get('communication_effect','?')}")

    # 错误
    for e in (result.get("errors") or []):
        st.markdown(f":red[**{e.get('severity','')}**] ~~{e.get('original','')}~~ → **{e.get('corrected','')}** *{e.get('explanation_cn','')}*")

    if result.get("score_rationale"):
        for s in result["score_rationale"]:
            st.caption(f"• {s}")

    r1, r2 = st.columns(2)
    with r1:
        st.subheader("Minimal Revision")
        st.text_area("minimal", result.get("minimal_revision", ""), height=200, label_visibility="collapsed")
    with r2:
        st.subheader("High-Score Revision")
        st.text_area("high", result.get("high_score_revision", ""), height=200, label_visibility="collapsed")


def render_result_politics(result: dict):
    """渲染政治批改结果"""
    pe = result.get("point_evaluation") or []

    col1, col2, col3 = st.columns(3)
    col1.metric("总分", f"{result.get('score','?')}/{result.get('max_score',10)}")
    col2.metric("采分来源", result.get("rubric_source", "?"))
    col3.metric("置信度", f"{(result.get('confidence',0) or 0)*100:.0f}%")

    if result.get("score_range"):
        st.caption(f"score_range: {result.get('score_range','?')}")

    # 各小问得分
    sb = result.get("score_breakdown") or []
    if sb:
        cols = st.columns(len(sb))
        for i, b in enumerate(sb):
            cols[i].metric(f"Q{b.get('subquestion_id','?')}", f"{b.get('score','?')}/{b.get('max_score','?')}", help=b.get("reason", ""))

    # 采分点评估
    if pe:
        st.subheader("采分点逐项评估")
        for p in pe:
            status = p.get("status", "?")
            icon = {"hit": "✅", "partial": "⚠️", "missed": "❌", "contradicted": "🚫"}.get(status, "?")
            st.markdown(f"{icon} **{p.get('point_id','')}**: {p.get('comment','')} (得 {p.get('awarded_points',0)} 分)")
            if p.get("student_evidence"):
                st.caption(f"  证据: {p['student_evidence']}")

    # 命中/遗漏
    for label, items, color in [
        ("命中采分点", result.get("hit_points") or [], "green"),
        ("部分命中", result.get("partial_points") or [], "orange"),
        ("遗漏采分点", result.get("missing_points") or [], "red"),
    ]:
        if items:
            with st.expander(f"{label} ({len(items)})"):
                for item in items:
                    st.markdown(f":{color}[• {item}]")

    if result.get("score_rationale"):
        st.subheader("评分依据")
        for s in result["score_rationale"]:
            st.caption(f"• {s}")

    if result.get("high_score_answer"):
        st.subheader("高分答案")
        st.text_area("high", result["high_score_answer"], height=250, label_visibility="collapsed")

    cmv = result.get("concise_memory_version") or []
    if cmv:
        st.subheader("可背诵精简版")
        for i, pt in enumerate(cmv, 1):
            st.markdown(f"{i}. {pt}")


# ── UI ──────────────────────────────

st.title("🤖 AI 作文 + 政治主观题批改")

# 提示词状态
prompts_ok = check_prompts()
all_ready = all(prompts_ok.values())
if not all_ready:
    missing = [k for k, v in prompts_ok.items() if not v]
    st.warning(f"⚠️ 提示词文件缺失: {', '.join(missing)}。请将对应 `.md` 文件放入 `prompts/` 目录。可参考 `.sample` 模板创建。")

# Tab 切换
tabs = st.tabs(["英语大作文", "英语小作文", "政治分析题"])

# ── Tab 1: 英语大作文 ──
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("输入")
        eb_exam = st.selectbox("考试类型", ["英语一", "英语二"], key="eb_exam")
        eb_max = st.number_input("满分", 10, 30, 20, key="eb_max")
        eb_prompt = st.text_area("题目 / 图画描述", height=80, key="eb_prompt",
            placeholder="Write an essay of 160-200 words based on the picture...")
        eb_essay = st.text_area("你的作文", height=300, key="eb_essay",
            placeholder="粘贴你的英语大作文全文...")
        if st.button("批改大作文", type="primary", disabled=st.session_state.grading or not prompts_ok.get("english_big"), key="btn_eb"):
            if not eb_essay.strip():
                st.error("请先粘贴作文内容")
            else:
                st.session_state.grading = True
                st.rerun()
    with col2:
        st.subheader("批改结果")
        if st.session_state.grading and "eb" not in st.session_state:
            with st.spinner("AI 批改中..."):
                g = EnglishGrader()
                r = g.grade_big(student_answer=eb_essay, prompt=eb_prompt, exam_type=eb_exam, max_score=eb_max)
                st.session_state["eb_result"] = r
                st.session_state.grading = False
            st.rerun()
        if "eb_result" in st.session_state:
            render_result_english(st.session_state["eb_result"])

# ── Tab 2: 英语小作文 ──
with tabs[1]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("输入")
        es_exam = st.selectbox("考试类型", ["英语一", "英语二"], key="es_exam")
        es_task = st.selectbox("文体", ["", "letter", "email", "notice", "invitation", "apology", "application", "recommendation", "other"], key="es_task")
        es_prompt = st.text_area("题目 / 情景说明", height=80, key="es_prompt",
            placeholder="Write a letter to your friend suggesting...")
        es_essay = st.text_area("你的小作文", height=250, key="es_essay",
            placeholder="粘贴你的英语小作文全文...")
        if st.button("批改小作文", type="primary", disabled=st.session_state.grading or not prompts_ok.get("english_small"), key="btn_es"):
            if not es_essay.strip():
                st.error("请先粘贴作文内容")
            else:
                st.session_state.grading = True
                st.rerun()
    with col2:
        st.subheader("批改结果")
        if st.session_state.grading and "es" not in st.session_state:
            with st.spinner("AI 批改中..."):
                g = EnglishGrader()
                r = g.grade_small(student_answer=es_essay, prompt=es_prompt, exam_type=es_exam, task_type_hint=es_task)
                st.session_state["es_result"] = r
                st.session_state.grading = False
            st.rerun()
        if "es_result" in st.session_state:
            render_result_small(st.session_state["es_result"])

# ── Tab 3: 政治分析题 ──
with tabs[2]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("输入")
        pp_subject = st.selectbox("学科", ["", "马原", "毛中特", "新思想", "史纲", "思修法治", "时政", "综合"], key="pp_subject")
        pp_max = st.number_input("满分", 5, 20, 10, key="pp_max")
        pp_question = st.text_area("设问", height=70, key="pp_question",
            placeholder="如：运用矛盾的普遍性原理，分析...")
        pp_materials = st.text_area("题目材料", height=100, key="pp_materials",
            placeholder="粘贴题目给出的材料...")
        pp_answer = st.text_area("你的答案", height=250, key="pp_answer",
            placeholder="粘贴你的答案...")
        pp_ref = st.text_area("参考答案 / 采分点（可选）", height=80, key="pp_ref",
            placeholder="可选：粘贴肖四/肖八对应答案或采分点，帮助AI更准确评分...")
        if st.button("批改分析题", type="primary", disabled=st.session_state.grading or not prompts_ok.get("politics"), key="btn_pp"):
            if not pp_answer.strip():
                st.error("请先粘贴答案内容")
            else:
                st.session_state.grading = True
                st.rerun()
    with col2:
        st.subheader("批改结果")
        if st.session_state.grading and "pp" not in st.session_state:
            with st.spinner("AI 批改中..."):
                g = PoliticsGrader()
                r = g.grade_single(student_answer=pp_answer, question=pp_question, materials=pp_materials,
                                   max_score=pp_max, subject_hint=pp_subject, reference_scoring_points=pp_ref)
                st.session_state["pp_result"] = r
                st.session_state.grading = False
            st.rerun()
        if "pp_result" in st.session_state:
            render_result_politics(st.session_state["pp_result"])

# ── 侧边栏：提示词管理 ──
with st.sidebar:
    st.subheader("📋 提示词管理")
    files = list_prompt_files()
    if files:
        for f in files:
            status = "✅" if f["task"] in prompts_ok and prompts_ok[f["task"]] else "⚠️"
            st.caption(f"{status} `{f['path']}` ({f['size']}B)")
    else:
        st.caption("（未检测到提示词文件）")
    st.caption(f"提示词目录: `prompts/`")
    st.caption(f"模型: `claude-sonnet-4-6` | temp=0.1")
