"""Main agent orchestration for practice menu generation."""

from pathlib import Path
from PIL import Image

from .llm_client import LLMClient
from .image_composer import ImageComposer
from .excel_generator import ExcelGenerator


class PracticeMenuAgent:
    """Agent that orchestrates practice menu generation."""

    def __init__(self, api_key: str | None = None, assets_dir: str | Path | None = None):
        """Initialize the agent.

        Args:
            api_key: OpenRouter API key. If not provided, reads from environment.
            assets_dir: Directory containing image assets.
        """
        self.llm_client = LLMClient(api_key=api_key)
        self.image_composer = ImageComposer(assets_dir=assets_dir)
        self.excel_generator = ExcelGenerator()

    def generate_practice_menu(
        self, challenge: str, output_path: str | Path = "practice_menu.xlsx"
    ) -> Path:
        """Generate a complete practice menu from a challenge description.

        Args:
            challenge: Practice challenge description in Japanese.
            output_path: Path for the output Excel file.

        Returns:
            Path to the generated Excel file.
        """
        print(f"🎯 練習課題を分析中: {challenge}")

        # Step 1: Get practice plan from LLM
        print("🤖 AIが練習メニューを設計中...")
        practice_plan = self.llm_client.generate_practice_plan(challenge)
        print(f"✅ 練習メニュー「{practice_plan.get('title', '')}」を生成しました")

        # Step 2: Generate images for each step (separate images for ground and players)
        print("🎨 図解を作成中...")
        step_images: list[dict] = []
        steps = practice_plan.get("steps", [])

        for i, step in enumerate(steps):
            print(f"   ステップ {i + 1}/{len(steps)}: {step.get('name', '')}")
            diagram_data = self.image_composer.compose_step_diagram_separate(step)
            step_images.append(diagram_data)

        # Step 3: Create Excel file
        print("📊 Excelファイルを作成中...")
        self.excel_generator.create_practice_sheet(practice_plan, step_images)

        # Step 4: Save the file
        output_path = Path(output_path)
        saved_path = self.excel_generator.save(output_path)
        print(f"✅ 完成: {saved_path}")

        # Cleanup
        self.excel_generator.cleanup()

        return saved_path

    def generate_from_plan(
        self, practice_plan: dict, output_path: str | Path = "practice_menu.xlsx"
    ) -> Path:
        """Generate Excel from an existing practice plan (skip LLM step).

        Args:
            practice_plan: Pre-generated practice plan dictionary.
            output_path: Path for the output Excel file.

        Returns:
            Path to the generated Excel file.
        """
        # Generate images for each step (separate images for ground and players)
        step_images: list[dict] = []
        steps = practice_plan.get("steps", [])

        for step in steps:
            diagram_data = self.image_composer.compose_step_diagram_separate(step)
            step_images.append(diagram_data)

        # Create Excel file
        self.excel_generator.create_practice_sheet(practice_plan, step_images)

        # Save the file
        output_path = Path(output_path)
        saved_path = self.excel_generator.save(output_path)

        # Cleanup
        self.excel_generator.cleanup()

        return saved_path
