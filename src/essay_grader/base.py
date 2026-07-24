"""基础批改器 —— 支持 DeepSeek / Anthropic / OpenAI 兼容 API"""

import json
import re
from openai import OpenAI

from .config import API_KEY, MODEL_NAME, TEMPERATURE, LLM_PROVIDER, DEEPSEEK_BASE_URL


class BaseGrader:
    """封装 LLM API 调用 + JSON 解析，自动适配 DeepSeek / Anthropic"""

    def __init__(self):
        self.provider = LLM_PROVIDER

        if self.provider == "anthropic":
            # Anthropic SDK（如果安装了）
            from anthropic import Anthropic as Client
            self.client = Client(api_key=API_KEY)
            self._mode = "anthropic"
        else:
            # OpenAI 兼容模式（DeepSeek / OpenAI / 其他）
            base_url = DEEPSEEK_BASE_URL if self.provider == "deepseek" else None
            self.client = OpenAI(api_key=API_KEY, base_url=base_url, timeout=120.0)
            self._mode = "openai"

        self.model = MODEL_NAME
        self.temperature = TEMPERATURE

    def _get_prompt(self, task_name: str) -> str:
        from .config import load_prompt
        return load_prompt(task_name)

    def _call_api(self, system_prompt: str, input_json: dict) -> dict:
        user_content = json.dumps(input_json, ensure_ascii=False, indent=2)

        if self._mode == "anthropic":
            return self._call_anthropic(system_prompt, user_content)
        else:
            return self._call_openai(system_prompt, user_content)

    def _call_openai(self, system_prompt: str, user_content: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return self._parse_json(response.choices[0].message.content)

    def _call_anthropic(self, system_prompt: str, user_content: str) -> dict:
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
