#!/usr/bin/env python3

import re
import subprocess
import Xlib

from . import configure

MOVIE_WINDOW_REGEXP = r'mplayer|ニコニコ動画|ニコニコ生放送|youtube|twitch|abema|openrec|prime|動画再生'
BROWSER_WINDW_REGEXP = r'chromium|chrome|firefox'

def get_window_class(window):
    """Fetch the WM_CLASS window property of the window WINDOW and return
    the class part of the property.  Return empty string if class is not
    retrieved."""
    try:
        cmd, cls = window.get_wm_class()
    # TODO: explicit exception -u1 [2020/06/20]
    except:
        return ''
    return cls if cls is not None else ''

def window_shortname(window):
    return format('0x{:x} [{}]'.format(window.id,
                                       get_window_class(window)))

def get_window_name(window):
    output = subprocess.getoutput('xwininfo -id 0x{:x}'.format(window.id))
    m = re.search(r'0x{:x} \"(.+)\"'.format(window.id), output)
    name = m.group(1) if m else ''
    return name

def is_terminal_window(window):
    """Check if the window WINDOW seems to be a terminal emulator."""
    cls = get_window_class(window)
    return 'xterm' in cls.lower()

def is_movie_window(window):
    name = get_window_name(window)
    return re.search(MOVIE_WINDOW_REGEXP, name.lower())

def is_browser_window(window):
    return re.search(BROWSER_WINDW_REGEXP, get_window_class(window).lower())

class DisplaySize():
    def __init__(self, display, screen):
        self.display = display
        self.screen = screen
        
    @property
    def exsist_expand_display(self):
        pass

    def get_screen_size(self, expand_disaply):
        resources = self.screen.root.xrandr_get_screen_resources()
        def is_connected(outputid):
            outinfo = self.display.xrandr_get_output_info(outputid, resources.timestamp)._data
            # connection: 1 -> connected, connection: 0 -> unconnected
            return not(outinfo['connection'])

        width, height = None, None
        for crtcid in reversed(resources._data['crtcs']):
            # reverse to sort as subs -> primary...
            try:
                crtcinfo = self.display.xrandr_get_crtc_info(crtcid, resources.timestamp)._data
                output = crtcinfo['outputs'][0]
            except (Xlib.error.XError, IndexError):
                # Xlib.error.XError -> output is not displayed...maybe
                # IndexError -> there is no output
                continue
            if is_connected(output):
                width, height = crtcinfo['width'], crtcinfo['height']
        return width, height

    def get_usable_screen_size(self, expand_disaply=False):
        width, height = self.get_screen_size(expand_disaply)
        width -= configure.FRAME_WIDTH * 2
        height -= configure.FRAME_WIDTH * 2 + configure.Y_OFFSET
        if expand_disaply:
            height += configure.Y_OFFSET
        return width, height

    def convert_geomtry(self, x, y, width, height, expand_disaply=False):
        screen_width, screen_height = self.get_usable_screen_size(expand_disaply)
        px, py = 0, configure.Y_OFFSET
        if expand_disaply:
            py = 0

        px += configure.FRAME_WIDTH + int(screen_width * x)
        py += configure.FRAME_WIDTH + int(screen_height * y)
        pwidth, pheight = int(screen_width * width), int(screen_height * height)
        return {'x': px, 'y': py, 'width': pwidth, 'height': pheight}
