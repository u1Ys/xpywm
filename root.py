#!/usr/bin/env python3

from Xlib import display

from .event_handler.event_handler import EventHandler
from .vscreen.vscreen_manager import VScreenManager
from .xwindow_component.frame_window import FrameWindow
from .xwindow_component.pointer import Pointer
from .xwindow_component.displaysize import DisplaySize


class WindowManager():
    """The *root* of all modules. Bridging objects between classes of
    different elements.

    """

    def __init__(self):
        self.display = display.Display()
        self.screen = self.display.screen()

        self.pointer = Pointer(self.display, self.screen)
        self.frame_window = FrameWindow(self.screen)
        self.vscreen_manager = VScreenManager(self.pointer,
                                              self.frame_window,
                                              DisplaySize(self.display, self.screen))

        self.event_handler = EventHandler(self.display, self.screen, self.vscreen_manager)

        self._manage_exsist_windows()

        # create frame windows here because frame windows is managed
        # if create them before _manage_exsist_windows()
        self.frame_window.create_frame_windows()
        # choose first window
        self.vscreen_manager.current_vscreen.select_other_window()

    def _manage_exsist_windows(self):
        # manage exsist windows
        for child in self.screen.root.query_tree().children:
            if child.get_attributes().map_state:
                self.vscreen_manager.current_vscreen.manage_window(child)

    def start(self):
        self.event_handler.event_loop()
