# Claude.ai's so called "memory-efficient" popover. I don't fully understand this code, but it works :)
from fabric.widgets.widget import Widget
import gi
from loguru import logger
gi.require_versions({"Gtk": "3.0", "Gdk": "3.0", "GtkLayerShell": "0.1", "GObject": "2.0"})
from gi.repository import Gdk, GLib,GtkLayerShell, GObject
from fabric.hyprland.service import HyprlandEvent
from fabric.widgets.wayland import WaylandWindow
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from utils.services import get_hyprland_connection

class PopoverManager:
    """Singleton manager to handle shared resources for popovers."""

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Shared overlay window for all popovers
        self.overlay = WaylandWindow(
            name="popover-overlay",
            style_classes="popover-overlay",
            title="fabric-shell-popover-overlay",
            anchor="left top right bottom",
            margin="-50px 0px 0px 0px",
            exclusivity="auto",
            layer="overlay",
            type="top-level",
            visible=False,
            all_visible=False,
            style="background-color: rgba(0,0,0,0.0);",
        )

        # Add empty box so GTK doesn't complain
        self.overlay.add(Box())

        # Keep track of active popovers
        self.active_popover = None
        self.available_windows = []

        # Close popover when clicking overlay
        self.overlay.connect("button-press-event", self._on_overlay_clicked)
        self._hyprland_connection = get_hyprland_connection()
        self._hyprland_connection.connect("event::focusedmonv2", self._on_monitor_change)

    def _on_monitor_change(self,_, event: HyprlandEvent):
        if self.active_popover:
            self.active_popover.hide_popover()
        return True

    def _on_overlay_clicked(self, widget, event):
        if self.active_popover:
            self.active_popover.hide_popover()
        return True

    def get_popover_window(self):
        """Get an available popover window or create a new one."""
        if self.available_windows:
            return self.available_windows.pop()

        window = WaylandWindow(
            type="popup",
            layer="overlay",
            name="popover-window",
            anchor="left top",
            visible=False,
            all_visible=False,
        )
        GtkLayerShell.set_keyboard_interactivity(window, True)
        window.set_keep_above(True)
        return window

    def return_popover_window(self, window):
        """Return a popover window to the pool."""
        # Remove any children
        for child in window.get_children():
            window.remove(child)

        window.hide()
        # Only keep a reasonable number of windows in the pool
        if len(self.available_windows) < 5:
            self.available_windows.append(window)
        else:
            # Let the window be garbage collected
            window.destroy()

    def activate_popover(self, popover):
        """Set the active popover and show overlay."""
        if self.active_popover and self.active_popover != popover:
            self.active_popover.hide_popover()

        self.active_popover = popover
        self.overlay.show_all()

class PopoverButton(Button):
    """A button that manages its own popover with lazy initialization."""

    def __init__(self, label=None, content_factory=None, **kwargs):
        """
        Initialize a button with popover support.

        Args:
            label: Button label
            content_factory: Function that returns the content widget when called
                             (allows lazy initialization)
            **kwargs: Additional arguments for Button
        """
        super().__init__(label=label, **kwargs)
        self._popover = None
        self._content_factory = content_factory
        self.connect("button-press-event", self._on_button_press)

    def _on_button_press(self, widget, event):
        if not self._popover:
            self._popover = Popover(self._content_factory, self)

        self._popover.open()
        return True

    @property
    def popover(self):
        """Lazy create the popover if accessed."""
        if not self._popover and self._content_factory:
            self._popover = Popover(self._content_factory, self)
        return self._popover

@GObject.Signal(flags=GObject.SignalFlags.RUN_LAST, return_type=GObject.TYPE_NONE, arg_types=())
def popover_opened(widget: Widget): ...

@GObject.Signal(flags=GObject.SignalFlags.RUN_LAST, return_type=GObject.TYPE_NONE, arg_types=())
def popover_closed(widget: Widget): ...

@GObject.type_register
class Popover(Widget):
    """Memory-efficient popover implementation."""

    __gsignals__ = {
        "popover-opened": (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, ()),
        "popover-closed": (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, content_factory, point_to):
        super().__init__()
        """
        Initialize a popover.

        Args:
            content_factory: Function that returns content widget when called
            point_to: Widget to position the popover next to
        """
        self._content_factory = content_factory
        self._point_to = point_to
        self._content_window = None
        self._content = None
        self._visible = False
        self._destroy_timeout = None
        # Use weak reference to avoid circular reference issues
        self._manager = PopoverManager.get_instance()

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            if self._manager.active_popover:
                self._manager.active_popover.hide_popover()

    def open(self):
        if self._destroy_timeout is not None:
            GLib.source_remove(self._destroy_timeout)
            self._destroy_timeout = None

        if not self._content_window:
            try:
                self._create_popover()
            except Exception as e:
                logger.error(f"Could not create popover! Error: {e}")
        else:
            self._manager.activate_popover(self)
            self._content_window.show_all()
            self._content_window.steal_input()
            self._visible = True

        self.emit("popover-opened")

    def _calculate_margins(self):
        widget_allocation = self._point_to.get_allocation()
        popover_size = self._content_window.get_size()

        display = Gdk.Display.get_default()
        screen = display.get_default()
        monitor_at_window = screen.get_monitor_at_window(self._point_to.get_window())
        monitor_geometry = monitor_at_window.get_geometry()

        x = (
            widget_allocation.x
            + (widget_allocation.width / 2)
            - (popover_size.width / 2)
        )
        y = widget_allocation.y - 5

        if x <= 0:
            x = widget_allocation.x
        elif x + popover_size.width >= monitor_geometry.width:
            x = widget_allocation.x - popover_size.width + widget_allocation.width

        return [y, 0, 0, x]

    def set_position(self, position: tuple[int, int, int, int] | None = None):
        if position is None:
            self._content_window.set_margin(self._calculate_margins())
            return False

        self._content_window.set_margin(position)
        return False

    def _on_content_ready(self, widget, event):
        self.set_position()

    def _create_popover(self):
        if not self._content and self._content_factory:
            self._content = self._content_factory()
        else:
            return

        # Get a window from the pool
        self._content_window = self._manager.get_popover_window()

        # This is a hack to fix wrong positioning for widgets that are not rendered immediately (e.g., Gtk.Calendar())
        self._content.connect("draw", self._on_content_ready)

        # Add content to window
        self._content_window.add(
            Box(style_classes="popover-content", children=self._content)
        )

        self._content_window.connect("focus-out-event", self._on_popover_focus_out)

        self._content_window.connect("key-press-event", self._on_key_press)
        self._manager.activate_popover(self)
        self._content_window.show_all()
        self._content_window.steal_input()
        self._visible = True

    def _on_popover_focus_out(self, widget, event):
        # This helps with keyboard focus issues
        GLib.timeout_add(100, self.hide_popover)
        return False

    def hide_popover(self):
        if not self._visible or not self._content_window:
            return False

        self._content_window.hide()
        self._manager.overlay.hide()
        self._visible = False

        if not self._destroy_timeout:
            self._destroy_timeout = GLib.timeout_add(1000 * 5, self._destroy_popover)

        self.emit("popover-closed")

        return False

    def _destroy_popover(self):
        """Return resources to the pool and clear references."""
        self._destroy_timeout = None
        self._visible = False

        if self._content_window:
            # Return window to the pool
            self._manager.return_popover_window(self._content_window)
            self._content_window = None

        # Allow content to be garbage collected if no longer needed
        self._content = None

        return False
