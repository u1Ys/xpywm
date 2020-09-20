#!/usr/bin/env python3

import os
import re
import subprocess

from .. import configure
from . import window_property

STOP_CURSOR_CLS = r'rxvt|emacs'


def get_mixer_level():
    """Return the master playback volume of the default ALSA audio device.
    Volume ranges between 0 and 100."""
    output = subprocess.getoutput('amixer get Master')
    m = re.search(r'Playback.*\[(\d+)%\]', output)
    if m:
        level = int(m.group(1))
        return level
    else:
        return None


def set_mixer_level(level):
    subprocess.getoutput('amixer set Master {}%'.format(level))


def audio_raise_volume(delta=5):
    level = get_mixer_level()
    if level is not None:
        level = max(0, min(level + delta, 100))
        set_mixer_level(level)


def audio_lower_volume(delta=5):
    audio_raise_volume(-delta)


def backlight_toggle(brightness, brightness_other):
    print(brightness, brightness_other)
    try:
        if int(subprocess.getoutput('backlight -get')) == brightness:
            brightness = brightness_other
        os.system(f'backlight -set {brightness}')
    except ValueError:
        return


# raise from: pointer.py
def enable_touchpad(bool_):
    os.system('synclient TouchpadOff={}'.format(int(not bool_)))


def screenshot(window='root'):
    os.system(f'import -window {window} /tmp/`date +%y%m%d-%H:%M:%S`.png')


# raise from: vscreen.py
def transset(window):
    if re.search(configure.INTRANSSET_CLS, window_property.get_window_class(window).lower()) \
       or window_property.is_browser_window(window):
        return
    os.system(f'pidof xcompmgr && transset --id {window.id} {configure.TRANSSET_ALPHA}')
