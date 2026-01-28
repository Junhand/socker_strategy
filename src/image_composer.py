"""Image composition for practice diagrams."""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class ImageComposer:
    """Compose practice diagrams from base assets."""

    def __init__(self, assets_dir: str | Path | None = None):
        """Initialize the image composer.

        Args:
            assets_dir: Directory containing image assets. Defaults to 'images/' in project root.
        """
        if assets_dir is None:
            # Default to images directory relative to this file
            assets_dir = Path(__file__).parent.parent / "images"
        self.assets_dir = Path(assets_dir)

        self.ground_path = self.assets_dir / "ground.png"
        self.person_path = self.assets_dir / "person.png"

        if not self.ground_path.exists():
            raise FileNotFoundError(f"Ground image not found: {self.ground_path}")
        if not self.person_path.exists():
            raise FileNotFoundError(f"Person image not found: {self.person_path}")

        # Load base images
        self.ground_image = Image.open(self.ground_path).convert("RGBA")
        self.person_image = Image.open(self.person_path).convert("RGBA")

        # Resize person image to appropriate size (relative to ground)
        person_size = max(30, min(self.ground_image.width, self.ground_image.height) // 15)
        self.person_image = self.person_image.resize(
            (person_size, person_size), Image.Resampling.LANCZOS
        )

    def compose_step_diagram(self, step: dict) -> Image.Image:
        """Compose a diagram for a practice step.

        Args:
            step: Step data containing players, movements, and ball_movements.

        Returns:
            Composed PIL Image.
        """
        # Create a copy of the ground image
        diagram = self.ground_image.copy()
        draw = ImageDraw.Draw(diagram)

        width, height = diagram.size
        person_w, person_h = self.person_image.size

        # Draw ball movements first (as dotted lines)
        ball_movements = step.get("ball_movements", [])
        for movement in ball_movements:
            from_pos = movement.get("from", {})
            to_pos = movement.get("to", {})

            from_x = int(from_pos.get("x", 0.5) * width)
            from_y = int(from_pos.get("y", 0.5) * height)
            to_x = int(to_pos.get("x", 0.5) * width)
            to_y = int(to_pos.get("y", 0.5) * height)

            # Draw dashed line for ball movement
            self._draw_dashed_line(draw, from_x, from_y, to_x, to_y, fill="orange", width=3)
            # Draw arrow head
            self._draw_arrow_head(draw, from_x, from_y, to_x, to_y, fill="orange", size=10)

        # Draw player movements (as solid arrows)
        movements = step.get("movements", [])
        player_positions = {p["id"]: p["position"] for p in step.get("players", [])}

        for movement in movements:
            from_player = movement.get("from_player", "")
            to_pos = movement.get("to_position", {})

            if from_player in player_positions:
                from_pos = player_positions[from_player]
                from_x = int(from_pos.get("x", 0.5) * width)
                from_y = int(from_pos.get("y", 0.5) * height)
                to_x = int(to_pos.get("x", 0.5) * width)
                to_y = int(to_pos.get("y", 0.5) * height)

                # Draw solid line for player movement
                draw.line([(from_x, from_y), (to_x, to_y)], fill="blue", width=2)
                self._draw_arrow_head(draw, from_x, from_y, to_x, to_y, fill="blue", size=8)

        # Draw players
        players = step.get("players", [])
        for player in players:
            pos = player.get("position", {})
            x = int(pos.get("x", 0.5) * width) - person_w // 2
            y = int(pos.get("y", 0.5) * height) - person_h // 2

            # Paste person image
            diagram.paste(self.person_image, (x, y), self.person_image)

            # Draw player label
            label = player.get("id", "")
            label_x = x + person_w // 2
            label_y = y - 15

            # Draw label background
            bbox = draw.textbbox((label_x, label_y), label)
            padding = 2
            draw.rectangle(
                [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
                fill="white",
            )
            draw.text((label_x, label_y), label, fill="black", anchor="mm")

        return diagram

    def _draw_dashed_line(
        self,
        draw: ImageDraw.ImageDraw,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        fill: str,
        width: int,
        dash_length: int = 10,
    ):
        """Draw a dashed line."""
        import math

        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)

        if distance == 0:
            return

        dash_count = int(distance / dash_length)
        if dash_count == 0:
            dash_count = 1

        for i in range(0, dash_count, 2):
            start_ratio = i / dash_count
            end_ratio = min((i + 1) / dash_count, 1.0)

            start_x = int(x1 + dx * start_ratio)
            start_y = int(y1 + dy * start_ratio)
            end_x = int(x1 + dx * end_ratio)
            end_y = int(y1 + dy * end_ratio)

            draw.line([(start_x, start_y), (end_x, end_y)], fill=fill, width=width)

    def _draw_arrow_head(
        self,
        draw: ImageDraw.ImageDraw,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        fill: str,
        size: int,
    ):
        """Draw an arrow head at the end of a line."""
        import math

        dx = x2 - x1
        dy = y2 - y1
        angle = math.atan2(dy, dx)

        # Arrow head points
        arrow_angle = math.pi / 6  # 30 degrees
        left_x = x2 - size * math.cos(angle - arrow_angle)
        left_y = y2 - size * math.sin(angle - arrow_angle)
        right_x = x2 - size * math.cos(angle + arrow_angle)
        right_y = y2 - size * math.sin(angle + arrow_angle)

        draw.polygon([(x2, y2), (int(left_x), int(left_y)), (int(right_x), int(right_y))], fill=fill)

    def save_diagram(self, image: Image.Image, output_path: str | Path) -> Path:
        """Save a diagram to file.

        Args:
            image: PIL Image to save.
            output_path: Path to save the image.

        Returns:
            Path to the saved image.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to RGB if saving as JPEG
        if output_path.suffix.lower() in [".jpg", ".jpeg"]:
            image = image.convert("RGB")

        image.save(output_path)
        return output_path
