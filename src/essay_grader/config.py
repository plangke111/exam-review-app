"""批改系统配置 —— 提示词从文件读取，API Key 从环境变量或 Streamlit secrets 获取

使用方式（三选一）：
  1. 环境变量:  export ANTHROPIC_API_KEY="sk-ant-..."
  2. Streamlit:  在 .streamlit/secrets.toml 中设置 ANTHROPIC_API_KEY
  3. .env 文件:  在项目根目录创建 .env 文件，写入 ANTHROPIC_API_KEY=sk-ant-...
"""

import os
from pathlib import Path

# === 项目根目录（自动检测） ===
PROJECT_ROOT = Path(__file__).parent.parent.parent

# === 加载 .env 文件 ===
def _load_dotenv():
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val

_load_dotenv()

# === 提示词目录 ===
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# === API 配置 ===
# 优先级: 环境变量 > Streamlit secrets > .env 文件
def _get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return ""

API_KEY = _get_api_key()
GRADING_MODEL = os.environ.get("GRADING_MODEL", "claude-sonnet-4-6")
TEMPERATURE = 0.1

# === 提示词文件映射 ===
# 每个任务对应一个提示词文件名，放在 prompts/ 目录下
PROMPT_FILES = {
    "english_big": "english_big.md",
    "english_small": "english_small.md",
    "politics": "politics.md",
}

# === 提示词管理 ===

def get_prompt_path(task_name: str) -> Path:
    """获取提示词文件路径"""
    filename = PROMPT_FILES.get(task_name, f"{task_name}.md")
    return PROMPTS_DIR / filename


def load_prompt(task_name: str) -> str:
    """读取提示词文件内容"""
    path = get_prompt_path(task_name)
    if not path.exists():
        raise FileNotFoundError(
            f"提示词文件不存在: {path}\n"
            f"请参考示例文件创建: {path}.sample\n"
            f"或从其他来源获取提示词文件放到 {PROMPTS_DIR}/"
        )
    return path.read_text(encoding="utf-8")


def list_available_prompts() -> dict[str, bool]:
    """列出所有任务的提示词是否已就绪"""
    return {
        task: get_prompt_path(task).exists()
        for task in PROMPT_FILES
    }


def list_prompt_files() -> list[dict]:
    """列出 prompts/ 目录下所有文件"""
    if not PROMPTS_DIR.exists():
        return []
    files = []
    for f in sorted(PROMPTS_DIR.iterdir()):
        if f.suffix in (".md", ".txt") and not f.name.endswith(".sample"):
            files.append({
                "task": f.stem,
                "path": str(f),
                "size": f.stat().st_size,
            })
    return files
