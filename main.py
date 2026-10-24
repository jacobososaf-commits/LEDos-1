import json
import os
import time
import math
import platform
import sys
import tkinter as tk
from tkinter import colorchooser
from pathlib import Path


# ============================================================
# LEDos 1.5
# ============================================================

OS_NAME = "LEDos 1"
RELEASE_VERSION = "1.5"

BASE_DIR = Path(__file__).resolve().parent

FS_FILE = BASE_DIR / "ledos_fs.json"
SETTINGS_FILE = BASE_DIR / "ledos_settings.json"

BG = "#BFBFBF"
FACE = "#D4D0C8"
WHITE = "#FFFFFF"
BLACK = "#000000"
GRAY = "#808080"
DARK_GRAY = "#404040"

TITLE_BLUE = "#000080"

ORANGE = "#FF8000"
ORANGE_DARK = "#C06000"

FONT = ("Courier New", 10)
FONT_BOLD = ("Courier New", 10, "bold")
FONT_SMALL = ("Courier New", 9)
FONT_BIG = ("Courier New", 16, "bold")


# ============================================================
# BUTTON
# ============================================================

class LEDosButton(tk.Button):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("bg", FACE)
        kwargs.setdefault("fg", BLACK)
        kwargs.setdefault("activebackground", ORANGE)
        kwargs.setdefault("activeforeground", BLACK)
        kwargs.setdefault("font", FONT)
        kwargs.setdefault("relief", "raised")
        kwargs.setdefault("bd", 2)

        super().__init__(master, **kwargs)


# ============================================================
# VIRTUAL FILESYSTEM
# ============================================================

class VirtualFS:
    def __init__(self, filename=FS_FILE):
        self.filename = filename

        self.root = {
            "type": "dir",
            "children": {}
        }

        self.load()
        self.create_defaults()

    def load(self):
        try:
            if os.path.exists(self.filename):
                with open(
                    self.filename,
                    "r",
                    encoding="utf-8"
                ) as f:
                    data = json.load(f)

                if (
                    isinstance(data, dict)
                    and data.get("type") == "dir"
                ):
                    self.root = data
                else:
                    self.root = {
                        "type": "dir",
                        "children": {}
                    }

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError
        ):
            self.root = {
                "type": "dir",
                "children": {}
            }

        self.normalize()

    def save(self):
        try:
            with open(
                self.filename,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    self.root,
                    f,
                    indent=2
                )
        except OSError:
            pass

    def normalize(self):
        if not isinstance(self.root, dict):
            self.root = {
                "type": "dir",
                "children": {}
            }

        if self.root.get("type") != "dir":
            self.root["type"] = "dir"

        if not isinstance(
            self.root.get("children"),
            dict
        ):
            self.root["children"] = {}

    def normalize_path(self, path):
        if not path:
            return ["C:"]

        path = path.replace("\\", "/")

        if path in ("C:", "C:/"):
            return ["C:"]

        if path.startswith("C:/"):
            path = path[3:]

        parts = [
            part
            for part in path.split("/")
            if part and part != "."
        ]

        result = ["C:"]

        for part in parts:
            if part == "..":
                if len(result) > 1:
                    result.pop()
            else:
                result.append(part)

        return result

    def valid_name(self, name):
        if not name:
            return False

        if name in (".", ".."):
            return False

        illegal = '<>:"/\\|?*'

        if any(
            char in name
            for char in illegal
        ):
            return False

        return True

    def get_node(self, path):
        parts = self.normalize_path(path)

        if parts == ["C:"]:
            return self.root

        node = self.root

        for part in parts[1:]:
            if node.get("type") != "dir":
                return None

            children = node.get(
                "children",
                {}
            )

            if part not in children:
                return None

            node = children[part]

        return node

    def exists(self, path):
        return self.get_node(path) is not None

    def parent(self, path):
        parts = self.normalize_path(path)

        if len(parts) <= 1:
            return None

        return self.get_node(
            "/".join(parts[:-1])
        )

    def mkdir(self, path):
        parts = self.normalize_path(path)

        if len(parts) <= 1:
            return False

        name = parts[-1]

        if not self.valid_name(name):
            return False

        parent = self.get_node(
            "/".join(parts[:-1])
        )

        if not parent:
            return False

        if parent.get("type") != "dir":
            return False

        children = parent.setdefault(
            "children",
            {}
        )

        if name in children:
            return False

        children[name] = {
            "type": "dir",
            "children": {}
        }

        self.save()
        return True

    def write_file(self, path, content):
        parts = self.normalize_path(path)

        if len(parts) <= 1:
            return False

        name = parts[-1]

        if not self.valid_name(name):
            return False

        parent = self.get_node(
            "/".join(parts[:-1])
        )

        if not parent:
            return False

        if parent.get("type") != "dir":
            return False

        parent.setdefault(
            "children",
            {}
        )[name] = {
            "type": "file",
            "content": str(content)
        }

        self.save()
        return True

    def read_file(self, path):
        node = self.get_node(path)

        if not node:
            return None

        if node.get("type") != "file":
            return None

        return node.get(
            "content",
            ""
        )

    def delete(self, path):
        parts = self.normalize_path(path)

        if len(parts) <= 1:
            return False

        name = parts[-1]

        parent = self.get_node(
            "/".join(parts[:-1])
        )

        if not parent:
            return False

        children = parent.get(
            "children",
            {}
        )

        if name not in children:
            return False

        del children[name]

        self.save()
        return True

    def entries(self, path):
        node = self.get_node(path)

        if not node:
            return []

        if node.get("type") != "dir":
            return []

        entries = []

        for name, data in node.get(
            "children",
            {}
        ).items():
            entries.append({
                "name": name,
                "type": data.get(
                    "type",
                    "file"
                )
            })

        entries.sort(
            key=lambda item: (
                item["type"] != "dir",
                item["name"].lower()
            )
        )

        return entries

    def create_defaults(self):
        folders = [
            "C:/SYSTEM",
            "C:/PROGRAMS",
            "C:/DOCUMENTS",
            "C:/GAMES"
        ]

        for folder in folders:
            if not self.exists(folder):
                self.mkdir(folder)

        if not self.exists(
            "C:/DOCUMENTS/README.TXT"
        ):
            self.write_file(
                "C:/DOCUMENTS/README.TXT",
                (
                    "Welcome to LEDos 1!\n\n"
                    "This is a tiny fictional operating "
                    "system built with Python and Tkinter.\n\n"
                    "Enjoy exploring LEDos."
                )
            )

        self.save()


# ============================================================
# LEDos WINDOW
# ============================================================

