#!/usr/bin/env python3

import os
import logging
import subprocess
import sys

from xpywm.util import external_command


class Callback():
    def __init__(self, vscreen_manager):
        self.vscreen_manager = vscreen_manager

    def call(self, event, entry):
        if 'os_command' in entry:
            os.system(entry['os_command'] + ' &')
        else:
            self.call_method(event, entry)

    def call_method(self, event, entry):
        object_ = {
            'vscreen_manager': self.vscreen_manager,
            'vscreen': self.vscreen_manager.current_vscreen,
            'callback': self,
            'pointer': self.vscreen_manager.pointer,
            'external_command': external_command,
        }[entry['type']]
        method = getattr(object_, entry['method'], None)
        if not method:
            logging.error("unable to call '%s'", entry['method'])
            return

        args = entry.get('args', ())
        if type(args) is not tuple:
            # convert to tuple via list because arguments of tuple
            # must be iteratable
            args = tuple([args])

        if entry.get('first_arg_window', False):
            window = event.child
            method(window, *args)
        else:
            method(*args)

    # ------------------------
    def raise_emacs(self):
        if subprocess.getoutput('pidof emacs'):
            self.vscreen_manager.pull_class_window('emacs')
        else:
            os.system('emacs &')

    def cb_screenshot(self, window):
        try:
            external_command.screenshot(window.id)
        except AttributeError:
            pass

    def restart(self):
        self.vscreen_manager.all_window_move_init_vscreen()
        logging.info('restarting %s...', sys.argv[0])
        os.execvp(sys.argv[0], [sys.argv[0]])
