"""
PyInstaller 打包入口 — 启动 Streamlit 服务器并打开浏览器。
直接双击 exe 即可运行，也可用 python run_app.py 运行。
"""

import os
import sys
import threading
import webbrowser
import logging

# 在导入 streamlit 之前抑制其调试日志
logging.getLogger("streamlit").setLevel(logging.WARNING)
logging.getLogger("streamlit.web").setLevel(logging.WARNING)
logging.getLogger("streamlit.runtime").setLevel(logging.WARNING)
logging.getLogger("streamlit.components").setLevel(logging.WARNING)


def main():
    # 确定两个关键路径：
    #   data_dir: 可写的数据目录（exe 旁边或源码根目录）
    #   app_dir:  代码文件目录（PyInstaller 的 _MEIPASS 或源码根目录）
    if getattr(sys, 'frozen', False):
        data_dir = os.path.dirname(sys.executable)
        app_dir = sys._MEIPASS
    else:
        data_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = data_dir

    # 将 src/db.py 的数据目录指向可写位置
    import src.db as db_module
    db_module.DB_DIR = os.path.join(data_dir, "data")
    db_module.DB_PATH = os.path.join(db_module.DB_DIR, "review.db")

    # Streamlit 需要在 app_dir 中运行才能发现 pages/ 目录
    os.chdir(app_dir)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # 初始化数据库
    from src.db import init_db
    init_db()

    # 诊断：检查关键文件是否存在
    app_path = os.path.join(app_dir, "app.py")
    pages_dir = os.path.join(app_dir, "pages")
    print(f"DEBUG app_dir: {app_dir}")
    print(f"DEBUG app.py exists: {os.path.exists(app_path)}")
    print(f"DEBUG pages dir exists: {os.path.isdir(pages_dir)}")
    if os.path.isdir(pages_dir):
        print(f"DEBUG pages contents: {os.listdir(pages_dir)}")

    # 打印启动信息
    print("=" * 50)
    print("  考研错题复习提醒系统")
    print(f"  浏览器访问: http://localhost:8501")
    print(f"  数据目录: {os.path.join(data_dir, 'data')}")
    print("  按 Ctrl+C 退出")
    print("=" * 50)

    # 延迟打开浏览器
    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open("http://localhost:8501")

    threading.Thread(target=open_browser, daemon=True).start()

    # 配置 Streamlit
    from streamlit import config as _config
    _config.set_option("global.developmentMode", False)
    _config.set_option("server.port", 8501)
    _config.set_option("server.headless", True)
    _config.set_option("server.fileWatcherType", "none")
    _config.set_option("server.runOnSave", False)
    _config.set_option("browser.serverAddress", "localhost")
    _config.set_option("browser.gatherUsageStats", False)
    _config.set_option("logger.level", "warning")

    # 直接使用 bootstrap.run，传递正确的 flag_options
    import streamlit.web.bootstrap as bootstrap
    flag_options = {
        "global.developmentMode": False,
        "server.port": 8501,
        "server.headless": True,
        "server.fileWatcherType": "none",
        "server.runOnSave": False,
        "browser.serverAddress": "localhost",
        "browser.gatherUsageStats": False,
        "logger.level": "warning",
    }
    bootstrap.run(app_path, False, [], flag_options)


if __name__ == "__main__":
    main()
