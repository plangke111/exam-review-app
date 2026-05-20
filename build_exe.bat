@echo off
chcp 65001 >nul
echo ========================================
echo  考研错题复习提醒系统 - EXE 打包脚本
echo ========================================
echo.

REM 尝试找到可用的 Python（3.10+）
set PYTHON=
for /f "delims=" %%p in ('where python 2^>nul') do (
    "%%p" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>nul
    if not errorlevel 1 (
        set PYTHON=%%p
        goto :found
    )
)
:found

if "%PYTHON%"=="" (
    echo [错误] 未找到 Python 3.10+，请先安装 Python。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] 使用 Python: %PYTHON%
echo.

REM 安装/更新依赖
echo [1/4] 检查依赖...
%PYTHON% -m pip install streamlit pyinstaller -q 2>nul
echo [1/4] 依赖就绪
echo.

REM 打包
echo [2/4] 开始打包（约 2-5 分钟，请耐心等待）...
echo.

%PYTHON% -m PyInstaller ^
    --name="考研错题复习系统" ^
    --onefile ^
    --console ^
    --noconfirm ^
    --add-data "pages;pages" ^
    --add-data "src;src" ^
    --add-data "app.py;." ^
    --copy-metadata streamlit ^
    --copy-metadata watchdog ^
    --copy-metadata pandas ^
    --copy-metadata numpy ^
    --copy-metadata pyarrow ^
    --hidden-import=streamlit ^
    --hidden-import=streamlit.web.bootstrap ^
    --hidden-import=streamlit.runtime ^
    --hidden-import=sqlite3 ^
    --hidden-import=src.db ^
    --hidden-import=src.services ^
    --hidden-import=src.task_scheduler ^
    --hidden-import=src.statistics ^
    --hidden-import=src.import_export ^
    --hidden-import=src.utils ^
    run_app.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo  打包失败！请检查上方错误信息。
    echo ========================================
    pause
    exit /b 1
)

echo.
echo [3/4] 打包完成！
echo [4/4] 清理临时文件...
rmdir /s /q build 2>nul
del /q "考研错题复习系统.spec" 2>nul
echo.
echo ========================================
echo  生成成功！
echo.
echo  文件位置: dist\考研错题复习系统.exe
echo.
echo  使用方法:
echo    1. 双击 "dist\考研错题复习系统.exe"
echo    2. 浏览器自动打开 http://localhost:8501
echo    3. 所有数据保存在 exe 旁边的 data\ 文件夹中
echo    4. 关闭窗口即可退出程序
echo.
echo  如需分享给他人，只需发送 exe 文件即可。
echo  （首次运行会自动创建 data 文件夹）
echo ========================================
pause
