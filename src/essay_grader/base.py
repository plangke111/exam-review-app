"""基础批改器"""

import json
import re
from pathlib import Path
from anthropic import Anthropic

from .config import API_KEY, GRADING_MODEL, TEMPERATURE, load_prompt


class BaseGrader:
    """封装 Anthropic API 调用 + 结构化输入构建 + JSON 解析"""

    def __init__(self):
        self.client = Anthropic(api_key=API_KEY)
        self.model = GRADING_MODEL
        self.temperature = TEMPERATURE

    def _get_prompt(self, task_name: str) -> str:
        """从 prompts/ 目录加载提示词文件"""
        return load_prompt(task_name)

    def _call_api(self, system_prompt: str, input_json: dict) -> dict:
        """以 system prompt + 结构化 JSON 输入调用 Claude"""
        user_content = json.dumps(input_json, ensure_ascii=False, indent=2)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            temperature=self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
            thinking={"type": "disabled"},
        )

        from anthropic.types import TextBlock
        for block in response.content:
            if isinstance(block, TextBlock):
                return self._parse_json(block.text)
        raise ValueError("API 返回中没有 TextBlock")

    def _parse_json(self, text: str) -> dict:
        """从 LLM 回复中提取 JSON"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法解析 LLM 返回的 JSON:\n{text[:800]}")
