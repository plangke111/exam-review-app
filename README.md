# 考研错题复习提醒系统

一个本地运行的考研学习复习辅助程序，帮助记录错题、管理章节、生成每日复习任务，并根据完成情况自动延期。

## 科目覆盖

- **数学课**：高等数学、线性代数、概率论
- **专业课**：数字电子技术

## 技术栈

- Python 3.10+
- Streamlit（Web UI）
- SQLite（数据持久化）

## 快速开始

### 方式一：直接运行（推荐）

**如果已提供 exe 文件**，直接双击 `考研错题复习系统.exe`：
- 浏览器自动打开 `http://localhost:8501`
- 所有数据保存在 exe 同目录下的 `data/` 文件夹
- 关闭控制台窗口即可退出

### 方式二：Python 源码运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

首次启动会自动创建 `data/review.db` 数据库并初始化 4 个默认科目。

### 使用流程

1. **章节管理** — 为各科目创建章节（如"极限"、"矩阵"等）
2. **新增错题** — 录入历史错题或每日新错题
3. **首页 → 生成今日任务** — 点击按钮自动生成每科最多 5 道复习题
4. **今日复习** — 逐题复习，标记完成/错误/掌握
5. **数据统计** — 查看复习进度概览

## 核心功能

| 功能 | 说明 |
|------|------|
| 章节管理 | 按科目自由创建/删除章节 |
| 错题录入 | 逐题录入 + 批量导入 + CSV 导入 |
| 错题库 | 多维度筛选（科目/章节/收藏/熟练/难度/关键词） |
| 每日复习 | 每科每日自动生成 5 题，按章节分散选取 |
| 延期机制 | 未完成任务自动延期至次日，高优先级出现 |
| 收藏/熟练 | 收藏题优先提醒，熟练题自动排除 |
| 统计总览 | 总错题/需复习/已复习/熟练/各科目进度 |
| 数据导出 | 错题 CSV 导出、复习记录 CSV 导出 |
| 数据库备份 | 一键备份 SQLite 数据库 |

## 每日任务生成规则

每科每日生成最多 5 道题，按优先级选取：

1. **延期题**（昨天及之前未完成的）—— 最高优先级
2. **收藏题**（已收藏且未熟练）—— 高优先级
3. **到期题**（next_review_date 到达或超过今天）
4. **补充题**（复习次数少、较久未复习的）

每科内部按**章节分散算法**轮询选取，尽量让 5 道题覆盖不同章节。

熟练题默认不进入每日任务池。

## 项目结构

```
exam_review_app/
├── app.py                    # Streamlit 主入口 + Dashboard
├── requirements.txt          # 依赖列表
├── README.md                 # 本文件
├── data/
│   └── review.db             # SQLite 数据库（自动创建）
├── src/
│   ├── db.py                 # 数据库初始化与连接
│   ├── services.py           # 业务逻辑层（CRUD）
│   ├── task_scheduler.py     # 每日任务生成 + 章节分散算法
│   ├── statistics.py         # 统计查询
│   ├── import_export.py      # CSV 导入导出 + 备份
│   └── utils.py              # 工具函数
└── pages/
    ├── 1_今日复习.py
    ├── 2_新增错题.py
    ├── 3_错题库.py
    ├── 4_章节管理.py
    ├── 5_复习记录.py
    ├── 6_数据统计.py
    └── 7_数据导入导出.py
```

## 数据备份

### 方法一：使用程序内备份

进入「数据导入导出」→「数据库备份」，点击按钮即可创建备份。

备份文件保存在 `data/backups/` 目录下。

### 方法二：手动备份

直接复制 `data/review.db` 文件到安全位置。

## CSV 导入格式

导入的 CSV 文件需包含以下列（带 `*` 的为必填）：

| 列名 | 必填 | 说明 |
|------|------|------|
| 题目标题 * | ✅ | 错题的简短标题 |
| 科目 * | ✅ | 必须是已存在的科目名 |
| 章节 | | 章节名，如不存在会自动创建 |
| 题目内容 | | 完整题目描述 |
| 错误原因 | | 分析错误原因 |
| 正确解法 | | 正确解题步骤 |
| 关键知识点 | | 涉及的知识点 |
| 来源 | | 真题/模拟题/习题册/课堂/自己整理 |
| 难度 | | 简单/中等/困难，默认中等 |
| 是否收藏 | | 1/是/True 表示收藏 |
| 是否熟练 | | 1/是/True 表示熟练 |
| 备注 | | 额外备注 |

## EXE 打包

如需生成独立的 .exe 文件（无需安装 Python 即可运行）：

```bash
# 确保已安装 Python 3.10+ 和 pip
# 然后运行打包脚本：
build_exe.bat
```

或手动打包：

```bash
pip install streamlit pyinstaller
pyinstaller --name="考研错题复习系统" --onefile --console --noconfirm \
    --add-data "pages;pages" --add-data "src;src" --add-data "app.py;." \
    --copy-metadata streamlit --copy-metadata watchdog \
    --copy-metadata pandas --copy-metadata numpy --copy-metadata pyarrow \
    --hidden-import=streamlit --hidden-import=streamlit.web.bootstrap \
    --hidden-import=streamlit.runtime --hidden-import=sqlite3 \
    --hidden-import=src.db --hidden-import=src.services \
    --hidden-import=src.task_scheduler --hidden-import=src.statistics \
    --hidden-import=src.import_export --hidden-import=src.utils \
    run_app.py
```

生成的 exe 位于 `dist/` 目录下。

## 后续可扩展方向

- 复习间隔算法（艾宾浩斯遗忘曲线）
- 错题图片上传
- 学习时间统计
- 自定义每日题目数量
- 导出为 Anki 卡片格式
- 数学公式渲染（LaTeX）
