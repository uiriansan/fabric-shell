from utils.plugins import ToolbarPlugin
from widgets.common_button import CommonButton
from .service import AudioService
from .popover import AudioPopover

class InternetStatus(ToolbarPlugin):
    def __init__(self):
        self.name = "audio"
        self.description = "Show audio button."

        self.audio_service = AudioService()

        self.shell_context = None

    def plugin_name(self):
        return self.name

    def plugin_description(self):
        return self.description

    def initialize(self, shell_context):
        self.shell_context = shell_context

    def get_popover_content(self):
        return AudioPopover()

    def register_toolbar_widget(self):
        return CommonButton(
            name="volume-button", icon="volume-max", title="Volume: 100%"
        )
