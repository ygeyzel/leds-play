#!/usr/bin/env python3
"""A small pixel-art editor for authoring games/<name>/logo.png (and
logo_small.png) files by hand: paint a grid at the menu's big-logo size
and another at its small carousel size, pick colors from a preset palette
or a full color-picker dialog, and save straight into a game's own
directory - including one that doesn't exist as a real game yet.

The small logo can either auto-follow the big one (nearest-neighbor
resized, same as the real menu falls back to at runtime when there's no
logo_small.png) or be hand-edited independently. Either way, whether
logo.png and/or logo_small.png actually get written on save is controlled
by their own checkboxes (both on by default).

Run with: python3 tools/logo_editor.py
"""
import inspect
import os
import re
import sys
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from games.menu import LOGO_SIZE, SMALL_LOGO_SIZE  # noqa: E402
from games.registry import GAMES  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES_DIR = os.path.join(REPO_ROOT, "games")

CELL_PX = 28
SMALL_CELL_PX = 28
CHECKER_LIGHT = "#d0d0d0"
CHECKER_DARK = "#a0a0a0"

# name -> RGB; alpha is always 255 for a painted cell (None means transparent).
PALETTE = [
    ("Black", (0, 0, 0)),
    ("White", (255, 255, 255)),
    ("Red", (220, 30, 30)),
    ("Green", (0, 200, 60)),
    ("Blue", (30, 110, 230)),
    ("Cyan", (0, 200, 220)),
    ("Yellow", (230, 210, 0)),
    ("Purple", (160, 30, 220)),
    ("Orange", (230, 120, 0)),
]


def game_dir_for(game_cls: type) -> str:
    """The directory game_cls's assets belong in - derived from its own
    LOGO_PATH if it's already pointed at one, otherwise from its module
    (matching games.base.default_score_file's convention for
    .best_score)."""
    if game_cls.LOGO_PATH:
        return os.path.dirname(game_cls.LOGO_PATH)
    return os.path.dirname(inspect.getfile(game_cls))


def new_game_dir_for(name: str) -> str:
    """Where a not-yet-existing game called `name` would live, following
    the games/<lowercase-dirname>/ convention (games/tetris, games/snake)."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return os.path.join(GAMES_DIR, slug)


def load_grid_from_image(path: str, cols: int, rows: int):
    """A (rows x cols) grid of RGB tuples (or None for transparent),
    nearest-neighbor resized from the PNG at path - the editor's in-memory
    equivalent of games/logo.py's load_logo."""
    img = Image.open(path).convert("RGBA").resize((cols, rows), Image.NEAREST)
    grid = []
    for row in range(rows):
        grid.append([
            (r, g, b) if a > 0 else None
            for r, g, b, a in (img.getpixel((col, row)) for col in range(cols))
        ])
    return grid


def grid_to_image(grid, cols: int, rows: int) -> Image.Image:
    img = Image.new("RGBA", (cols, rows), (0, 0, 0, 0))
    for row in range(rows):
        for col in range(cols):
            color = grid[row][col]
            if color is not None:
                img.putpixel((col, row), (*color, 255))
    return img


def blank_grid(cols: int, rows: int):
    return [[None for _ in range(cols)] for _ in range(rows)]


