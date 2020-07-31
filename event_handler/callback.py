#!/usr/bin/env python3

import os
import subprocess
import sys

from ..util import external_command
from ..util.log import error, debug

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
            error(self, "unable to call '%s'", entry['method'])
            return
        first_arg_window, args = entry.get('first_arg_window', False), entry.get('args', False)
        if args and type(args) is not tuple:
            # convert to tuple via list because arguments of tuple
            # must be iteratable
            args = tuple([args])
        if first_arg_window:
            window = event.child
            method(window, *args) if args \
                else method(window)
        else:
            method(*args) if args \
                else method()

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
        debug('restarting %s...', sys.argv[0])
        os.execvp(sys.argv[0], [sys.argv[0]])
