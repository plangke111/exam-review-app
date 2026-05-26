"""
每日复习任务生成模块。
实现选题优先级排序 + 章节/题号/题型 三维分散轮询算法。
"""

import random
from collections import defaultdict
from datetime import date
from src.db import get_connection
from src.services import get_pending_tasks_before_date


def select_balanced_by_chapter(candidates, limit=5):
    """
    从候选错题列表中选出 limit 道题。
    优先保证章节分散（同一天尽量不重复选同一章），章节内题型/题号随机。

    candidates: [(mistake_id, chapter_id, priority_layer, ...), ...]
    返回: [mistake_id, ...]
    """
    if not candidates:
        return []

    # 按章节分组
    chapter_groups = defaultdict(list)
    for item in candidates:
        ch_id = item[1] if item[1] is not None else 0
        chapter_groups[ch_id].append(item)

    # 各章节内随机打乱（保证题型、题号随机）
    for ch_id in chapter_groups:
        random.shuffle(chapter_groups[ch_id])

    selected = []
    selected_ids = set()
    chapter_queue = list(chapter_groups.keys())
    chapter_pos = {ch: 0 for ch in chapter_queue}
    used_chapters = set()

    while len(selected) < limit:
        # 还有候选题的章节
        available = [
            ch for ch in chapter_queue
            if chapter_pos[ch] < len(chapter_groups[ch])
        ]
        if not available:
            break

        # 优先选本轮还没用过的章节
        fresh = [ch for ch in available if ch not in used_chapters]
        if fresh:
            ch = random.choice(fresh)
        else:
            ch = random.choice(available)
            used_chapters.clear()

        item = chapter_groups[ch][chapter_pos[ch]]
        chapter_pos[ch] += 1
        used_chapters.add(ch)

        m_id = item[0]
        if m_id not in selected_ids:
            selected.append(m_id)
            selected_ids.add(m_id)

    return selected


def generate_daily_tasks(task_date=None):
    """
    为指定日期生成每日复习任务。
    每个科目最多生成 5 题，按优先级 + 章节/题号/题型分散选取。
    返回: { subject_name: [mistake_id, ...], ... }
    """
    if task_date is None:
        task_date = date.today().isoformat()

    conn = get_connection()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY sort_order").fetchall()
    result = {}

    for subj in subjects:
        subj_id = subj["id"]

        # 检查当天是否已有该科目的 pending/postponed 任务
        pending_count = conn.execute(
            """SELECT COUNT(*) as cnt FROM daily_tasks
               WHERE task_date = ? AND subject_id = ? AND status IN ('pending', 'postponed')""",
            (task_date, subj_id),
        ).fetchone()["cnt"]
        if pending_count > 0:
            continue

        # 已完成题数，计算剩余槽位
        done_count = conn.execute(
            """SELECT COUNT(*) as cnt FROM daily_tasks
               WHERE task_date = ? AND subject_id = ? AND status = 'done'""",
            (task_date, subj_id),
        ).fetchone()["cnt"]
        remaining_slots = max(0, 5 - done_count)
        if remaining_slots == 0:
            continue

        selected_ids = set()
        candidates_all = []  # (mistake_id, chapter_id, layer, question_number, question_type)

        # ── Layer 1: 延期未完成题 ──
        overdue = conn.execute(
            """SELECT DISTINCT m.id, m.chapter_id, m.question_number, m.question_type
               FROM daily_tasks dt
               JOIN mistakes m ON dt.mistake_id = m.id
               WHERE dt.task_date < ? AND dt.status IN ('pending', 'postponed')
                 AND dt.subject_id = ? AND m.is_mastered = 0
               ORDER BY dt.task_date ASC""",
            (task_date, subj_id),
        ).fetchall()
        for row in overdue:
            if row["id"] not in selected_ids:
                candidates_all.append((
                    row["id"], row["chapter_id"], 1,
                    row["question_number"], row["question_type"] or "",
                ))
                selected_ids.add(row["id"])

        # ── Layer 2: 收藏且未熟练题 ──
        favorites = conn.execute(
            """SELECT id, chapter_id, question_number, question_type FROM mistakes
               WHERE subject_id = ? AND is_favorite = 1 AND is_mastered = 0
               ORDER BY review_count ASC, last_review_date ASC NULLS FIRST""",
            (subj_id,),
        ).fetchall()
        for row in favorites:
            if row["id"] not in selected_ids:
                candidates_all.append((
                    row["id"], row["chapter_id"], 2,
                    row["question_number"], row["question_type"] or "",
                ))
                selected_ids.add(row["id"])

        # ── Layer 3: 到期题（next_review_date <= today） ──
        due = conn.execute(
            """SELECT id, chapter_id, question_number, question_type FROM mistakes
               WHERE subject_id = ? AND is_mastered = 0
                 AND next_review_date <= ?
               ORDER BY review_count ASC, last_review_date ASC NULLS FIRST""",
            (subj_id, task_date),
        ).fetchall()
        for row in due:
            if row["id"] not in selected_ids:
                candidates_all.append((
                    row["id"], row["chapter_id"], 3,
                    row["question_number"], row["question_type"] or "",
                ))
                selected_ids.add(row["id"])

        # ── Layer 4: 复习次数少 / 久未复习的普通题 ──
        remaining = conn.execute(
            """SELECT id, chapter_id, question_number, question_type FROM mistakes
               WHERE subject_id = ? AND is_mastered = 0
               ORDER BY review_count ASC, last_review_date ASC NULLS FIRST""",
            (subj_id,),
        ).fetchall()
        for row in remaining:
            if row["id"] not in selected_ids:
                candidates_all.append((
                    row["id"], row["chapter_id"], 4,
                    row["question_number"], row["question_type"] or "",
                ))
                selected_ids.add(row["id"])

        # 三维分散选取
        chosen_ids = select_balanced_by_chapter(candidates_all, limit=remaining_slots)

        # 写入 daily_tasks
        for m_id in chosen_ids:
            conn.execute(
                """INSERT OR IGNORE INTO daily_tasks (task_date, mistake_id, subject_id)
                   VALUES (?, ?, ?)""",
                (task_date, m_id, subj_id),
            )

        result[subj["name"]] = chosen_ids

    conn.commit()
    conn.close()
    return result


def regenerate_daily_tasks(task_date=None):
    """重新生成任务：删除当天 pending / postponed 后重新生成，已完成保留。"""
    if task_date is None:
        task_date = date.today().isoformat()

    conn = get_connection()
    conn.execute(
        "DELETE FROM daily_tasks WHERE task_date = ? AND status != 'done'",
        (task_date,),
    )
    conn.commit()
    conn.close()

    return generate_daily_tasks(task_date)


if __name__ == "__main__":
    from src.db import init_db
    init_db()
    result = generate_daily_tasks()
    print("生成结果:", result)
