"""工具函数模块。"""

from datetime import date, timedelta

# 艾宾浩斯遗忘曲线复习间隔（天数）
# 第1次复习后隔1天，第2次后隔2天，第3次后隔4天，第4次后隔7天，第5次后隔15天，第6次后隔30天
EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]


def get_ebbinghaus_interval(review_stage):
    """
    根据艾宾浩斯复习阶段返回下次复习间隔天数。
    review_stage: 当前已完成的复习阶段（0 = 从未复习）
    返回下一次复习应隔多少天。
    """
    if review_stage < 0:
        review_stage = 0
    idx = min(review_stage, len(EBBINGHAUS_INTERVALS) - 1)
    return EBBINGHAUS_INTERVALS[idx]


def format_date(d):
    """格式化日期为 YYYY-MM-DD 字符串。"""
    if d is None:
        return ""
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


def get_today_str():
    return date.today().isoformat()


def get_recent_dates(days=7):
    """返回最近 N 天的日期列表（倒序）。"""
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(days)]


def difficulty_color(difficulty):
    """返回难度等级对应的 Streamlit 颜色标记。"""
    mapping = {"简单": "green", "中等": "orange", "困难": "red"}
    return mapping.get(difficulty, "grey")


def status_label(status):
    """任务状态的中文显示。"""
    mapping = {"pending": "待完成", "done": "已完成", "postponed": "已延期"}
    return mapping.get(status, status)
