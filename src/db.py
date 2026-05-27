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
IMAGE_DIR = os.path.join(DB_DIR, "images")


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

    # ==== 健身相关表 ====
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS exercises (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            muscle_group TEXT    NOT NULL,
            equipment    TEXT    DEFAULT '',
            default_sets INTEGER DEFAULT 3,
            default_reps TEXT    DEFAULT '12',
            day_type     TEXT    NOT NULL,
            description  TEXT    DEFAULT '',
            sort_order   INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS workout_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date     TEXT    NOT NULL,
            exercise_id     INTEGER NOT NULL REFERENCES exercises(id),
            completed_sets  INTEGER DEFAULT 0,
            completed_reps  TEXT    DEFAULT '',
            is_done         INTEGER DEFAULT 0,
            note            TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS fitness_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    # 预置动作库（如已存在则忽略）
    _init_exercises(cursor)
    # 初始化健身设置（如已存在则忽略）
    _init_fitness_settings(cursor)

    # 数据库迁移：添加 review_stage 列（艾宾浩斯复习阶段）
    try:
        cursor.execute("ALTER TABLE mistakes ADD COLUMN review_stage INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # 列已存在

    # 为已有复习记录的错题初始化 review_stage（用 review_count 作为初始阶段，上限 6）
    cursor.execute(
        "UPDATE mistakes SET review_stage = MIN(review_count, 6) WHERE review_stage = 0 AND review_count > 0"
    )

    # 数据库迁移：添加 image_path 列（错题图片）
    try:
        cursor.execute("ALTER TABLE mistakes ADD COLUMN image_path TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # 列已存在

    # 数据库迁移：添加 question_type / question_number 列（快捷录入）
    try:
        cursor.execute("ALTER TABLE mistakes ADD COLUMN question_type TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE mistakes ADD COLUMN question_number INTEGER")
    except sqlite3.OperationalError:
        pass

    # 数据库迁移：为 exercises.name 添加唯一约束（防重复插入）
    _migrate_exercises_unique(cursor)

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

    # 数据库迁移：为 chapters 添加唯一索引，防止同一科目下章节名重复
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_chapters_subject_name ON chapters(subject_id, name)"
    )

    # 插入默认章节（按 目录章节整理.md 定义）
    _init_default_chapters(cursor)

    conn.commit()
    conn.close()


def _init_default_chapters(cursor):
    """插入所有预置的标准章节。使用 INSERT OR IGNORE 避免重复。"""
    # 获取科目 ID 映射
    subject_rows = cursor.execute("SELECT id, name FROM subjects").fetchall()
    subject_map = {row["name"]: row["id"] for row in subject_rows}

    default_chapters = {
        "高等数学": [
            "第1讲 函数极限与连续",
            "第2讲 数列极限",
            "第3讲 一元函数微分学的概念",
            "第4讲 一元函数微分学的计算",
            "第5讲 一元函数微分学的应用（一）——几何应用",
            "第6讲 一元函数微分学的应用（二）——中值定理、微分等式与微分不等式",
            "第7讲 一元函数微分学的应用（三）——物理应用与经济应用",
            "第8讲 一元函数积分学的概念与性质",
            "第9讲 一元函数积分学的计算",
            "第10讲 一元函数积分学的应用（一）——几何应用",
            "第11讲 一元函数积分学的应用（二）——积分等式与积分不等式",
            "第12讲 一元函数积分学的应用（三）——物理应用与经济应用",
            "第13讲 多元函数微分学",
            "第14讲 二重积分",
            "第15讲 微分方程",
            "第16讲 无穷级数（仅数学一、数学三）",
            "第17讲 多元函数积分学的预备知识（仅数学一）",
            "第18讲 多元函数积分学（仅数学一）",
        ],
        "线性代数": [
            "第0讲 零基础课——线性代数入门",
            "第1讲 行列式",
            "第2讲 矩阵",
            "第3讲 向量组",
            "第4讲 线性方程组",
            "第5讲 特征值与特征向量",
            "第6讲 二次型",
        ],
        "概率论": [
            "第1讲 随机事件与概率",
            "第2讲 一维随机变量及其分布",
            "第3讲 多维随机变量及其分布",
            "第4讲 随机变量的数字特征",
            "第5讲 大数定律与中心极限定理",
            "第6讲 数理统计",
        ],
        "数字电子技术": [
            "第一章 数字逻辑概论",
            "第二章 逻辑代数与硬件描述语言基础",
            "第三章 逻辑门电路",
            "第四章 组合逻辑电路",
            "第五章 锁存器和触发器",
            "第六章 时序逻辑电路",
            "第七章 半导体存储器",
            "第八章 CPLD 和 FPGA",
            "第九章 脉冲波形的变换与产生",
            "第十章 数模与模数转换器",
            "第十一章 数字系统设计基础",
        ],
    }

    for subject_name, chapters in default_chapters.items():
        sid = subject_map.get(subject_name)
        if sid is None:
            continue
        for ch_name in chapters:
            cursor.execute(
                "INSERT OR IGNORE INTO chapters (subject_id, name) VALUES (?, ?)",
                (sid, ch_name),
            )


def _init_exercises(cursor):
    """预置健身动作库（宿舍可用器械：弹力绳、哑铃、引体向上杆）。"""
    # 已存在动作则跳过，防止每次 init_db() 重复插入
    cursor.execute("SELECT COUNT(*) FROM exercises")
    if cursor.fetchone()[0] > 0:
        return

    exercises = [
        # Pull Day (拉力日)
        ("引体向上",          "背部",   "引体向上杆", 3, "8-12", "pull",  "正手宽握，下巴过杠", 1),
        ("哑铃划船",          "背部",   "哑铃",      3, "10-12","pull",  "单臂支撑，感受背部收缩", 2),
        ("弹力绳划船",        "背部",   "弹力绳",    3, "12-15","pull",  "坐姿，弹力绳固定于脚底", 3),
        ("弹力绳面拉",        "肩部",   "弹力绳",    3, "12-15","pull",  "拉动至面部，肩胛后缩", 4),
        ("哑铃二头弯举",      "手臂",   "哑铃",      3, "10-12","pull",  "肘部固定，慢放快起", 5),

        # Push Day (推力日)
        ("哑铃卧推",          "胸部",   "哑铃",      3, "8-12", "push",  "仰卧地面或床上，肘部45°", 1),
        ("哑铃推举",          "肩部",   "哑铃",      3, "8-12", "push",  "坐姿，哑铃从肩推到头顶", 2),
        ("哑铃侧平举",        "肩部",   "哑铃",      3, "10-15","push",  "轻重量，感受三角肌中束", 3),
        ("弹力绳推举",        "肩部",   "弹力绳",    3, "12-15","push",  "站姿，弹力绳踩在脚下", 4),
        ("哑铃三头臂屈伸",    "手臂",   "哑铃",      3, "10-12","push",  "单手颈后，控制下落", 5),
        ("俯卧撑",            "胸部",   "自重",      3, "10-15","push",  "宽距/窄距/下斜", 6),

        # Leg Day (腿部日)
        ("哑铃深蹲",          "腿部",   "哑铃",      3, "10-15","legs",  "哑铃持于胸前，腰背挺直", 1),
        ("保加利亚分腿蹲",    "腿部",   "哑铃",      3, "8-12", "legs",  "后脚搭在椅子/床上", 2),
        ("哑铃硬拉",          "臀部",   "哑铃",      3, "10-12","legs",  "哑铃放于脚两侧，直背拉起", 3),
        ("弹力绳侧步走",      "臀部",   "弹力绳",    3, "10-12","legs",  "弹力绳套脚踝，侧向移动", 4),
        ("自重深蹲",          "腿部",   "自重",      3, "12-20","legs",  "可升级为手枪深蹲辅助", 5),

        # Core (核心)
        ("平板支撑",          "核心",   "自重",      3, "30s",  "core",  "肘部撑地，身体一条直线", 1),
        ("卷腹",              "核心",   "自重",      3, "15-20","core",  "肩胛离开地面即可", 2),
        ("悬垂举腿",          "核心",   "引体向上杆",3, "8-12", "core",  "悬挂于引体杆，抬腿至水平", 3),
        ("俄罗斯转体",        "核心",   "哑铃",      3, "10-15","core",  "坐姿，转体带动哑铃", 4),
    ]
    cursor.executemany(
        """INSERT OR IGNORE INTO exercises
           (name, muscle_group, equipment, default_sets, default_reps, day_type, description, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        exercises,
    )


def _init_fitness_settings(cursor):
    """初始化健身设置（开始日期等）。"""
    today = __import__("datetime").date.today().isoformat()
    cursor.execute(
        "INSERT OR IGNORE INTO fitness_settings (key, value) VALUES (?, ?)",
        ("start_date", today),
    )


def _migrate_exercises_unique(cursor):
    """清理 exercises 表重复数据并添加唯一索引。"""
    try:
        # 先清重：保留每组同名中 id 最小的那条
        cursor.execute("""
            DELETE FROM exercises WHERE id NOT IN (
                SELECT MIN(id) FROM exercises GROUP BY name
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_exercises_name ON exercises(name)")
    except sqlite3.OperationalError:
        pass


if __name__ == "__main__":
    init_db()
    print(f"数据库已初始化: {DB_PATH}")
