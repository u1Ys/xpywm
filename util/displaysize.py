#!/usr/bin/env python3

import Xlib

from .. import configure
from .log import debug


class DisplaySize():
    def __init__(self, display, screen):
        self.display = display
        self.screen = screen

        self.last_crtcinfos = FetchXRandr(self.display, self.screen).connected_crtcinfos

    def create_xrandr_request(self):
        debug(self, 'create_xrandr_request')
        # This is because the xradnr_get_* will take some time.
        resources = self.screen.root.xrandr_get_screen_resources()
        timestamp = resources.timestamp
        crtcinfos = None
        # To reduce the number of xrandr_get_*, when the timestamp of
        # the last information fetch is the same as the current
        # timestamp, information is not newly fetched and use the last
        # fetched information
        if timestamp == self.last_crtcinfos[0]['timestamp']:
            crtcinfos = self.last_crtcinfos
        xradnr = FetchXRandr(self.display, self.screen, resources, crtcinfos)
        self.last_crtcinfos = xradnr.crtcinfos
        return xradnr


class FetchXRandr():
    def __init__(self, display, screen, resources=None, crtcinfos=None):
        self.display = display
        self.screen = screen

        if crtcinfos is None:
            self.crtcinfos = self._get_crtcinfos(resources)
        else:
            debug(self, 'skip get*')
            self.crtcinfos = crtcinfos
            pass
        self.connected_crtcinfos = self._get_connected(self.crtcinfos)

    def _get_crtcinfos(self, resources=None):
        if resources is None:
            resources = self.screen.root.xrandr_get_screen_resources()
        timestamp = resources.timestamp

        def get_crtcinfo(crtcid):
            try:
                debug(self, f'xrandr_get_crtc_info {crtcid} {timestamp}')
                crtcinfo = self.display.xrandr_get_crtc_info(crtcid, timestamp)._data
                return crtcinfo
            except Xlib.error.XError:
                # Xlib.error.XError -> output is not displayed, maybe
                return None

        crtcinfos = []
        for crtcid in resources._data['crtcs']:
            crtcinfo = get_crtcinfo(crtcid)
            if crtcinfo is None:
                continue
            crtcinfos.append(crtcinfo)
        return crtcinfos

    def _get_connected(self, crtcinfos):
        def is_connected(crtcinfo):
            if crtcinfo['outputs'] == []:
                return False
            outputid, timestamp = crtcinfo['outputs'][0], crtcinfo['timestamp']
            debug(self, f'xrandr_get_output_info {outputid} {timestamp}')
            outinfo = self.display.xrandr_get_output_info(outputid, timestamp)._data
            # connection: 1 -> connected, connection: 0 -> unconnected
            return not(outinfo['connection'])

        return [crtcinfo for crtcinfo in crtcinfos if is_connected(crtcinfo)]

    def get_expand_display_x(self):
        return max([crtcinfo['x'] for crtcinfo in self.connected_crtcinfos])

    @property
    def exsist_expand_display(self):
        return not self.get_expand_display_x() == 0

    def get_screen_size(self, force_primary=False):
        for crtcinfo in self.connected_crtcinfos:
            width, height = crtcinfo['width'], crtcinfo['height']
            # crtcinfos is sorted as external -> ... -> primary
            if force_primary:
                return width, height
        return width, height

    def get_screen_xy(self, exsist_xpymon=True):
        # exsist_xpymon: false = expand-display
        x = 0 if exsist_xpymon else self.get_expand_display_x()
        y = configure.Y_OFFSET if exsist_xpymon else 0
        return x, y

    def get_maximized_geometry(self, force_primary=False):
        exsist_xpymon = force_primary or not self.exsist_expand_display
        x, y = self.get_screen_xy(exsist_xpymon)
        width, height = self.get_screen_size(force_primary)
        return {'x': x, 'y': y, 'width': width, 'height': height}

    def get_usable_geometry(self, force_primary=False):
        x, y, width, height = self.get_maximized_geometry(force_primary).values()
        width -= configure.FRAME_WIDTH * 2
        height -= configure.FRAME_WIDTH * 2 + y
        return x, y, width, height

    def convert_geomtry(self, px, py, pwidth, pheight, force_primary=False):
        x, y, width, height = self.get_usable_geometry(force_primary)
        x += configure.FRAME_WIDTH + int(width * px)
        y += configure.FRAME_WIDTH + int(height * py)
        width, height = int(width * pwidth), int(height * pheight)
        return {'x': x, 'y': y, 'width': width, 'height': height}