#!/usr/bin/env python3

import itertools
import re

from Xlib import X

from xpywm import configure
from xpywm.vscreen.vscreen import VScreen
from xpywm.util import window_property


class VScreenExapndBase(VScreen):
    def __init__(self, displaysize, *args):
        super().__init__(*args)

        self.displaysize = displaysize

    @staticmethod
    def select_window_at_last(method):
        '''Decorator to execute the METHOD and select the window after
        executing the METHOD.

        '''
        def wrapper(self, window, *args, **kargs):
            method(self, window, *args, **kargs)
            self.select_window(window)
        return wrapper


class MaximizeWindow(VScreenExapndBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.unmaximized_window_geometries = {}

    @VScreen.execute_when_window_is_managed
    def maximize_window(self, window, xrandr, output=None):
        '''Resize the geometry of the window WINDOW to cover the screen
        horizontally and/or vertically.'''
        _specify_window = window if output is None else None
        window.configure(**xrandr.get_maximized_geometry(window=_specify_window,
                                                         output=output))

    def _is_maximized(self, window, geom, xrandr):
        '''Check if the window WINDOW seems to have been maximized.'''
        return {'x': geom.x, 'y': geom.y, 'width': geom.width, 'height': geom.height} \
            == xrandr.get_maximized_geometry(window=window)

    def _save_window_geometry(self, window, geom):
        '''Save the current geometry of the window WINDOW.'''
        self.unmaximized_window_geometries[window] = {'x': geom.x, 'y': geom.y,
                                                      'width': geom.width, 'height': geom.height}

    @VScreen.execute_when_window_is_managed
    @window_property.return_with_get_geometry_exception
    @VScreenExapndBase.select_window_at_last
    def toggle_maximize_window(self, window):
        geom = window.get_geometry()
        xrandr = self.displaysize.create_xrandr_request()
        unmaximized_geometry = self.unmaximized_window_geometries.get(window, None)
        if self._is_maximized(window, geom, xrandr) and unmaximized_geometry is not None:
            window.configure(**unmaximized_geometry)
            del self.unmaximized_window_geometries[window]
        else:
            self._save_window_geometry(window, geom)
            self.maximize_window(window, xrandr)


class LayoutWindow(VScreenExapndBase):
    @VScreenExapndBase.select_window_at_last
    def layout_all_windows(self, selected_window):
        '''NOTICE: selected_window argument is used in decorator'''
        def layout_window(window, xrandr):
            for regexp, geom in configure.LAYOUT_RULES.items():
                geom = [*geom]
                if re.search(regexp, window_property.get_window_class(window).lower(),
                             flags=re.IGNORECASE):
                    window.configure(**xrandr.convert_geomtry(*geom))

        xrandr = self.displaysize.create_xrandr_request()
        for window in self.managed_windows:
            layout_window(window, xrandr)


class TileWindow(MaximizeWindow):
    def _window_sort_key(self, window):
        # force Emacs be the last, movie be the first in the
        # window list
        if 'emacs' in window_property.get_window_class(window).lower():
            return 0x7fffffff
        elif window_property.is_movie_window(window):
            return 0x00000000
        else:
            return window.id

    def _tile_windows(self, windows, xrandr, output=None):
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
                self.maximize_window(window, xrandr, output=output)
                break
            elif not windows:
                # the last window is stretched to fill the remaining area
                rest_height = 1 / nrows * row
                y -= rest_height
                height += rest_height
            window.configure(**xrandr.convert_geomtry(x, y, width, height, output=output))

    @VScreenExapndBase.select_window_at_last
    def tile_all_windows(self, selected_window):
        '''NOTICE: selected_window argument is used in decorator'''
        xrandr = self.displaysize.create_xrandr_request()
        if xrandr.exist_expand_display:
            windows = sorted(self.managed_windows, key=self._window_sort_key,
                             reverse=True)

            outputs = xrandr.outputs
            # divide as equally as possible
            split_window_counts = ((len(windows) + i) // len(outputs)
                                   for i in range(len(outputs)))

            last_windows = windows
            for output, window_count in zip(outputs, split_window_counts):
                self._tile_windows(last_windows[:window_count], xrandr, output=output)
                last_windows = last_windows[window_count:]
        else:
            self._tile_windows(self.managed_windows, xrandr)


class HorizontalSplitWindow(VScreenExapndBase):
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


class PictureInPicture(VScreenExapndBase):
    PWIDTH = .25
    PHEIGHT = .25

    def __init__(self, *args):
        super().__init__(*args)

        # pip = PictureInPicture
        self.pip_window = None
        self.pip_window_geometry = None

    # ------------------------
    def open(self):
        super().open()
        if self.pip_window is not None:
            self.pip_window.map()

    def close(self):
        super().close()
        if self.pip_window is not None:
            self.pip_window.unmap()

    # ------------------------
    def manage_window(self, window):
        if window == self.pip_window:
            return
        return super().manage_window(window)

    def select_window(self, window):
        super().select_window(window)
        if self.pip_window is not None:
            self.pip_window.configure(stack_mode=X.Above)

    # ------------------------
    @window_property.return_with_get_geometry_exception
    def manage_pip_window(self, window):
        geom = window.get_geometry()

        self.pip_window = window
        self.pip_window_geometry = {'x': geom.x, 'y': geom.y,
                                    'width': geom.width, 'height': geom.height}

        self.unmanage_window(window)
        xrandr = self.displaysize.create_xrandr_request()
        window.configure(**xrandr.convert_geomtry(px=(1 - PictureInPicture.PWIDTH),
                                                  py=(1 - PictureInPicture.PHEIGHT),
                                                  pwidth=PictureInPicture.PWIDTH,
                                                  pheight=PictureInPicture.PHEIGHT,
                                                  window=window),
                         stack_mode=X.Above)

    def unmanage_pip_window(self):
        pip_window, pip_window_geometry = self.pip_window, self.pip_window_geometry
        self.pip_window, self.pip_window_geometry = None, None

        success_manage_window = self.manage_window(pip_window)
        if success_manage_window:
            pip_window.configure(**pip_window_geometry)
            self.select_window(pip_window)

    def toggle_pip_window(self, window=None):
        if self.pip_window is None:
            if self.pip_window is not None:
                return
            self.manage_pip_window(window)
        else:
            self.unmanage_pip_window()


class VScreenExpand(HorizontalSplitWindow,
                    TileWindow,
                    LayoutWindow,
                    MaximizeWindow,
                    PictureInPicture):
    pass
