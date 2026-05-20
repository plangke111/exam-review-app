"""
业务逻辑服务层，封装所有数据库 CRUD 操作。
"""

import os
from datetime import date
from src.db import get_connection
from src.utils import get_ebbinghaus_interval


# ==================== 科目 ====================

def get_all_subjects():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM subjects ORDER BY sort_order").fetchall()
    conn.close()
    return rows


def get_subject_by_id(subject_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    conn.close()
    return row


# ==================== 章节 ====================

def create_chapter(subject_id, name, description=""):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO chapters (subject_id, name, description) VALUES (?, ?, ?)",
        (subject_id, name, description),
    )
    conn.commit()
    chapter_id = cur.lastrowid
    conn.close()
    return chapter_id


def get_chapters_by_subject(subject_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM chapters WHERE subject_id = ? ORDER BY id", (subject_id,)
    ).fetchall()
    conn.close()
    return rows


def get_all_chapters():
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.*, s.name as subject_name
           FROM chapters c JOIN subjects s ON c.subject_id = s.id
           ORDER BY s.sort_order, c.id"""
    ).fetchall()
    conn.close()
    return rows


def get_chapter_by_id(chapter_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,)).fetchone()
    conn.close()
    return row


def delete_chapter(chapter_id):
    conn = get_connection()
    # 检查章节下是否有错题
    count = conn.execute(
        "SELECT COUNT(*) as cnt FROM mistakes WHERE chapter_id = ?", (chapter_id,)
    ).fetchone()["cnt"]
    if count > 0:
        conn.close()
        return False, f"该章节下有 {count} 道错题，请先迁移或删除错题后再删除章节。"
    conn.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
    conn.commit()
    conn.close()
    return True, "章节已删除。"


def update_chapter(chapter_id, name=None, description=None):
    conn = get_connection()
    if name is not None:
        conn.execute("UPDATE chapters SET name = ? WHERE id = ?", (name, chapter_id))
    if description is not None:
        conn.execute("UPDATE chapters SET description = ? WHERE id = ?", (description, chapter_id))
    conn.commit()
    conn.close()


# ==================== 错题 ====================

def create_mistake(data: dict) -> int:
    """新增错题，data 为字段字典，返回新错题 ID。"""
    conn = get_connection()
    fields = [
        "subject_id", "chapter_id", "title", "content", "wrong_reason",
        "solution", "knowledge_points", "source", "difficulty",
        "is_favorite", "is_mastered", "note", "next_review_date", "image_path",
    ]
    values = {k: data.get(k, "") for k in fields}
    values.setdefault("difficulty", "中等")
    values.setdefault("is_favorite", 0)
    values.setdefault("is_mastered", 0)
    # 下次复习日期默认今天，确保新错题立即进入复习池
    if not values.get("next_review_date"):
        values["next_review_date"] = date.today().isoformat()
    # 确保 chapter_id 为整数或 NULL
    if values["chapter_id"] == "" or values["chapter_id"] is None:
        values["chapter_id"] = None

    columns = ", ".join(values.keys())
    placeholders = ", ".join(["?" for _ in values])
    cur = conn.execute(
        f"INSERT INTO mistakes ({columns}) VALUES ({placeholders})",
        list(values.values()),
    )
    conn.commit()
    mistake_id = cur.lastrowid
    conn.close()
    return mistake_id


def update_mistake(mistake_id, data: dict):
    """更新错题字段。"""
    conn = get_connection()
    allowed = [
        "subject_id", "chapter_id", "title", "content", "wrong_reason",
        "solution", "knowledge_points", "source", "difficulty",
        "is_favorite", "is_mastered", "note", "next_review_date", "image_path",
    ]
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        conn.close()
        return
    # 处理 chapter_id
    if "chapter_id" in updates:
        if updates["chapter_id"] == "" or updates["chapter_id"] is None:
            updates["chapter_id"] = None
    updates["updated_at"] = "datetime('now','localtime')"
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    conn.execute(
        f"UPDATE mistakes SET {set_clause} WHERE id = ?",
        list(updates.values()) + [mistake_id],
    )
    conn.commit()
    conn.close()


def delete_mistake(mistake_id):
    """删除错题及其关联的任务、复习记录和图片。"""
    conn = get_connection()
    row = conn.execute("SELECT image_path FROM mistakes WHERE id = ?", (mistake_id,)).fetchone()
    if row and row["image_path"]:
        img = row["image_path"]
        abs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", img)
        if os.path.exists(abs_path):
            os.remove(abs_path)

    conn.execute("DELETE FROM daily_tasks WHERE mistake_id = ?", (mistake_id,))
    conn.execute("DELETE FROM review_records WHERE mistake_id = ?", (mistake_id,))
    conn.execute("DELETE FROM mistakes WHERE id = ?", (mistake_id,))
    conn.commit()
    conn.close()


def get_mistake_by_id(mistake_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT m.*, s.name as subject_name, c.name as chapter_name
           FROM mistakes m
           LEFT JOIN subjects s ON m.subject_id = s.id
           LEFT JOIN chapters c ON m.chapter_id = c.id
           WHERE m.id = ?""",
        (mistake_id,),
    ).fetchone()
    conn.close()
    return row


