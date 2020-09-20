#!/usr/bin/env python3

import re

import Xlib

from .. import configure
from ..util import external_command
from ..util import property_


class Pointer():
    def __init__(self, display, screen):
        self.display = display
        self.screen = screen

        self.geometries = {}
        self.last_geometry = None

        # hold/check last command, because it seems xfixes_hide_cursor
        # instuction is stacked. (If X times execute
        # xfixes_hide_cursor, X times exexutoin of xfixes_show_cursor
        # is need to show cursor) -u1 [2019/10/28]
        self.last_show_request = None
        self.always_show_cursor = False

    @property
    def current_geometry(self):
        return {'x': self.screen.root.query_pointer().root_x,
                'y': self.screen.root.query_pointer().root_y}

    @property
    def default_geometry(self):
        return {'x': 0, 'y': 0}

    # ------------------------
    def move(self, geometry):
        """Move pointer to absoulute GEOMETRY"""
        current_geometry = self.current_geometry
        self.display.warp_pointer(geometry['x'] - current_geometry['x'],
                                  geometry['y'] - current_geometry['y'])

    def move_to(self, window):
        def shift(pval):
            return {
                0: configure.POINTER_OFFSET,
                1: -1 * configure.POINTER_OFFSET,
            }.get(pval, 0)

        geom = property_.get_window_geometry(window)
        if geom is None:
            return
        p_geom = self.geometries.get(window, configure.DEFAULT_POINTER_GEOMETRY)
        # MEMO: window.warp_pointer()
        self.move({
            'x': geom.x + int(geom.width * p_geom['x']) + shift(p_geom['x']),
            'y': geom.y + int(geom.height * p_geom['y']) + shift(p_geom['y']),
        })

    def save_temporary_geometry(self):
        self.last_geometry = self.current_geometry

    def pop_temporary_geometry(self):
        last_geometry = self.last_geometry
        self.last_geometry = None
        return last_geometry

    def save_geometry_at(self, window, geom_abs):
        """Save the relative geometry of the pointer in the window. Because
        the window size changes often, save the *relative* position of
        the pointer, not the absolute position. If the pointer is
        outside the window frame, it is considered invalid and is not
        saved.

        """
        def is_bound(lower, value, upper):
            return lower <= value and value <= upper

        geom = property_.get_window_geometry(window)
        if geom is None or geom_abs is None:
            return
        x_in_window, y_in_window = geom_abs['x'] - geom.x, geom_abs['y'] - geom.y
        p_x, p_y = x_in_window / geom.width, y_in_window / geom.height
        if any(map(lambda p: not is_bound(0, p, 1), [p_x, p_y])):
            return
        self.geometries[window] = {'x': p_x, 'y': p_y}

    def remove_geometry_of(self, window):
        if window in self.geometries:
            del self.geometries[window]

    # ------------------------
    def show_cursor(self, request):
        show = self.always_show_cursor or request
        if self.last_show_request == show:
            return
        self.display.xfixes_query_version()
        if show:
            self.screen.root.xfixes_show_cursor()
        else:
            self.screen.root.xfixes_hide_cursor()
        self.display.flush()
        self.last_show_request = show

    def toggle_always_show_cursor(self):
        self.always_show_cursor = not self.always_show_cursor
        self.show_cursor(self.always_show_cursor)

    def cursor_set(self, window):
        m = re.search(configure.STOP_CURSOR_CLS,
                      property_.get_window_class(window).lower())
        external_command.enable_touchpad(not m)
        self.show_cursor(not m)
