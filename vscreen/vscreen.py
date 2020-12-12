#!/usr/bin/env python3

import logging

import Xlib
from Xlib import X

from xpywm.util import external_command, window_property


class VscreenBase():
    @staticmethod
    def execute_when_window_is_managed(method):
        def wrapper(self, window, *args, **kargs):
            if self.is_managed(window):
                method(self, window, *args, **kargs)
        return wrapper


class Vscreen(VscreenBase):
    '''Manage windows within a single vscreen (virtual screen).  Here,
    only basic functions are implemented.

    '''

    def __init__(self, vscreen_number, frame_window, pointer):
        self.vscreen_number = vscreen_number
        self.frame_window = frame_window
        self.pointer = pointer

        # windows in managed_windows is sorted by recently focused on
        self.managed_windows = WindowList()

    # ------------------------
    def is_managed(self,
                   window=None,
                   window_class=None):
        if window is not None:
            return window in self.managed_windows
        elif window_class is not None:
            for window in self.managed_windows:
                if window_class in window_property.get_window_class(window).lower():
                    return window
        return False

    @property
    def current_focused_window(self):
        return self.managed_windows[-1] if self.managed_windows else None

    # ------------------------
    def open(self):
        for window in self.managed_windows:
            window.map()

        if self.managed_windows:
            self.pointer.move_to(self.current_focused_window)
        else:
            self.pointer.move(self.pointer.default_geometry)

    def close(self):
        for window in self.managed_windows:
            window.unmap()

    # ------------------------ basic operation
    def manage_window(self, window):
        '''The window WINDOW is put under the control of the window manager.
        The window is forced to be mapped on the current virtual screen.  The
        geometry of the window is unchnaged.'''
        # skip if the window seems invalid
        try:
            attrs = window.get_attributes()
        except Xlib.error.BadWindow:
            return False
        # skip if the window should not be managed by window manager
        # or the window is already under our control
        if attrs.override_redirect or self.is_managed(window):
            return False
        self.managed_windows.append(window)
        window.map()
        mask = X.EnterWindowMask | X.LeaveWindowMask
        window.change_attributes(event_mask=mask)
        external_command.transset(window)

        return True

    @VscreenBase.execute_when_window_is_managed
    def unmanage_window(self, window):
        '''The window WINDOW leaves from the control of the window manager.'''
        self.managed_windows.remove(window)

    @VscreenBase.execute_when_window_is_managed
    def destroy_window(self, window):
        '''Kill the window WINDOW.'''
        window.destroy()
        self.unmanage_window(window)

    @VscreenBase.execute_when_window_is_managed
    def activate_window(self, window):
        '''Activate the input to the window WINDOW and the window frame is
        displayed.'''
        self.pointer.cursor_set(window)
        window.set_input_focus(X.RevertToParent, 0)
        self.frame_window.draw_frame_windows(window)
        # move the current window to last of managed_windows
        self.managed_windows.move_to_end(window)

    @VscreenBase.execute_when_window_is_managed
    def select_window(self, window):
        '''Change the active window to WINDOW.  The active window is raised
        and activated.  The pointer is moved to the window.
        '''
        window.raise_window()
        self.pointer.move_to(window)
        self.activate_window(window)

    @window_property.return_with_get_geometry_exception
    def select_other_window(self, current_window=None, reverse=False):
        '''Change the active window from the window WINDOW to the next one.

        '''
        def _sort_key(window):
            geom = window.get_geometry()
            return geom.x * 10000 + geom.y

        # fix integrity is only here
        self.managed_windows.fix_integrity()
        if not self.managed_windows:
            return
        windows = sorted(self.managed_windows.sorted(), key=_sort_key)

        if reverse:
            windows = list(reversed(windows))
        try:
            i = windows.index(current_window)
            next_window = windows[(i + 1) % len(windows)]
        except ValueError:
            # ValueError -> failed in windows.index(current_window),
            # current_window isn't in windows
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


class WindowList(list):
    def move_to_end(self, elem):
        index = self.index(elem)
        self.append(self.pop(index))

    def sorted(self):
        '''Returns a sorted list. This method is used for *sorting*. The
        reason is that Python sorting depends on the order of the
        source iterators (for example, when the values are the same),
        but this list is often reordered.

        '''
        return list(sorted(self,
                           key=lambda window: window.id))

    def fix_integrity(self):
        '''Remove invalid window which can't be got geometry from managed
        windows

        '''
        for window in self:
            try:
                window.get_geometry()
            except (Xlib.error.BadWindow, Xlib.error.BadDrawable):
                logging.error('remove %s from managed windows', window)
                self.remove(window)
