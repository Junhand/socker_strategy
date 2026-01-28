"""Excel file generation with embedded images."""

from pathlib import Path
from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import tempfile
import os


class ExcelGenerator:
    """Generate Excel files with practice menus and images."""

    def __init__(self):
        """Initialize the Excel generator."""
        self.workbook = Workbook()
        self.temp_files: list[str] = []

    def create_practice_sheet(self, practice_plan: dict, step_images: list[Image.Image]) -> None:
        """Create a practice sheet with images and descriptions.

        Args:
            practice_plan: Practice plan data from LLM.
            step_images: List of PIL Images for each step.
        """
        ws = self.workbook.active
        ws.title = "練習メニュー"

        # Styles
        title_font = Font(name="Meiryo", size=16, bold=True)
        header_font = Font(name="Meiryo", size=12, bold=True)
        normal_font = Font(name="Meiryo", size=10)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="top", wrap_text=True)
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font_white = Font(name="Meiryo", size=12, bold=True, color="FFFFFF")

        # Set column widths
        ws.column_dimensions["A"].width = 5
        ws.column_dimensions["B"].width = 50
        ws.column_dimensions["C"].width = 40
        ws.column_dimensions["D"].width = 15

        current_row = 1

        # Title
        ws.merge_cells(f"A{current_row}:D{current_row}")
        title_cell = ws.cell(row=current_row, column=1, value=practice_plan.get("title", "練習メニュー"))
        title_cell.font = title_font
        title_cell.alignment = center_align
        ws.row_dimensions[current_row].height = 30
        current_row += 1

        # Description
        ws.merge_cells(f"A{current_row}:D{current_row}")
        desc_cell = ws.cell(row=current_row, column=1, value=practice_plan.get("description", ""))
        desc_cell.font = normal_font
        desc_cell.alignment = left_align
        ws.row_dimensions[current_row].height = 40
        current_row += 2

        # Header row
        headers = ["#", "図解", "説明", "時間"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = header_font_white
            cell.alignment = center_align
            cell.border = thin_border
            cell.fill = header_fill
        ws.row_dimensions[current_row].height = 25
        current_row += 1

        # Steps
        steps = practice_plan.get("steps", [])
        for i, step in enumerate(steps):
            step_start_row = current_row

            # Step number
            ws.cell(row=current_row, column=1, value=step.get("step_number", i + 1))
            ws.cell(row=current_row, column=1).font = header_font
            ws.cell(row=current_row, column=1).alignment = center_align
            ws.cell(row=current_row, column=1).border = thin_border

            # Image
            if i < len(step_images):
                img = step_images[i]
                # Save image to temp file
                temp_path = self._save_temp_image(img, f"step_{i}.png")
                xl_img = XLImage(temp_path)

                # Resize image to fit cell
                max_width = 350
                max_height = 200
                aspect_ratio = img.width / img.height

                if img.width > max_width:
                    xl_img.width = max_width
                    xl_img.height = int(max_width / aspect_ratio)
                if xl_img.height > max_height:
                    xl_img.height = max_height
                    xl_img.width = int(max_height * aspect_ratio)

                # Add image to cell
                img_cell = f"B{current_row}"
                ws.add_image(xl_img, img_cell)

            ws.cell(row=current_row, column=2).border = thin_border

            # Description
            step_desc = f"【{step.get('name', '')}】\n\n{step.get('description', '')}"
            ws.cell(row=current_row, column=3, value=step_desc)
            ws.cell(row=current_row, column=3).font = normal_font
            ws.cell(row=current_row, column=3).alignment = left_align
            ws.cell(row=current_row, column=3).border = thin_border

            # Duration
            duration = step.get("duration_minutes", 5)
            ws.cell(row=current_row, column=4, value=f"{duration}分")
            ws.cell(row=current_row, column=4).font = normal_font
            ws.cell(row=current_row, column=4).alignment = center_align
            ws.cell(row=current_row, column=4).border = thin_border

            # Set row height for image
            ws.row_dimensions[current_row].height = 160

            current_row += 1

        # Key points section
        current_row += 1
        ws.merge_cells(f"A{current_row}:D{current_row}")
        kp_header = ws.cell(row=current_row, column=1, value="📌 重要ポイント")
        kp_header.font = header_font
        kp_header.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        ws.row_dimensions[current_row].height = 25
        current_row += 1

        key_points = practice_plan.get("key_points", [])
        for point in key_points:
            ws.merge_cells(f"A{current_row}:D{current_row}")
            point_cell = ws.cell(row=current_row, column=1, value=f"• {point}")
            point_cell.font = normal_font
            point_cell.alignment = left_align
            current_row += 1

    def _save_temp_image(self, img: Image.Image, filename: str) -> str:
        """Save image to a temporary file.

        Args:
            img: PIL Image to save.
            filename: Filename for the temp file.

        Returns:
            Path to the temporary file.
        """
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        img.convert("RGB").save(temp_path, "PNG")
        self.temp_files.append(temp_path)
        return temp_path

    def save(self, output_path: str | Path) -> Path:
        """Save the workbook to file.

        Args:
            output_path: Path to save the Excel file.

        Returns:
            Path to the saved file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.workbook.save(output_path)
        return output_path

    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except OSError:
                pass
        self.temp_files.clear()

    def __del__(self):
        """Destructor to clean up temp files."""
        self.cleanup()
