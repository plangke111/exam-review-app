"""
健身计划服务层。
提供周数计算、每日训练内容、训练记录、进度统计等。
"""

from datetime import date, timedelta
from src.db import get_connection


# 一周训练安排：周一~周日
# None = 休息日, "cardio" = 跑步日
WEEKLY_PLAN = {
    0: "pull",    # 周一 拉力
    1: "push",    # 周二 推力
    2: "legs",    # 周三 腿部
    3: None,      # 周四 休息
    4: "pull",    # 周五 拉力
    5: "push",    # 周六 推力
    6: "cardio",  # 周日 跑步
}

DAY_TYPE_NAMES = {
    "pull":   "拉力日",
    "push":   "推力日",
    "legs":   "腿部日",
    "cardio": "跑步日",
    None:     "休息日",
}


def get_start_date():
    """获取健身计划的起始日期。"""
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM fitness_settings WHERE key = 'start_date'"
    ).fetchone()
    conn.close()
    if row:
        return date.fromisoformat(row["value"])
    return date.today()


def get_workout_week(target_date=None):
    """
    计算第几周（从 start_date 所在周算起）。
    返回 (week_number, week_start_date, week_end_date).
    week_number 从 1 开始。
    """
    if target_date is None:
        target_date = date.today()
    start = get_start_date()
    # 将 start 对齐到周一
    start_weekday = start.weekday()
    week_start = start - timedelta(days=start_weekday)

    days_diff = (target_date - week_start).days
    week_number = days_diff // 7 + 1
    if week_number < 1:
        week_number = 1

    current_week_start = week_start + timedelta(weeks=(week_number - 1))
    current_week_end = current_week_start + timedelta(days=6)

    return week_number, current_week_start, current_week_end


def get_progression(week_number):
    """
    根据周数返回推荐训练量。
    返回 dict: sets, rep_label, level_name
    """
    if week_number <= 2:
        return {
            "sets": 2,
            "rep_label": "8-10 次",
            "level_name": "第 1-2 周 · 适应期",
            "level": "adapt",
        }
    elif week_number <= 4:
        return {
            "sets": 3,
            "rep_label": "10-12 次",
            "level_name": "第 3-4 周 · 基础期",
            "level": "basic",
        }
    elif week_number <= 6:
        return {
            "sets": 3,
            "rep_label": "12-15 次",
            "level_name": "第 5-6 周 · 提升期",
            "level": "progress",
        }
    elif week_number <= 8:
        return {
            "sets": 4,
            "rep_label": "10-12 次",
            "level_name": "第 7-8 周 · 强化期",
            "level": "intensify",
        }
    else:
        return {
            "sets": 4,
            "rep_label": "12-15 次",
            "level_name": "第 9+ 周 · 维持期",
            "level": "maintain",
        }


def get_day_type(target_date=None):
    """获取指定日期的训练类型。"""
    if target_date is None:
        target_date = date.today()
    return WEEKLY_PLAN.get(target_date.weekday(), None)


def get_exercises_by_day_type(day_type):
    """
    根据训练类型获取动作列表，按 sort_order 排序。
    day_type: "pull" / "push" / "legs" / "core" / None
    """
    if day_type is None:
        return []
    conn = get_connection()
    if day_type == "cardio":
        # 跑步日返回一条占位记录
        conn.close()
        return [{
            "id": -1,
            "name": "户外跑步",
            "muscle_group": "全身有氧",
            "equipment": "跑鞋",
            "default_sets": 1,
            "default_reps": "30min",
            "day_type": "cardio",
            "description": "匀速跑 30 分钟，心率控制在 140-160",
            "sort_order": 0,
        }]
    rows = conn.execute(
        "SELECT * FROM exercises WHERE day_type = ? ORDER BY sort_order",
        (day_type,),
    ).fetchall()
    conn.close()
    return rows


def get_todays_workout():
    """获取今日完整训练信息。"""
    today = date.today()
    week_no, week_start, week_end = get_workout_week(today)
    day_type = get_day_type(today)
    exercises = get_exercises_by_day_type(day_type)
    progression = get_progression(week_no)

    return {
        "date": today.isoformat(),
        "weekday": today.weekday(),
        "week_no": week_no,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "day_type": day_type,
        "day_type_name": DAY_TYPE_NAMES.get(day_type, "休息日"),
        "exercises": exercises,
        "progression": progression,
        "is_rest_day": day_type is None,
    }


