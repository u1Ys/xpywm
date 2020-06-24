#!/usr/bin/env python3

import itertools
import re

from .vscreen import Vscreen

from .. import configure
from .. import property_

class VscreenExpand(Vscreen):
    """Manage windows within a single vscreen (virtual screen). Here, the
extended functions using the basic functions implemented in VScreen
are implemented."""

    def __init__(self, *args):
        super().__init__(*args)
        
        self.last_index_hz = 0

    # ------------------------ maximize
    # TODO
    def is_maximized(self, window):
        """Check if the window WINDOW seems to have been maximized."""
        geom = window.get_geometry()
        width, height = self.get_screen_size()
        if geom.x == 0 and geom.width == width:
            return True
        if geom.y == configure.Y_OFFSET and geom.height == (height - configure.Y_OFFSET):
            return True
        return False

    def save_window_geometry(self, window):
        """Save the current geometry of the window WINDOW."""
        geom = window.get_geometry()
        self.geometries[window] = {
            'x': geom.x, 'y': geom.y, 'width': geom.width, 'height':
            geom.height
        }

    def load_window_geometry(self, window):
        """Return the saved geometry of the window WINDOW.  If not saved yet,
        return None."""
        return self.geometries.get(window, None)

    def maximize_window(self, window, horizontally=True, vertically=True):
        """Resize the geometry of the window WINDOW to cover the screen
        horizontally and/or vertically."""
        if not self.is_exposed_window(window):
            return
        geom = window.get_geometry()
        x, y = geom.x, geom.y
        width, height = geom.width, geom.height

        screen_width, screen_height = self.get_screen_size()
        if horizontally:
            x, width = 0, screen_width
        if vertically:
            y, height = configure.Y_OFFSET, screen_height - configure.Y_OFFSET
        window.configure(x=x, y=y, width=width, height=height, stack_mode=X.Above)

        self.draw_frame_windows(window)
        self.warp_pointer(window)

    # ------------------------ layout
    def layout_all_windows(self):
        def layout_window(window, class_, half_size=False):
            for regexp, geom in configure.LAYOUT_RULES.items():
                geom = [*geom]
                if re.search(regexp, class_, flags=re.IGNORECASE):
                    if half_size is not None:
                        # 0, 1, 2, 3 = x, y, w, h
                        geom[3] *= 1/2
                        geom[1] += geom[3]
                    window.configure(**self.displaysize.convert_geomtry(*geom))

        for window in self.managed_windows:
            class_ = property_.get_window_class(window).lower()
            layout_window(window, class_,
                          half_size=property_.is_movie_window(window))

    # ------------------------ tile
    def _window_sort_key(self, window):
        # force Emacs be the last, movie be the first in the
        # window list
        if 'emacs' in property_.get_window_class(window).lower():
            return 0x7fffffff
        elif property_.is_movie_window(window):
            return 0x00000000
        else:
            return window.id

    def _tile_windows(self, windows, expand_disaply=False):
        windows = sorted(windows, key=self._window_sort_key)
        ncols, nrows = configure.TILE_COUNTS[len(windows)]
        for col, row in itertools.product(reversed(range(ncols)),
                                          reversed(range(nrows))):
            if not windows:
                break
            window = windows.pop(0)
            x = 1 / ncols * col
            y = 1 / nrows * row
            width = 1 / ncols
            height = 1 / nrows

            if ncols == 1 and nrows == 1:
                self.maximize_window(window)
                break
            elif not windows:
                # the last window is stretched to fill the remaining area
                rest_height = 1 / nrows * row
                y -= rest_height
                height += rest_height
            window.configure(**self.displaysize.convert_geomtry(x, y, width, height, expand_disaply))

    def tile_all_windows(self):
        if self.displaysize.exsist_expand_display:
            windows = sorted(self.managed_windows, key=self._window_sort_key)
            n_windows = int(len(windows))
            windows_on_main, windows_on_expand = windows[:(n_windows + n_windows % 2)], \
                windows[n_windows * (-1):]
            self._tile_windows(windows=windows_on_main)
            self._tile_windows(windows=windows_on_expand, expand_disaply=True)
        else:
            self._tile_windows(windows=self.managed_windows)

    # ------------------------ horizontal split windows
    def horizontal_split_windows(self, next_=True):
        self.last_index_hz += 1 if next_ else -1
        hz_combinations = list(itertools.combinations(self.managed_windows, 2))
        if self.last_index_hz >= len(hz_combinations):
            self.last_index_hz = 0
        hz_combinations[self.last_index_hz]
        windows = sorted(hz_combinations[self.last_index_hz], key=self._window_sort_key)
        self._tile_windows(windows=windows)
        self.select_window(windows[0])
