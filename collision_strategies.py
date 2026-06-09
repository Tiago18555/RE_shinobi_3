from PIL import Image, ImageDraw, ImageFont


# Synthetic collision configs for stages whose tilemap-based collision is invalid.
# Each entry: (width_quads, height_quads, solid_bottom_rows)
SYNTHETIC_COLLISION_CONFIG = {
    "stage 2-1": (0x40, 0x10, 3),
    "stage 4-1": (0x40, 0x10, 4),
    "stage 4-3": (0x40, 0x20, 4),
}

# Shared color table (matches image_exporter.py)
_NIBBLE_COLORS = {
    0x0: ("#1a1a1e", "#2e2e36", "#aaaaaa"),
    0x1: ("#b0b0bc", "#8a8a96", "#111111"),
    0x2: ("#ff7675", "#cc5a59", "#ffffff"),
    0x3: ("#fd79a8", "#c0547f", "#ffffff"),
    0x4: ("#55efc4", "#2db58e", "#000000"),
    0x5: ("#00b894", "#007f65", "#ffffff"),
    0x6: ("#fdcb6e", "#c9962a", "#000000"),
    0x7: ("#e17055", "#a84a2f", "#ffffff"),
    0xC: ("#74b9ff", "#3a8fd1", "#000000"),
    0xD: ("#a29bfe", "#6c5ce7", "#ffffff"),
    0xF: ("#0984e3", "#0660a8", "#ffffff"),
}
_UNCOLORED_NIBBLES = {0x8, 0x9, 0xA, 0xB, 0xE}


class CollisionStrategies:
    @staticmethod
    def _build_synthetic_grid(width_quads: int, height_quads: int, solid_bottom_rows: int) -> list[list[int]]:
        """
        Returns a 2-D grid [row][col] of collision values (0x00 or 0x01).
        The bottom `solid_bottom_rows` rows are 0x01 (solid), everything else 0x00.
        """
        grid = []
        for row in range(height_quads):
            val = 0x01 if row >= height_quads - solid_bottom_rows else 0x00
            grid.append([val] * width_quads)
        return grid

    @classmethod
    def _render_grid(cls, grid: list[list[int]], output_path: str, scale: int):
        """
        Directly renders a 2-D collision grid to a PNG.
        Grid dimensions drive the image size exactly (no fixed-32 constraint).
        """
        height_quads = len(grid)
        width_quads = len(grid[0]) if grid else 0
        block_size = 16 * scale if scale >= 1 else 16

        img = Image.new("RGB", (width_quads * block_size, height_quads * block_size), "#1a1a1e")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default(size=max(8, 8 * scale))

        for quad_y, row in enumerate(grid):
            for quad_x, coll_val in enumerate(row):
                x1 = quad_x * block_size
                y1 = quad_y * block_size
                x2 = x1 + block_size
                y2 = y1 + block_size

                lower = coll_val & 0xF
                label = f"{coll_val:02X}"

                if lower in _UNCOLORED_NIBBLES:
                    draw.rectangle([x1, y1, x2 - 1, y2 - 1], fill="#1a1a1e", outline="#2e2e36")
                else:
                    fill, outline, text_color = _NIBBLE_COLORS[lower]
                    draw.rectangle([x1, y1, x2 - 1, y2 - 1], fill=fill, outline=outline)
                    if block_size >= 8:
                        cx = x1 + block_size // 2
                        cy = y1 + block_size // 2
                        draw.text((cx, cy), label, fill=text_color, anchor="mm", font=font)

        img.save(output_path, "PNG")

    @classmethod
    def export(cls, stage_name: str, output_path: str, scale: int = 1) -> bool:
        """
        Generates the synthetic collision PNG for a special stage.
        Returns True if the stage was handled, False if it is not a special case.
        """
        if stage_name not in SYNTHETIC_COLLISION_CONFIG:
            return False

        width_quads, height_quads, solid_rows = SYNTHETIC_COLLISION_CONFIG[stage_name]
        grid = cls._build_synthetic_grid(width_quads, height_quads, solid_rows)
        cls._render_grid(grid, output_path, scale)
        return True