def save_workout_record(exercise_id, record_date, completed_sets, completed_reps, is_done=1, note=""):
    """保存一条训练记录。"""
    conn = get_connection()
    # 检查是否已有记录，有则更新，无则插入
    existing = conn.execute(
        "SELECT id FROM workout_records WHERE exercise_id = ? AND record_date = ?",
        (exercise_id, record_date),
    ).fetchone()
    if existing:
        conn.execute(
            """UPDATE workout_records
               SET completed_sets = ?, completed_reps = ?, is_done = ?, note = ?
               WHERE id = ?""",
            (completed_sets, completed_reps, is_done, note, existing["id"]),
        )
    else:
        conn.execute(
            """INSERT INTO workout_records (record_date, exercise_id, completed_sets, completed_reps, is_done, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (record_date, exercise_id, completed_sets, completed_reps, is_done, note),
        )
    conn.commit()
    conn.close()


def get_workout_records(target_date=None):
    """获取指定日期的训练记录。"""
    if target_date is None:
        target_date = date.today().isoformat()
    if isinstance(target_date, date):
        target_date = target_date.isoformat()
    conn = get_connection()
    rows = conn.execute(
        """SELECT wr.*, e.name, e.muscle_group, e.equipment, e.default_sets, e.default_reps,
                  e.day_type, e.description, e.sort_order
           FROM workout_records wr
           JOIN exercises e ON wr.exercise_id = e.id
           WHERE wr.record_date = ?
           ORDER BY e.sort_order""",
        (target_date,),
    ).fetchall()
    conn.close()
    return rows


def get_week_records(target_date=None):
    """获取目标日期所在周的完整训练记录。"""
    if target_date is None:
        target_date = date.today()
    _, week_start, week_end = get_workout_week(target_date)
    conn = get_connection()
    rows = conn.execute(
        """SELECT wr.*, e.name, e.muscle_group, e.day_type
           FROM workout_records wr
           JOIN exercises e ON wr.exercise_id = e.id
           WHERE wr.record_date >= ? AND wr.record_date <= ?
           ORDER BY wr.record_date, e.sort_order""",
        (week_start.isoformat(), week_end.isoformat()),
    ).fetchall()
    conn.close()
    return rows


def get_workout_history(limit=30):
    """获取最近训练历史。"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT wr.*, e.name, e.muscle_group, e.day_type
           FROM workout_records wr
           JOIN exercises e ON wr.exercise_id = e.id
           ORDER BY wr.record_date DESC, wr.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def get_workout_stats():
    """获取健身统计。"""
    conn = get_connection()
    today = date.today().isoformat()
    week_no, week_start, week_end = get_workout_week()

    total_workouts = conn.execute(
        "SELECT COUNT(DISTINCT record_date) as cnt FROM workout_records WHERE is_done = 1"
    ).fetchone()["cnt"]

    this_week_workouts = conn.execute(
        "SELECT COUNT(DISTINCT record_date) as cnt FROM workout_records WHERE is_done = 1 AND record_date >= ? AND record_date <= ?",
        (week_start.isoformat(), week_end.isoformat()),
    ).fetchone()["cnt"]

    today_done = conn.execute(
        "SELECT COUNT(*) as cnt FROM workout_records WHERE record_date = ? AND is_done = 1",
        (today,),
    ).fetchone()["cnt"]

    streak = _calc_streak(conn)

    conn.close()

    # 本周应训练天数
    week_days = 0
    for i in range(7):
        d = week_start + timedelta(days=i)
        if WEEKLY_PLAN.get(d.weekday()) is not None:
            week_days += 1

    return {
        "total_workouts": total_workouts,
        "this_week_workouts": this_week_workouts,
        "this_week_target": week_days,
        "today_done": today_done,
        "streak": streak,
        "week_no": week_no,
    }


def _calc_streak(conn):
    """计算连续训练天数（从今天向前推）。"""
    streak = 0
    d = date.today()
    for _ in range(365):
        day_type = WEEKLY_PLAN.get(d.weekday())
        if day_type is None:
            d -= timedelta(days=1)
            continue  # 休息日不计入连续
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM workout_records WHERE record_date = ? AND is_done = 1",
            (d.isoformat(),),
        ).fetchone()["cnt"]
        if count > 0:
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak


def get_today_weekday_name():
    """返回今天的中文星期几。"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[date.today().weekday()]