def query_mistakes(subject_id=None, chapter_id=None, is_favorite=None,
                   is_mastered=None, keyword=None, difficulty=None,
                   source=None, order_by="created_at DESC"):
    """多条件查询错题列表。"""
    conn = get_connection()
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
    if difficulty:
        conditions.append("m.difficulty = ?")
        params.append(difficulty)
    if source:
        conditions.append("m.source = ?")
        params.append(source)
    if keyword:
        conditions.append(
            "(m.title LIKE ? OR m.content LIKE ? OR m.knowledge_points LIKE ? OR m.wrong_reason LIKE ?)"
        )
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw, kw])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    query = f"""
        SELECT m.*, s.name as subject_name, c.name as chapter_name
        FROM mistakes m
        LEFT JOIN subjects s ON m.subject_id = s.id
        LEFT JOIN chapters c ON m.chapter_id = c.id
        {where}
        ORDER BY {order_by}
    """
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def toggle_favorite(mistake_id):
    """切换收藏状态。标记收藏时自动取消熟练，返回新状态。"""
    conn = get_connection()
    cur = conn.execute("SELECT is_favorite, is_mastered FROM mistakes WHERE id = ?", (mistake_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    new_val = 0 if row["is_favorite"] else 1
    if new_val == 1:
        # 收藏时自动取消熟练（互斥）
        conn.execute(
            "UPDATE mistakes SET is_favorite = 1, is_mastered = 0, updated_at = datetime('now','localtime') WHERE id = ?",
            (mistake_id,),
        )
    else:
        conn.execute(
            "UPDATE mistakes SET is_favorite = 0, updated_at = datetime('now','localtime') WHERE id = ?",
            (mistake_id,),
        )
    conn.commit()
    conn.close()
    return new_val


def toggle_mastered(mistake_id):
    """切换熟练状态。标记熟练时自动取消收藏。返回新状态。"""
    conn = get_connection()
    cur = conn.execute("SELECT is_mastered FROM mistakes WHERE id = ?", (mistake_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    new_val = 0 if row["is_mastered"] else 1
    if new_val == 1:
        # 标记熟练时同时取消收藏
        conn.execute(
            "UPDATE mistakes SET is_mastered = 1, is_favorite = 0, updated_at = datetime('now','localtime') WHERE id = ?",
            (mistake_id,),
        )
    else:
        conn.execute(
            "UPDATE mistakes SET is_mastered = 0, updated_at = datetime('now','localtime') WHERE id = ?",
            (mistake_id,),
        )
    conn.commit()
    conn.close()
    return new_val


# ==================== 每日任务 ====================

def get_tasks_by_date(task_date):
    """获取指定日期的所有任务（含错题信息）。"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT dt.*, m.title, m.difficulty, m.is_favorite, m.is_mastered,
                  m.content, m.solution, m.wrong_reason, m.knowledge_points,
                  m.chapter_id, m.image_path,
                  s.name as subject_name, c.name as chapter_name
           FROM daily_tasks dt
           JOIN mistakes m ON dt.mistake_id = m.id
           JOIN subjects s ON dt.subject_id = s.id
           LEFT JOIN chapters c ON m.chapter_id = c.id
           WHERE dt.task_date = ?
           ORDER BY s.sort_order, dt.id""",
        (task_date,),
    ).fetchall()
    conn.close()
    return rows


def get_today_tasks():
    """获取今日任务。"""
    today = date.today().isoformat()
    return get_tasks_by_date(today)


def update_task_status(task_id, status, is_correct=None, marked_mastered=0):
    """更新任务状态，同时自动创建复习记录并更新错题统计。"""
    from datetime import date, timedelta
    conn = get_connection()
    if is_correct is not None:
        conn.execute(
            """UPDATE daily_tasks SET status = ?, is_correct = ?,
               completed_at = datetime('now','localtime') WHERE id = ?""",
            (status, is_correct, task_id),
        )
    elif status == 'done':
        conn.execute(
            """UPDATE daily_tasks SET status = ?,
               completed_at = datetime('now','localtime') WHERE id = ?""",
            (status, task_id),
        )
    else:
        conn.execute("UPDATE daily_tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()

    # 获取任务信息用于更新错题统计和创建复习记录
    task = conn.execute(
        "SELECT mistake_id, subject_id FROM daily_tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if task:
        today = date.today().isoformat()
        is_completed = 1 if status == 'done' else 0
        review_correct = is_correct if is_correct is not None else 1

        # 自动创建复习记录
        conn.execute(
            """INSERT INTO review_records (mistake_id, review_date, is_completed, is_correct, marked_mastered, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (task["mistake_id"], today, is_completed, review_correct, marked_mastered, ""),
        )

        # 更新错题统计（仅实际完成时更新，延期不更新）
        if status == 'done':
            conn.execute(
                "UPDATE mistakes SET review_count = review_count + 1, last_review_date = date('now'), updated_at = datetime('now','localtime') WHERE id = ?",
                (task["mistake_id"],),
            )
            if is_correct == 0:
                # 答错：错误计数+1，重置复习阶段，1天后重试
                conn.execute(
                    "UPDATE mistakes SET wrong_count = wrong_count + 1, review_stage = 0, next_review_date = date('now', '+1 days'), updated_at = datetime('now','localtime') WHERE id = ?",
                    (task["mistake_id"],),
                )
            else:
                # 答对：复习阶段+1，按艾宾浩斯曲线设置下次复习日期
                old_stage = conn.execute(
                    "SELECT review_stage FROM mistakes WHERE id = ?", (task["mistake_id"],)
                ).fetchone()["review_stage"]
                new_stage = (old_stage or 0) + 1
                interval = get_ebbinghaus_interval(new_stage)
                next_date = (date.today() + timedelta(days=interval)).isoformat()
                conn.execute(
                    "UPDATE mistakes SET review_stage = ?, next_review_date = ?, updated_at = datetime('now','localtime') WHERE id = ?",
                    (new_stage, next_date, task["mistake_id"]),
                )
        conn.commit()
    conn.close()


def mark_task_done(task_id, marked_mastered=0):
    """标记任务为已完成。"""
    update_task_status(task_id, 'done', is_correct=1, marked_mastered=marked_mastered)


def mark_task_wrong(task_id):
    """标记任务为仍然错误。"""
    update_task_status(task_id, 'done', is_correct=0)


def postpone_task(task_id):
    """将任务标记为延期。"""
    update_task_status(task_id, 'postponed')


def get_pending_tasks_before_date(target_date):
    """获取指定日期之前未完成的 pending 任务。"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT dt.*, m.title, m.chapter_id, m.is_favorite, m.is_mastered,
                  m.review_count, m.last_review_date, m.next_review_date,
                  s.name as subject_name
           FROM daily_tasks dt
           JOIN mistakes m ON dt.mistake_id = m.id
           JOIN subjects s ON dt.subject_id = s.id
           WHERE dt.task_date < ? AND dt.status IN ('pending', 'postponed')
             AND m.is_mastered = 0
           ORDER BY dt.task_date ASC""",
        (target_date,),
    ).fetchall()
    conn.close()
    return rows


def task_exists_for_date(task_date):
    """检查指定日期是否已有任务。"""
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM daily_tasks WHERE task_date = ?", (task_date,)
    ).fetchone()
    conn.close()
    return row["cnt"] > 0


def get_task_by_id(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM daily_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row


# ==================== 复习记录 ====================

def create_review_record(mistake_id, review_date, is_completed=1, is_correct=1,
                         marked_mastered=0, note=""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO review_records (mistake_id, review_date, is_completed, is_correct, marked_mastered, note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (mistake_id, review_date, is_completed, is_correct, marked_mastered, note),
    )
    conn.commit()
    conn.close()


def get_review_records_by_mistake(mistake_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM review_records WHERE mistake_id = ? ORDER BY review_date DESC",
        (mistake_id,),
    ).fetchall()
    conn.close()
    return rows


def get_review_records_by_date_range(start_date, end_date, subject_id=None):
    conn = get_connection()
    query = """
        SELECT rr.*, m.title, s.name as subject_name
        FROM review_records rr
        JOIN mistakes m ON rr.mistake_id = m.id
        JOIN subjects s ON m.subject_id = s.id
        WHERE rr.review_date BETWEEN ? AND ?
    """
    params = [start_date, end_date]
    if subject_id:
        query += " AND m.subject_id = ?"
        params.append(subject_id)
    query += " ORDER BY rr.review_date DESC, rr.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_all_review_records(limit=200, subject_id=None):
    conn = get_connection()
    query = """
        SELECT rr.*, m.title, s.name as subject_name
        FROM review_records rr
        JOIN mistakes m ON rr.mistake_id = m.id
        JOIN subjects s ON m.subject_id = s.id
    """
    params = []
    if subject_id:
        query += " WHERE m.subject_id = ?"
        params.append(subject_id)
    query += " ORDER BY rr.review_date DESC, rr.created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
