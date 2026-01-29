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
        """Compose a diagram for a practice step (legacy method for backward compatibility).

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

    def compose_step_diagram_separate(self, step: dict) -> dict:
        """Compose a diagram with separate images for ground, players, and arrows.

        Args:
            step: Step data containing players, movements, and ball_movements.

        Returns:
            Dictionary containing:
                - ground: Ground image without overlays (PIL Image)
                - players: List of dicts with 'image', 'x', 'y', 'label' for each player
                - arrows: List of dicts with 'image', 'x', 'y', 'type' for each arrow
                - ground_size: Tuple (width, height) of ground image
        """
        # Use clean ground image (no arrows drawn on it)
        ground = self.ground_image.copy()

        width, height = ground.size
        person_w, person_h = self.person_image.size

        # Create arrow images for ball movements (orange, dashed, offset to one side)
        arrow_data = []
        ball_movements = step.get("ball_movements", [])
        for movement in ball_movements:
            from_pos = movement.get("from", {})
            to_pos = movement.get("to", {})

            from_x = int(from_pos.get("x", 0.5) * width)
            from_y = int(from_pos.get("y", 0.5) * height)
            to_x = int(to_pos.get("x", 0.5) * width)
            to_y = int(to_pos.get("y", 0.5) * height)

            # Create arrow image with positive perpendicular offset
            arrow_img, arrow_x, arrow_y = self._create_arrow_image(
                from_x, from_y, to_x, to_y, color="orange", dashed=True,
                offset_perpendicular=6  # Offset to avoid overlap with player arrows
            )
            arrow_data.append({
                "image": arrow_img,
                "x": arrow_x,
                "y": arrow_y,
                "type": "ball",
            })

        # Create arrow images for player movements (blue, solid, offset to other side)
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

                # Create arrow image with negative perpendicular offset
                arrow_img, arrow_x, arrow_y = self._create_arrow_image(
                    from_x, from_y, to_x, to_y, color="blue", dashed=False,
                    offset_perpendicular=-6  # Offset to opposite side from ball arrows
                )
                arrow_data.append({
                    "image": arrow_img,
                    "x": arrow_x,
                    "y": arrow_y,
                    "type": "player",
                })

        # Create player images with labels
        player_data = []
        players = step.get("players", [])
        for player in players:
            pos = player.get("position", {})
            # Calculate position (center of player)
            center_x = int(pos.get("x", 0.5) * width)
            center_y = int(pos.get("y", 0.5) * height)

            # Create player image with label
            label = player.get("id", "")
            player_img = self._create_labeled_player(label)

            player_data.append({
                "image": player_img,
                "x": center_x,
                "y": center_y,
                "label": label,
            })

        return {
            "ground": ground,
            "players": player_data,
            "arrows": arrow_data,
            "ground_size": (width, height),
        }

    def _create_arrow_image(
        self, from_x: int, from_y: int, to_x: int, to_y: int,
        color: str, dashed: bool, offset_perpendicular: int = 0,
        length_ratio: float = 0.75
    ) -> tuple[Image.Image, int, int]:
        """Create a transparent arrow image.

        Args:
            from_x, from_y: Start position.
            to_x, to_y: End position.
            color: Arrow color.
            dashed: Whether to draw dashed line.
            offset_perpendicular: Offset perpendicular to the arrow direction (to avoid overlap).
            length_ratio: Ratio of arrow length (0.75 = 75% of original length).

        Returns:
            Tuple of (arrow image, center_x, center_y) where center is the position
            to place the image on the ground.
        """
        import math

        # Shorten arrow to specified ratio (from center of the line)
        if length_ratio < 1.0:
            center_x_orig = (from_x + to_x) / 2
            center_y_orig = (from_y + to_y) / 2
            # Scale from center
            from_x = int(center_x_orig + (from_x - center_x_orig) * length_ratio)
            from_y = int(center_y_orig + (from_y - center_y_orig) * length_ratio)
            to_x = int(center_x_orig + (to_x - center_x_orig) * length_ratio)
            to_y = int(center_y_orig + (to_y - center_y_orig) * length_ratio)

        # Apply perpendicular offset to avoid overlapping arrows
        if offset_perpendicular != 0:
            dx = to_x - from_x
            dy = to_y - from_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                # Perpendicular unit vector
                perp_x = -dy / length
                perp_y = dx / length
                # Apply offset
                from_x = int(from_x + perp_x * offset_perpendicular)
                from_y = int(from_y + perp_y * offset_perpendicular)
                to_x = int(to_x + perp_x * offset_perpendicular)
                to_y = int(to_y + perp_y * offset_perpendicular)

        # Calculate bounding box with padding for arrow head
        padding = 25  # Increased padding for larger arrows
        min_x = min(from_x, to_x) - padding
        min_y = min(from_y, to_y) - padding
        max_x = max(from_x, to_x) + padding
        max_y = max(from_y, to_y) + padding

        img_width = max_x - min_x
        img_height = max_y - min_y

        # Ensure minimum size
        img_width = max(img_width, 40)
        img_height = max(img_height, 40)

        # Create transparent image
        arrow_img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(arrow_img)

        # Translate coordinates to image space
        local_from_x = from_x - min_x
        local_from_y = from_y - min_y
        local_to_x = to_x - min_x
        local_to_y = to_y - min_y

        # Draw line with increased width
        line_width = 5  # Increased from 3
        if dashed:
            self._draw_dashed_line(
                draw, local_from_x, local_from_y, local_to_x, local_to_y,
                fill=color, width=line_width, dash_length=15
            )
        else:
            draw.line(
                [(local_from_x, local_from_y), (local_to_x, local_to_y)],
                fill=color, width=line_width
            )

        # Draw larger arrow head
        self._draw_arrow_head(
            draw, local_from_x, local_from_y, local_to_x, local_to_y,
            fill=color, size=18  # Increased from 10
        )

        # Return image and its center position on the ground
        center_x = min_x + img_width // 2
        center_y = min_y + img_height // 2

        return arrow_img, center_x, center_y

    def _create_labeled_player(self, label: str) -> Image.Image:
        """Create a player image with a label above it.

        Args:
            label: Label text for the player.

        Returns:
            PIL Image with player and label.
        """
        person_w, person_h = self.person_image.size
        label_height = 20
        padding = 4

        # Create canvas for player + label
        canvas_width = max(person_w, len(label) * 8 + padding * 2)
        canvas_height = person_h + label_height
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        # Paste person image centered
        person_x = (canvas_width - person_w) // 2
        person_y = label_height
        canvas.paste(self.person_image, (person_x, person_y), self.person_image)

        # Draw label
        draw = ImageDraw.Draw(canvas)
        label_x = canvas_width // 2
        label_y = label_height // 2

        # Draw label background
        bbox = draw.textbbox((label_x, label_y), label, anchor="mm")
        draw.rectangle(
            [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
            fill="white",
        )
        draw.text((label_x, label_y), label, fill="black", anchor="mm")

        return canvas

    def get_ground_image(self) -> Image.Image:
        """Get a copy of the ground image.

        Returns:
            Copy of the ground PIL Image.
        """
        return self.ground_image.copy()

    def get_player_image(self) -> Image.Image:
        """Get a copy of the player image.

        Returns:
            Copy of the player PIL Image.
        """
        return self.person_image.copy()

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
