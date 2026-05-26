"""
健身计划页面 — 查看今日训练、周进度、训练记录。
"""

import streamlit as st
from datetime import date, timedelta

from src.db import init_db
from src.fitness_service import (
    get_todays_workout, get_workout_records, save_workout_record,
    get_workout_stats, get_week_records, get_workout_history,
    get_workout_week, get_day_type, DAY_TYPE_NAMES, WEEKLY_PLAN,
    get_progression, get_today_weekday_name, get_start_date,
)

init_db()


def main():
    st.title("🏋️ 健身计划")
    st.caption("由少到多，循序渐进。宿舍可用器械：弹力绳、哑铃、引体向上杆")

    tab_today, tab_week, tab_history, tab_settings = st.tabs([
        "💪 今日训练", "📅 本周计划", "📋 训练记录", "⚙️ 设置"
    ])

    with tab_today:
        _today_tab()

    with tab_week:
        _week_tab()

    with tab_history:
        _history_tab()

    with tab_settings:
        _settings_tab()


def _today_tab():
    """今日训练面板。"""
    workout = get_todays_workout()

    # 顶部信息
    col_info, col_progress = st.columns([2, 1])
    with col_info:
        st.subheader(f"{get_today_weekday_name()} {workout['date']}")
        week_no = workout["week_no"]
        prog = workout["progression"]
        st.markdown(f"**训练类型：** {workout['day_type_name']}")
        st.markdown(f"**{prog['level_name']}** — {prog['sets']} 组，每组 {prog['rep_label']}")

    with col_progress:
        stats = get_workout_stats()
        st.metric("本周训练", f"{stats['this_week_workouts']}/{stats['this_week_target']} 天")
        st.metric("连续训练", f"{stats['streak']} 天")

    # 休息日提示
    if workout["is_rest_day"]:
        st.info("今天是休息日 🧘 让肌肉充分恢复，明天继续！")
        st.markdown("""
        **休息日建议：**
        - 拉伸放松（肩部、背部、腿部各 30 秒）
        - 泡沫轴按摩（如有）
        - 保证 7-8 小时睡眠
        """)
        return

    # 跑步日
    if workout["day_type"] == "cardio":
        _render_cardio_day(workout)
        return

    # 力量训练日
    _render_strength_day(workout)


def _render_cardio_day(workout):
    """渲染跑步日。"""
    st.subheader("🏃 户外跑步")
    st.markdown("""
    **推荐计划：**
    - 匀速跑 20-30 分钟
    - 心率控制在 140-160 次/分
    - 跑后拉伸 5-10 分钟
    """)

    today_records = get_workout_records(workout["date"])
    done = any(r["is_done"] for r in today_records)

    if done:
        st.success("✅ 今日跑步已完成！")
        for r in today_records:
            st.caption(f"距离/时长：{r['completed_reps']}，备注：{r['note'] or '无'}")
    else:
        with st.form("cardio_form"):
            duration = st.text_input("跑步时长（如 30min）", value="30min")
            note = st.text_input("备注（如距离、体感）", placeholder="3km，感觉良好")
            submitted = st.form_submit_button("🏃 记录完成", type="primary", use_container_width=True)
            if submitted:
                save_workout_record(
                    exercise_id=-1,
                    record_date=workout["date"],
                    completed_sets=1,
                    completed_reps=duration,
                    is_done=1,
                    note=note,
                )
                st.success("已记录！")
                st.rerun()


