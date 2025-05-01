from typing import List, Tuple, Callable

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from utils.plugins import LauncherEntry, LauncherPlugin
from gi.repository import Gtk
from utils.plugins import LauncherAction, LauncherCommandType

class PluginEntry:
    def __init__(self):
        self.name = ""
        self.description = ""
        self.location = ""

class PluginManager(LauncherPlugin):
    def __init__(self):
        super().__init__()

        self.name = "plugin_manager"
        self.description = "Manages plugins"
        self.shell_context = None

        self.commands: List[str] = [
            "plugin-list",
            "plugins-list",
            "pl",
            "plugin-reload",
            "plugins-reload",
            "pr",
            "plugin-list-ui",
            "plugins-list-ui",
            "plui"
        ]

    def plugin_name(self):
        return self.name

    def plugin_description(self):
        return self.description

    def initialize(self, shell_context):
        self.shell_context = shell_context

    def register_commands(self) -> List[str]:
        return self.commands

    def run_command(self, command) -> Tuple[LauncherCommandType, Callable] | None:
        match command:
            case (
                "plugin-list" |
                "plugins-list" |
                "pl"
            ):
                return (
                    LauncherCommandType.LIST_COMMAND,
                    self.list_plugins
                )
            case (
                "plugin-reload" |
                "plugins-reload" |
                "pr"
            ):
                return (
                    LauncherCommandType.SINGLE_ENTRY_COMMAND,
                    self.reload_plugins_command
                )
            case (
                "plugin-list-ui" |
                "plugins-list-ui" |
                "plui"
            ):
                return (
                    LauncherCommandType.WIDGET_COMMAND,
                    self.list_plugins_ui
                )
            case _:
                return None


    def reload_plugins_command(self, prompt: str) -> LauncherEntry:
        icon: str = ""
        title: str = "Reload plugins"
        contents: str = ""
        right_label: str = "Plugin manager"
        actions: List[LauncherAction] = [
            LauncherAction(
                name="Reload plugins",
                keys="enter",
                action=self.reload_plugins
            )
        ]

        return LauncherEntry(
            icon,
            title,
            description_markup=contents,
            label=right_label,
            actions=actions
        )

    def reload_plugins(self):
        self.shell_context.reload_plugins()

    def disable_plugin(self, plugin_name):
        ...
        # plugin = plugins[plugin_name]
        # plugin.disable() # whatever

    def list_plugins(self, prompt: str) -> List[LauncherEntry]:
        icon = ""
        plugin_list: List[PluginEntry] = []

        entries = []
        for plugin in plugin_list:
            actions: List[LauncherAction] = [
                LauncherAction(
                    name = "",
                    keys="ctrl+x",
                    action = self.disable_plugin,
                    data = tuple(plugin.name)
                )
            ]

            entries.append(
                LauncherEntry(
                    icon = icon,
                    title = plugin.name,
                    description_markup = plugin.description,
                    label = plugin.location,
                    actions = actions
                )
            )

        return entries

    def list_plugins_ui(self, prompt: str) -> Gtk.Widget:
        return Box(
            children=Label(label="Hello from plugin!")
        )
