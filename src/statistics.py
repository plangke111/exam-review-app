"""
统计查询模块。
提供总览统计、按科目统计、按章节统计等查询函数。
"""

from datetime import date
from src.db import get_connection


def get_total_statistics():
    """获取全局统计数据。"""
    conn = get_connection()
    today = date.today().isoformat()

    total = conn.execute("SELECT COUNT(*) as cnt FROM mistakes").fetchone()["cnt"]
    mastered = conn.execute("SELECT COUNT(*) as cnt FROM mistakes WHERE is_mastered = 1").fetchone()["cnt"]
    reviewed = conn.execute("SELECT COUNT(*) as cnt FROM mistakes WHERE review_count > 0").fetchone()["cnt"]
    unreviewed = conn.execute("SELECT COUNT(*) as cnt FROM mistakes WHERE review_count = 0").fetchone()["cnt"]
    favorite = conn.execute("SELECT COUNT(*) as cnt FROM mistakes WHERE is_favorite = 1").fetchone()["cnt"]

    # 今日任务
    today_pending = conn.execute(
        "SELECT COUNT(*) as cnt FROM daily_tasks WHERE task_date = ? AND status IN ('pending', 'postponed')",
        (today,),
    ).fetchone()["cnt"]
    today_done = conn.execute(
        "SELECT COUNT(*) as cnt FROM daily_tasks WHERE task_date = ? AND status = 'done'",
        (today,),
    ).fetchone()["cnt"]

    # 当前需要复习数：
    # 未熟练 且 (今日有 pending 任务 或 有历史延期 或 next_review_date <= today 或 is_favorite=1)
    need_review = conn.execute(
        """SELECT COUNT(DISTINCT m.id) as cnt FROM mistakes m
           WHERE m.is_mastered = 0 AND (
               m.id IN (SELECT mistake_id FROM daily_tasks WHERE task_date <= ? AND status IN ('pending', 'postponed'))
               OR m.next_review_date <= ?
               OR m.is_favorite = 1
           )""",
        (today, today),
    ).fetchone()["cnt"]

    # 延期题数
    postponed = conn.execute(
        """SELECT COUNT(DISTINCT mistake_id) as cnt FROM daily_tasks
           WHERE task_date < ? AND status IN ('pending', 'postponed')""",
        (today,),
    ).fetchone()["cnt"]

    conn.close()
    return {
        "total": total,
        "mastered": mastered,
        "reviewed": reviewed,
        "unreviewed": unreviewed,
        "favorite": favorite,
        "need_review": need_review,
        "today_pending": today_pending,
        "today_done": today_done,
        "postponed": postponed,
    }


def get_subject_statistics():
    """按科目统计。"""
    conn = get_connection()
    today = date.today().isoformat()

    subjects = conn.execute("SELECT * FROM subjects ORDER BY sort_order").fetchall()
    result = []
    for subj in subjects:
        sid = subj["id"]
        total = conn.execute("SELECT COUNT(*) as cnt FROM mistakes WHERE subject_id = ?", (sid,)).fetchone()["cnt"]
        mastered = conn.execute(
            "SELECT COUNT(*) as cnt FROM mistakes WHERE subject_id = ? AND is_mastered = 1", (sid,)
        ).fetchone()["cnt"]
        reviewed = conn.execute(
            "SELECT COUNT(*) as cnt FROM mistakes WHERE subject_id = ? AND review_count > 0", (sid,)
        ).fetchone()["cnt"]
        favorite = conn.execute(
            "SELECT COUNT(*) as cnt FROM mistakes WHERE subject_id = ? AND is_favorite = 1", (sid,)
        ).fetchone()["cnt"]
        today_tasks = conn.execute(
            "SELECT COUNT(*) as cnt FROM daily_tasks WHERE subject_id = ? AND task_date = ?", (sid, today)
        ).fetchone()["cnt"]
        today_done = conn.execute(
            "SELECT COUNT(*) as cnt FROM daily_tasks WHERE subject_id = ? AND task_date = ? AND status = 'done'",
            (sid, today),
        ).fetchone()["cnt"]

        # 需要复习数
        need_review = conn.execute(
            """SELECT COUNT(DISTINCT m.id) as cnt FROM mistakes m
               WHERE m.subject_id = ? AND m.is_mastered = 0 AND (
                   m.id IN (SELECT mistake_id FROM daily_tasks WHERE task_date <= ? AND status IN ('pending', 'postponed'))
                   OR m.next_review_date <= ?
                   OR m.is_favorite = 1
               )""",
            (sid, today, today),
        ).fetchone()["cnt"]

        result.append({
            "subject_id": sid,
            "subject_name": subj["name"],
            "category": subj["category"],
            "total": total,
            "mastered": mastered,
            "reviewed": reviewed,
            "favorite": favorite,
            "need_review": need_review,
            "today_tasks": today_tasks,
            "today_done": today_done,
        })
    conn.close()
    return result


