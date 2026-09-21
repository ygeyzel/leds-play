#!/usr/bin/env python3
"""View every glyph in games/menu/font.py at once, sim-style (lit/unlit
LED cells), and edit them by clicking pixels. Saving rewrites just the
_GLYPHS dict in font.py, in place - everything else in that file (the
FONT_HEIGHT/FONT_WIDTH constants, glyph_shape/text_shape) is left alone.

Run with: python3 tools/font_editor.py
"""
import importlib
import os
import re
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from games.menu import font as font_module  # noqa: E402

FONT_PATH = font_module.__file__

OVERVIEW_CELL_PX = 4
EDIT_CELL_PX = 32
LIT_COLOR = "#39ff6a"
UNLIT_COLOR = "#151515"
GRID_LINE = "#2a2a2a"
CHARS_PER_ROW = 9

# The app itself only ever looks up uppercase (menu text is .upper()'d
# before rendering), so _GLYPHS in font.py normally has no lowercase
# entries - but the editor still shows a-z as blank, editable slots
# alongside everything else, in case a game name (or a future caller)
# ever wants them styled differently from their uppercase form.
ALL_CHARS = (
    [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    + [chr(c) for c in range(ord("a"), ord("z") + 1)]
    + [str(d) for d in range(10)]
    + [" "]
)


def load_glyphs():
    """A fresh char -> list-of-row-strings copy of font_module's _GLYPHS,
    filled out to ALL_CHARS (missing ones start blank) so editing it
    doesn't mutate the live module."""
    existing = font_module._GLYPHS
    blank = ["0" * font_module.FONT_WIDTH for _ in range(font_module.FONT_HEIGHT)]
    return {ch: list(existing[ch]) if ch in existing else list(blank) for ch in ALL_CHARS}


def sort_key(ch):
    if ch.isalpha():
        return (0, ch)
    if ch.isdigit():
        return (1, ch)
    return (2, ch)


def is_blank(rows) -> bool:
    blank_row = "0" * font_module.FONT_WIDTH
    return all(row == blank_row for row in rows)


def write_glyphs(glyphs, keep_if_blank):
    """Rewrites just the _GLYPHS = {...} block in font.py, leaving the
    rest of the file (docstring, FONT_HEIGHT/WIDTH, functions) untouched.
    A blank glyph is only written if `keep_if_blank(ch)` says so -
    otherwise every untouched ALL_CHARS placeholder (e.g. all of a-z,
    normally) would flood the file. A character that was already in
    font.py stays even if cleared to blank, since that's a deliberate
    edit."""
    dict_lines = ["_GLYPHS = {"]
    for ch in sorted(glyphs, key=sort_key):
        rows = glyphs[ch]
        if is_blank(rows) and not keep_if_blank(ch):
            continue
        row_src = ", ".join(f'"{r}"' for r in rows)
        dict_lines.append(f"    {ch!r}: [{row_src}],")
    dict_lines.append("}")
    new_dict_src = "\n".join(dict_lines)

    with open(FONT_PATH) as file:
        content = file.read()

    new_content, count = re.subn(
        r"_GLYPHS = \{.*?\n\}", lambda _match: new_dict_src, content,
        count=1, flags=re.DOTALL)
    if count == 0:
        raise RuntimeError(f"couldn't find a _GLYPHS = {{...}} block in {FONT_PATH}")

    with open(FONT_PATH, "w") as file:
        file.write(new_content)


class FontEditor:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("LEDs Play - Font Editor")

        self.width = font_module.FONT_WIDTH
        self.height = font_module.FONT_HEIGHT
        self.glyphs = load_glyphs()
        self.original_chars = set(font_module._GLYPHS)
        self.selected_char = sorted(self.glyphs, key=sort_key)[0]
        self.overview_canvases = {}

        self._build_ui()
        self._redraw_overview()
        self._redraw_editor()

    # ---- UI construction ----

    def _build_ui(self):
        main = tk.Frame(self.root, padx=10, pady=10)
        main.pack()

        top = tk.Frame(main)
        top.pack(fill="x")
        tk.Label(top, text=f"All glyphs ({self.width}x{self.height}) - click one to edit:").pack(side="left")
        tk.Button(top, text="Add character...", command=self._add_char).pack(side="right")

        self.overview_frame = tk.Frame(main, pady=6)
        self.overview_frame.pack()

        editor_row = tk.Frame(main, pady=10)
        editor_row.pack()
        self.editor_label = tk.Label(editor_row, text="", font=("TkDefaultFont", 14, "bold"))
        self.editor_label.pack()
        self.editor_canvas = tk.Canvas(
            editor_row, width=self.width * EDIT_CELL_PX, height=self.height * EDIT_CELL_PX,
            highlightthickness=1, highlightbackground="#666")
        self.editor_canvas.pack(pady=(4, 0))
        self.editor_canvas.bind("<Button-1>", self._on_edit_click)

        actions = tk.Frame(main, pady=8)
        actions.pack()
        tk.Button(actions, text="Clear glyph", command=self._clear_glyph).pack(side="left", padx=4)
        tk.Button(actions, text="Reload from font.py", command=self._reload).pack(side="left", padx=4)
        tk.Button(actions, text="Save to font.py", command=self._save).pack(side="left", padx=4)

        self.status_label = tk.Label(main, text=f"Editing {FONT_PATH}", fg="#666")
        self.status_label.pack(pady=(4, 0))

    def _build_overview_grid(self):
        for widget in self.overview_frame.winfo_children():
            widget.destroy()
        self.overview_canvases = {}

        for idx, ch in enumerate(sorted(self.glyphs, key=sort_key)):
            row, col = divmod(idx, CHARS_PER_ROW)
            cell = tk.Frame(self.overview_frame)
            cell.grid(row=row, column=col, padx=4, pady=4)
            border = "#e00" if ch == self.selected_char else "#666"
            canvas = tk.Canvas(
                cell, width=self.width * OVERVIEW_CELL_PX, height=self.height * OVERVIEW_CELL_PX,
                highlightthickness=2, highlightbackground=border)
            canvas.pack()
            canvas.bind("<Button-1>", lambda _event, c=ch: self._select_char(c))
            tk.Label(cell, text="' '" if ch == " " else ch).pack()
            self.overview_canvases[ch] = canvas

    # ---- rendering ----

    def _redraw_overview(self):
        self._build_overview_grid()
        for ch, canvas in self.overview_canvases.items():
            self._draw_glyph(canvas, self.glyphs[ch], OVERVIEW_CELL_PX)

    def _redraw_editor(self):
        label = "' ' (space)" if self.selected_char == " " else f"'{self.selected_char}'"
        self.editor_label.config(text=label)
        self._draw_glyph(self.editor_canvas, self.glyphs[self.selected_char], EDIT_CELL_PX)

    @staticmethod
    def _draw_glyph(canvas, rows, cell_px):
        canvas.delete("all")
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                x0, y0 = c * cell_px, r * cell_px
                fill = LIT_COLOR if bit == "1" else UNLIT_COLOR
                canvas.create_rectangle(
                    x0, y0, x0 + cell_px, y0 + cell_px, fill=fill, outline=GRID_LINE)

    # ---- editing ----

    def _select_char(self, ch):
        self.selected_char = ch
        self._redraw_overview()
        self._redraw_editor()

    def _on_edit_click(self, event):
        col, row = event.x // EDIT_CELL_PX, event.y // EDIT_CELL_PX
        if 0 <= row < self.height and 0 <= col < self.width:
            current_row = self.glyphs[self.selected_char][row]
            flipped = "0" if current_row[col] == "1" else "1"
            self.glyphs[self.selected_char][row] = current_row[:col] + flipped + current_row[col + 1:]
            self._redraw_editor()
            self._draw_glyph(
                self.overview_canvases[self.selected_char], self.glyphs[self.selected_char],
                OVERVIEW_CELL_PX)

    def _clear_glyph(self):
        self.glyphs[self.selected_char] = ["0" * self.width for _ in range(self.height)]
        self._redraw_editor()
        self._draw_glyph(
            self.overview_canvases[self.selected_char], self.glyphs[self.selected_char],
            OVERVIEW_CELL_PX)

    def _add_char(self):
        typed = simpledialog.askstring("Add character", "Character to add:")
        if not typed:
            return
        ch = typed[0]
        if ch not in self.glyphs:
            self.glyphs[ch] = ["0" * self.width for _ in range(self.height)]
        self.selected_char = ch
        self._redraw_overview()
        self._redraw_editor()

    # ---- file operations ----

    def _reload(self):
        if not messagebox.askyesno("Reload", "Discard changes and reload from font.py?"):
            return
        importlib.reload(font_module)
        self.glyphs = load_glyphs()
        self.original_chars = set(font_module._GLYPHS)
        if self.selected_char not in self.glyphs:
            self.selected_char = sorted(self.glyphs, key=sort_key)[0]
        self._redraw_overview()
        self._redraw_editor()
        self.status_label.config(text=f"Reloaded {FONT_PATH}")

    def _save(self):
        write_glyphs(self.glyphs, keep_if_blank=lambda ch: ch in self.original_chars)
        # Whatever just got written (non-blank, or already there before)
        # is "original" from here on, so re-clearing it to blank later
        # in this same session still counts as a deliberate edit worth
        # keeping, not a fresh placeholder to skip.
        self.original_chars = {ch for ch, rows in self.glyphs.items() if not is_blank(rows)} \
            | self.original_chars
        self.status_label.config(text=f"Saved {FONT_PATH}")


def main():
    root = tk.Tk()
    FontEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
