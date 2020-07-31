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

        # hold/check last command, because it seems xfixes_hide_cursor
        # instuction is stacked. (If X times execute
        # xfixes_hide_cursor, X times exexutoin of xfixes_show_cursor
        # is need to show cursor) -u1 [2019/10/28]
        self.last_show_request = None
        self.always_show_cursor = False

    def current_geometry(self):
        return {'x': self.screen.root.query_pointer().root_x,
                'y': self.screen.root.query_pointer().root_y}

    @property
    def default_geometry(self):
        return {'x': 0, 'y': 0}

    # ------------------------
    def move(self, geometry):
        current_geometry = self.current_geometry()
        self.display.warp_pointer(geometry['x'] - current_geometry['x'],
                                  geometry['y'] - current_geometry['y'])

    def move_to_window(self, window):
        try:
            geom = window.get_geometry()
        except Xlib.error.BadDrawable:
            return
        window.warp_pointer(geom.width - configure.POINTER_OFFSET, configure.POINTER_OFFSET)

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
