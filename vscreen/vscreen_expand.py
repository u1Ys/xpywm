#!/usr/bin/env python3

import itertools
import re

from .vscreen import Vscreen

from .. import configure
from ..util import property_


class VscreenExapndBase(Vscreen):
    def __init__(self, displaysize, *args):
        super().__init__(*args)

        self.displaysize = displaysize

    def exec_method_with_hook(self, method, window, method_args=[]):
        """Execute the METHOD and hooks before and after executing the
        METHOD. It is not mandatory to use this method for the
        callback method.

        """
        method(*method_args)
        # after changing the layout, select the window selected before
        # changing the layout
        if self.is_managed(window):
            self.select_window(window)


class MaximizeWindow(VscreenExapndBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.unmaximized_window_geometries = {}

    def maximize_window(self, window, xrandr, force_primary=False):
        """Resize the geometry of the window WINDOW to cover the screen
        horizontally and/or vertically."""
        if not self.is_managed(window):
            return
        window.configure(**xrandr.get_maximized_geometry(force_primary=force_primary))

    def _is_force_primary(self, window, geom, xrandr):
        return xrandr.exsist_expand_display and \
            geom.x <= xrandr.get_expand_display_x()

    def _is_maximized(self, window, geom, xrandr):
        """Check if the window WINDOW seems to have been maximized."""
        return {'x': geom.x, 'y': geom.y, 'width': geom.width, 'height': geom.height} \
            == xrandr.get_maximized_geometry(force_primary=self._is_force_primary(window, geom, xrandr))

    def _save_window_geometry(self, window, geom):
        """Save the current geometry of the window WINDOW."""
        self.unmaximized_window_geometries[window] = {'x': geom.x, 'y': geom.y,
                                                      'width': geom.width, 'height': geom.height}

    def _toggle_maximize_window(self, window):
        geom = property_.get_window_geometry(window)
        if geom is None:
            return
        xrandr = self.displaysize.create_xrandr_request()
        unmaximized_geometry = self.unmaximized_window_geometries.get(window, None)
        if self._is_maximized(window, geom, xrandr) and unmaximized_geometry is not None:
            window.configure(**unmaximized_geometry)
            del self.unmaximized_window_geometries[window]
        else:
            self._save_window_geometry(window, geom)
            self.maximize_window(window, xrandr, force_primary=self._is_force_primary(window, geom, xrandr))

    def toggle_maximize_window(self, window):
        self.exec_method_with_hook(self._toggle_maximize_window, window,
                                   method_args=[window])


class LayoutWindow(VscreenExapndBase):
    def _layout_all_windows(self):
        def layout_window(window, xrandr, half_size_windows=[]):
            for regexp, geom in configure.LAYOUT_RULES.items():
                geom = [*geom]
                if re.search(regexp, property_.get_window_class(window).lower(),
                             flags=re.IGNORECASE):
                    if window in half_size_windows:
                        i = half_size_windows.index(window)
                        # 0, 1, 2, 3 = x, y, w, h
                        geom[3] *= 1 / 2
                        # switch window position between upper and lower half
                        geom[1] += (i + 1) % 2 * geom[3]
                    window.configure(**xrandr.convert_geomtry(*geom))

        xrandr = self.displaysize.create_xrandr_request()
        half_size_windows = [window for window in self.managed_windows
                             if property_.is_browser_window(window)]
        if len(half_size_windows) <= 1:
            half_size_windows = []
        for window in self.managed_windows:
            layout_window(window, xrandr, half_size_windows=half_size_windows)

    def layout_all_windows(self, window=None):
        self.exec_method_with_hook(self._layout_all_windows, window)


class TileWindow(MaximizeWindow):
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

    def _tile_all_windows(self):
        xrandr = self.displaysize.create_xrandr_request()
        if xrandr.exsist_expand_display:
            windows = sorted(self.managed_windows, key=self._window_sort_key)
            n_windows_on_primary = int((len(windows) + 1) / 2)
            # assume expand display is larger than primary one
            windows_on_primary, windows_on_expand = windows[:n_windows_on_primary], windows[n_windows_on_primary:]
            self._tile_windows(windows_on_primary, xrandr, force_primary=True)
            self._tile_windows(windows_on_expand, xrandr, force_primary=False)
        else:
            self._tile_windows(self.managed_windows, xrandr)

    def tile_all_windows(self, window=None):
        self.exec_method_with_hook(self._tile_all_windows, window)


class HorizontalSplitWindow(VscreenExapndBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.last_index_hz = 0

    def horizontal_split_windows(self):
        hz_combinations = list(itertools.combinations(self.managed_windows.sorted(), 2))
        self.last_index_hz += 1
        if self.last_index_hz >= len(hz_combinations):
            self.last_index_hz = 0
        windows = hz_combinations[self.last_index_hz]
        self._tile_windows(windows=windows,
                           xrandr=self.displaysize.create_xrandr_request())
        # trick to use `select_last_window` between `windows`
        # move the current window to last of managed_windows
        self.managed_windows.move_to_end(windows[1])
        self.select_window(windows[0])
        [window.raise_window() for window in windows]


class VscreenExpand(HorizontalSplitWindow,
                    TileWindow,
                    LayoutWindow,
                    MaximizeWindow):
    pass
