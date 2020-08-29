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

    # ------------------------
    def is_managed(self, window=None, window_class=None):
        if window is not None:
            return window in self.managed_windows
        elif window is None and window_class is not None:
            for window in self.managed_windows:
                if window_class in property_.get_window_class(window).lower():
                    return window
        return False

    @property
    def current_focused_window(self):
        return self.managed_windows[-1] if self.managed_windows else None

    # ------------------------
    def open(self):
        if self.managed_windows:
            self.pointer.move_to(self.current_focused_window)
        else:
            self.pointer.move(self.pointer.default_geometry)

        for window in self.managed_windows:
            window.map()

    def close(self):
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
        if not self.is_managed(window):
            return
        self.managed_windows.remove(window)

    def destroy_window(self, window):
        """Kill the window WINDOW."""
        if not self.is_managed(window):
            return
        window.destroy()
        self.unmanage_window(window)

    def activate_window(self, window):
        """Activate the input to the window WINDOW and the window frame is
        displayed."""
        self.pointer.cursor_set(window)
        window.set_input_focus(X.RevertToParent, 0)
        self.frame_window.draw_frame_windows(window)
        # move the current window to last of managed_windows
        self.managed_windows.append(
            self.managed_windows.pop(self.managed_windows.index(window))
        )

    def select_window(self, window):
        """Change the active window to WINDOW.  The active window is raised
        and activated.  The pointer is moved to the window.
        """
        window.raise_window()
        self.pointer.move_to(window)
        self.activate_window(window)

    def select_other_window(self, window=None, reverse=False):
        """Change the active window from the window WINDOW to the next one.

        """
        def _sort_key(window):
            geom = window.get_geometry()
            return geom.x * 10000 + geom.y
        # if no window alive, do nothing
        if not self.managed_windows:
            return
        # sort active windows with their geometries
        windows = sorted(self.managed_windows, key=_sort_key)
        if reverse:
            windows = list(reversed(windows))
        try:
            i = windows.index(window)
            next_window = windows[(i + 1) % len(windows)]
        except (IndexError, ValueError):
            next_window = windows[0]
        self.select_window(next_window)

    def select_last_window(self, window):
        if len(self.managed_windows) < 2:
            return
        last_focused_window = self.managed_windows[-2]
        self.select_window(last_focused_window)

    def select_class_window(self, window_class):
        window = self.is_managed(window_class=window_class)
        if not window:
            return False
        self.select_window(window)
        return True
