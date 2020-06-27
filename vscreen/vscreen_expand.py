#!/usr/bin/env python3

import itertools
import re

from .vscreen import Vscreen

from .. import configure
from ..util import property_


class VscreenExpand(Vscreen):
    """Manage windows within a single vscreen (virtual screen). Here, the
extended functions using the basic functions implemented in VScreen
are implemented."""

    def __init__(self, displaysize, *args):
        super().__init__(*args)

        self.displaysize = displaysize

        self.unmaximized_window_geometries = {}
        self.last_index_hz = 0

    # ------------------------ maximize
    def maximize_window(self, window, xrandr, force_primary=False):
        """Resize the geometry of the window WINDOW to cover the screen
        horizontally and/or vertically."""
        if not self.is_managed(window):
            return
        window.configure(**xrandr.get_maximized_geometry(force_primary=force_primary))
        self.select_window(window)

    def _force_primary(self, window, xrandr):
        geom = window.get_geometry()
        return xrandr.exsist_expand_display and \
            geom.x <= xrandr.get_expand_display_x()

    def _is_maximized(self, window, xrandr):
        """Check if the window WINDOW seems to have been maximized."""
        geom = window.get_geometry()
        return {'x': geom.x, 'y': geom.y,
                'width': geom.width, 'height': geom.height} \
                == xrandr.get_maximized_geometry(force_primary=self._force_primary(window, xrandr))

    def _save_window_geometry(self, window):
        """Save the current geometry of the window WINDOW."""
        geom = window.get_geometry()
        self.unmaximized_window_geometries[window] = {'x': geom.x, 'y': geom.y,
                                                      'width': geom.width, 'height': geom.height}

    def toggle_maximize_window(self, window):
        xrandr = self.displaysize.create_xrandr_request()
        unmaximized_geometry = self.unmaximized_window_geometries.get(window, None)
        if self._is_maximized(window, xrandr) and unmaximized_geometry is not None:
            window.configure(**unmaximized_geometry)
            del self.unmaximized_window_geometries[window]
            self.select_window(window)
        else:
            self._save_window_geometry(window)
            self.maximize_window(window, xrandr, force_primary=self._force_primary(window, xrandr))

    # ------------------------ layout
    def layout_all_windows(self):
        def layout_window(window, class_, xrandr, half_size=False):
            for regexp, geom in configure.LAYOUT_RULES.items():
                geom = [*geom]
                if re.search(regexp, class_, flags=re.IGNORECASE):
                    if half_size is not None:
                        # 0, 1, 2, 3 = x, y, w, h
                        geom[3] *= 1 / 2
                        geom[1] += geom[3]
                    window.configure(**xrandr.convert_geomtry(*geom))

        xrandr = self.displaysize.create_xrandr_request()
        for window in self.managed_windows:
            class_ = property_.get_window_class(window).lower()
            layout_window(window, class_, xrandr,
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

    def _tile_windows(self, windows, xrandr, force_primary=False):
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
                self.maximize_window(window, xrandr, force_primary)
                break
            elif not windows:
                # the last window is stretched to fill the remaining area
                rest_height = 1 / nrows * row
                y -= rest_height
                height += rest_height
            window.configure(**xrandr.convert_geomtry(x, y, width, height, force_primary))

    def tile_all_windows(self, window=None):
        xrandr = self.displaysize.create_xrandr_request()
        if xrandr.exsist_expand_display:
            windows = sorted(self.managed_windows, key=self._window_sort_key)
            n_windows_half = int(len(windows) / 2)
            # assume expand display is larger than primary one
            windows_on_primary, windows_on_expand = windows[:int(n_windows_half + len(windows) % 2)], \
                windows[n_windows_half * (-1):]
            self._tile_windows(windows_on_primary, xrandr, force_primary=True)
            self._tile_windows(windows_on_expand, xrandr, force_primary=False)
        else:
            self._tile_windows(self.managed_windows, xrandr)
        if self.is_managed(window):
            self.select_window(window)

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