def get_chapter_statistics(subject_id=None):
    """按章节统计。"""
    conn = get_connection()
    today = date.today().isoformat()

    query = """
        SELECT c.id as chapter_id, c.name as chapter_name, c.subject_id,
               s.name as subject_name,
               COUNT(m.id) as total,
               SUM(CASE WHEN m.review_count > 0 THEN 1 ELSE 0 END) as reviewed,
               SUM(CASE WHEN m.review_count = 0 THEN 1 ELSE 0 END) as unreviewed,
               SUM(CASE WHEN m.is_mastered = 1 THEN 1 ELSE 0 END) as mastered,
               SUM(CASE WHEN m.is_favorite = 1 THEN 1 ELSE 0 END) as favorite
        FROM chapters c
        JOIN subjects s ON c.subject_id = s.id
        LEFT JOIN mistakes m ON c.id = m.chapter_id
    """
    params = []
    if subject_id:
        query += " WHERE c.subject_id = ?"
        params.append(subject_id)
    query += " GROUP BY c.id ORDER BY s.sort_order, c.id"

    rows = conn.execute(query, params).fetchall()

    # 为每个章节补充待复习数
    result = []
    for row in rows:
        ch_id = row["chapter_id"]
        need_review = conn.execute(
            """SELECT COUNT(DISTINCT m.id) as cnt FROM mistakes m
               WHERE m.chapter_id = ? AND m.is_mastered = 0 AND (
                   m.id IN (SELECT mistake_id FROM daily_tasks WHERE task_date <= ? AND status IN ('pending', 'postponed'))
                   OR m.next_review_date <= ?
                   OR m.is_favorite = 1
               )""",
            (ch_id, today, today),
        ).fetchone()["cnt"]

        result.append({
            "chapter_id": row["chapter_id"],
            "chapter_name": row["chapter_name"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "total": row["total"] or 0,
            "reviewed": row["reviewed"] or 0,
            "unreviewed": row["unreviewed"] or 0,
            "mastered": row["mastered"] or 0,
            "favorite": row["favorite"] or 0,
            "need_review": need_review,
        })
    conn.close()
    return result


def get_due_mistakes(today=None):
    """获取当前需要复习的错题列表。"""
    if today is None:
        today = date.today().isoformat()
    conn = get_connection()
    rows = conn.execute(
        """SELECT DISTINCT m.*, s.name as subject_name, c.name as chapter_name
           FROM mistakes m
           LEFT JOIN subjects s ON m.subject_id = s.id
           LEFT JOIN chapters c ON m.chapter_id = c.id
           WHERE m.is_mastered = 0 AND (
               m.id IN (SELECT mistake_id FROM daily_tasks WHERE task_date <= ? AND status IN ('pending', 'postponed'))
               OR m.next_review_date <= ?
               OR m.is_favorite = 1
           )
           ORDER BY s.sort_order, m.id""",
        (today, today),
    ).fetchall()
    conn.close()
    return rows


def get_reviewed_mistakes():
    """获取已复习过的错题列表。"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, s.name as subject_name, c.name as chapter_name
           FROM mistakes m
           LEFT JOIN subjects s ON m.subject_id = s.id
           LEFT JOIN chapters c ON m.chapter_id = c.id
           WHERE m.review_count > 0
           ORDER BY m.last_review_date DESC"""
    ).fetchall()
    conn.close()
    return rows


def get_unreviewed_mistakes():
    """获取从未复习过的错题列表。"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, s.name as subject_name, c.name as chapter_name
           FROM mistakes m
           LEFT JOIN subjects s ON m.subject_id = s.id
           LEFT JOIN chapters c ON m.chapter_id = c.id
           WHERE m.review_count = 0
           ORDER BY s.sort_order, m.id"""
    ).fetchall()
    conn.close()
    return rows


def get_mistakes_by_filter(subject_id=None, chapter_id=None, is_favorite=None,
                           is_mastered=None, is_due=None, is_reviewed=None):
    """
    综合筛选错题列表。
    is_due: True=需要复习(未熟练且到期/延期/收藏), False=不需要复习
    is_reviewed: True=已复习过, False=从未复习过
    """
    conn = get_connection()
    today = date.today().isoformat()

    conditions = []
    params = []

    if subject_id:
        conditions.append("m.subject_id = ?")
        params.append(subject_id)
    if chapter_id:
        conditions.append("m.chapter_id = ?")
        params.append(chapter_id)
    if is_favorite is not None:
        conditions.append("m.is_favorite = ?")
        params.append(int(is_favorite))
    if is_mastered is not None:
        conditions.append("m.is_mastered = ?")
        params.append(int(is_mastered))
    if is_due is True:
        conditions.append("""m.is_mastered = 0 AND (
            m.id IN (SELECT mistake_id FROM daily_tasks WHERE task_date <= ? AND status IN ('pending', 'postponed'))
            OR m.next_review_date <= ?
            OR m.is_favorite = 1
        )""")
        params.extend([today, today])
    elif is_due is False:
        conditions.append("""NOT (m.is_mastered = 0 AND (
            m.id IN (SELECT mistake_id FROM daily_tasks WHERE task_date <= ? AND status IN ('pending', 'postponed'))
            OR m.next_review_date <= ?
            OR m.is_favorite = 1
        ))""")
        params.extend([today, today])
    if is_reviewed is True:
        conditions.append("m.review_count > 0")
    elif is_reviewed is False:
        conditions.append("m.review_count = 0")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT m.*, s.name as subject_name, c.name as chapter_name
        FROM mistakes m
        LEFT JOIN subjects s ON m.subject_id = s.id
        LEFT JOIN chapters c ON m.chapter_id = c.id
        {where}
        ORDER BY s.sort_order, m.id
    """
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
