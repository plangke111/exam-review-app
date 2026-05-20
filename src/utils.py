"""工具函数模块。"""

from datetime import date, timedelta


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