class LEDosWindow:
    offset = 0

    def __init__(
        self,
        app,
        title,
        width=500,
        height=350
    ):
        self.app = app

        self.frame = tk.Frame(
            app.desktop,
            bg=BLACK,
            bd=1,
            relief="solid"
        )

        offset = (
            LEDosWindow.offset * 25
        ) % 180

        LEDosWindow.offset += 1

        x = 150 + offset
        y = 80 + offset

        self.frame.place(
            x=x,
            y=y,
            width=width,
            height=height
        )

        self.titlebar = tk.Frame(
            self.frame,
            bg=TITLE_BLUE,
            height=25
        )
        self.titlebar.pack(
            fill="x"
        )

        self.title_label = tk.Label(
            self.titlebar,
            text=title,
            bg=TITLE_BLUE,
            fg=WHITE,
            font=FONT_BOLD,
            anchor="w"
        )
        self.title_label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        self.close_button = tk.Button(
            self.titlebar,
            text="X",
            bg=FACE,
            fg=BLACK,
            activebackground=ORANGE,
            activeforeground=BLACK,
            font=FONT_BOLD,
            width=3,
            relief="raised",
            bd=1,
            command=self.close
        )
        self.close_button.pack(
            side="right",
            padx=2,
            pady=2
        )

        self.content = tk.Frame(
            self.frame,
            bg=FACE
        )
        self.content.pack(
            fill="both",
            expand=True
        )

        for widget in (
            self.frame,
            self.titlebar,
            self.title_label
        ):
            widget.bind(
                "<Button-1>",
                lambda event: self.bring_front()
            )

        self.titlebar.bind(
            "<ButtonPress-1>",
            self.drag_start
        )

        self.titlebar.bind(
            "<B1-Motion>",
            self.drag_move
        )

        self.title_label.bind(
            "<ButtonPress-1>",
            self.drag_start
        )

        self.title_label.bind(
            "<B1-Motion>",
            self.drag_move
        )

        self.bring_front()

    def drag_start(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def drag_move(self, event):
        try:
            x = (
                self.frame.winfo_x()
                + event.x
                - self.drag_x
            )

            y = (
                self.frame.winfo_y()
                + event.y
                - self.drag_y
            )

            x = max(0, x)
            y = max(0, y)

            desktop_width = (
                self.app.desktop.winfo_width()
            )

            desktop_height = (
                self.app.desktop.winfo_height()
            )

            max_x = (
                desktop_width
                - self.frame.winfo_width()
            )

            max_y = (
                desktop_height
                - self.frame.winfo_height()
            )

            if max_x > 0:
                x = min(x, max_x)

            if max_y > 0:
                y = min(y, max_y)

            self.frame.place(
                x=x,
                y=y
            )

            self.bring_front()

        except tk.TclError:
            pass

    def bring_front(self):
        try:
            if self.frame.winfo_exists():
                self.frame.lift()
        except tk.TclError:
            pass

    def close(self):
        try:
            if self.frame.winfo_exists():
                self.frame.destroy()
        except tk.TclError:
            pass


# ============================================================
# ERROR DIALOG
# ============================================================

class ErrorDialog:
    @staticmethod
    def show(app, message):
        win = LEDosWindow(
            app,
            "LEDos Error",
            420,
            190
        )

        content = win.content

        icon = tk.Label(
            content,
            text="!",
            bg=app.secondary_color,
            fg=BLACK,
            font=("Courier New", 22, "bold"),
            width=3
        )
        icon.pack(
            pady=(25, 10)
        )

        label = tk.Label(
            content,
            text=message,
            bg=FACE,
            fg=BLACK,
            font=FONT,
            wraplength=350
        )
        label.pack(
            pady=5
        )

        LEDosButton(
            content,
            text="OK",
            command=win.close
        ).pack(
            pady=10
        )


# ============================================================
# FILE MANAGER
# ============================================================

class FileManager:
    def __init__(self, app):
        self.app = app
        self.current_path = "C:"

        self.win = LEDosWindow(
            app,
            "File Manager",
            650,
            470
        )

        content = self.win.content

        top = tk.Frame(
            content,
            bg=FACE
        )
        top.pack(
            fill="x",
            padx=8,
            pady=8
        )

        tk.Label(
            top,
            text="Path:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack(
            side="left"
        )

        self.path_entry = tk.Entry(
            top,
            bg=WHITE,
            fg=BLACK,
            font=FONT
        )
        self.path_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        LEDosButton(
            top,
            text="GO",
            command=self.go_path
        ).pack(
            side="left"
        )

        toolbar = tk.Frame(
            content,
            bg=FACE
        )
        toolbar.pack(
            fill="x",
            padx=8
        )

        LEDosButton(
            toolbar,
            text="New Folder",
            command=self.new_folder
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            toolbar,
            text="New File",
            command=self.new_file
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            toolbar,
            text="Open",
            command=self.open_selected
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            toolbar,
            text="Delete",
            command=self.delete_selected
        ).pack(
            side="left",
            padx=2
        )

        list_frame = tk.Frame(
            content,
            bg=FACE
        )
        list_frame.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        self.listbox = tk.Listbox(
            list_frame,
            bg=WHITE,
            fg=BLACK,
            selectbackground=TITLE_BLUE,
            selectforeground=WHITE,
            font=FONT
        )
        self.listbox.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = tk.Scrollbar(
            list_frame,
            command=self.listbox.yview
        )
        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.listbox.config(
            yscrollcommand=scrollbar.set
        )

        self.listbox.bind(
            "<Double-Button-1>",
            lambda event: self.open_selected()
        )

        self.refresh()

    def refresh(self):
        self.listbox.delete(
            0,
            tk.END
        )

        self.path_entry.delete(
            0,
            tk.END
        )

        self.path_entry.insert(
            0,
            self.current_path
        )

        entries = self.app.fs.entries(
            self.current_path
        )

        for entry in entries:
            prefix = (
                "[DIR] "
                if entry["type"] == "dir"
                else "      "
            )

            self.listbox.insert(
                tk.END,
                prefix + entry["name"]
            )

    def go_path(self):
        path = self.path_entry.get().strip()

        node = self.app.fs.get_node(path)

        if node and node.get("type") == "dir":
            self.current_path = (
                "/".join(
                    self.app.fs.normalize_path(path)
                )
            )

            self.refresh()
            return

        ErrorDialog.show(
            self.app,
            "Directory not found."
        )

    def selected_entry(self):
        selection = self.listbox.curselection()

        if not selection:
            return None

        text = self.listbox.get(
            selection[0]
        )

        if text.startswith("[DIR] "):
            name = text[6:]
            entry_type = "dir"
        else:
            name = text.strip()
            entry_type = "file"

        return name, entry_type

    def new_folder(self):
        self.app.prompt(
            "New Folder",
            "Folder name:",
            self.create_folder
        )

    def create_folder(self, name):
        name = name.strip()

        if not self.app.fs.valid_name(name):
            ErrorDialog.show(
                self.app,
                "Invalid folder name."
            )
            return

        path = (
            self.current_path
            + "/"
            + name
        )

        if not self.app.fs.mkdir(path):
            ErrorDialog.show(
                self.app,
                "Could not create folder."
            )

        self.refresh()

    def new_file(self):
        self.app.prompt(
            "New File",
            "File name:",
            self.create_file
        )

    def create_file(self, name):
        name = name.strip()

        if not self.app.fs.valid_name(name):
            ErrorDialog.show(
                self.app,
                "Invalid file name."
            )
            return

        path = (
            self.current_path
            + "/"
            + name
        )

        if not self.app.fs.write_file(
            path,
            ""
        ):
            ErrorDialog.show(
                self.app,
                "Could not create file."
            )

        self.refresh()

    def open_selected(self):
        selected = self.selected_entry()

        if not selected:
            return

        name, entry_type = selected

        path = (
            self.current_path
            + "/"
            + name
        )

        if entry_type == "dir":
            self.current_path = path
            self.refresh()
        else:
            self.app.open_notepad(path)

    def delete_selected(self):
        selected = self.selected_entry()

        if not selected:
            return

        name, _ = selected

        path = (
            self.current_path
            + "/"
            + name
        )

        if not self.app.fs.delete(path):
            ErrorDialog.show(
                self.app,
                "Could not delete item."
            )

        self.refresh()


# ============================================================
# NOTEPAD
# ============================================================

class Notepad:
    def __init__(self, app, path=None):
        self.app = app
        self.path = path

        self.win = LEDosWindow(
            app,
            "Notepad",
            650,
            470
        )

        content = self.win.content

        toolbar = tk.Frame(
            content,
            bg=FACE
        )
        toolbar.pack(
            fill="x",
            padx=5,
            pady=5
        )

        LEDosButton(
            toolbar,
            text="New",
            command=self.new
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            toolbar,
            text="Open",
            command=self.open
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            toolbar,
            text="Save",
            command=self.save
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            toolbar,
            text="Save As",
            command=self.save_as
        ).pack(
            side="left",
            padx=2
        )

        self.path_entry = tk.Entry(
            content,
            bg=WHITE,
            fg=BLACK,
            font=FONT
        )
        self.path_entry.pack(
            fill="x",
            padx=8,
            pady=(0, 5)
        )

        self.text = tk.Text(
            content,
            bg=WHITE,
            fg=BLACK,
            insertbackground=BLACK,
            font=FONT,
            undo=True
        )
        self.text.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        if path:
            self.path_entry.insert(
                0,
                path
            )
            self.load_path(path)

    def new(self):
        self.text.delete(
            "1.0",
            tk.END
        )

        self.path = None

        self.path_entry.delete(
            0,
            tk.END
        )

    def open(self):
        self.app.prompt(
            "Open File",
            "Path:",
            self.open_path
        )

    def open_path(self, path):
        path = path.strip()

        content = self.app.fs.read_file(
            path
        )

        if content is None:
            ErrorDialog.show(
                self.app,
                "File not found."
            )
            return

        self.path = path

        self.path_entry.delete(
            0,
            tk.END
        )

        self.path_entry.insert(
            0,
            path
        )

        self.text.delete(
            "1.0",
            tk.END
        )

        self.text.insert(
            "1.0",
            content
        )

    def load_path(self, path):
        content = self.app.fs.read_file(
            path
        )

        if content is not None:
            self.text.insert(
                "1.0",
                content
            )

    def save(self):
        path = self.path_entry.get().strip()

        if not path:
            self.save_as()
            return

        self.save_to(path)

    def save_as(self):
        self.app.prompt(
            "Save As",
            "Path:",
            self.save_to
        )

    def save_to(self, path):
        path = path.strip()

        parts = self.app.fs.normalize_path(
            path
        )

        if len(parts) <= 1:
            ErrorDialog.show(
                self.app,
                "Please enter a file path."
            )
            return

        if not self.app.fs.valid_name(
            parts[-1]
        ):
            ErrorDialog.show(
                self.app,
                "Invalid file name."
            )
            return

        content = self.text.get(
            "1.0",
            "end-1c"
        )

        if not self.app.fs.write_file(
            path,
            content
        ):
            ErrorDialog.show(
                self.app,
                "Could not save file."
            )
            return

        self.path = path

        self.path_entry.delete(
            0,
            tk.END
        )

        self.path_entry.insert(
            0,
            path
        )


# ============================================================
# CALCULATOR
# ============================================================

class Calculator:
    def __init__(self, app):
        self.app = app
        self.expression = ""

        self.win = LEDosWindow(
            app,
            "Calculator",
            330,
            430
        )

        content = self.win.content

        self.display = tk.Entry(
            content,
            bg=WHITE,
            fg=BLACK,
            font=("Courier New", 18),
            justify="right"
        )

        self.display.pack(
            fill="x",
            padx=10,
            pady=15
        )

        buttons = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", "(", ")", "+"]
        ]

        for row in buttons:
            frame = tk.Frame(
                content,
                bg=FACE
            )
            frame.pack(
                fill="x"
            )

            for value in row:
                LEDosButton(
                    frame,
                    text=value,
                    width=5,
                    command=lambda v=value: self.add(v)
                ).pack(
                    side="left",
                    expand=True,
                    padx=2,
                    pady=2
                )

        bottom = tk.Frame(
            content,
            bg=FACE
        )
        bottom.pack(
            fill="x",
            pady=8
        )

        LEDosButton(
            bottom,
            text="C",
            width=7,
            command=self.clear
        ).pack(
            side="left",
            expand=True,
            padx=4
        )

        LEDosButton(
            bottom,
            text="=",
            width=7,
            command=self.calculate
        ).pack(
            side="left",
            expand=True,
            padx=4
        )

    def add(self, value):
        self.expression += value

        self.display.delete(
            0,
            tk.END
        )

        self.display.insert(
            0,
            self.expression
        )

    def clear(self):
        self.expression = ""

        self.display.delete(
            0,
            tk.END
        )

    def calculate(self):
        if not self.expression:
            return

        allowed = set(
            "0123456789+-*/(). "
        )

        if any(
            char not in allowed
            for char in self.expression
        ):
            ErrorDialog.show(
                self.app,
                "Invalid calculator expression."
            )
            return

        try:
            result = eval(
                self.expression,
                {
                    "__builtins__": {}
                },
                {}
            )

            self.expression = str(result)

            self.display.delete(
                0,
                tk.END
            )

            self.display.insert(
                0,
                self.expression
            )

        except Exception:
            ErrorDialog.show(
                self.app,
                "Invalid calculation."
            )


# ============================================================
# PAINT 1.4
# ============================================================

