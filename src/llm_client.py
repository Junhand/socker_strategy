"""OpenRouter API client for LLM interactions."""

import json
import os
from openai import OpenAI


class LLMClient:
    """Client for interacting with OpenRouter API using OpenAI SDK."""

    def __init__(self, api_key: str | None = None):
        """Initialize the LLM client.

        Args:
            api_key: OpenRouter API key. If not provided, reads from OPENROUTER_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        self.model = "openai/gpt-4o"  # Using GPT-4o via OpenRouter

    def generate_practice_plan(self, challenge: str) -> dict:
        """Generate a practice plan for the given challenge.

        Args:
            challenge: Description of the practice challenge in Japanese.

        Returns:
            Structured practice plan with steps, positions, and movements.
        """
        system_prompt = """あなたはサッカーの練習メニューを設計する専門家です。
ユーザーから練習の課題を受け取り、具体的な練習ステップを設計してください。

以下のJSON形式で回答してください:
{
    "title": "練習メニューのタイトル",
    "description": "練習の概要説明",
    "steps": [
        {
            "step_number": 1,
            "name": "ステップ名",
            "description": "このステップの説明",
            "duration_minutes": 5,
            "players": [
                {
                    "id": "A",
                    "position": {"x": 0.5, "y": 0.3},
                    "role": "パサー"
                }
            ],
            "movements": [
                {
                    "from_player": "A",
                    "to_position": {"x": 0.7, "y": 0.5},
                    "type": "run"
                }
            ],
            "ball_movements": [
                {
                    "from": {"x": 0.5, "y": 0.3},
                    "to": {"x": 0.7, "y": 0.5},
                    "type": "pass"
                }
            ]
        }
    ],
    "key_points": ["ポイント1", "ポイント2"]
}

位置座標は0.0から1.0の範囲で、フィールド上の相対位置を表します。
x=0は左端、x=1は右端、y=0は上端、y=1は下端です。

必ず有効なJSONのみを返してください。説明文は含めないでください。"""

        user_prompt = f"以下の練習課題に対する練習メニューを設計してください:\n\n{challenge}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()

        # Remove markdown code block if present
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        return json.loads(content)
