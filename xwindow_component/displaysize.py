#!/usr/bin/env python3

import logging

import Xlib

from xpywm import configure


class DisplaySize():
    '''If you want to get screen_size...
# 1. create DisplaySize instance
displaysize = DisplaySize()
# 2. create _XrandrRequest instance for each get timing
xrandr = displaysize.create_xrandr_request()
# 3. request
geom = xrandr.get_maximized_geometry()
    '''

    def __init__(self, display, screen):
        self.display = display
        self.screen = screen

        self.primary_output = self.screen.root.xrandr_get_output_primary().output
        self.last_crtcinfos = _XrandrRequest(self.display, self.screen,
                                             self.primary_output).crtcinfos

    def create_xrandr_request(self):
        # This is because the xradnr_get_* will take some time.
        logging.info('')
        resources = self.screen.root.xrandr_get_screen_resources()
        timestamp = resources.timestamp
        # To reduce the number of xrandr_get_*, when the timestamp of
        # the last information fetch is the same as the current
        # timestamp, information is not newly fetched and use the last
        # fetched information
        crtcinfos = None
        if timestamp == self.last_crtcinfos[0]['timestamp']:
            crtcinfos = self.last_crtcinfos
        xradnr = _XrandrRequest(self.display, self.screen, self.primary_output,
                                resources, crtcinfos)
        self.last_crtcinfos = xradnr.crtcinfos
        return xradnr


class _XrandrRequest():
    def __init__(self, display, screen, primary_output, resources=None, crtcinfos=None):
        self.display = display
        self.screen = screen

        self.primary_output = primary_output

        # save crtcinfos for reuse it when the connection state changes
        if crtcinfos is None:
            self.crtcinfos = self._get_crtcinfos(resources)
        else:
            self.crtcinfos = crtcinfos
        # Check the connection information every time because the
        # timestamp does not change even if the display connection is
        # changed
        connected_crtcinfos = self._get_connected(self.crtcinfos)
        self.connected_crtcinfos = self._create_crtcinfo_dict(connected_crtcinfos)

    def _create_crtcinfo_dict(self, crtcinfos):
        '''Sort crtcinfo as external -> ... -> primary'''
        crtcinfo_dict = {}
        for crtcinfo in reversed(crtcinfos):
            crtcinfo_dict[crtcinfo['outputs'][0]] = crtcinfo
        return crtcinfo_dict

    def _get_crtcinfos(self, resources=None):
        if resources is None:
            resources = self.screen.root.xrandr_get_screen_resources()
        timestamp = resources.timestamp

        def get_crtcinfo(crtcid):
            try:
                logging.info(f'crtc {crtcid} timestamp {timestamp}')
                crtcinfo = self.display.xrandr_get_crtc_info(crtcid, timestamp)._data
                return crtcinfo
            except Xlib.error.XError:  # Xlib.error.XError -> output is not displayed, maybe
                return None

        return [crtcinfo for crtcinfo in
                [get_crtcinfo(crtcid) for crtcid in resources._data['crtcs']]
                if crtcinfo is not None]

    def _get_connected(self, crtcinfos):
        def is_connected(crtcinfo):
            if crtcinfo['outputs'] == []:
                return False
            outputid, timestamp = crtcinfo['outputs'][0], crtcinfo['timestamp']
            logging.info(f'xrandr_get_output_info output {outputid} timestamp {timestamp}')
            outinfo = self.display.xrandr_get_output_info(outputid, timestamp)._data
            # connection: 0 -> connected, connection: 1 -> unconnected
            return outinfo['connection'] == 0

        return [crtcinfo for crtcinfo in crtcinfos if is_connected(crtcinfo)]

    @property
    def exist_expand_display(self):
        return any((crtcinfo['x'] != 0
                    for crtcinfo in self.connected_crtcinfos.values()))

    @property
    def outputs(self):
        return self.connected_crtcinfos.keys()

    @property
    def default_output(self):
        return list(self.outputs)[0]

    def get_maximized_geometry(self, output=None, window=None):
        output = self._specify_output(output, window)

        crtcinfo = self.connected_crtcinfos[output]
        exist_xpymon = not self.exist_expand_display \
            or output == self.primary_output

        x = crtcinfo['x']
        y = configure.Y_OFFSET if exist_xpymon else 0

        width, height = crtcinfo['width'], crtcinfo['height']

        return {'x': x, 'y': y, 'width': width, 'height': height - y}

    def _specify_output(self, output, window):
        if output is not None:
            return output
        elif window is not None:
            return self._where_output_is_window(window)
        return self.default_output

    def _where_output_is_window(self, window):
        try:
            x = window.get_geometry().x
        except (Xlib.error.BadWindow, Xlib.error.BadDrawable):
            # MEMO: no particular reason for this value
            x = 0
        for output, crtcinfo in self.connected_crtcinfos.items():
            if crtcinfo['x'] <= x and x <= crtcinfo['x'] + crtcinfo['width']:
                return output

    def _get_usable_geometry(self, output):
        x, y, width, height = self.get_maximized_geometry(output).values()
        width -= configure.FRAME_WIDTH * 2
        height -= configure.FRAME_WIDTH * 2
        return x, y, width, height

    def convert_geomtry(self, px, py, pwidth, pheight,
                        output=None, window=None):
        output = self._specify_output(output, window)

        x, y, width, height = self._get_usable_geometry(output)
        x += configure.FRAME_WIDTH + int(width * px)
        y += configure.FRAME_WIDTH + int(height * py)
        width, height = int(width * pwidth), int(height * pheight)
        return {'x': x, 'y': y, 'width': width, 'height': height}
