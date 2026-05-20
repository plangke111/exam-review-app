"""
每日复习任务生成模块。
实现选题优先级排序 + 章节分散轮询算法。
"""

from collections import defaultdict
from datetime import date
from src.db import get_connection
from src.services import get_pending_tasks_before_date


def select_balanced_by_chapter(candidates, limit=5):
    """
    从候选错题列表中按章节分散轮询选出 limit 道题。
    candidates: [(mistake_id, chapter_id, priority_layer), ...]
    返回: [mistake_id, ...]
    """
    if not candidates:
        return []

    # 按章节分组，保持每组内部顺序（即保持优先级）
    chapter_groups = defaultdict(list)
    for m_id, ch_id, layer in candidates:
        chapter_groups[ch_id or 0].append(m_id)

    selected = []
    chapter_ids = list(chapter_groups.keys())
    indices = {ch: 0 for ch in chapter_ids}

    # 轮询选取
    while len(selected) < limit:
        added_this_round = False
        for ch_id in chapter_ids:
            if indices[ch_id] < len(chapter_groups[ch_id]):
                selected.append(chapter_groups[ch_id][indices[ch_id]])
                indices[ch_id] += 1
                added_this_round = True
                if len(selected) >= limit:
                    break
        if not added_this_round:
            break  # 所有章节的题都选完了

    return selected


def generate_daily_tasks(task_date=None):
    """
    为指定日期生成每日复习任务。
    每个科目最多生成 5 题，按优先级 + 章节分散规则选取。
    返回: { subject_name: [mistake_id, ...], ... }
    """
    if task_date is None:
        task_date = date.today().isoformat()

    conn = get_connection()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY sort_order").fetchall()
    result = {}

    for subj in subjects:
        subj_id = subj["id"]

        # 检查当天是否已有该科目任务
        existing = conn.execute(
            "SELECT COUNT(*) as cnt FROM daily_tasks WHERE task_date = ? AND subject_id = ?",
            (task_date, subj_id),
        ).fetchone()
        if existing["cnt"] > 0:
            # 该科目今日已有任务，跳过生成
            continue

        selected_ids = set()
        candidates_all = []  # (mistake_id, chapter_id, layer)

        # === Layer 1: 延期未完成题（task_date < today 的 pending/postponed） ===
        overdue = conn.execute(
            """SELECT DISTINCT m.id, m.chapter_id
               FROM daily_tasks dt
               JOIN mistakes m ON dt.mistake_id = m.id
               WHERE dt.task_date < ? AND dt.status IN ('pending', 'postponed')
                 AND dt.subject_id = ? AND m.is_mastered = 0
               ORDER BY dt.task_date ASC""",
            (task_date, subj_id),
        ).fetchall()
        for row in overdue:
            if row["id"] not in selected_ids:
                candidates_all.append((row["id"], row["chapter_id"], 1))
                selected_ids.add(row["id"])

        # === Layer 2: 收藏且未熟练题 ===
        favorites = conn.execute(
            """SELECT id, chapter_id FROM mistakes
               WHERE subject_id = ? AND is_favorite = 1 AND is_mastered = 0
               ORDER BY review_count ASC, last_review_date ASC NULLS FIRST""",
            (subj_id,),
        ).fetchall()
        for row in favorites:
            if row["id"] not in selected_ids:
                candidates_all.append((row["id"], row["chapter_id"], 2))
                selected_ids.add(row["id"])

        # === Layer 3: 到期题（next_review_date <= today） ===
        due = conn.execute(
            """SELECT id, chapter_id FROM mistakes
               WHERE subject_id = ? AND is_mastered = 0
                 AND next_review_date <= ?
               ORDER BY review_count ASC, last_review_date ASC NULLS FIRST""",
            (subj_id, task_date),
        ).fetchall()
        for row in due:
            if row["id"] not in selected_ids:
                candidates_all.append((row["id"], row["chapter_id"], 3))
                selected_ids.add(row["id"])

        # === Layer 4: 复习次数少、最近较久未复习的普通题 ===
        remaining = conn.execute(
            """SELECT id, chapter_id FROM mistakes
               WHERE subject_id = ? AND is_mastered = 0
               ORDER BY review_count ASC, last_review_date ASC NULLS FIRST""",
            (subj_id,),
        ).fetchall()
        for row in remaining:
            if row["id"] not in selected_ids:
                candidates_all.append((row["id"], row["chapter_id"], 4))
                selected_ids.add(row["id"])

        # 章节分散选取
        chosen_ids = select_balanced_by_chapter(candidates_all, limit=5)

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
    """
    重新生成任务：删除当天 pending 和 postponed 的任务后重新生成。
    已完成的任务保留。
    """
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
    # 测试运行
    from src.db import init_db
    init_db()
    result = generate_daily_tasks()
    print("生成结果:", result)
