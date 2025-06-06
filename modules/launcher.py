import operator, gi
gi.require_version("Gtk", "3.0")
from collections.abc import Iterator
from typing import Callable, Dict, Tuple
from fabric.utils import DesktopApp, get_desktop_applications, idle_add, remove_handler
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.image import Image
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.wayland import WaylandWindow as Window
from utils.plugins import LauncherCommandType
from widgets.tag_entry import TagEntry

class Launcher(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="launcher",
            layer="top",
            anchor="center",
            exclusivity="none",
            keyboard_mode="on-demand",
            visible=False,
            all_visible=False,
            **kwargs,
        )
        self._arranger_handler: int = 0
        self._all_apps = get_desktop_applications()

        self._commands = {}
        self._command_handler = None

        self.viewport = Box(spacing=2, orientation="v")
        self.search_entry = Entry(
            name="launcher-prompt",
            placeholder="Search Applications...",
            h_expand=True,
            notify_text=lambda entry, *_: self.arrange_viewport(entry.get_text()),
        )

        self.tag_entry = TagEntry(
            h_expand=True, placeholder="Tags", available_tags=["tag1", "tag2", "tag3"]
        )

        self.scrolled_window = ScrolledWindow(
            min_content_size=(280, 320),
            max_content_size=(280 * 2, 320),
            child=self.viewport,
        )

        self.add(
            Box(
                name="launcher-contents",
                spacing=2,
                orientation="v",
                children=[
                    # the header with the search entry
                    Box(
                        spacing=2,
                        orientation="h",
                        children=[
                            self.search_entry,
                            Button(
                                image=Image(icon_name="window-close"),
                                tooltip_text="Exit",
                                on_clicked=lambda *_: self.hide(),
                            ),
                        ],
                    ),
                    # self.tag_entry,
                    # the actual slots holder
                    self.scrolled_window,
                ],
            )
        )
        self.show_all()

        self.search_entry.grab_focus_without_selecting()
        self.hide()

    def arrange_viewport(self, query: str = ""):
        # reset everything so we can filter current viewport's slots...
        # remove the old handler so we can avoid race conditions
        remove_handler(self._arranger_handler) if self._arranger_handler else None

        # remove all children from the viewport
        self.viewport.children = []

        # make a new iterator containing the filtered apps
        command = None
        prompt = ""
        try:
            command, prompt = query.split(" ", 1)
        except:
            command = query

        if len(command) > 0 and self._command_handler:
            command_data: Tuple[LauncherCommandType, Callable] | None = None
            if (command_data := self._command_handler(command)) is not None:
                command_type, command_factory = command_data
                result = command_factory(prompt)

                if command_type == LauncherCommandType.SINGLE_ENTRY_COMMAND:
                    print(result.title, result.label)
                elif command_type == LauncherCommandType.LIST_COMMAND:
                    ...
                else:
                    ...
                return False
        filtered_apps_iter = iter(
            [
                app
                for app in self._all_apps
                if query.casefold()
                in (
                    (app.display_name or "")
                    + (" " + app.name + " ")
                    + (app.generic_name or "")
                ).casefold()
            ]
        )
        should_resize = operator.length_hint(filtered_apps_iter) == len(self._all_apps)

        # all aboard...
        # start the process of adding slots with a lazy executor
        # using this method makes the process of adding slots way more less
        # resource expensive without blocking the main thread and resulting in a lock
        self._arranger_handler = idle_add(
            lambda *args: self.add_next_application(*args)
            or (self.resize_viewport() if should_resize else False),
            filtered_apps_iter,
            pin=True,
        )

        return False

    def add_next_application(self, apps_iter: Iterator[DesktopApp]):
        if not (app := next(apps_iter, None)):
            return False

        self.viewport.add(self.bake_application_slot(app))
        return True

    def resize_viewport(self):
        self.scrolled_window.set_min_content_width(
            self.viewport.get_allocation().width  # type: ignore
        )
        return False

    def bake_application_slot(self, app: DesktopApp, **kwargs) -> Button:
        return Button(
            style_classes="launcher-button",
            child=Box(
                orientation="h",
                spacing=12,
                children=[
                    Image(pixbuf=app.get_icon_pixbuf(), h_align="start", size=32),
                    Label(
                        label=app.display_name or "Unknown",
                        v_align="center",
                        h_align="center",
                    ),
                ],
            ),
            tooltip_text=app.description,
            on_clicked=lambda *_: (
                app.launch(),
                self.hide(),
                self.search_entry.set_text(""),
            ),
            **kwargs,
        )

    def set_commands(self, commands: Dict):
        self._commands = commands

    def set_command_handler(self, command_handler: Callable):
        self._command_handler = command_handler

    def toggle(self):
        visible = self.get_visible()
        if visible:
            return self.set_visible(False)
        self._all_apps = get_desktop_applications()
        self.search_entry.set_text(""),
        self.search_entry.grab_focus_without_selecting()
        return self.set_visible(True)

    def launch(self, command: str):
        self.search_entry.set_text(command)
