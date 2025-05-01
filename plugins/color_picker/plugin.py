from utils.plugins import ToolbarPlugin
from widgets.common_button import CommonButton


class InternetStatus(ToolbarPlugin):
    def __init__(self):
        self.name = "color_picker"
        self.description = "Show color picker button."

        self.shell_context = None

    def plugin_name(self):
        return self.name

    def plugin_description(self):
        return self.description

    def initialize(self, shell_context):
        self.shell_context = shell_context

    def register_toolbar_widget(self):
        return CommonButton(
            name="color-picker-button", icon="color-picker", title="Pick color"
        )
