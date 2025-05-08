# Taken from `https://gist.github.com/johnlane/351adff97df196add08a`

import gi
gi.require_versions({"Gtk": "3.0", "Gdk": "3.0"})
from gi.repository import Gtk, Gdk
from fabric.widgets.window import Window
import Xlib
from Xlib.display import Display
from Xlib import X

class X11DockWindow(Window):
    def __init__(self, x: int, y: int, width: int, height: int, **kwargs):
        super().__init__(
            type="top-level",
            visible=True,
            all_visible=True,
            **kwargs,
        )
        self._x = x
        self._y = y
        self._width = width
        self._height = height

        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_decorated(False)

        self.move(self._x, self._y)
        self.resize(self._width, self._height)

        # it must be shown before changing properties
        self.show_all()

        # (d) reserve space (a "strut") for the bar so it does not become obscured
        #     when other windows are maximized, etc
        # http://stackoverflow.com/questions/33719686  property_change not in gtk3.0
        # https://sourceforge.net/p/python-xlib/mailman/message/27574603
        display = Display()
        topw = display.create_resource_object('window', self.get_toplevel().get_window().get_xid())

        # http://python-xlib.sourceforge.net/doc/html/python-xlib_21.html#SEC20
        topw.change_property(display.intern_atom('_NET_WM_STRUT'),
                            display.intern_atom('CARDINAL'), 32,
                            [0, 0, self._height, 0 ],
                            X.PropModeReplace)
        topw.change_property(display.intern_atom('_NET_WM_STRUT_PARTIAL'),
                            display.intern_atom('CARDINAL'), 32,
                            [0, 0, self._height, 0, 0, 0, 0, 0, self._x, self._x + self._width - 1, 0, 0],
                            X.PropModeReplace)


        # we set _NET_WM_STRUT, the older mechanism as well as _NET_WM_STRUT_PARTIAL
        # but window managers ignore the former if they support the latter.
        #
        # the numbers in the array are as follows:
        #
        # 0, 0, bar_size, 0 are the number of pixels to reserve along each edge of the
        # screen given in the order left, right, top, bottom. Here the size of the bar
        # is reserved at the top of the screen and the other edges are left alone.
        #
        # _NET_WM_STRUT_PARTIAL also supplies a further four pairs, each being a
        # start and end position for the strut (they don't need to occupy the entire
        # edge).
        #
        # In the example, we set the top start to the current monitor's x co-ordinate
        # and the top-end to the same value plus that monitor's width, deducting one.
        # because the co-ordinate system starts at zero rather than 1. The net result
        # is that space is reserved only on the current monitor.
        #
        # co-ordinates are specified relative to the screen (i.e. all monitors together).
        #

    def get_position(self):
        return self._x, self._y

    def set_position(self, position: tuple[int, int]):
        self._x = position[0]
        self._y = position[1]

    def get_size(self):
        return self._width, self._height

    def set_size(self, size: tuple[int, int]):
        self._width = size[0]
        self._height = size[1]
