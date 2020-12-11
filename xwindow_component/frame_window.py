#!/usr/bin/env python3

from Xlib import X

from xpywm import configure
from xpywm.util import window_property


class FrameWindow():
    def __init__(self, screen):
        self.screen = screen
        self.frame_windows = {}
        self.framed_window = None

    def create_frame_windows(self):
        """Create and map a window frame consisting of four windows."""
        colormap = self.screen.default_colormap
        # create four frame windows
        pixel = colormap.alloc_named_color(configure.FRAME_COLOR).pixel
        for side in ['frame_l', 'frame_r', 'frame_u', 'frame_d']:
            window = self.screen.root.create_window(
                0,
                0,
                16,
                16,
                0,
                self.screen.root_depth,
                X.InputOutput,
                background_pixel=pixel,
                override_redirect=1,
            )
            window.map()
            self.frame_windows[side] = window

    @window_property.return_with_get_geometry_exception
    def draw_frame_windows(self, framed_window):
        """Draw a frame window surrounding a windwow WINDOW."""
        geom = framed_window.get_geometry()
        self.framed_window = framed_window

        for side in ['frame_l', 'frame_r', 'frame_u', 'frame_d']:
            x, y, width, height = 0, 0, 0, 0
            if side == 'frame_l':
                x = geom.x - configure.FRAME_WIDTH
                y = geom.y
                width = configure.FRAME_WIDTH
                height = geom.height
            elif side == 'frame_r':
                x = geom.x + geom.width
                y = geom.y
                width = configure.FRAME_WIDTH
                height = geom.height
            elif side == 'frame_u':
                x = geom.x - configure.FRAME_WIDTH
                y = geom.y - configure.FRAME_WIDTH
                width = geom.width + 2 * configure.FRAME_WIDTH
                height = configure.FRAME_WIDTH
            elif side == 'frame_d':
                x = geom.x - configure.FRAME_WIDTH
                y = geom.y + geom.height
                width = geom.width + 2 * configure.FRAME_WIDTH
                height = configure.FRAME_WIDTH

            window = self.frame_windows[side]
            window.configure(x=x, y=y, width=width, height=height)

            # NOTE: might be redundant
            window.map()
            window.raise_window()

    def clear_frame_window(self, window):
        if self.framed_window == window:
            for side in ['frame_l', 'frame_r', 'frame_u', 'frame_d']:
                win = self.frame_windows[side]
                win.unmap()