class Paint:
    WIDTH = 720
    HEIGHT = 390

    def __init__(self, app):
        self.app = app

        # ----------------------------------------------------
        # IMPORTANT:
        # These MUST exist before render_all() can ever run.
        # ----------------------------------------------------

        self.destroyed = False
        self.playing = False
        self.play_job = None

        self.current_color = BLACK
        self.tool = "pencil"

        self.frames = []
        self.current_frame = 0

        self.drawing = False
        self.start_x = None
        self.start_y = None

        self.fps = 8

        self.pixels = self.blank_frame()

        self.frames.append(
            self.pixels
        )

        self.win = LEDosWindow(
            app,
            "Paint 1.4",
            850,
            610
        )

        content = self.win.content

        # ----------------------------------------------------
        # TOOLBAR
        # ----------------------------------------------------

        toolbar = tk.Frame(
            content,
            bg=FACE
        )
        toolbar.pack(
            fill="x",
            padx=5,
            pady=5
        )

        tools = [
            ("Pencil", "pencil"),
            ("Eraser", "eraser"),
            ("Rectangle", "rectangle"),
            ("Oval", "oval"),
            ("Fill", "fill")
        ]

        for text, tool in tools:
            LEDosButton(
                toolbar,
                text=text,
                command=lambda t=tool: self.set_tool(t)
            ).pack(
                side="left",
                padx=2
            )

        LEDosButton(
            toolbar,
            text="Clear",
            command=self.clear
        ).pack(
            side="left",
            padx=2
        )

        # ----------------------------------------------------
        # ANIMATION BAR
        # ----------------------------------------------------

        animation_bar = tk.Frame(
            content,
            bg=FACE
        )
        animation_bar.pack(
            fill="x",
            padx=5,
            pady=(0, 5)
        )

        LEDosButton(
            animation_bar,
            text="New Frame",
            command=self.new_frame
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            animation_bar,
            text="Duplicate",
            command=self.duplicate_frame
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            animation_bar,
            text="< Prev",
            command=self.previous_frame
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            animation_bar,
            text="Next >",
            command=self.next_frame
        ).pack(
            side="left",
            padx=2
        )

        LEDosButton(
            animation_bar,
            text="Delete Frame",
            command=self.delete_frame
        ).pack(
            side="left",
            padx=2
        )

        self.play_button = LEDosButton(
            animation_bar,
            text="Play",
            command=self.toggle_playback
        )
        self.play_button.pack(
            side="left",
            padx=8
        )

        tk.Label(
            animation_bar,
            text="FPS:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack(
            side="left"
        )

        self.fps_var = tk.IntVar(
            value=self.fps
        )

        self.fps_spin = tk.Spinbox(
            animation_bar,
            from_=1,
            to=30,
            width=4,
            textvariable=self.fps_var,
            font=FONT
        )

        self.fps_spin.pack(
            side="left",
            padx=3
        )

        self.frame_label = tk.Label(
            animation_bar,
            text="Frame 1 / 1",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        )

        self.frame_label.pack(
            side="left",
            padx=10
        )

        # ----------------------------------------------------
        # PALETTE
        # ----------------------------------------------------

        palette = tk.Frame(
            content,
            bg=FACE
        )
        palette.pack(
            fill="x",
            padx=5,
            pady=3
        )

        colors = [
            ("Black", BLACK),
            ("White", WHITE),
            ("Gray", GRAY),
            ("Red", "#FF0000"),
            ("Green", "#008000"),
            ("Blue", "#0000FF"),
            ("Yellow", "#FFFF00"),
            ("Orange", ORANGE)
        ]

        for name, color in colors:
            tk.Button(
                palette,
                bg=color,
                fg=BLACK,
                width=4,
                height=1,
                relief="raised",
                bd=2,
                command=lambda c=color: self.set_color(c)
            ).pack(
                side="left",
                padx=2
            )

        # ----------------------------------------------------
        # CANVAS
        # ----------------------------------------------------

        canvas_frame = tk.Frame(
            content,
            bg=DARK_GRAY
        )
        canvas_frame.pack(
            padx=8,
            pady=5
        )

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg=WHITE,
            highlightthickness=1,
            highlightbackground=BLACK
        )
        self.canvas.pack()

        self.photo = tk.PhotoImage(
            width=self.WIDTH,
            height=self.HEIGHT
        )

        self.canvas.create_image(
            0,
            0,
            image=self.photo,
            anchor="nw"
        )

        self.canvas.bind(
            "<ButtonPress-1>",
            self.start
        )

        self.canvas.bind(
            "<B1-Motion>",
            self.draw
        )

        self.canvas.bind(
            "<ButtonRelease-1>",
            self.finish
        )

        # ----------------------------------------------------
        # FIX:
        # destroyed is already initialized above.
        # ----------------------------------------------------

        self.render_all()

        self.win.frame.bind(
            "<Destroy>",
            self.on_destroy
        )

    # --------------------------------------------------------
    # FRAME DATA
    # --------------------------------------------------------

    def blank_frame(self):
        return [
            [WHITE for _ in range(self.WIDTH)]
            for _ in range(self.HEIGHT)
        ]

    def copy_frame(self, frame):
        return [
            row[:]
            for row in frame
        ]

    def save_current_frame(self):
        if (
            0 <= self.current_frame
            < len(self.frames)
        ):
            self.frames[
                self.current_frame
            ] = self.pixels

    def load_frame(self, index):
        if not (
            0 <= index
            < len(self.frames)
        ):
            return

        self.save_current_frame()

        self.current_frame = index
        self.pixels = self.frames[index]

        self.render_all()
        self.update_frame_label()

    def update_frame_label(self):
        try:
            self.frame_label.config(
                text=(
                    f"Frame "
                    f"{self.current_frame + 1}"
                    f" / "
                    f"{len(self.frames)}"
                )
            )
        except tk.TclError:
            pass

    def new_frame(self):
        if self.playing:
            self.stop_playback()

        self.save_current_frame()

        self.frames.insert(
            self.current_frame + 1,
            self.blank_frame()
        )

        self.current_frame += 1

        self.pixels = self.frames[
            self.current_frame
        ]

        self.render_all()
        self.update_frame_label()

    def duplicate_frame(self):
        if self.playing:
            self.stop_playback()

        self.save_current_frame()

        new_frame = self.copy_frame(
            self.pixels
        )

        self.frames.insert(
            self.current_frame + 1,
            new_frame
        )

        self.current_frame += 1
        self.pixels = new_frame

        self.render_all()
        self.update_frame_label()

    def previous_frame(self):
        if len(self.frames) <= 1:
            return

        self.load_frame(
            (
                self.current_frame - 1
            ) % len(self.frames)
        )

    def next_frame(self):
        if len(self.frames) <= 1:
            return

        self.load_frame(
            (
                self.current_frame + 1
            ) % len(self.frames)
        )

    def delete_frame(self):
        if len(self.frames) <= 1:
            ErrorDialog.show(
                self.app,
                "You cannot delete the only frame."
            )
            return

        if self.playing:
            self.stop_playback()

        self.save_current_frame()

        del self.frames[
            self.current_frame
        ]

        self.current_frame = min(
            self.current_frame,
            len(self.frames) - 1
        )

        self.pixels = self.frames[
            self.current_frame
        ]

        self.render_all()
        self.update_frame_label()

    # --------------------------------------------------------
    # PLAYBACK
    # --------------------------------------------------------

    def toggle_playback(self):
        if self.playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        if self.destroyed:
            return

        if len(self.frames) <= 1:
            ErrorDialog.show(
                self.app,
                "Create at least two frames first."
            )
            return

        try:
            fps = int(
                self.fps_var.get()
            )
        except (
            ValueError,
            tk.TclError
        ):
            fps = 8

        fps = max(
            1,
            min(30, fps)
        )

        self.fps = fps
        self.playing = True

        try:
            if self.play_button.winfo_exists():
                self.play_button.config(
                    text="Stop"
                )
        except tk.TclError:
            self.playing = False
            return

        self.play_next()

    def stop_playback(self):
        self.playing = False

        if self.play_job is not None:
            try:
                self.app.root.after_cancel(
                    self.play_job
                )
            except tk.TclError:
                pass

            self.play_job = None

        try:
            if (
                hasattr(self, "play_button")
                and self.play_button.winfo_exists()
            ):
                self.play_button.config(
                    text="Play"
                )
        except tk.TclError:
            pass

    def play_next(self):
        if not self.playing:
            return

        if self.destroyed:
            self.playing = False
            self.play_job = None
            return

        if not self.frames:
            self.playing = False
            self.play_job = None
            return

        self.current_frame = (
            self.current_frame + 1
        ) % len(self.frames)

        self.pixels = self.frames[
            self.current_frame
        ]

        self.render_all()
        self.update_frame_label()

        try:
            fps = int(
                self.fps_var.get()
            )
        except (
            ValueError,
            tk.TclError
        ):
            fps = self.fps

        self.fps = max(
            1,
            min(30, fps)
        )

        delay = max(
            1,
            int(1000 / self.fps)
        )

        try:
            self.play_job = (
                self.app.root.after(
                    delay,
                    self.play_next
                )
            )
        except tk.TclError:
            self.playing = False
            self.play_job = None

    # --------------------------------------------------------
    # PAINT TOOLS
    # --------------------------------------------------------

    def set_tool(self, tool):
        self.tool = tool

        self.drawing = False
        self.start_x = None
        self.start_y = None

    def set_color(self, color):
        self.current_color = color

    def inside(self, x, y):
        return (
            0 <= x < self.WIDTH
            and 0 <= y < self.HEIGHT
        )

    def put_pixel(
        self,
        x,
        y,
        color=None
    ):
        if not self.inside(x, y):
            return

        if color is None:
            color = self.current_color

        self.pixels[y][x] = color

    def draw_line(
        self,
        x1,
        y1,
        x2,
        y2,
        color=None
    ):
        if color is None:
            color = self.current_color

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        sx = (
            1
            if x1 < x2
            else -1
        )

        sy = (
            1
            if y1 < y2
            else -1
        )

        error = dx - dy

        while True:
            self.put_pixel(
                x1,
                y1,
                color
            )

            if (
                x1 == x2
                and y1 == y2
            ):
                break

            e2 = 2 * error

            if e2 > -dy:
                error -= dy
                x1 += sx

            if e2 < dx:
                error += dx
                y1 += sy

    def start(self, event):
        if self.destroyed:
            return

        if self.playing:
            self.stop_playback()

        x = int(
            self.canvas.canvasx(
                event.x
            )
        )

        y = int(
            self.canvas.canvasy(
                event.y
            )
        )

        if not self.inside(x, y):
            return

        self.drawing = True

        self.start_x = x
        self.start_y = y

        if self.tool == "pencil":
            self.put_pixel(
                x,
                y,
                self.current_color
            )

            self.render_all()

        elif self.tool == "eraser":
            self.put_pixel(
                x,
                y,
                WHITE
            )

            self.render_all()

        elif self.tool == "fill":
            self.flood_fill(
                x,
                y,
                self.current_color
            )

            self.render_all()

            self.drawing = False
            self.start_x = None
            self.start_y = None

    def draw(self, event):
        if self.destroyed:
            return

        if not self.drawing:
            return

        x = int(
            self.canvas.canvasx(
                event.x
            )
        )

        y = int(
            self.canvas.canvasy(
                event.y
            )
        )

        if not self.inside(x, y):
            return

        if self.tool == "pencil":
            self.draw_line(
                self.start_x,
                self.start_y,
                x,
                y,
                self.current_color
            )

            self.start_x = x
            self.start_y = y

            self.render_all()

        elif self.tool == "eraser":
            self.draw_line(
                self.start_x,
                self.start_y,
                x,
                y,
                WHITE
            )

            self.start_x = x
            self.start_y = y

            self.render_all()

    def finish(self, event):
        if self.destroyed:
            return

        if not self.drawing:
            return

        x = int(
            self.canvas.canvasx(
                event.x
            )
        )

        y = int(
            self.canvas.canvasy(
                event.y
            )
        )

        if self.inside(x, y):
            if self.tool == "rectangle":
                self.draw_rectangle(
                    self.start_x,
                    self.start_y,
                    x,
                    y
                )

            elif self.tool == "oval":
                self.draw_oval(
                    self.start_x,
                    self.start_y,
                    x,
                    y
                )

        self.drawing = False

        self.start_x = None
        self.start_y = None

        self.render_all()

    def draw_rectangle(
        self,
        x1,
        y1,
        x2,
        y2
    ):
        left = min(
            x1,
            x2
        )

        right = max(
            x1,
            x2
        )

        top = min(
            y1,
            y2
        )

        bottom = max(
            y1,
            y2
        )

        self.draw_line(
            left,
            top,
            right,
            top
        )

        self.draw_line(
            right,
            top,
            right,
            bottom
        )

        self.draw_line(
            right,
            bottom,
            left,
            bottom
        )

        self.draw_line(
            left,
            bottom,
            left,
            top
        )

    def draw_oval(
        self,
        x1,
        y1,
        x2,
        y2
    ):
        left = min(
            x1,
            x2
        )

        right = max(
            x1,
            x2
        )

        top = min(
            y1,
            y2
        )

        bottom = max(
            y1,
            y2
        )

        width = right - left
        height = bottom - top

        if width == 0 or height == 0:
            return

        steps = max(
            32,
            int(
                (width + height)
                * 1.5
            )
        )

        last_x = None
        last_y = None

        for i in range(
            steps + 1
        ):
            angle = (
                2
                * math.pi
                * i
                / steps
            )

            x = int(
                (left + right) / 2
                + (
                    width / 2
                ) * math.cos(angle)
            )

            y = int(
                (top + bottom) / 2
                + (
                    height / 2
                ) * math.sin(angle)
            )

            if last_x is not None:
                self.draw_line(
                    last_x,
                    last_y,
                    x,
                    y
                )

            last_x = x
            last_y = y

    def flood_fill(
        self,
        x,
        y,
        new_color
    ):
        if not self.inside(x, y):
            return

        old_color = self.pixels[y][x]

        if old_color == new_color:
            return

        stack = [
            (x, y)
        ]

        while stack:
            px, py = stack.pop()

            if not self.inside(
                px,
                py
            ):
                continue

            if (
                self.pixels[py][px]
                != old_color
            ):
                continue

            self.pixels[py][px] = new_color

            stack.append(
                (px + 1, py)
            )

            stack.append(
                (px - 1, py)
            )

            stack.append(
                (px, py + 1)
            )

            stack.append(
                (px, py - 1)
            )

    def clear(self):
        if self.destroyed:
            return

        if self.playing:
            self.stop_playback()

        self.pixels = self.blank_frame()

        self.frames[
            self.current_frame
        ] = self.pixels

        self.render_all()

    # --------------------------------------------------------
    # PAINT RENDER
    # --------------------------------------------------------

    def render_all(self):
        # Defensive check.
        if getattr(
            self,
            "destroyed",
            False
        ):
            return

        try:
            if not self.canvas.winfo_exists():
                return

            rows = []

            for row in self.pixels:
                rows.append(
                    "{" +
                    " ".join(row) +
                    "}"
                )

            self.photo.put(
                " ".join(rows),
                to=(
                    0,
                    0,
                    self.WIDTH,
                    self.HEIGHT
                )
            )

        except tk.TclError:
            pass

    # --------------------------------------------------------
    # PAINT DESTROY
    # --------------------------------------------------------

    def on_destroy(self, event):
        if event.widget != self.win.frame:
            return

        if getattr(
            self,
            "destroyed",
            False
        ):
            return

        self.destroyed = True
        self.playing = False

        if self.play_job is not None:
            try:
                self.app.root.after_cancel(
                    self.play_job
                )
            except tk.TclError:
                pass

            self.play_job = None


