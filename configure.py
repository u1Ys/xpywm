#!/usr/bin/env python3

import os

from Xlib import X

# ------------------------ default configure
MAX_VSCREEN = 2
FRAME_WIDTH = 2
FRAME_COLOR = os.environ.get('THEME_COLOR', 'aquamarine1')
Y_OFFSET = 8

VSCREEN_FILE = '/tmp/wm_vscreen_num'

TRANSSET_ALPHA = '.85'
INTRANSSET_CLS = r'emacs|mupdf|mplayer|code'

POINTER_OFFSET = 16
DEFAULT_POINTER_GEOMETRY = {'x': 1, 'y': 0}
STOP_CURSOR_CLS = r'rxvt|emacs'

LAYOUT_RULES = {
    r'xterm|rxvt': [.5, .3, 1 - .5, .7],
    r'code|emacs': [0, 0, .5, 1],
    r'firefox|iceweasel|chrom(e|ium)|midori|vivaldi':
    [.5, 0, .5, 1],
    r'(open|libre)office|acroread|xpdf|evince|mupdf|xdvi|tgif|xmathematical|gv|teams':
    [.5, 0, .5, 1],
}

TILE_COUNTS = {
    0: [0, 0],
    1: [1, 1],
    2: [2, 1],
    3: [2, 2],
    4: [2, 2],
    5: [3, 2],
    6: [3, 2],
    7: [3, 3],
    8: [3, 3],
    9: [3, 3],
    10: [4, 3],
    11: [4, 3],
    12: [4, 3],
    13: [4, 4],
    14: [4, 4],
    15: [4, 4],
    16: [4, 4],
    17: [5, 4],
    18: [5, 4],
    19: [5, 4],
    20: [5, 4],
    21: [5, 5],
    22: [5, 5],
    23: [5, 5],
    24: [5, 5],
    25: [5, 5],
    26: [6, 5],
    27: [6, 5],
    28: [6, 5],
    29: [6, 5],
    30: [6, 5],
}

KEY_HANDLER = {
    # for debugging
    'Delete': {'modifier': X.Mod1Mask | X.ControlMask,
               'type': 'callback',
               'method': 'restart'},
    # window move
    'i': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'vscreen',
          'method': 'select_other_window',
          'first_arg_window': True},
    'o': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'vscreen',
          'method': 'select_other_window',
          'first_arg_window': True, 'args': True},
    'u': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'vscreen',
          'method': 'select_last_window',
          'first_arg_window': True},
    'z': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'vscreen',
          'method': 'destroy_window',
          'first_arg_window': True},
    # window transformation
    'apostrophe': {'modifier': X.Mod1Mask | X.ControlMask, 'callback': True,
                   'type': 'vscreen',
                   'method': 'toggle_maximize_window',
                   'first_arg_window': True},
    # window layouting
    'comma': {'modifier': X.Mod1Mask | X.ControlMask,
              'type': 'vscreen',
              'method': 'layout_all_windows',
              'first_arg_window': True},
    'period': {'modifier': X.Mod1Mask | X.ControlMask,
               'type': 'vscreen',
               'method': 'tile_all_windows',
               'first_arg_window': True},
    'm': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'vscreen',
          'method': 'horizontal_split_windows'},
    'bar': {'modifier': X.Mod1Mask | X.ControlMask,
            'type': 'vscreen',
            'method': 'toggle_pip_window',
            'first_arg_window': True},
    # vsceen manage
    'x': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'vscreen_manager',
          'method': 'select_last_vscreen'},
    'w': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'vscreen_manager',
          'method': 'toggle_window_vscreen',
          'first_arg_window': True},
    't': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'vscreen_manager',
          'method': 'all_window_move_init_vscreen'},
    # pointer
    'f': {'modifier': X.Mod1Mask | X.ControlMask, 'callback': True,
          'type': 'pointer',
          'method': 'toggle_always_show_cursor'},
    # os-command - x-application
    '1': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'callback',
          'method': 'raise_emacs'},
    '2': {'modifier': X.Mod1Mask | X.ControlMask,
          'os_command': '(unset STY; rxvt-unicode)'},
    '3': {'modifier': X.Mod1Mask | X.ControlMask,
          'os_command': 'google-chrome'},
    '9': {'modifier': X.Mod1Mask | X.ControlMask,
          'os_command': 'xfsearch'},
    '0': {'modifier': X.Mod1Mask | X.ControlMask,
          'os_command': '{}/bin/init/recall-xutils'.format(os.getenv('HOME', ''))},
    # os-command - screenshot
    'F5': {'modifier': X.ShiftMask,
           'os_command': 'pyscreenshot'},
    'F6': {'modifier': X.ShiftMask,
           'os_command': 'xrandr-auto --mode 800x600'},
    'F7': {'modifier': X.ShiftMask,
           'os_command': 'xrandr-auto _max'},
    'F8': {'modifier': X.ShiftMask,
           'os_command': 'xrandr-auto _max --left-of _primary'},
    'XF86Display': {'modifier': X.NONE,
                    'os_command': 'xrandr-toggle'},
    # os-command - music player
    'F9': {'modifier': X.ShiftMask,
           'os_command': 'control-mplayer pause'},
    'F10': {'modifier': X.ShiftMask,
            'os_command': 'control-mplayer pt_step -1'},
    'F11': {'modifier': X.ShiftMask,
            'os_command': 'control-mplayer pt_step  1'},
    'F12': {'modifier': X.ShiftMask,
            'os_command': 'pidof mplayer && control-mplayer quit || play-music -ar'},
    'Left': {'modifier': X.Mod1Mask | X.ControlMask,
             'os_command': 'pidof mplayer && control-mplayer seek -30'},
    'Right': {'modifier': X.Mod1Mask | X.ControlMask,
              'os_command': 'pidof mplayer && control-mplayer seek 30'},
    # os-command - network
    'XF86WLAN': {'modifier': X.NONE,
                 'os_command': 'pidof wpa_supplicant && sudo wi_cli stop || sudo wi_cli start'},
    'XF86Tools': {'modifier': X.NONE,
                  'os_command': 'sudo wi_cli reconf-ip'},
    # os-command - sound
    'XF86AudioRaiseVolume': {'modifier': X.NONE,
                             'type': 'external_command',
                             'method': 'audio_raise_volume'},
    'XF86AudioLowerVolume': {'modifier': X.NONE,
                             'type': 'external_command',
                             'method': 'audio_lower_volume'},
    'XF86AudioMute': {'modifier': X.NONE,
                      'os_command': 'audio-toggle-mute'},
    # os-command - backlight
    'XF86MonBrightnessUp': {'modifier': X.NONE,
                            'os_command': 'backlight -inc 10'},
    'XF86MonBrightnessDown': {'modifier': X.NONE,
                              'os_command': 'backlight -dec 10'},
    'a': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'external_command',
          'method': 'backlight_toggle',
          'args': (40, 100)},
    's': {'modifier': X.Mod1Mask | X.ControlMask,
          'type': 'external_command',
          'method': 'backlight_toggle',
          'args': (1, 0)},
    # os-command - other
    'XF86AudioMicMute': {'modifier': X.NONE,
                         'os_command': 'xtrlock -b'},
}

KEY_HANDLER['d'] = KEY_HANDLER['i']


LOG_FILE = '/var/tmp/xpywm.log'
