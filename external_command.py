#!/usr/bin/env python3

import os
import re
import subprocess

from . import configure
from . import property_

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

def backlight_toggle(brightness_a, brightness_b):
    try:
        brightness = int(subprocess.getoutput('backlight -get'))
    except ValueError:
        return
    brightness_new = brightness_b if brightness == brightness_a \
                     else brightness_a
    os.system(f'backlight -set {brightness_new}')

# raise from: pointer.py
def enable_touchpad(bool_):
    os.system('synclient TouchpadOff={}'.format(int(not bool_)))

def screenshot(window='root'):
    os.system(f'import -window {window} /tmp/`date +%y%m%d-%H:%M:%S`.png')

# raise from: vscreen.py
def transset(window):
    if not re.search(configure.INTRANSSET_CLS, property_.get_window_class(window).lower()) \
       and not property_.is_browser_window(window):
        os.system('pidof xcompmgr && transset --id {window.id} {configure.TRANSSET_ALPHA}')
