import sys
from pathlib import Path
from typing import Optional, List
from PIL import Image
import customtkinter as ctk

import database as db

# Base directories
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"

# Set Modern Appearance Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Design Palette (Obsidian / Crimson / Clean Minimalist)
COLOR_BG = "#08070A"
COLOR_CONTAINER_BG = "#0F0D13"
COLOR_SURFACE = "#15131A"
COLOR_SURFACE_HOVER = "#201B26"
COLOR_SURFACE_ACTIVE = "#282230"
COLOR_CRIMSON = "#FF1E44"
COLOR_CRIMSON_HOVER = "#E01438"
COLOR_CRIMSON_MUTED = "#3D121B"
COLOR_TEXT_PRIMARY = "#F4F3F6"
COLOR_TEXT_SECONDARY = "#9E9AA7"
COLOR_TEXT_MUTED = "#5E5A68"
COLOR_BORDER = "#25212E"
COLOR_BORDER_FOCUS = "#FF1E44"
COLOR_SUCCESS = "#10B981"


class TodoApp(ctk.CTk):
    """TaskFlow - Desktop Productivity Stream & Local Command Engine."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("TASKFLOW ® // Desktop Stream")
        self.geometry("780x830")
        self.minsize(560, 680)
        self.configure(fg_color=COLOR_BG)

        # State
        self.editing_task_id: Optional[int] = None
        self.current_filter: str = "all"  # 'all', 'active', 'completed'
        self.search_query: str = ""
        self.loaded_images = {}

        # Initialize DB
        db.setup_database()

        # Load Assets Safely
        self._load_assets()

        # Build Main View
        self._build_layout()

        # Keyboard shortcuts
        self.bind("<Return>", lambda event: self.submit_task())
        self.bind("<Escape>", lambda event: self.cancel_edit())
        self.bind("<Control-f>", lambda event: self.search_entry.focus_set())

        # Initial Render
        self.refresh_tasks()

    def _load_assets(self):
        """Loads icons safely if present in assets folder."""
        def load_icon(filename: str, size=(18, 18)):
            path = ASSETS_DIR / filename
            if path.exists():
                try:
                    pil_img = Image.open(path)
                    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                except Exception:
                    return None
            return None

        self.loaded_images["add"] = load_icon("icons8-add-button-96.png", size=(20, 20))
        self.loaded_images["edit"] = load_icon("icons8-edit-48.png", size=(16, 16))
        self.loaded_images["trash"] = load_icon("icons8-trash-48.png", size=(16, 16))

    def _build_layout(self):
        """Builds centered constrained layout that looks great on any screen resolution."""
        # Root Centered Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=28, pady=24)

        # Header Section (Clean brand with ® mark)
        self._create_header()

        # Input & Actions Section
        self._create_input_section()

        # Filter Tabs & Search Bar
        self._create_filter_bar()

        # Scrollable Task Cards Area
        self._create_task_list_container()

        # Footer Status Bar
        self._create_footer_bar()

    def _create_header(self):
        """Top Brand Header with TASKFLOW® and Live Progress Pill."""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 18))

        # Brand Title Row: TASK + FLOW + ®
        title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_row.pack(side="left", anchor="w")

        logo_prefix = ctk.CTkLabel(
            title_row,
            text="TASK",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        logo_prefix.pack(side="left")

        logo_suffix = ctk.CTkLabel(
            title_row,
            text="FLOW",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLOR_CRIMSON,
        )
        logo_suffix.pack(side="left", padx=(2, 2))

        # Registered Mark: Small, raised, elegant muted accent
        reg_mark = ctk.CTkLabel(
            title_row,
            text="®",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        reg_mark.pack(side="left", anchor="n", pady=(2, 0))

        # Right Stat Widget
        self.stats_pill = ctk.CTkLabel(
            header_frame,
            text="0 / 0 Done",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY,
            fg_color=COLOR_SURFACE,
            corner_radius=12,
            padx=14,
            pady=6,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.stats_pill.pack(side="right")

    def _create_input_section(self):
        """Input field with embedded glowing accent button."""
        input_card = ctk.CTkFrame(
            self.main_container,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=14,
        )
        input_card.pack(fill="x", pady=(0, 14))

        self.task_entry = ctk.CTkEntry(
            input_card,
            placeholder_text="What needs to be done? (Press Enter to add)",
            placeholder_text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="transparent",
            text_color=COLOR_TEXT_PRIMARY,
            border_width=0,
            height=48,
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(14, 8), pady=4)

        self.action_btn = ctk.CTkButton(
            input_card,
            text="Add Task",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            image=self.loaded_images.get("add"),
            width=100,
            height=36,
            corner_radius=10,
            fg_color=COLOR_CRIMSON,
            hover_color=COLOR_CRIMSON_HOVER,
            command=self.submit_task,
        )
        self.action_btn.pack(side="right", padx=8, pady=4)

    def _create_filter_bar(self):
        """Segmented Filters (All / Active / Done) and Live Search."""
        filter_bar = ctk.CTkFrame(self.main_container, fg_color="transparent")
        filter_bar.pack(fill="x", pady=(0, 12))

        # Tab Buttons Container
        tabs_box = ctk.CTkFrame(filter_bar, fg_color=COLOR_SURFACE, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        tabs_box.pack(side="left", pady=2)

        self.tab_buttons = {}
        tab_specs = [("all", "All"), ("active", "Active"), ("completed", "Done")]

        for key, label in tab_specs:
            btn = ctk.CTkButton(
                tabs_box,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                width=64,
                height=28,
                corner_radius=8,
                fg_color="transparent",
                text_color=COLOR_TEXT_SECONDARY,
                hover_color=COLOR_SURFACE_HOVER,
                command=lambda k=key: self.set_filter(k),
            )
            btn.pack(side="left", padx=3, pady=3)
            self.tab_buttons[key] = btn

        self._update_tab_styles()

        # Search box on right
        search_card = ctk.CTkFrame(filter_bar, fg_color=COLOR_SURFACE, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        search_card.pack(side="right", pady=2)

        self.search_entry = ctk.CTkEntry(
            search_card,
            placeholder_text="Search tasks... (Ctrl+F)",
            placeholder_text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            text_color=COLOR_TEXT_PRIMARY,
            border_width=0,
            width=160,
            height=28,
        )
        self.search_entry.pack(side="left", padx=8)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

    def _create_task_list_container(self):
        """Task cards scrolling canvas."""
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.main_container,
            fg_color="transparent",
            corner_radius=12,
            scrollbar_button_color="#221E2A",
            scrollbar_button_hover_color=COLOR_CRIMSON,
        )
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 10))

    def _create_footer_bar(self):
        """Bottom Action / Info Bar."""
        self.footer = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.footer.pack(fill="x", pady=(4, 0))

        self.count_label = ctk.CTkLabel(
            self.footer,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.count_label.pack(side="left")

        self.clear_btn = ctk.CTkButton(
            self.footer,
            text="Clear Completed",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            text_color=COLOR_TEXT_MUTED,
            hover_color=COLOR_SURFACE,
            height=24,
            corner_radius=6,
            command=self.clear_completed_tasks,
        )
        self.clear_btn.pack(side="right")

    def set_filter(self, filter_name: str):
        """Switches active filter between All, Active, and Completed."""
        self.current_filter = filter_name
        self._update_tab_styles()
        self.refresh_tasks()

    def _update_tab_styles(self):
        """Highlights the active filter tab."""
        for key, btn in self.tab_buttons.items():
            if key == self.current_filter:
                btn.configure(fg_color=COLOR_CRIMSON, text_color=COLOR_TEXT_PRIMARY, hover_color=COLOR_CRIMSON_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_SECONDARY, hover_color=COLOR_SURFACE_HOVER)

    def on_search_change(self, event=None):
        """Live search filter callback."""
        self.search_query = self.search_entry.get().strip().lower()
        self.refresh_tasks()

    def refresh_tasks(self):
        """Rerenders task cards with modern Linear-style cards."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        all_tasks = db.get_tasks()
        total_count = len(all_tasks)
        completed_count = sum(1 for t in all_tasks if t["completed"])
        active_count = total_count - completed_count

        # Update Badges
        self.stats_pill.configure(text=f"{completed_count}/{total_count} Done")
        self.tab_buttons["all"].configure(text=f"All ({total_count})")
        self.tab_buttons["active"].configure(text=f"Active ({active_count})")
        self.tab_buttons["completed"].configure(text=f"Done ({completed_count})")

        # Filter List
        filtered: List = []
        for task in all_tasks:
            is_done = bool(task["completed"])
            task_text = task["task"]

            # Filter Tab match
            if self.current_filter == "active" and is_done:
                continue
            if self.current_filter == "completed" and not is_done:
                continue

            # Search Query match
            if self.search_query and self.search_query not in task_text.lower():
                continue

            filtered.append(task)

        # Update footer count
        self.count_label.configure(text=f"Showing {len(filtered)} of {total_count} items")

        # Empty State
        if not filtered:
            empty_box = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_SURFACE, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
            empty_box.pack(fill="x", pady=30, padx=8)

            msg = "No tasks found."
            if self.search_query:
                msg = f'No tasks matching "{self.search_query}"'
            elif self.current_filter == "active":
                msg = "No active tasks! You are all caught up. 🎉"
            elif self.current_filter == "completed":
                msg = "No completed tasks yet."

            ctk.CTkLabel(
                empty_box,
                text=msg,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLOR_TEXT_SECONDARY,
                pady=30,
            ).pack()
            return

        # Render Task Cards
        for task in filtered:
            task_id = task["id"]
            task_text = task["task"]
            is_done = bool(task["completed"])

            # Outer Card
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=COLOR_SURFACE if not is_done else "#100E14",
                corner_radius=12,
                border_width=1,
                border_color=COLOR_BORDER if not is_done else "#18141F",
                height=58,
            )
            card.pack(fill="x", pady=5, padx=4)
            card.pack_propagate(False)

            # Left Edge Accent Indicator
            accent_bar = ctk.CTkFrame(
                card,
                width=4,
                fg_color=COLOR_CRIMSON if not is_done else "transparent",
                corner_radius=2,
            )
            accent_bar.pack(side="left", fill="y", padx=(0, 8))

            # Modern Checkbox
            cb = ctk.CTkCheckBox(
                card,
                text="",
                width=22,
                checkbox_width=20,
                checkbox_height=20,
                corner_radius=6,
                border_width=2,
                border_color=COLOR_CRIMSON if not is_done else COLOR_TEXT_MUTED,
                fg_color=COLOR_CRIMSON,
                hover_color=COLOR_CRIMSON_HOVER,
                command=lambda tid=task_id: self.toggle_task(tid),
            )
            if is_done:
                cb.select()
            cb.pack(side="left", padx=(4, 10))

            # Task Text (wrapped safely)
            font_config = ctk.CTkFont(family="Segoe UI", size=13, overstrike=is_done)
            label = ctk.CTkLabel(
                card,
                text=task_text,
                font=font_config,
                text_color=COLOR_TEXT_MUTED if is_done else COLOR_TEXT_PRIMARY,
                anchor="w",
            )
            label.pack(side="left", fill="x", expand=True, padx=(0, 10))

            # Delete Button
            del_btn = ctk.CTkButton(
                card,
                text="" if self.loaded_images.get("trash") else "✕",
                image=self.loaded_images.get("trash"),
                width=32,
                height=32,
                fg_color="transparent",
                hover_color=COLOR_SURFACE_HOVER,
                text_color=COLOR_TEXT_MUTED,
                corner_radius=8,
                command=lambda tid=task_id: self.delete_task(tid),
            )
            del_btn.pack(side="right", padx=(2, 10))

            # Edit Button (only allowed on active tasks)
            if not is_done:
                edit_btn = ctk.CTkButton(
                    card,
                    text="" if self.loaded_images.get("edit") else "✎",
                    image=self.loaded_images.get("edit"),
                    width=32,
                    height=32,
                    fg_color="transparent",
                    hover_color=COLOR_SURFACE_HOVER,
                    text_color=COLOR_TEXT_MUTED,
                    corner_radius=8,
                    command=lambda tid=task_id, ttxt=task_text: self.start_edit_task(tid, ttxt),
                )
                edit_btn.pack(side="right", padx=2)

    def submit_task(self):
        """Handles creating a new task or saving an edit."""
        text = self.task_entry.get().strip()
        if not text:
            return

        if self.editing_task_id is not None:
            db.update_task_text(self.editing_task_id, text)
            self.cancel_edit()
        else:
            db.add_task(text)
            self.task_entry.delete(0, "end")

        self.refresh_tasks()

    def start_edit_task(self, task_id: int, current_text: str):
        """Enters edit mode for a specific task."""
        self.editing_task_id = task_id
        self.task_entry.delete(0, "end")
        self.task_entry.insert(0, current_text)
        self.task_entry.focus_set()

        # Visual indicator that we're editing
        self.action_btn.configure(text="Save", image=None, fg_color=COLOR_SUCCESS, hover_color="#0D946A")

    def cancel_edit(self):
        """Exits active edit mode."""
        self.editing_task_id = None
        self.task_entry.delete(0, "end")
        self.action_btn.configure(
            text="Add Task",
            image=self.loaded_images.get("add"),
            fg_color=COLOR_CRIMSON,
            hover_color=COLOR_CRIMSON_HOVER,
        )

    def toggle_task(self, task_id: int):
        """Toggles completed status."""
        db.toggle_task_completed(task_id)
        self.refresh_tasks()

    def delete_task(self, task_id: int):
        """Deletes task from database."""
        if self.editing_task_id == task_id:
            self.cancel_edit()
        db.delete_task(task_id)
        self.refresh_tasks()

    def clear_completed_tasks(self):
        """Removes all checked-off items."""
        all_tasks = db.get_tasks()
        for t in all_tasks:
            if t["completed"]:
                db.delete_task(t["id"])
        self.refresh_tasks()


if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