# ============================================================
# TERMINAL
# ============================================================

class Terminal:
    """LEDos virtual terminal with filesystem and native package commands."""

    REPOSITORY = {
        "manual": {
            "version": "1.0",
            "description": "LEDos command reference and getting-started guide.",
            "files": {
                "README.TXT": (
                    "LEDos Manual 1.0\n\n"
                    "Use HELP in Terminal to see available commands.\n"
                    "The C: drive is a virtual filesystem stored by LEDos.\n"
                    "Use DIR, CD, MKDIR, TYPE, and DEL to manage virtual files.\n"
                ),
                "COMMANDS.TXT": (
                    "FILESYSTEM: DIR, CD, MKDIR, DEL, TYPE, COPY, REN, PWD\n"
                    "SYSTEM: HELP, VER, TIME, DATE, WHOAMI, SYSINFO, APPS\n"
                    "TERMINAL: CLS, ECHO, EXIT\n"
                    "PACKAGES: SEARCH, PACKAGES, INFO, INSTALL, INSTALLED, REMOVE\n"
                ),
            },
        },
        "examples": {
            "version": "1.0",
            "description": "Sample text files for experimenting with LEDos.",
            "files": {
                "HELLO.TXT": "Hello from the LEDos package repository!\n",
                "IDEAS.TXT": "Ideas to try:\n- Make a folder\n- Write a note\n- Copy a file\n- Explore Terminal\n",
            },
        },
        "devkit": {
            "version": "1.0",
            "description": "Starter notes and templates for LEDos experiments.",
            "files": {
                "README.TXT": "LEDos DevKit\n\nUse this folder for your own virtual projects.\n",
                "TEMPLATE.PY": "# LEDos virtual project template\n# This file is stored in the virtual C: drive.\n",
            },
        },
    }

    def __init__(self, app):
        self.app = app
        self.cwd = "C:"

        self.win = LEDosWindow(app, "Terminal", 700, 480)
        content = self.win.content

        self.output = tk.Text(
            content, bg=BLACK, fg=WHITE, insertbackground=WHITE,
            font=FONT, state="disabled", wrap="word"
        )
        self.output.pack(fill="both", expand=True, padx=5, pady=5)

        bottom = tk.Frame(content, bg=BLACK)
        bottom.pack(fill="x")

        self.prompt_label = tk.Label(
            bottom, text="C:>", bg=BLACK, fg=WHITE, font=FONT
        )
        self.prompt_label.pack(side="left", padx=4)

        self.entry = tk.Entry(
            bottom, bg=BLACK, fg=WHITE, insertbackground=WHITE,
            relief="flat", font=FONT
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda event: self.execute())

        self.write(
            f"{OS_NAME} Terminal\nRelease {RELEASE_VERSION}\n"
            "Virtual C: drive ready. Type HELP for commands.\n\n"
        )
        self.update_prompt()
        self.entry.focus_set()

    def write(self, text):
        try:
            self.output.config(state="normal")
            self.output.insert(tk.END, str(text))
            self.output.see(tk.END)
            self.output.config(state="disabled")
        except tk.TclError:
            pass

    def update_prompt(self):
        try:
            self.prompt_label.config(text=self.cwd + ">")
        except tk.TclError:
            pass

    def clear_output(self):
        try:
            self.output.config(state="normal")
            self.output.delete("1.0", tk.END)
            self.output.config(state="disabled")
        except tk.TclError:
            pass

    def resolve_path(self, value):
        value = value.strip().strip('"')
        if not value:
            return self.cwd
        if value.upper() in ("C:", "C:/", "C:\\"):
            return "C:"
        normalized = value.replace("\\", "/")
        if normalized.startswith("C:/"):
            return "/".join(self.app.fs.normalize_path(normalized))
        if normalized.startswith("/"):
            normalized = normalized.lstrip("/")
        if self.cwd == "C:":
            combined = "C:/" + normalized
        else:
            combined = self.cwd.rstrip("/") + "/" + normalized
        return "/".join(self.app.fs.normalize_path(combined))

    def package_root(self, name):
        return f"C:/PROGRAMS/{name}"

    def installed_package_names(self):
        return [
            entry["name"] for entry in self.app.fs.entries("C:/PROGRAMS")
            if entry["type"] == "dir" and entry["name"].lower() in self.REPOSITORY
            and self.app.fs.exists(self.package_root(entry["name"].lower()) + "/PACKAGE.INFO")
        ]

    def package_install(self, name):
        name = name.lower()
        package = self.REPOSITORY.get(name)
        if not package:
            self.write(f"Package not found: {name}\nUse SEARCH to browse the repository.\n")
            return

        root = self.package_root(name)
        if self.app.fs.exists(root):
            if self.app.fs.exists(root + "/PACKAGE.INFO"):
                self.write(f"{name} is already installed.\n")
            else:
                self.write(f"Cannot install {name}: destination already exists.\n")
            return

        if not self.app.fs.mkdir(root):
            self.write("Installation failed: could not create package directory.\n")
            return

        info = (
            f"Name: {name}\nVersion: {package['version']}\n"
            f"Description: {package['description']}\n"
            "Source: LEDos built-in repository\n"
        )
        success = self.app.fs.write_file(root + "/PACKAGE.INFO", info)
        for filename, content in package["files"].items():
            success = self.app.fs.write_file(root + "/" + filename, content) and success

        if success:
            self.write(f"Installed {name} {package['version']} successfully.\n")
        else:
            self.write("Installation was incomplete. Check C:/PROGRAMS.\n")

    def package_remove(self, name):
        name = name.lower()
        if name not in self.REPOSITORY:
            self.write(f"Unknown package: {name}\n")
            return
        root = self.package_root(name)
        if not self.app.fs.exists(root + "/PACKAGE.INFO"):
            self.write(f"{name} is not installed.\n")
            return
        # Remove only files owned by this package; leave unexpected user files alone.
        package = self.REPOSITORY[name]
        for filename in list(package["files"].keys()) + ["PACKAGE.INFO"]:
            self.app.fs.delete(root + "/" + filename)
        remaining = self.app.fs.entries(root)
        if not remaining:
            self.app.fs.delete(root)
            self.write(f"Removed {name}.\n")
        else:
            self.write(f"Removed managed files from {name}; folder kept because it contains other files.\n")

    def execute(self):
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not command:
            return

        self.write(f"{self.cwd}>{command}\n")
        # Split once so file/folder names and ECHO text may contain spaces.
        pieces = command.split(maxsplit=1)
        cmd = pieces[0].upper()
        rest = pieces[1].strip() if len(pieces) > 1 else ""
        args = rest.split(maxsplit=1) if rest else []

        if cmd == "HELP":
            self.write(
                "LEDos Terminal Commands\n"
                "HELP       Show this command list\n"
                "DIR        List the current directory\n"
                "CD         Change directory (CD .. goes up)\n"
                "PWD        Show current directory\n"
                "MKDIR      Create a directory\n"
                "DEL        Delete a virtual file/folder\n"
                "TYPE       Display a text file\n"
                "COPY       Copy a virtual file\n"
                "REN        Rename a virtual file/folder\n"
                "ECHO       Print text\n"
                "CLS        Clear the terminal\n"
                "VER        Show LEDos version\n"
                "TIME/DATE  Show current time/date\n"
                "WHOAMI     Show current user\n"
                "SYSINFO    Show system information\n"
                "APPS       List built-in applications\n"
                "SEARCH     Search the package repository\n"
                "PACKAGES   List repository packages\n"
                "INFO       Show package details\n"
                "INSTALL    Install a repository package\n"
                "INSTALLED  List installed packages\n"
                "REMOVE     Remove an installed package\n"
                "EXIT       Close Terminal\n\n"
                "Paths are virtual C: paths. Quote paths containing spaces.\n\n"
            )

        elif cmd == "DIR":
            path = self.resolve_path(rest) if rest else self.cwd
            node = self.app.fs.get_node(path)
            if not node or node.get("type") != "dir":
                self.write("Directory not found.\n")
                return
            entries = self.app.fs.entries(path)
            self.write(f"Directory of {path}\n\n")
            if not entries:
                self.write("Directory is empty.\n")
            else:
                for item in entries:
                    prefix = "<DIR> " if item["type"] == "dir" else "      "
                    self.write(prefix + item["name"] + "\n")
            self.write("\n")

        elif cmd == "CD":
            if not rest:
                self.write(self.cwd + "\n")
                return
            path = self.resolve_path(rest)
            node = self.app.fs.get_node(path)
            if node and node.get("type") == "dir":
                self.cwd = path
                self.update_prompt()
            else:
                self.write("Directory not found.\n")

        elif cmd == "PWD":
            self.write(self.cwd + "\n")

        elif cmd == "MKDIR":
            if not rest:
                self.write("Usage: MKDIR <name or path>\n")
                return
            path = self.resolve_path(rest)
            if self.app.fs.mkdir(path):
                self.write(f"Directory created: {path}\n")
            else:
                self.write("Could not create directory (invalid name, parent missing, or already exists).\n")

        elif cmd == "DEL":
            if not rest:
                self.write("Usage: DEL <name or path>\n")
                return
            path = self.resolve_path(rest)
            if path == "C:" or path.upper() in ("C:/SYSTEM",):
                self.write("Protected system path.\n")
                return
            if self.app.fs.delete(path):
                self.write(f"Deleted: {path}\n")
                if self.cwd == path or self.cwd.startswith(path.rstrip("/") + "/"):
                    self.cwd = "C:"
                    self.update_prompt()
            else:
                self.write("File or directory not found.\n")

        elif cmd == "TYPE":
            if not rest:
                self.write("Usage: TYPE <file path>\n")
                return
            path = self.resolve_path(rest)
            content = self.app.fs.read_file(path)
            if content is None:
                self.write("File not found.\n")
            else:
                self.write(str(content) + ("" if str(content).endswith("\n") else "\n"))

        elif cmd == "COPY":
            copy_args = rest.split(maxsplit=1)
            if len(copy_args) != 2:
                self.write('Usage: COPY <source> <destination> (quote paths containing spaces)\n')
                return
            source = self.resolve_path(copy_args[0])
            destination = self.resolve_path(copy_args[1])
            content = self.app.fs.read_file(source)
            if content is None:
                self.write("Source file not found.\n")
            elif self.app.fs.exists(destination):
                self.write("Destination already exists.\n")
            elif self.app.fs.write_file(destination, content):
                self.write("File copied.\n")
            else:
                self.write("Copy failed. Make sure the destination folder exists.\n")

        elif cmd == "REN":
            rename_args = rest.split(maxsplit=1)
            if len(rename_args) != 2:
                self.write("Usage: REN <source path> <new name>\n")
                return
            source = self.resolve_path(rename_args[0])
            new_name = rename_args[1].strip().strip('"')
            if not self.app.fs.valid_name(new_name):
                self.write("Invalid new name.\n")
                return
            parts = self.app.fs.normalize_path(source)
            if len(parts) <= 1 or not self.app.fs.exists(source):
                self.write("Source not found.\n")
                return
            destination = "/".join(parts[:-1] + [new_name])
            if self.app.fs.exists(destination):
                self.write("An item with that name already exists.\n")
                return
            node = self.app.fs.get_node(source)
            parent = self.app.fs.get_node("/".join(parts[:-1]))
            if not parent or not isinstance(parent.get("children"), dict):
                self.write("Rename failed.\n")
                return
            parent["children"][new_name] = node
            del parent["children"][parts[-1]]
            self.app.fs.save()
            if self.cwd == source:
                self.cwd = destination
                self.update_prompt()
            self.write(f"Renamed to {destination}\n")

        elif cmd == "ECHO":
            self.write((rest if rest else "") + "\n")

        elif cmd == "CLS":
            self.clear_output()

        elif cmd == "VER":
            self.write(f"{OS_NAME} {RELEASE_VERSION}\n")

        elif cmd == "TIME":
            self.write(time.strftime("%H:%M:%S") + "\n")

        elif cmd == "DATE":
            self.write(time.strftime("%Y-%m-%d") + "\n")

        elif cmd == "WHOAMI":
            self.write(str(getattr(self.app, "username", "User")) + "\n")

        elif cmd == "SYSINFO":
            self.write(
                f"Operating system: {OS_NAME}\n"
                f"Release: {RELEASE_VERSION}\n"
                f"Host platform: {platform.system()} {platform.release()}\n"
                f"Python: {platform.python_version()}\n"
                f"Architecture: {platform.machine() or 'Unknown'}\n"
                f"User: {getattr(self.app, 'username', 'User')}\n"
                "Storage: LEDos virtual C: drive\n"
                "Graphics: Tkinter\n\n"
            )

        elif cmd == "APPS":
            self.write(
                "Built-in applications\n"
                "- File Manager\n- Notepad\n- Calculator\n"
                "- Paint (with animation frames)\n- Clock\n- Terminal\n"
                "- Settings\n- About LEDos\n\n"
            )

        elif cmd == "SEARCH":
            query = rest.lower()
            matches = [
                (name, package) for name, package in self.REPOSITORY.items()
                if not query or query in name or query in package["description"].lower()
            ]
            if not matches:
                self.write("No packages matched your search.\n")
            else:
                for name, package in matches:
                    status = " [installed]" if name in [n.lower() for n in self.installed_package_names()] else ""
                    self.write(f"{name} {package['version']}{status} - {package['description']}\n")
                self.write("\n")

        elif cmd == "PACKAGES":
            self.write("LEDos built-in package repository\n")
            for name, package in self.REPOSITORY.items():
                self.write(f"{name:<12} {package['version']:<6} {package['description']}\n")
            self.write("\nUse INSTALL <package> to install one.\n\n")

        elif cmd == "INFO":
            name = rest.lower()
            package = self.REPOSITORY.get(name)
            if not name:
                self.write("Usage: INFO <package>\n")
            elif not package:
                self.write(f"Package not found: {name}\n")
            else:
                status = "Installed" if name in [n.lower() for n in self.installed_package_names()] else "Not installed"
                self.write(
                    f"{name} {package['version']}\n{package['description']}\n"
                    f"Status: {status}\nFiles: {', '.join(package['files'])}\n\n"
                )

        elif cmd == "INSTALL":
            if not rest:
                self.write("Usage: INSTALL <package>\n")
            else:
                self.package_install(rest)

        elif cmd == "INSTALLED":
            installed = self.installed_package_names()
            if not installed:
                self.write("No LEDos packages are installed. Use PACKAGES to browse.\n")
            else:
                self.write("Installed packages\n")
                for name in installed:
                    package = self.REPOSITORY.get(name.lower(), {})
                    self.write(f"{name} {package.get('version', '')}\n")
                self.write("\n")

        elif cmd == "REMOVE":
            if not rest:
                self.write("Usage: REMOVE <package>\n")
            else:
                self.package_remove(rest)

        elif cmd == "EXIT":
            self.win.close()

        else:
            self.write(f"Unknown command: {cmd}\nType HELP for a list of commands.\n")

