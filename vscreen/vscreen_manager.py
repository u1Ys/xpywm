#!/usr/bin/env python3

from .vscreen_expand import VscreenExpand

from .. import configure
from ..util.log import debug

class VScreenManager():
    """Manage vscreen (virtual screeen). Also, move windows between
vscreens."""

    def __init__(self, pointer, frame_window, displaysize):
        self.pointer = pointer
        self.frame_window = frame_window

        # create vscreens
        self.vscreens = {i: VscreenExpand(displaysize, i, self.frame_window, self.pointer)
                         for i in range(1, configure.MAX_VSCREEN+1)}

        self.current_vscreen = self.vscreens[1]
        self.last_vscreen = self.vscreens[2]

    def is_vscreen_of(self, window):
        for vscreen in self.vscreens.values():
            if vscreen.is_managed(window):
                return vscreen
        return None

    def exsist(self, window):
        return self.is_vscreen_of(window)

    def find_managed_class_window(self, window_class):
        for vscreen in self.vscreens.values():
            window = vscreen.is_managed(window_class=window_class)
            if window:
                return window
        return False

    # ------------------------
    def select_vscreen(self, n):
        """Change the virtual screen to N."""
        debug(self, 'select_vscreen: %d', n)
        next_, last = self.vscreens[n], self.current_vscreen
        if next_ == last:
            return
        next_.open()
        last.close()
        self.current_vscreen, self.last_vscreen = next_, last

        f = open(configure.VSCREEN_FILE, mode='w')
        print(n, file=f, flush=True)
        f.close()

    def select_last_vscreen(self):
        self.select_vscreen(self.last_vscreen.vscreen_number)

    # ------------------------ window manage between vscreens
    def move_window_another_vscreen(self, window, n):
        next_, last = self.vscreens[n], self.is_vscreen_of(window)
        if last is None or next_ == last:
            return
        next_.manage_window(window)
        last.unmanage_window(window)
        if last == self.current_vscreen:
            window.unmap()

    def pull_class_window(self, window_class):
        window = self.find_managed_class_window(window_class)
        if not window:
            return
        self.move_window_another_vscreen(window, self.current_vscreen.vscreen_number)
        self.current_vscreen.select_window(window)

    def all_move_init_vscreen(self):
        for i in range(2, configure.MAX_VSCREEN+1):
            vscreen_ = self.vscreens[i]
            for window in vscreen_.managed_windows:
                self.move_window_another_vscreen(window, 1)
        self.select_vscreen(1)
