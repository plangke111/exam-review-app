"""
CSV 导入导出与数据库备份模块。
"""

import csv
import io
import shutil
import os
from datetime import date, datetime
from src.db import DB_PATH, get_connection
from src.services import create_mistake, get_all_subjects, get_chapters_by_subject


def export_mistakes_csv():
    """导出全部错题为 CSV 字符串。"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.title, s.name as subject_name, c.name as chapter_name,
                  m.content, m.wrong_reason, m.solution, m.knowledge_points,
                  m.source, m.difficulty, m.is_favorite, m.is_mastered,
                  m.created_at, m.last_review_date, m.next_review_date,
                  m.review_count, m.wrong_count, m.note
           FROM mistakes m
           LEFT JOIN subjects s ON m.subject_id = s.id
           LEFT JOIN chapters c ON m.chapter_id = c.id
           ORDER BY s.sort_order, m.id"""
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "题目标题", "科目", "章节", "题目内容", "错误原因", "正确解法",
        "关键知识点", "来源", "难度", "是否收藏", "是否熟练",
        "创建日期", "最近复习日期", "下次复习日期", "复习次数", "错误次数", "备注"
    ])
    for r in rows:
        writer.writerow([
            r["title"], r["subject_name"], r["chapter_name"], r["content"],
            r["wrong_reason"], r["solution"], r["knowledge_points"],
            r["source"], r["difficulty"], r["is_favorite"], r["is_mastered"],
            r["created_at"], r["last_review_date"], r["next_review_date"],
            r["review_count"], r["wrong_count"], r["note"],
        ])
    return output.getvalue()


def import_mistakes_csv(csv_content: str):
    """
    从 CSV 字符串导入错题。
    返回 (success_count, errors_list)。
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    success = 0
    errors = []

    # 预加载科目和章节映射，复用同一连接
    conn = get_connection()
    subjects = {s["name"]: s["id"] for s in conn.execute("SELECT * FROM subjects").fetchall()}
    chapters_map = {}  # (subject_id, chapter_name) -> chapter_id
    all_chapters = conn.execute("SELECT * FROM chapters").fetchall()
    for ch in all_chapters:
        chapters_map[(ch["subject_id"], ch["name"])] = ch["id"]

    for i, row in enumerate(reader, start=2):
        try:
            title = (row.get("题目标题") or "").strip()
            if not title:
                errors.append(f"第 {i} 行：题目标题不能为空，已跳过")
                continue

            subject_name = (row.get("科目") or "").strip()
            if subject_name not in subjects:
                errors.append(f"第 {i} 行：未知科目 '{subject_name}'，已跳过")
                continue
            subject_id = subjects[subject_name]

            chapter_name = (row.get("章节") or "").strip()
            chapter_id = None
            if chapter_name:
                key = (subject_id, chapter_name)
                if key in chapters_map:
                    chapter_id = chapters_map[key]
                else:
                    # 在复用连接上创建章节
                    cur = conn.execute(
                        "INSERT INTO chapters (subject_id, name) VALUES (?, ?)",
                        (subject_id, chapter_name),
                    )
                    chapter_id = cur.lastrowid
                    chapters_map[key] = chapter_id

            data = {
                "subject_id": subject_id,
                "chapter_id": chapter_id,
                "title": title,
                "content": (row.get("题目内容") or "").strip(),
                "wrong_reason": (row.get("错误原因") or "").strip(),
                "solution": (row.get("正确解法") or "").strip(),
                "knowledge_points": (row.get("关键知识点") or "").strip(),
                "source": (row.get("来源") or "").strip(),
                "difficulty": (row.get("难度") or "中等").strip(),
                "is_favorite": 1 if str(row.get("是否收藏", "0")).strip() in ("1", "True", "是") else 0,
                "is_mastered": 1 if str(row.get("是否熟练", "0")).strip() in ("1", "True", "是") else 0,
                "note": (row.get("备注") or "").strip(),
                "next_review_date": (row.get("下次复习日期") or "").strip() or None,
            }
            if data["difficulty"] not in ("简单", "中等", "困难"):
                data["difficulty"] = "中等"

            create_mistake(data)
            success += 1
        except Exception as e:
            errors.append(f"第 {i} 行：导入失败 ({str(e)})，已跳过")

    conn.commit()
    conn.close()
    return success, errors


def export_review_records_csv():
    """导出复习记录为 CSV 字符串。"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT rr.review_date, m.title, s.name as subject_name,
                  rr.is_completed, rr.is_correct, rr.marked_mastered, rr.note
           FROM review_records rr
           JOIN mistakes m ON rr.mistake_id = m.id
           JOIN subjects s ON m.subject_id = s.id
           ORDER BY rr.review_date DESC"""
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "复习日期", "题目标题", "科目", "是否完成", "是否答对", "是否标记熟练", "备注"
    ])
    for r in rows:
        writer.writerow([
            r["review_date"], r["title"], r["subject_name"],
            r["is_completed"], r["is_correct"], r["marked_mastered"], r["note"],
        ])
    return output.getvalue()


def backup_database():
    """备份数据库并返回备份文件路径。"""
    backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"review_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path