class LogoEditor:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("LEDs Play - Logo Editor")

        self.cols, self.rows = LOGO_SIZE
        self.small_cols, self.small_rows = SMALL_LOGO_SIZE
        self.grid = blank_grid(self.cols, self.rows)
        self.small_grid = blank_grid(self.small_cols, self.small_rows)
        self.current_color = PALETTE[0][1]

        self._build_ui()
        self._redraw_big()
        self._redraw_small()

    # ---- UI construction ----

    def _build_ui(self):
        main = tk.Frame(self.root, padx=10, pady=10)
        main.pack()

        canvases = tk.Frame(main)
        canvases.pack()

        big_frame = tk.Frame(canvases)
        big_frame.pack(side="left", padx=(0, 20))
        tk.Label(big_frame, text=f"Big logo ({self.cols}x{self.rows})").pack()
        self.big_canvas = tk.Canvas(
            big_frame, width=self.cols * CELL_PX, height=self.rows * CELL_PX,
            highlightthickness=1, highlightbackground="#666")
        self.big_canvas.pack()
        self.big_canvas.bind("<Button-1>", self._on_big_paint)
        self.big_canvas.bind("<B1-Motion>", self._on_big_paint)
        self.big_canvas.bind("<Button-3>", self._on_big_erase)
        self.big_canvas.bind("<B3-Motion>", self._on_big_erase)

        small_frame = tk.Frame(canvases)
        small_frame.pack(side="left")
        tk.Label(small_frame, text=f"Small logo ({self.small_cols}x{self.small_rows})").pack()
        self.small_canvas = tk.Canvas(
            small_frame, width=self.small_cols * SMALL_CELL_PX,
            height=self.small_rows * SMALL_CELL_PX,
            highlightthickness=1, highlightbackground="#666")
        self.small_canvas.pack()
        self.small_canvas.bind("<Button-1>", self._on_small_paint)
        self.small_canvas.bind("<B1-Motion>", self._on_small_paint)
        self.small_canvas.bind("<Button-3>", self._on_small_erase)
        self.small_canvas.bind("<B3-Motion>", self._on_small_erase)

        self.auto_small = tk.BooleanVar(value=True)
        auto_row = tk.Frame(small_frame)
        auto_row.pack(pady=(4, 0), fill="x")
        tk.Checkbutton(
            auto_row, text="Auto-generate from big logo", variable=self.auto_small,
            command=self._on_auto_toggle,
        ).pack(side="left")
        tk.Button(auto_row, text="Regenerate now", command=self._regenerate_small).pack(
            side="left", padx=(6, 0))
        tk.Label(
            small_frame, fg="#666", justify="left",
            text="Paint the small logo directly to turn auto-generate off.",
        ).pack(pady=(4, 0), anchor="w")

        palette_frame = tk.Frame(main, pady=10)
        palette_frame.pack()
        tk.Label(palette_frame, text="Color:").pack(side="left")

        for name, rgb in PALETTE:
            self._add_swatch(palette_frame, rgb)

        tk.Button(palette_frame, text="Custom...", command=self._pick_custom_color).pack(
            side="left", padx=(8, 4))
        tk.Button(palette_frame, text="Eraser", command=self._select_eraser).pack(
            side="left", padx=4)

        self.selected_label = tk.Label(palette_frame, text="", width=10, relief="sunken")
        self.selected_label.pack(side="left", padx=(12, 0))
        self._update_selected_label()

        actions = tk.Frame(main, pady=6)
        actions.pack()
        tk.Button(actions, text="Clear", command=self._clear).pack(side="left", padx=4)
        tk.Button(actions, text="Open...", command=self._open_dialog).pack(side="left", padx=4)
        tk.Button(actions, text="Save As...", command=self._save_as_dialog).pack(side="left", padx=4)

        self.save_large = tk.BooleanVar(value=True)
        self.save_small = tk.BooleanVar(value=True)
        save_targets = tk.Frame(main)
        save_targets.pack(pady=(0, 4))
        tk.Label(save_targets, text="Save to a game directory:").pack(side="left")
        tk.Checkbutton(save_targets, text="Large logo", variable=self.save_large).pack(
            side="left", padx=(6, 0))
        tk.Checkbutton(save_targets, text="Small logo", variable=self.save_small).pack(
            side="left", padx=(6, 0))

        save_frame = tk.Frame(main, pady=6)
        save_frame.pack()
        tk.Label(save_frame, text="Save to existing game:").pack(side="left")
        game_names = [g.NAME for g in GAMES]
        self.game_var = tk.StringVar(value=game_names[0] if game_names else "")
        self.game_dropdown = ttk.Combobox(
            save_frame, textvariable=self.game_var, values=game_names,
            state="readonly", width=12)
        self.game_dropdown.pack(side="left", padx=4)
        tk.Button(save_frame, text="Save", command=self._save_to_selected_game).pack(
            side="left", padx=4)

        new_game_frame = tk.Frame(main, pady=6)
        new_game_frame.pack()
        tk.Label(new_game_frame, text="Save as new game named:").pack(side="left")
        self.new_game_var = tk.StringVar()
        tk.Entry(new_game_frame, textvariable=self.new_game_var, width=14).pack(
            side="left", padx=4)
        tk.Button(new_game_frame, text="Save New", command=self._save_new_game).pack(
            side="left", padx=4)
        tk.Label(
            new_game_frame, fg="#666",
            text="-> games/<name>/ (created if it doesn't exist yet)",
        ).pack(side="left", padx=(6, 0))

        self.status_label = tk.Label(main, text="", fg="#008000")
        self.status_label.pack(pady=(6, 0))

    def _add_swatch(self, parent, rgb):
        hexcolor = "#%02x%02x%02x" % rgb
        tk.Button(
            parent, bg=hexcolor, activebackground=hexcolor, width=2, relief="raised",
            command=lambda c=rgb: self._select_color(c),
        ).pack(side="left", padx=2)

    # ---- color selection ----

    def _select_color(self, rgb):
        self.current_color = rgb
        self._update_selected_label()

    def _select_eraser(self):
        self.current_color = None
        self._update_selected_label()

    def _update_selected_label(self):
        if self.current_color is None:
            self.selected_label.config(text="eraser", bg="#eeeeee")
        else:
            hexcolor = "#%02x%02x%02x" % self.current_color
            self.selected_label.config(text=hexcolor, bg=hexcolor)

    def _pick_custom_color(self):
        rgb, _ = colorchooser.askcolor(title="Pick a color")
        if rgb is None:
            return
        rgb = tuple(int(c) for c in rgb)
        self._add_swatch(self.selected_label.master, rgb)
        self._select_color(rgb)

    # ---- painting ----

    @staticmethod
    def _cell_at(event, cell_px, cols, rows):
        col, row = event.x // cell_px, event.y // cell_px
        if 0 <= row < rows and 0 <= col < cols:
            return row, col
        return None

    def _on_big_paint(self, event):
        cell = self._cell_at(event, CELL_PX, self.cols, self.rows)
        if cell:
            self.grid[cell[0]][cell[1]] = self.current_color
            self._redraw_big()
            if self.auto_small.get():
                self._regenerate_small()

    def _on_big_erase(self, event):
        cell = self._cell_at(event, CELL_PX, self.cols, self.rows)
        if cell:
            self.grid[cell[0]][cell[1]] = None
            self._redraw_big()
            if self.auto_small.get():
                self._regenerate_small()

    def _on_small_paint(self, event):
        cell = self._cell_at(event, SMALL_CELL_PX, self.small_cols, self.small_rows)
        if cell:
            self._stop_auto_small()
            self.small_grid[cell[0]][cell[1]] = self.current_color
            self._redraw_small()

    def _on_small_erase(self, event):
        cell = self._cell_at(event, SMALL_CELL_PX, self.small_cols, self.small_rows)
        if cell:
            self._stop_auto_small()
            self.small_grid[cell[0]][cell[1]] = None
            self._redraw_small()

    def _stop_auto_small(self):
        """A hand-edit on the small canvas takes it out of auto-generate
        mode, same as unchecking the box - editing it directly means you
        want it to stop following the big logo."""
        self.auto_small.set(False)

    def _on_auto_toggle(self):
        if self.auto_small.get():
            self._regenerate_small()

    def _regenerate_small(self):
        """Nearest-neighbor downsample of the big grid into small_grid -
        the same algorithm games/logo.py's load_logo (via Pillow) applies
        to a single logo.png at runtime, so this matches what the real
        menu shows when there's no separate logo_small.png."""
        self.small_grid = [
            [self.grid[min(self.rows - 1, ty * self.rows // self.small_rows)]
                       [min(self.cols - 1, tx * self.cols // self.small_cols)]
             for tx in range(self.small_cols)]
            for ty in range(self.small_rows)
        ]
        self._redraw_small()

    # ---- rendering ----

    def _redraw_big(self):
        self.big_canvas.delete("all")
        for row in range(self.rows):
            for col in range(self.cols):
                self._draw_cell(self.big_canvas, row, col, CELL_PX, self.grid[row][col])

    def _redraw_small(self):
        self.small_canvas.delete("all")
        for row in range(self.small_rows):
            for col in range(self.small_cols):
                self._draw_cell(self.small_canvas, row, col, SMALL_CELL_PX, self.small_grid[row][col])

    @staticmethod
    def _draw_cell(canvas, row, col, cell_px, color):
        x0, y0 = col * cell_px, row * cell_px
        x1, y1 = x0 + cell_px, y0 + cell_px
        if color is None:
            fill = CHECKER_LIGHT if (row + col) % 2 == 0 else CHECKER_DARK
        else:
            fill = "#%02x%02x%02x" % color
        canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#444")

    # ---- file operations ----

    def _clear(self):
        if messagebox.askyesno("Clear", "Clear both canvases?"):
            self.grid = blank_grid(self.cols, self.rows)
            self.small_grid = blank_grid(self.small_cols, self.small_rows)
            self.auto_small.set(True)
            self._redraw_big()
            self._redraw_small()
            self.status_label.config(text="")

    def _save_big_to_path(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        grid_to_image(self.grid, self.cols, self.rows).save(path)

    def _save_to_dir(self, directory):
        """Writes logo.png and/or logo_small.png alongside it, whichever
        of the Large logo/Small logo checkboxes above are on (both by
        default) - MenuGame prefers logo_small.png over an auto-shrunk
        logo.png whenever it exists."""
        os.makedirs(directory, exist_ok=True)
        saved = []

        if self.save_large.get():
            big_path = os.path.join(directory, "logo.png")
            grid_to_image(self.grid, self.cols, self.rows).save(big_path)
            saved.append(big_path)

        if self.save_small.get():
            small_path = os.path.join(directory, "logo_small.png")
            grid_to_image(self.small_grid, self.small_cols, self.small_rows).save(small_path)
            saved.append(small_path)

        if saved:
            self.status_label.config(text=f"Saved {' and '.join(saved)}")
        else:
            self.status_label.config(text="Nothing saved - check Large logo/Small logo above")

    def _save_to_selected_game(self):
        name = self.game_var.get()
        game_cls = next((g for g in GAMES if g.NAME == name), None)
        if game_cls is None:
            messagebox.showerror("Save", "No game selected")
            return
        self._save_to_dir(game_dir_for(game_cls))

    def _save_new_game(self):
        name = self.new_game_var.get().strip()
        if not name:
            messagebox.showerror("Save New", "Enter a game name first")
            return
        self._save_to_dir(new_game_dir_for(name))

    def _save_as_dialog(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG image", "*.png")],
            initialfile="logo.png", title="Save the big logo as")
        if path:
            self._save_big_to_path(path)
            self.status_label.config(text=f"Saved {path}")

    def _open_dialog(self):
        path = filedialog.askopenfilename(
            filetypes=[("PNG image", "*.png")], title="Open an existing logo.png")
        if not path:
            return
        self.grid = load_grid_from_image(path, self.cols, self.rows)
        self._redraw_big()

        small_path = os.path.join(os.path.dirname(path), "logo_small.png")
        if os.path.exists(small_path):
            self.small_grid = load_grid_from_image(small_path, self.small_cols, self.small_rows)
            self.auto_small.set(False)
            self._redraw_small()
            self.status_label.config(text=f"Opened {path} and {small_path}")
        else:
            self.auto_small.set(True)
            self._regenerate_small()
            self.status_label.config(text=f"Opened {path}")


def main():
    root = tk.Tk()
    LogoEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