# ============================================================
# CLOCK
# ============================================================

class Clock:
    def __init__(self, app):
        self.app = app

        self.win = LEDosWindow(
            app,
            "Clock",
            350,
            230
        )

        content = self.win.content

        self.time_label = tk.Label(
            content,
            text="00:00:00",
            bg=FACE,
            fg=app.secondary_color,
            font=("Courier New", 28, "bold")
        )

        self.time_label.pack(
            pady=(40, 10)
        )

        self.date_label = tk.Label(
            content,
            text="",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        )

        self.date_label.pack()

        self.update()

    def update(self):
        try:
            self.time_label.config(
                text=self.app.format_time(),
                fg=self.app.secondary_color
            )

            self.date_label.config(
                text=time.strftime(
                    "%A, %Y-%m-%d"
                )
            )

            self.win.frame.after(
                1000,
                self.update
            )

        except tk.TclError:
            pass


# ============================================================
# SETTINGS
# ============================================================

class Settings:
    def __init__(self, app):
        self.app = app

        self.win = LEDosWindow(
            app,
            "Settings",
            560,
            650
        )

        content = self.win.content

        # ----------------------------------------------------
        # USER
        # ----------------------------------------------------

        tk.Label(
            content,
            text="User",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 5)
        )

        user_frame = tk.Frame(
            content,
            bg=FACE
        )
        user_frame.pack(
            fill="x",
            padx=12
        )

        tk.Label(
            user_frame,
            text="Username:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack(
            side="left"
        )

        self.username_entry = tk.Entry(
            user_frame,
            bg=WHITE,
            fg=BLACK,
            font=FONT
        )

        self.username_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        self.username_entry.insert(
            0,
            self.app.username
        )

        LEDosButton(
            user_frame,
            text="Change",
            command=self.change_username
        ).pack(
            side="left"
        )

        password_frame = tk.Frame(
            content,
            bg=FACE
        )
        password_frame.pack(
            fill="x",
            padx=12,
            pady=8
        )

        LEDosButton(
            password_frame,
            text="Change Password",
            command=self.change_password
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # APPEARANCE
        # ----------------------------------------------------

        tk.Label(
            content,
            text="Appearance",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 5)
        )

        appearance = tk.Frame(
            content,
            bg=FACE
        )
        appearance.pack(
            fill="x",
            padx=12
        )

        LEDosButton(
            appearance,
            text="Accent Color",
            command=self.choose_color
        ).pack(
            side="left",
            padx=3
        )

        LEDosButton(
            appearance,
            text="Reset Accent",
            command=lambda: self.app.set_secondary_color(
                ORANGE
            )
        ).pack(
            side="left",
            padx=3
        )

        # ----------------------------------------------------
        # BACKGROUND
        # ----------------------------------------------------

        background = tk.Frame(
            content,
            bg=FACE
        )
        background.pack(
            fill="x",
            padx=12,
            pady=10
        )

        LEDosButton(
            background,
            text="Desktop Background",
            command=self.choose_background
        ).pack(
            side="left",
            padx=3
        )

        LEDosButton(
            background,
            text="Reset Background",
            command=lambda: self.app.set_background(
                BG
            )
        ).pack(
            side="left",
            padx=3
        )

        # ----------------------------------------------------
        # CLOCK
        # ----------------------------------------------------

        tk.Label(
            content,
            text="Clock",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        ).pack(
            anchor="w",
            padx=12,
            pady=(8, 5)
        )

        clock_frame = tk.Frame(
            content,
            bg=FACE
        )
        clock_frame.pack(
            fill="x",
            padx=12
        )

        self.clock_var = tk.BooleanVar(
            value=app.clock_visible
        )

        tk.Checkbutton(
            clock_frame,
            text="Show desktop clock",
            variable=self.clock_var,
            bg=FACE,
            fg=BLACK,
            activebackground=FACE,
            font=FONT,
            command=self.toggle_clock
        ).pack(
            side="left"
        )

        self.format_var = tk.StringVar(
            value=app.clock_format
        )

        tk.Label(
            clock_frame,
            text=" Format:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack(
            side="left"
        )

        format_menu = tk.OptionMenu(
            clock_frame,
            self.format_var,
            "24-hour",
            "12-hour",
            command=self.change_clock_format
        )

        format_menu.config(
            bg=FACE,
            fg=BLACK,
            font=FONT,
            relief="raised",
            bd=2
        )

        format_menu.pack(
            side="left",
            padx=5
        )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        tk.Label(
            content,
            text="Display",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        ).pack(
            anchor="w",
            padx=12,
            pady=(15, 5)
        )

        LEDosButton(
            content,
            text="Toggle Fullscreen",
            command=self.app.toggle_fullscreen
        ).pack(
            anchor="w",
            padx=12
        )

        # ----------------------------------------------------
        # SYSTEM
        # ----------------------------------------------------

        tk.Label(
            content,
            text="System",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        ).pack(
            anchor="w",
            padx=12,
            pady=(15, 5)
        )

        LEDosButton(
            content,
            text="Reset Virtual Filesystem",
            command=self.reset_fs
        ).pack(
            anchor="w",
            padx=12
        )

        # ----------------------------------------------------
        # INFO
        # ----------------------------------------------------

        info = tk.Label(
            content,
            text=(
                f"OS: {OS_NAME}\n"
                f"Release: {RELEASE_VERSION}\n"
                f"User: {self.app.username}\n"
                "RAM: 640 KB\n"
                "Graphics: Tkinter Desktop\n"
                "Storage: Virtual Filesystem\n"
                "Graphics Tool: Raster Paint"
            ),
            bg=FACE,
            fg=BLACK,
            font=FONT,
            justify="left"
        )

        info.pack(
            anchor="w",
            padx=12,
            pady=15
        )

    def change_username(self):
        username = (
            self.username_entry
            .get()
            .strip()
        )

        if not username:
            ErrorDialog.show(
                self.app,
                "Username cannot be empty."
            )
            return

        if len(username) > 24:
            ErrorDialog.show(
                self.app,
                "Username is too long."
            )
            return

        self.app.username = username
        self.app.save_settings()

        self.app.update_user_display()

        ErrorDialog.show(
            self.app,
            "Username changed successfully."
        )

    def change_password(self):
        self.app.password_prompt(
            "Change Password",
            self.app.set_password
        )

    def choose_color(self):
        color = colorchooser.askcolor(
            title="Choose LEDos Accent Color"
        )

        if color and color[1]:
            self.app.set_secondary_color(
                color[1]
            )

    def choose_background(self):
        color = colorchooser.askcolor(
            title="Choose Desktop Background"
        )

        if color and color[1]:
            self.app.set_background(
                color[1]
            )

    def toggle_clock(self):
        self.app.clock_visible = (
            self.clock_var.get()
        )

        self.app.save_settings()
        self.app.update_desktop_clock()

    def change_clock_format(self, value):
        self.app.clock_format = value

        self.app.save_settings()
        self.app.update_desktop_clock()

    def reset_fs(self):
        self.app.fs = VirtualFS(
            self.app.fs.filename
        )

        ErrorDialog.show(
            self.app,
            "Virtual filesystem reset."
        )


