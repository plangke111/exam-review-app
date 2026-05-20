"""
数据库初始化与连接管理模块。
负责创建 SQLite 数据库、建表、插入初始科目数据。
"""

import sqlite3
import os
import sys
from datetime import datetime


def _get_base_dir():
    """获取应用根目录，兼容 PyInstaller 打包和正常 Python 运行。"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，exe 所在目录
        return os.path.dirname(sys.executable)
    else:
        # 正常 Python 运行，本文件在 src/ 下，根目录是上级
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = _get_base_dir()
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "review.db")


def get_connection():
    """获取数据库连接，自动创建 data 目录。"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库：建表 + 插入默认科目。如果表已存在则跳过建表。"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS subjects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            category    TEXT    NOT NULL,
            sort_order  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS chapters (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id  INTEGER NOT NULL REFERENCES subjects(id),
            name        TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS mistakes (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id        INTEGER NOT NULL REFERENCES subjects(id),
            chapter_id        INTEGER REFERENCES chapters(id),
            title             TEXT    NOT NULL,
            content           TEXT    DEFAULT '',
            wrong_reason      TEXT    DEFAULT '',
            solution          TEXT    DEFAULT '',
            knowledge_points  TEXT    DEFAULT '',
            source            TEXT    DEFAULT '',
            difficulty        TEXT    DEFAULT '中等',
            is_favorite       INTEGER DEFAULT 0,
            is_mastered       INTEGER DEFAULT 0,
            created_at        TEXT    NOT NULL DEFAULT (date('now')),
            updated_at        TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            last_review_date  TEXT,
            next_review_date  TEXT,
            review_count      INTEGER DEFAULT 0,
            wrong_count       INTEGER DEFAULT 0,
            note              TEXT    DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS daily_tasks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            task_date    TEXT    NOT NULL,
            mistake_id   INTEGER NOT NULL REFERENCES mistakes(id),
            subject_id   INTEGER NOT NULL REFERENCES subjects(id),
            status       TEXT    NOT NULL DEFAULT 'pending',
            is_completed INTEGER DEFAULT 0,
            is_correct   INTEGER DEFAULT 1,
            created_at   TEXT    DEFAULT (datetime('now','localtime')),
            completed_at TEXT,
            UNIQUE(task_date, mistake_id)
        );

        CREATE TABLE IF NOT EXISTS review_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            mistake_id      INTEGER NOT NULL REFERENCES mistakes(id),
            review_date     TEXT    NOT NULL,
            is_completed    INTEGER DEFAULT 1,
            is_correct      INTEGER DEFAULT 1,
            marked_mastered INTEGER DEFAULT 0,
            note            TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now','localtime'))
        );
    """)

    # 插入默认科目（如已存在则忽略）
    default_subjects = [
        ("高等数学", "数学课", 1),
        ("线性代数", "数学课", 2),
        ("概率论",   "数学课", 3),
        ("数字电子技术", "专业课", 4),
    ]
    for name, category, sort_order in default_subjects:
        cursor.execute(
            "INSERT OR IGNORE INTO subjects (name, category, sort_order) VALUES (?, ?, ?)",
            (name, category, sort_order),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"数据库已初始化: {DB_PATH}")