def _render_strength_day(workout):
    """渲染力量训练日。"""
    exercises = workout["exercises"]
    prog = workout["progression"]
    recommended_sets = prog["sets"]

    if not exercises:
        st.warning("该训练类型暂无动作数据。")
        return

    st.subheader(f"今日动作（{len(exercises)} 个动作，每组 {recommended_sets} 组）")

    today_records = get_workout_records(workout["date"])
    done_ids = {r["exercise_id"] for r in today_records if r["is_done"]}

    all_done = len(exercises) > 0 and all(e["id"] in done_ids for e in exercises)

    if all_done:
        st.success("✅ 今日训练全部完成！")
    else:
        remaining = sum(1 for e in exercises if e["id"] not in done_ids)
        st.info(f"剩余 {remaining} 个动作未完成")

    for ex in exercises:
        is_done = ex["id"] in done_ids
        existing_record = next((r for r in today_records if r["exercise_id"] == ex["id"]), None)

        with st.container(border=True):
            col_name, col_status = st.columns([3, 1])
            with col_name:
                st.markdown(f"**{ex['name']}**  —  {ex['muscle_group']}  |  {ex['equipment']}")
                st.caption(f"{ex['description']}")
            with col_status:
                if is_done:
                    st.success("已完成 ✅")

            if is_done:
                if st.button("🔄 修改", key=f"edit_{ex['id']}", use_container_width=True):
                    st.session_state[f"edit_ex_{ex['id']}"] = True

            if not is_done or st.session_state.get(f"edit_ex_{ex['id']}", False):
                with st.form(key=f"form_{ex['id']}"):
                    cols = st.columns(3)
                    with cols[0]:
                        rec_sets = existing_record["completed_sets"] if existing_record else recommended_sets
                        sets = st.number_input("完成组数", min_value=0, max_value=10, value=rec_sets, step=1)
                    with cols[1]:
                        rec_reps = existing_record["completed_reps"] if existing_record else ""
                        reps = st.text_input("每组次数", value=rec_reps, placeholder=f"推荐 {prog['rep_label']}")
                    with cols[2]:
                        rec_note = existing_record["note"] if existing_record else ""
                        note = st.text_input("备注", value=rec_note, placeholder="如：力竭、减重")
                    submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)
                    if submitted:
                        save_workout_record(
                            exercise_id=ex["id"],
                            record_date=workout["date"],
                            completed_sets=sets,
                            completed_reps=reps,
                            is_done=1,
                            note=note,
                        )
                        st.session_state.pop(f"edit_ex_{ex['id']}", None)
                        st.success(f"{ex['name']} 已记录！")
                        st.rerun()

    st.divider()

    # 一键全部完成
    if not all_done:
        if st.button("✅ 全部标记完成", type="primary", use_container_width=True):
            for ex in exercises:
                save_workout_record(
                    exercise_id=ex["id"],
                    record_date=workout["date"],
                    completed_sets=recommended_sets,
                    completed_reps=prog["rep_label"],
                    is_done=1,
                    note="",
                )
            st.success("全部记录完成！")
            st.rerun()


def _week_tab():
    """本周计划查看面板。"""
    today = date.today()
    week_no, week_start, week_end = get_workout_week(today)
    prog = get_progression(week_no)

    st.subheader(f"第 {week_no} 周 ({prog['level_name']})")
    st.caption(f"{week_start.isoformat()} ~ {week_end.isoformat()}")

    week_records = get_week_records(today)
    records_by_date = {}
    for r in week_records:
        records_by_date.setdefault(r["record_date"], []).append(r)

    cols = st.columns(7)
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_type = WEEKLY_PLAN.get(d.weekday())
        day_name = ["一", "二", "三", "四", "五", "六", "日"][d.weekday()]
        is_today = d == today

        with cols[i]:
            if is_today:
                st.markdown(f"**{day_name}**")
            else:
                st.markdown(f"{day_name}")

            st.caption(d.strftime("%m/%d"))

            if day_type is None:
                st.markdown("🧘 休")
            elif day_type == "cardio":
                done = d.isoformat() in records_by_date
                if done:
                    st.markdown("🏃 ✅")
                else:
                    st.markdown("🏃")
            else:
                day_exercises = records_by_date.get(d.isoformat(), [])
                done_count = sum(1 for e in day_exercises if e["is_done"])
                total = _get_exercise_count_for_day_type(day_type)
                if done_count >= total:
                    st.markdown("💪 ✅")
                elif done_count > 0:
                    st.markdown(f"💪 {done_count}/{total}")
                else:
                    st.markdown("💪")