# ============================================================
# ABOUT
# ============================================================

class About:
    def __init__(self, app):
        self.app = app

        self.win = LEDosWindow(
            app,
            "About LEDos",
            480,
            360
        )

        content = self.win.content

        tk.Label(
            content,
            text=OS_NAME,
            bg=FACE,
            fg=app.secondary_color,
            font=("Courier New", 24, "bold")
        ).pack(
            pady=(35, 10)
        )

        tk.Label(
            content,
            text=f"Release {RELEASE_VERSION}",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        ).pack()

        tk.Label(
            content,
            text=(
                "\n"
                "A tiny fictional operating system\n"
                "built with Python and Tkinter.\n\n"
                "Retro desktop environment\n"
                "Virtual filesystem\n"
                "Raster graphics\n"
                "Animated Paint frames\n\n"
                "640 KB RAM"
            ),
            bg=FACE,
            fg=BLACK,
            font=FONT,
            justify="center"
        ).pack(
            pady=15
        )

        LEDosButton(
            content,
            text="OK",
            command=self.win.close
        ).pack(
            pady=5
        )


# ============================================================
# LEDos
# ============================================================

class LEDos:
    SETTINGS_FILE = SETTINGS_FILE

    def __init__(self, root):
        self.root = root

        self.root.title(
            OS_NAME
        )

        self.root.geometry(
            "1024x768"
        )

        self.root.resizable(
            False,
            False
        )

        self.root.configure(
            bg=BG
        )

        # ----------------------------------------------------
        # DEFAULT SETTINGS
        # ----------------------------------------------------

        self.secondary_color = ORANGE
        self.desktop_background = BG

        self.fullscreen = False

        self.clock_visible = True
        self.clock_format = "24-hour"

        self.username = "User"
        self.password = ""

        self.account_exists = False

        self.load_settings()

        self.fs = VirtualFS()

        self.windows = []

        self.booting = True
        self.logged_in = False

        self.root.bind(
            "<F11>",
            lambda event: self.toggle_fullscreen()
        )

        self.root.bind(
            "<Escape>",
            lambda event: self.exit_fullscreen()
        )

        self.build_boot()

    # --------------------------------------------------------
    # SETTINGS STORAGE
    # --------------------------------------------------------

    def load_settings(self):
        try:
            if not os.path.exists(
                self.SETTINGS_FILE
            ):
                return

            with open(
                self.SETTINGS_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return

            self.username = str(
                data.get(
                    "username",
                    "User"
                )
            )

            self.password = str(
                data.get(
                    "password",
                    ""
                )
            )

            self.account_exists = bool(
                data.get(
                    "account_exists",
                    bool(self.password)
                )
            )

            self.secondary_color = str(
                data.get(
                    "accent_color",
                    ORANGE
                )
            )

            self.desktop_background = str(
                data.get(
                    "desktop_background",
                    BG
                )
            )

            self.clock_visible = bool(
                data.get(
                    "clock_visible",
                    True
                )
            )

            self.clock_format = data.get(
                "clock_format",
                "24-hour"
            )

            if self.clock_format not in (
                "24-hour",
                "12-hour"
            ):
                self.clock_format = "24-hour"

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError
        ):
            pass

    def save_settings(self):
        data = {
            "username": self.username,
            "password": self.password,
            "account_exists": self.account_exists,
            "accent_color": self.secondary_color,
            "desktop_background": self.desktop_background,
            "clock_visible": self.clock_visible,
            "clock_format": self.clock_format
        }

        try:
            with open(
                self.SETTINGS_FILE,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    data,
                    f,
                    indent=2
                )
        except OSError:
            pass

    # --------------------------------------------------------
    # BOOT
    # --------------------------------------------------------

    def build_boot(self):
        self.boot = tk.Frame(
            self.root,
            bg=BLACK
        )

        self.boot.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            self.boot,
            text="LEDos BIOS",
            bg=BLACK,
            fg=WHITE,
            font=("Courier New", 22, "bold")
        ).pack(
            pady=(150, 30)
        )

        self.boot_status = tk.Label(
            self.boot,
            text="Checking memory...",
            bg=BLACK,
            fg=WHITE,
            font=FONT
        )

        self.boot_status.pack()

        self.root.after(
            400,
            lambda: self.safe_boot_status(
                "Checking disk..."
            )
        )

        self.root.after(
            800,
            lambda: self.safe_boot_status(
                "Checking graphics..."
            )
        )

        self.root.after(
            1200,
            lambda: self.safe_boot_status(
                "Loading LEDos..."
            )
        )

        self.root.after(
            1600,
            lambda: self.safe_boot_status(
                OS_NAME
            )
        )

        self.root.after(
            1800,
            self.start_login
        )

    def safe_boot_status(self, text):
        try:
            self.boot_status.config(
                text=text
            )
        except tk.TclError:
            pass

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    def start_login(self):
        try:
            self.boot.destroy()
        except tk.TclError:
            pass

        self.booting = False

        if not self.account_exists:
            self.build_account_setup()
        else:
            self.build_login()

    def clear_screen(self):
        try:
            for widget in self.root.winfo_children():
                widget.destroy()
        except tk.TclError:
            pass

    def build_login(self):
        self.clear_screen()

        self.login = tk.Frame(
            self.root,
            bg=TITLE_BLUE
        )

        self.login.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            self.login,
            text=OS_NAME,
            bg=TITLE_BLUE,
            fg=WHITE,
            font=("Courier New", 30, "bold")
        ).pack(
            pady=(150, 10)
        )

        tk.Label(
            self.login,
            text="Welcome back",
            bg=TITLE_BLUE,
            fg=WHITE,
            font=FONT_BOLD
        ).pack(
            pady=(0, 25)
        )

        panel = tk.Frame(
            self.login,
            bg=FACE,
            bd=2,
            relief="raised"
        )

        panel.pack(
            ipadx=30,
            ipady=20
        )

        tk.Label(
            panel,
            text=f"User: {self.username}",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        ).pack(
            pady=(5, 10)
        )

        tk.Label(
            panel,
            text="Password:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack(
            pady=(5, 3)
        )

        self.login_password = tk.Entry(
            panel,
            bg=WHITE,
            fg=BLACK,
            show="*",
            font=FONT,
            width=28
        )

        self.login_password.pack(
            padx=20
        )

        LEDosButton(
            panel,
            text="Log In",
            command=self.check_login
        ).pack(
            pady=15
        )

        self.login_message = tk.Label(
            panel,
            text="",
            bg=FACE,
            fg=BLACK,
            font=FONT
        )

        self.login_message.pack(
            pady=(0, 5)
        )

        self.login_password.focus_set()

        self.login_password.bind(
            "<Return>",
            lambda event: self.check_login()
        )

    def check_login(self):
        password = self.login_password.get()

        if password == self.password:
            self.logged_in = True
            self.start_desktop()
            return

        try:
            self.login_message.config(
                text="Incorrect password."
            )

            self.login_password.delete(
                0,
                tk.END
            )

            self.login_password.focus_set()

        except tk.TclError:
            pass

    # --------------------------------------------------------
    # FIRST ACCOUNT SETUP
    # --------------------------------------------------------

    def build_account_setup(self):
        self.clear_screen()

        self.setup = tk.Frame(
            self.root,
            bg=TITLE_BLUE
        )

        self.setup.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            self.setup,
            text=OS_NAME,
            bg=TITLE_BLUE,
            fg=WHITE,
            font=("Courier New", 30, "bold")
        ).pack(
            pady=(110, 10)
        )

        tk.Label(
            self.setup,
            text="First-time setup",
            bg=TITLE_BLUE,
            fg=WHITE,
            font=FONT_BOLD
        ).pack(
            pady=(0, 20)
        )

        panel = tk.Frame(
            self.setup,
            bg=FACE,
            bd=2,
            relief="raised"
        )

        panel.pack(
            ipadx=35,
            ipady=20
        )

        tk.Label(
            panel,
            text="Create your LEDos account",
            bg=FACE,
            fg=BLACK,
            font=FONT_BOLD
        ).pack(
            pady=(5, 15)
        )

        tk.Label(
            panel,
            text="Username:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack()

        self.setup_username = tk.Entry(
            panel,
            bg=WHITE,
            fg=BLACK,
            font=FONT,
            width=28
        )

        self.setup_username.pack(
            padx=20,
            pady=(3, 10)
        )

        tk.Label(
            panel,
            text="Password:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack()

        self.setup_password = tk.Entry(
            panel,
            bg=WHITE,
            fg=BLACK,
            show="*",
            font=FONT,
            width=28
        )

        self.setup_password.pack(
            padx=20,
            pady=(3, 10)
        )

        tk.Label(
            panel,
            text="Confirm password:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack()

        self.setup_confirm = tk.Entry(
            panel,
            bg=WHITE,
            fg=BLACK,
            show="*",
            font=FONT,
            width=28
        )

        self.setup_confirm.pack(
            padx=20
        )

        LEDosButton(
            panel,
            text="Create Account",
            command=self.create_account
        ).pack(
            pady=15
        )

        self.setup_message = tk.Label(
            panel,
            text="",
            bg=FACE,
            fg=BLACK,
            font=FONT
        )

        self.setup_message.pack()

        self.setup_username.focus_set()

        self.setup_confirm.bind(
            "<Return>",
            lambda event: self.create_account()
        )

    def create_account(self):
        username = (
            self.setup_username
            .get()
            .strip()
        )

        password = self.setup_password.get()
        confirm = self.setup_confirm.get()

        if not username:
            self.show_setup_message(
                "Username cannot be empty."
            )
            return

        if len(username) > 24:
            self.show_setup_message(
                "Username is too long."
            )
            return

        if not password:
            self.show_setup_message(
                "Password cannot be empty."
            )
            return

        if password != confirm:
            self.show_setup_message(
                "Passwords do not match."
            )
            return

        self.username = username
        self.password = password
        self.account_exists = True

        self.save_settings()

        self.logged_in = True

        self.start_desktop()

    def show_setup_message(self, message):
        try:
            self.setup_message.config(
                text=message
            )
        except tk.TclError:
            pass

    # --------------------------------------------------------
    # PASSWORD PROMPT
    # --------------------------------------------------------

    def password_prompt(
        self,
        title,
        callback
    ):
        window = tk.Toplevel(
            self.root
        )

        window.title(title)

        window.geometry(
            "420x190"
        )

        window.configure(
            bg=FACE
        )

        window.transient(
            self.root
        )

        tk.Label(
            window,
            text="New password:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack(
            pady=(20, 5)
        )

        password_entry = tk.Entry(
            window,
            bg=WHITE,
            fg=BLACK,
            show="*",
            font=FONT
        )

        password_entry.pack(
            fill="x",
            padx=20
        )

        tk.Label(
            window,
            text="Confirm password:",
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack(
            pady=(10, 5)
        )

        confirm_entry = tk.Entry(
            window,
            bg=WHITE,
            fg=BLACK,
            show="*",
            font=FONT
        )

        confirm_entry.pack(
            fill="x",
            padx=20
        )

        buttons = tk.Frame(
            window,
            bg=FACE
        )

        buttons.pack(
            pady=12
        )

        def submit():
            password = password_entry.get()
            confirm = confirm_entry.get()

            if not password:
                ErrorDialog.show(
                    self,
                    "Password cannot be empty."
                )
                return

            if password != confirm:
                ErrorDialog.show(
                    self,
                    "Passwords do not match."
                )
                return

            try:
                callback(password)
            finally:
                try:
                    window.destroy()
                except tk.TclError:
                    pass

        LEDosButton(
            buttons,
            text="OK",
            command=submit
        ).pack(
            side="left",
            padx=5
        )

        LEDosButton(
            buttons,
            text="Cancel",
            command=window.destroy
        ).pack(
            side="left",
            padx=5
        )

        password_entry.focus_set()

    def set_password(self, password):
        self.password = password
        self.account_exists = True
        self.save_settings()

        ErrorDialog.show(
            self,
            "Password changed successfully."
        )

    # --------------------------------------------------------
    # DESKTOP
    # --------------------------------------------------------

    def start_desktop(self):
        try:
            for widget in self.root.winfo_children():
                widget.destroy()
        except tk.TclError:
            pass

        self.booting = False

        self.desktop = tk.Frame(
            self.root,
            bg=self.desktop_background
        )

        self.desktop.pack(
            fill="both",
            expand=True
        )

        self.build_menu()

        # ----------------------------------------------------
        # DESKTOP CLOCK
        # ----------------------------------------------------

        self.clock_label = tk.Label(
            self.desktop,
            text="",
            bg=self.desktop_background,
            fg=self.secondary_color,
            font=("Courier New", 16, "bold")
        )

        self.clock_label.place(
            x=25,
            y=48
        )

        # ----------------------------------------------------
        # DESKTOP USER
        # ----------------------------------------------------

        self.user_label = tk.Label(
            self.desktop,
            text="",
            bg=self.desktop_background,
            fg=BLACK,
            font=FONT_BOLD
        )

        self.user_label.place(
            x=25,
            y=132
        )

        # ----------------------------------------------------
        # DESKTOP TITLE
        # ----------------------------------------------------

        self.desktop_title = tk.Label(
            self.desktop,
            text=OS_NAME,
            bg=self.desktop_background,
            fg=self.secondary_color,
            font=FONT_BIG
        )

        self.desktop_title.place(
            x=25,
            y=85
        )

        self.desktop_subtitle = tk.Label(
            self.desktop,
            text="Personal Computer",
            bg=self.desktop_background,
            fg=BLACK,
            font=FONT
        )

        self.desktop_subtitle.place(
            x=27,
            y=112
        )

        self.update_user_display()

        self.build_icons()

        # ----------------------------------------------------
        # STATUS BAR
        # ----------------------------------------------------

        self.status_bar = tk.Frame(
            self.desktop,
            bg=FACE,
            bd=1,
            relief="raised"
        )

        self.status_label = tk.Label(
            self.status_bar,
            text="",
            bg=FACE,
            fg=BLACK,
            font=FONT_SMALL
        )

        self.status_label.pack(
            side="left",
            padx=8
        )

        self.update_status_bar()

        self.update_desktop_clock()

        self.position_status_bar()

        self.root.bind(
            "<Configure>",
            self.on_root_resize
        )

    def update_user_display(self):
        if not hasattr(
            self,
            "user_label"
        ):
            return

        try:
            self.user_label.config(
                text=f"User: {self.username}",
                bg=self.desktop_background,
                fg=BLACK
            )

            if hasattr(
                self,
                "status_label"
            ):
                self.status_label.config(
                    text=(
                        f"{OS_NAME} | "
                        f"{self.username} | "
                        "640 KB RAM | "
                        "C: READY"
                    )
                )

        except tk.TclError:
            pass

    def build_menu(self):
        self.menu_bar = tk.Frame(
            self.desktop,
            bg=FACE,
            bd=1,
            relief="raised"
        )

        self.menu_bar.pack(
            fill="x"
        )

        # ----------------------------------------------------
        # LEDos MENU
        # ----------------------------------------------------

        ledos_button = tk.Menubutton(
            self.menu_bar,
            text="LEDos",
            bg=FACE,
            fg=BLACK,
            activebackground=self.secondary_color,
            activeforeground=BLACK,
            font=FONT_BOLD,
            relief="raised"
        )

        ledos_button.pack(
            side="left"
        )

        ledos_menu = tk.Menu(
            ledos_button,
            tearoff=False
        )

        ledos_menu.add_command(
            label="Settings",
            command=self.open_settings
        )

        ledos_menu.add_command(
            label="About LEDos",
            command=self.open_about
        )

        ledos_menu.add_separator()

        ledos_menu.add_command(
            label="Log Out",
            command=self.logout
        )

        ledos_menu.add_command(
            label="Exit",
            command=self.root.destroy
        )

        ledos_button.config(
            menu=ledos_menu
        )

        self.ledos_menu_button = ledos_button

        # ----------------------------------------------------
        # PROGRAMS MENU
        # ----------------------------------------------------

        programs_button = tk.Menubutton(
            self.menu_bar,
            text="Programs",
            bg=FACE,
            fg=BLACK,
            activebackground=self.secondary_color,
            activeforeground=BLACK,
            font=FONT_BOLD,
            relief="raised"
        )

        programs_button.pack(
            side="left"
        )

        programs_menu = tk.Menu(
            programs_button,
            tearoff=False
        )

        programs_menu.add_command(
            label="File Manager",
            command=self.open_file_manager
        )

        programs_menu.add_command(
            label="Notepad",
            command=self.open_notepad
        )

        programs_menu.add_command(
            label="Calculator",
            command=self.open_calculator
        )

        programs_menu.add_command(
            label="Paint",
            command=self.open_paint
        )

        programs_menu.add_command(
            label="Terminal",
            command=self.open_terminal
        )

        programs_menu.add_command(
            label="Clock",
            command=self.open_clock
        )

        programs_button.config(
            menu=programs_menu
        )

        self.programs_menu_button = programs_button

        # ----------------------------------------------------
        # HELP MENU
        # ----------------------------------------------------

        help_button = tk.Menubutton(
            self.menu_bar,
            text="Help",
            bg=FACE,
            fg=BLACK,
            activebackground=self.secondary_color,
            activeforeground=BLACK,
            font=FONT_BOLD,
            relief="raised"
        )

        help_button.pack(
            side="left"
        )

        help_menu = tk.Menu(
            help_button,
            tearoff=False
        )

        help_menu.add_command(
            label="About LEDos",
            command=self.open_about
        )

        help_button.config(
            menu=help_menu
        )

        self.help_menu_button = help_button

    def build_icons(self):
        icons = [
            (
                "File Manager",
                self.open_file_manager
            ),
            (
                "Notepad",
                self.open_notepad
            ),
            (
                "Calculator",
                self.open_calculator
            ),
            (
                "Paint",
                self.open_paint
            ),
            (
                "Terminal",
                self.open_terminal
            ),
            (
                "Clock",
                self.open_clock
            ),
            (
                "Settings",
                self.open_settings
            ),
            (
                "About LEDos",
                self.open_about
            )
        ]

        x = 40
        y = 175

        for index, (
            name,
            command
        ) in enumerate(icons):

            if index == 4:
                x = 170
                y = 175

            if index == 7:
                x = 300
                y = 175

            self.desktop_icon(
                name,
                command,
                x,
                y
            )

            y += 80

    def desktop_icon(
        self,
        name,
        command,
        x,
        y
    ):
        icon = tk.Frame(
            self.desktop,
            bg=self.desktop_background,
            width=110,
            height=65
        )

        icon.place(
            x=x,
            y=y
        )

        symbol = tk.Label(
            icon,
            text="■",
            bg=self.desktop_background,
            fg=self.secondary_color,
            font=("Courier New", 18, "bold")
        )

        symbol.pack()

        label = tk.Label(
            icon,
            text=name,
            bg=self.desktop_background,
            fg=BLACK,
            font=FONT_SMALL
        )

        label.pack()

        # ----------------------------------------------------
        # ONE CLICK
        # ----------------------------------------------------

        for widget in (
            icon,
            symbol,
            label
        ):
            widget.bind(
                "<Button-1>",
                lambda event, c=command: c()
            )

            widget.bind(
                "<Enter>",
                lambda event, s=symbol: self.safe_icon_hover(
                    s,
                    True
                )
            )

            widget.bind(
                "<Leave>",
                lambda event, s=symbol: self.safe_icon_hover(
                    s,
                    False
                )
            )

    def safe_icon_hover(
        self,
        symbol,
        entered
    ):
        try:
            if symbol.winfo_exists():
                symbol.config(
                    fg=self.secondary_color
                )
        except tk.TclError:
            pass

    # --------------------------------------------------------
    # CLOCK
    # --------------------------------------------------------

    def format_time(self):
        if self.clock_format == "12-hour":
            return time.strftime(
                "%I:%M:%S %p"
            )

        return time.strftime(
            "%H:%M:%S"
        )

    def update_desktop_clock(self):
        if not hasattr(
            self,
            "clock_label"
        ):
            return

        try:
            if self.clock_visible:
                self.clock_label.place(
                    x=25,
                    y=48
                )

                self.clock_label.config(
                    text=self.format_time(),
                    fg=self.secondary_color,
                    bg=self.desktop_background
                )

            else:
                self.clock_label.place_forget()

            self.root.after(
                1000,
                self.update_desktop_clock
            )

        except tk.TclError:
            pass

    # --------------------------------------------------------
    # STATUS BAR
    # --------------------------------------------------------

    def update_status_bar(self):
        if hasattr(
            self,
            "status_label"
        ):
            try:
                self.status_label.config(
                    text=(
                        f"{OS_NAME} | "
                        f"{self.username} | "
                        "640 KB RAM | "
                        "C: READY"
                    )
                )
            except tk.TclError:
                pass

    def position_status_bar(self):
        if not hasattr(
            self,
            "status_bar"
        ):
            return

        try:
            width = self.desktop.winfo_width()
            height = self.desktop.winfo_height()

            if width <= 1:
                width = 1024

            if height <= 1:
                height = 768

            self.status_bar.place(
                x=0,
                y=max(
                    0,
                    height - 28
                ),
                width=width,
                height=28
            )

        except tk.TclError:
            pass

    def on_root_resize(self, event):
        if not self.booting:
            self.position_status_bar()

    # --------------------------------------------------------
    # COLORS
    # --------------------------------------------------------

    def set_secondary_color(self, color):
        if not color:
            return

        self.secondary_color = color

        self.save_settings()

        if hasattr(
            self,
            "desktop"
        ):
            self.update_accent_colors()

    def update_accent_colors(self):
        try:
            if hasattr(
                self,
                "clock_label"
            ):
                self.clock_label.config(
                    fg=self.secondary_color
                )

            if hasattr(
                self,
                "desktop_title"
            ):
                self.desktop_title.config(
                    fg=self.secondary_color
                )

            if hasattr(
                self,
                "ledos_menu_button"
            ):
                self.ledos_menu_button.config(
                    activebackground=self.secondary_color
                )

            if hasattr(
                self,
                "programs_menu_button"
            ):
                self.programs_menu_button.config(
                    activebackground=self.secondary_color
                )

            if hasattr(
                self,
                "help_menu_button"
            ):
                self.help_menu_button.config(
                    activebackground=self.secondary_color
                )

            self.update_accent_recursive(
                self.desktop
            )

        except tk.TclError:
            pass

    def update_accent_recursive(self, widget):
        try:
            # Labels that represent accent UI.
            if widget == getattr(
                self,
                "clock_label",
                None
            ):
                widget.config(
                    fg=self.secondary_color
                )

            elif widget == getattr(
                self,
                "desktop_title",
                None
            ):
                widget.config(
                    fg=self.secondary_color
                )

            # Desktop icon symbols.
            elif (
                isinstance(widget, tk.Label)
                and str(
                    widget.cget("text")
                ) == "■"
            ):
                widget.config(
                    fg=self.secondary_color
                )

            # Buttons use the accent as active background.
            if isinstance(
                widget,
                tk.Button
            ):
                widget.config(
                    activebackground=self.secondary_color
                )

            if isinstance(
                widget,
                tk.Menubutton
            ):
                widget.config(
                    activebackground=self.secondary_color
                )

        except tk.TclError:
            pass

        try:
            for child in widget.winfo_children():
                self.update_accent_recursive(
                    child
                )
        except tk.TclError:
            pass

    def set_background(self, color):
        if not color:
            return

        old_color = self.desktop_background

        self.desktop_background = color

        self.save_settings()

        if not hasattr(
            self,
            "desktop"
        ):
            return

        try:
            self.desktop.config(
                bg=color
            )
        except tk.TclError:
            return

        self.update_background(
            self.desktop,
            old_color,
            color
        )

        try:
            self.clock_label.config(
                bg=color
            )

            self.desktop_title.config(
                bg=color
            )

            self.desktop_subtitle.config(
                bg=color
            )

            self.user_label.config(
                bg=color
            )

        except tk.TclError:
            pass

    def update_background(
        self,
        widget,
        old_color,
        new_color
    ):
        try:
            if isinstance(
                widget,
                (
                    tk.Frame,
                    tk.Label
                )
            ):
                current = str(
                    widget.cget("bg")
                )

                if current.lower() == old_color.lower():
                    widget.config(
                        bg=new_color
                    )

        except tk.TclError:
            pass

        try:
            for child in widget.winfo_children():
                self.update_background(
                    child,
                    old_color,
                    new_color
                )
        except tk.TclError:
            pass

    # --------------------------------------------------------
    # FULLSCREEN
    # --------------------------------------------------------

    def toggle_fullscreen(self):
        self.fullscreen = (
            not self.fullscreen
        )

        try:
            self.root.attributes(
                "-fullscreen",
                self.fullscreen
            )
        except tk.TclError:
            pass

    def exit_fullscreen(self):
        self.fullscreen = False

        try:
            self.root.attributes(
                "-fullscreen",
                False
            )
        except tk.TclError:
            pass

    # --------------------------------------------------------
    # LOG OUT
    # --------------------------------------------------------

    def logout(self):
        self.logged_in = False

        self.clear_screen()

        self.build_login()

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    def prompt(
        self,
        title,
        message,
        callback
    ):
        window = tk.Toplevel(
            self.root
        )

        window.title(title)

        window.geometry(
            "420x150"
        )

        window.configure(
            bg=FACE
        )

        window.transient(
            self.root
        )

        tk.Label(
            window,
            text=message,
            bg=FACE,
            fg=BLACK,
            font=FONT
        ).pack(
            pady=(20, 5)
        )

        entry = tk.Entry(
            window,
            bg=WHITE,
            fg=BLACK,
            font=FONT
        )

        entry.pack(
            fill="x",
            padx=20
        )

        buttons = tk.Frame(
            window,
            bg=FACE
        )

        buttons.pack(
            pady=12
        )

        def submit():
            value = entry.get()

            try:
                callback(value)
            finally:
                try:
                    window.destroy()
                except tk.TclError:
                    pass

        LEDosButton(
            buttons,
            text="OK",
            command=submit
        ).pack(
            side="left",
            padx=5
        )

        LEDosButton(
            buttons,
            text="Cancel",
            command=window.destroy
        ).pack(
            side="left",
            padx=5
        )

        entry.focus_set()

        entry.bind(
            "<Return>",
            lambda event: submit()
        )

    # --------------------------------------------------------
    # PROGRAM OPENERS
    # --------------------------------------------------------

    def open_file_manager(self):
        FileManager(self)

    def open_notepad(self, path=None):
        Notepad(
            self,
            path
        )

    def open_calculator(self):
        Calculator(self)

    def open_paint(self):
        Paint(self)

    def open_terminal(self):
        Terminal(self)

    def open_clock(self):
        Clock(self)

    def open_settings(self):
        Settings(self)

    def open_about(self):
        About(self)


# ============================================================
# MAIN
# ============================================================

def main():
    root = tk.Tk()

    LEDos(root)

    root.mainloop()


if __name__ == "__main__":
    main()