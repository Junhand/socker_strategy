"""LLM API client supporting OpenRouter and Azure OpenAI."""

import json
import os
from openai import OpenAI, AzureOpenAI


class LLMClient:
    """Client for interacting with LLM APIs (OpenRouter or Azure OpenAI)."""

    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        azure_endpoint: str | None = None,
        azure_deployment: str | None = None,
        azure_api_version: str | None = None,
    ):
        """Initialize the LLM client.

        Args:
            provider: LLM provider ("openrouter" or "azure"). Auto-detected from env if not specified.
            api_key: API key. If not provided, reads from environment variables.
            azure_endpoint: Azure OpenAI endpoint URL.
            azure_deployment: Azure OpenAI deployment name.
            azure_api_version: Azure OpenAI API version.
        """
        # Auto-detect provider from environment variables
        if provider is None:
            if os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_ENDPOINT"):
                provider = "azure"
            else:
                provider = "openrouter"

        self.provider = provider.lower()

        if self.provider == "azure":
            self._init_azure(api_key, azure_endpoint, azure_deployment, azure_api_version)
        elif self.provider == "openrouter":
            self._init_openrouter(api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'openrouter' or 'azure'.")

    def _init_openrouter(self, api_key: str | None):
        """Initialize OpenRouter client."""
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

    def _init_azure(
        self,
        api_key: str | None,
        endpoint: str | None,
        deployment: str | None,
        api_version: str | None,
    ):
        """Initialize Azure OpenAI client."""
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        if not self.api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
        if not self.endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
        )
        self.model = self.deployment

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

    def get_provider_info(self) -> dict:
        """Get information about the current provider configuration.

        Returns:
            Dictionary with provider information.
        """
        if self.provider == "azure":
            return {
                "provider": "Azure OpenAI",
                "endpoint": self.endpoint,
                "deployment": self.deployment,
                "api_version": self.api_version,
            }
        else:
            return {
                "provider": "OpenRouter",
                "model": self.model,
            }