def _get_exercise_count_for_day_type(day_type):
    """获取某训练类型的动作数量。"""
    from src.fitness_service import get_exercises_by_day_type
    return len(get_exercises_by_day_type(day_type))


def _history_tab():
    """训练记录查看面板。"""
    st.subheader("训练记录")

    days = st.slider("查看最近几天", min_value=7, max_value=90, value=30, step=1)
    history = get_workout_history(limit=days * 10)

    if not history:
        st.info("暂无训练记录。开始训练吧！")
        return

    # 按日期分组
    grouped = {}
    for r in history:
        grouped.setdefault(r["record_date"], []).append(r)

    stats = get_workout_stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("总训练天数", stats["total_workouts"])
    col2.metric("本周", f"{stats['this_week_workouts']}/{stats['this_week_target']} 天")
    col3.metric("连续训练", f"{stats['streak']} 天")

    st.divider()

    for rec_date in sorted(grouped.keys(), reverse=True):
        records = grouped[rec_date]
        day_date = date.fromisoformat(rec_date)
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][day_date.weekday()]
        day_type = get_day_type(day_date)
        type_name = DAY_TYPE_NAMES.get(day_type, "休息日")
        done = sum(1 for r in records if r["is_done"])
        total = len(records)

        with st.expander(f"{rec_date} {weekday}  —  {type_name}  ({done}/{total})", expanded=False):
            for r in records:
                st.markdown(
                    f"{'✅' if r['is_done'] else '⬜'} **{r['name']}**  "
                    f"| {r['completed_sets']} 组 × {r['completed_reps']} "
                    f"{'| ' + r['note'] if r['note'] else ''}"
                )


def _settings_tab():
    """健身设置面板。"""
    st.subheader("⚙️ 健身设置")

    start = get_start_date()
    st.markdown(f"**计划开始日期：** {start.isoformat()}")

    week_no, _, _ = get_workout_week()
    st.markdown(f"**当前进度：** 第 {week_no} 周")

    st.divider()
    st.markdown("**每周训练安排**")
    schedule_data = [
        ("周一", "拉力日 (Pull)", "背部、二头"),
        ("周二", "推力日 (Push)", "胸部、肩部、三头"),
        ("周三", "腿部日 (Legs)", "腿部、臀部"),
        ("周四", "休息日", "恢复"),
        ("周五", "拉力日 (Pull)", "背部、二头"),
        ("周六", "推力日 (Push)", "胸部、肩部、三头"),
        ("周日", "跑步日", "户外有氧"),
    ]
    for day, plan, focus in schedule_data:
        st.markdown(f"- **{day}**：{plan}（{focus}）")

    st.divider()
    st.markdown("**进阶路线**")
    st.markdown("""
    - **第 1-2 周**：适应期，2 组 × 8-10 次，轻重量找发力感
    - **第 3-4 周**：基础期，3 组 × 10-12 次，逐步加重
    - **第 5-6 周**：提升期，3 组 × 12-15 次，中等重量
    - **第 7-8 周**：强化期，4 组 × 10-12 次，大重量低次数
    - **第 9+ 周**：维持期，4 组 × 12-15 次，自由调整
    """)

    if st.button("🔄 重置开始日期为今天", type="secondary"):
        from src.db import get_connection
        conn = get_connection()
        conn.execute(
            "UPDATE fitness_settings SET value = ? WHERE key = 'start_date'",
            (date.today().isoformat(),),
        )
        conn.commit()
        conn.close()
        st.success(f"开始日期已重置为 {date.today().isoformat()}")
        st.rerun()


if __name__ == "__main__":
    main()
