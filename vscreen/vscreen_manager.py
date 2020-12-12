#!/usr/bin/env python3

from .vscreen_expand import VscreenExpand

from xpywm import configure


class VScreenManager():
    '''Manage vscreen (virtual screeen). Also, move windows between
vscreens.'''

    def __init__(self, pointer, frame_window, displaysize):
        self.pointer = pointer
        self.frame_window = frame_window

        # create vscreens
        self.vscreens = {i: VscreenExpand(displaysize, i, self.frame_window, self.pointer)
                         for i in range(1, configure.MAX_VSCREEN + 1)}

        self.current_vscreen = self.vscreens[1]
        self.last_vscreen = self.vscreens[2]

        self.updatefile = _FileUpdate(1)

    def is_vscreen_of(self, window):
        for vscreen in self.vscreens.values():
            if vscreen.is_managed(window):
                return vscreen
        return None

    def exist(self, window):
        return self.is_vscreen_of(window)

    def find_managed_class_window(self, window_class):
        for vscreen in self.vscreens.values():
            window = vscreen.is_managed(window_class=window_class)
            if window:
                return window
        return False

    # ------------------------
    def select_vscreen(self, n):
        '''Change the virtual screen to N.'''
        next_, last = self.vscreens[n], self.current_vscreen
        if next_ == last:
            return
        last.close()
        next_.open()
        self.current_vscreen, self.last_vscreen = next_, last

        self.updatefile.update(n)

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

    def _all_window_move_vscreen(self, n):
        for vscreen in self.vscreens.values():
            if vscreen.vscreen_number == n:
                continue
            # create a new list object, because
            # vscreen.managed_windows is changed in
            # self.move_window_another_vscreen method
            for window in list(vscreen.managed_windows):
                self.move_window_another_vscreen(window, n)
        self.select_vscreen(n)

    def all_window_move_init_vscreen(self):
        self._all_window_move_vscreen(1)


class _FileUpdate():
    def __init__(self, init):
        # if you annoy file writing, set this variable True
        self.disable = False

        self.filename = configure.VSCREEN_FILE

        self._create_file(init)

    def _write(self, s, mode):
        if self.disable:
            return
        f = open(self.filename, mode=mode)
        print(str(s), file=f, flush=True)
        f.close()

    def _create_file(self, s):
        self._write(s, 'a')

    def update(self, s):
        self._write(s, 'w')
