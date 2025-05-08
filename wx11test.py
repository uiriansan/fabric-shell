# Taken from `https://gist.github.com/johnlane/351adff97df196add08a`

import gi
gi.require_versions({'Gtk':'3.0', "Gdk": "3.0"})
from gi.repository import Gtk, Gdk
import Xlib
from Xlib.display import Display
from Xlib import X
from fabric.core.application import Application

# Colour style for (b)
stylesheet=b"""
window#bar {
  background-color: alpha(#161617, 0.1);
}
"""
#  the size of the bar (its height), in pixels
bar_size = 30

class X11DockWindow(Gtk.Window):
    # (a) Create an undecorated dock
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

        self.set_name("bar")
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_decorated(False)

        # (b) Style it
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(stylesheet)
        Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # the screen contains all monitors
        display = Gdk.Display.get_default()
        mon = display.get_monitor(self.monitor)
        mg = mon.get_geometry()

        x = mg.x
        y = mg.y
        width = mg.width
        height = mg.height

        # display bar along the top of the current monitor
        self.move(x,y)
        self.resize(width,bar_size)

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
                            [0, 0, bar_size, 0 ],
                            X.PropModeReplace)
        topw.change_property(display.intern_atom('_NET_WM_STRUT_PARTIAL'),
                            display.intern_atom('CARDINAL'), 32,
                            [0, 0, bar_size, 0, 0, 0, 0, 0, x, x+width-1, 0, 0],
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

if __name__ == "__main__":
    bars = []
    for m in range(2):
      bars.append(X11DockWindow(m))

    app = Application("test", *bars)
    app.run()
