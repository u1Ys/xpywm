#!/usr/bin/env python3

from Xlib import X, XK

from . import keysyms
from . import callback
from .. import configure
from ..util.log import debug

EVENT_HANDLER = {
    X.KeyPress: 'handle_keypress',
    X.ButtonPress: 'handle_button_press',
    X.MotionNotify: 'handle_motion_notify',
    X.ButtonRelease: 'handle_button_release',
    X.MapRequest: 'handle_map_request',
    X.ConfigureRequest: 'handle_configure_request',
    X.UnmapNotify: 'handle_unmap_notify',
    X.EnterNotify: 'handle_enter_notify',
    X.LeaveNotify: 'handle_leave_notify',
    X.DestroyNotify: 'handle_destroy_notify',
    X.MapNotify: 'handle_map_notify',
}

DRAG_THRESH = 16
MIN_WIN_SIZE = 16
BOUNCE_RATIO = 1 / 8


class EventHandler():
    def __init__(self, display, screen, vscreen_manager):
        self.vscreen_manager = vscreen_manager
        self.display = display
        self.screen = screen
        self.callback = callback.Callback(vscreen_manager)

        self.key_handlers = {}

        self.drag_window = None
        self.drag_button = None
        self.drag_geometry = None
        self.drag_start_xy = None
        self.drag_last_xy = None

        self.catch_events()
        self.grab_keys()
        self.grab_buttons()

    def catch_events(self):
        """Configure the root window to receive all events needed for managing
        windows."""
        mask = (X.SubstructureRedirectMask | X.SubstructureNotifyMask
                | X.EnterWindowMask | X.LeaveWindowMask | X.FocusChangeMask)
        self.screen.root.change_attributes(event_mask=mask)

    def grab_keys(self):
        for string, entry in configure.KEY_HANDLER.items():
            keysym = XK.string_to_keysym(string)
            # FIXME: use keysymdef/xf86.py
            if not keysym and string in keysyms.KEYSYM_TBL:
                keysym = keysyms.KEYSYM_TBL[string]
            keycode = self.display.keysym_to_keycode(keysym)
            if not keycode:
                continue

            modifier = entry.get('modifier', X.NONE)
            self.screen.root.grab_key(keycode, modifier, True, X.GrabModeAsync,
                                      X.GrabModeAsync)
            self.key_handlers[keycode] = entry

    def grab_buttons(self):
        """Configure the root window to receive mouse button events."""
        for button in [1, 3]:
            self.screen.root.grab_button(button, X.Mod1Mask, True,
                                         X.ButtonPressMask, X.GrabModeAsync,
                                         X.GrabModeAsync, X.NONE, X.NONE)

    def handle_keypress(self, event):
        """Event handler for KeyPress events.  Callback functions for every
        key combination are defined in the variable `KEYBOARD_HANDLER', from
        which the jump table (dictionary mapping from a keycode to the
        corresponding action entry is composed and stored in
        `self.key_handlers'."""
        keycode = event.detail
        entry = self.key_handlers.get(keycode, None)
        if not entry:
            return
        debug(self, 'handle_keypress: %s -> %s', keycode, entry)
        self.callback.call(event, entry)

    def handle_button_press(self, event):
        """Initiate window repositioning with the button 1 or window resizing
        with the button 3.  All mouse pointer motion events are captured until
        the button is relased."""
        window = event.child
        if not self.vscreen_manager.exist(window):
            return

        self.screen.root.grab_pointer(
            True, X.PointerMotionMask | X.ButtonReleaseMask, X.GrabModeAsync,
            X.GrabModeAsync, X.NONE, X.NONE, 0)
        self.drag_window = window
        self.drag_button = event.detail
        self.drag_geometry = window.get_geometry()
        self.drag_start_xy = self.drag_last_xy = event.root_x, event.root_y

    def handle_button_release(self, event):
        """Terminate window repositioning/resizing."""
        self.display.ungrab_pointer(0)

    def handle_motion_notify(self, event):
        """Reposition or resize the current window according to the current
        pointer position.  The maximum rate of repositioning and resizeing is
        bounded by DRAG_MAX_FPS."""
        x, y = event.root_x, event.root_y
        # prevent to reposition window too frequently
        if abs(x - self.drag_last_xy[0]) + abs(
                y - self.drag_last_xy[1]) <= DRAG_THRESH:
            return
        self.drag_last_xy = x, y

        dx = x - self.drag_start_xy[0]
        dy = y - self.drag_start_xy[1]
        if self.drag_button == 1:
            # reposition
            self.drag_window.configure(x=self.drag_geometry.x + dx,
                                       y=self.drag_geometry.y + dy)
        else:
            # resize
            self.drag_window.configure(
                width=max(MIN_WIN_SIZE, self.drag_geometry.width + dx),
                height=max(MIN_WIN_SIZE, self.drag_geometry.height + dy))
        self.vscreen_manager.frame_window.draw_frame_windows(self.drag_window)

    def handle_map_request(self, event):
        """Event handler for MapRequest events."""
        window = event.window
        vscreen = self.vscreen_manager.current_vscreen
        vscreen.manage_window(window)
        vscreen.select_window(window)

    def handle_unmap_notify(self, event):
        """Event handler for UnmapNotify events."""
        window = event.window
        vscreen = self.vscreen_manager.current_vscreen
        if vscreen.is_managed(window):
            vscreen.unmanage_window(window)
        self.vscreen_manager.frame_window.clear_frame_window(window)

    def handle_map_notify(self, event):
        """Event handler for MapNotify events."""
        window = event.window
        if window in self.vscreen_manager.frame_window.frame_windows.values():
            return
        vscreen = self.vscreen_manager.current_vscreen
        vscreen.manage_window(window)

    def handle_enter_notify(self, event):
        """Event handler for EnterNotify events."""
        window = event.window
        vscreen = self.vscreen_manager.current_vscreen
        if vscreen.is_managed(window):
            vscreen.activate_window(window)

    def handle_leave_notify(self, event):
        """Event handler for LeaveNotify events."""
        window = event.window
        pointer = self.vscreen_manager.pointer
        if self.vscreen_manager.exist(window):
            pointer.save_geometry_at(window, pointer.pop_temporary_geometry())

    def handle_destroy_notify(self, event):
        """Event handler for DestroyNotify events."""
        window = event.window
        vscreen = self.vscreen_manager.current_vscreen
        vscreen.unmanage_window(window)
        vscreen.pointer.remove_geometry_of(window)
        self.vscreen_manager.frame_window.clear_frame_window(window)

    def handle_configure_request(self, event):
        """Event handler for ConfigureRequest events."""
        window = event.window
        x, y = event.x, event.y
        width, height = event.width, event.height
        mask = event.value_mask
        if mask == 0b1111:
            window.configure(x=x, y=y, width=width, height=height)
        elif mask == 0b1100:
            window.configure(width=width, height=height)
        elif mask == 0b0011:
            window.configure(x=x, y=y)
        elif mask == 0b01000000:
            window.configure(event.stack_mode)

    def event_loop(self):
        """The main event loop of the window manager.  Continuously receive an
        event from the X11 server, and dispatch an appropriate handler if
        possible."""
        while True:
            event = self.display.next_event()
            type_ = event.type
            if type_ is X.KeyPress:
                # Templary save the geomery of pointer here. Because
                # when LeaveNotify is raised, pointer is already moved
                # away.
                self.vscreen_manager.pointer.save_temporary_geometry()
            if type_ in EVENT_HANDLER:
                handler = getattr(self, EVENT_HANDLER[type_], None)
                if handler:
                    handler(event)
