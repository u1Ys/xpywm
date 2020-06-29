#!/usr/bin/env python3

import Xlib
from Xlib import X

from ..util import external_command
from ..util import property_


class Vscreen():
    """Manage windows within a single vscreen (virtual screen). Here, only
basic functions are implemented."""

    def __init__(self, vscreen_number, frame_window, pointer):
        self.vscreen_number = vscreen_number
        self.frame_window = frame_window
        self.pointer = pointer

        self.managed_windows = []
        self.last_focused_window = None
        self.pointer_geometry = pointer.default_geometry

    # ------------------------
    def is_managed(self, window=None, window_class=None):
        if window is not None:
            return window in self.managed_windows
        elif window is None and window_class is not None:
            for window in self.managed_windows:
                if window_class in property_.get_window_class(window).lower():
                    return window
        return False

    # ------------------------
    def open(self):
        self.pointer.move(self.pointer_geometry)
        for window in self.managed_windows:
            window.map()

    def close(self):
        self.pointer_geometry = self.pointer.current_geometry()
        for window in self.managed_windows:
            window.unmap()

    # ------------------------ basic operation
    def manage_window(self, window):
        """The window WINDOW is put under the control of the window manager.
        The window is forced to be mapped on the current virtual screen.  The
        geometry of the window is unchnaged."""
        # skip if the window seems invalid
        try:
            attrs = window.get_attributes()
        except Xlib.error.BadWindow:
            return
        # skip if the window should not be intercepted by window manager/
        # skip if the window is under our control
        # TODO: need check is managed?
        if attrs.override_redirect or self.is_managed(window):
            return
        self.managed_windows.append(window)
        window.map()
        mask = X.EnterWindowMask | X.LeaveWindowMask
        window.change_attributes(event_mask=mask)            
        external_command.transset(window)

    def unmanage_window(self, window):
        """The window WINDOW leaves from the control of the window manager."""
        # TODO: need check is managed?
        if self.is_managed(window):
            self.managed_windows.remove(window)

    def destroy_window(self, window):
        """Kill the window WINDOW."""
        if self.is_managed(window):
            window.destroy()
            self.unmanage_window(window)

    def focus_window(self, window):
        """Activate the input to the window WINDOW and the window frame is
        displayed."""

        self.pointer.cursor_set(window)
        window.set_input_focus(X.RevertToParent, 0)
        self.frame_window.draw_frame_windows(window)

    def select_window(self, window):
        window.raise_window()
        self.focus_window(window)
        self.pointer.move_to_window(window)

    def select_other_window(self, window=None, reverse=False):
        """Change the active window from the window WINDOW to the next one.
        The active window is raised and focused.  The pointer is moved
        to the north-west of the window. If reverse is True, reverse
        the order. (move toprevious one)

        """
        def _sort_key(window):
            geom = window.get_geometry()
            return geom.x * 10000 + geom.y
        # sort active windows with their geometries
        windows = sorted(self.managed_windows, key=_sort_key)
        if reverse:
            windows = list(reversed(windows))
        # if no window alive, do nothing
        if not windows:
            return
        try:
            i = windows.index(window)
            next_window = windows[(i + 1) % len(windows)]
        except (IndexError, ValueError):
            next_window = windows[0]
        self.select_window(next_window)

    def select_last_window(self, window):
        if not self.is_managed(self.last_focused_window) \
           or window == self.last_focused_window:
            return
        self.select_window(self.last_focused_window)

    def select_class_window(self, window_class):
        window = self.is_managed(window_class=window_class)
        if not window:
            return False
        self.select_window(window)
        return True
