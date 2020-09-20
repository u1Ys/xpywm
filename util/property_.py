#!/usr/bin/env python3

import re
import subprocess

import Xlib

MOVIE_WINDOW_REGEXP = r'mplayer|ニコニコ動画|ニコニコ生放送|youtube|twitch|abema|openrec|prime|動画再生|(apple music)'
BROWSER_WINDOW_REGEXP = r'chromium|chrome|firefox|vivaldi'


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
    return re.search(BROWSER_WINDOW_REGEXP, get_window_class(window).lower())


def get_window_geometry(window, default=None):
    """Safe version of window.get_geometry. Return DEFAULT even if
    window.get_geometry raised error

    """
    try:
        geom = window.get_geometry()
    except (Xlib.error.BadWindow, Xlib.error.BadDrawable):
        geom = default
    return geom
