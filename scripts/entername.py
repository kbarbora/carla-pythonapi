import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os

class EntryWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Driving Simulator")
        self.set_size_request(300, 100)

        self.timeout_id = None
        self.connect("destroy", Gtk.main_quit)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.image_back = Gtk.Image.new_from_file('../media/images/map_icon.png')
        # vbox.pack_start()

        self.entry = Gtk.Entry()
        self.entry.set_text("Driver ID")
        self.entry.connect("activate", self.on_click)   # listen for enter key in entry
        vbox.pack_start(self.entry, True, True, 0)

        hbox = Gtk.Box(spacing=6)
        vbox.pack_start(hbox, True, True, 0)

        button = Gtk.Button.new_with_label("Start")
        button.connect("clicked", self.on_click)    # listen for button click
        vbox.pack_start(button, True, True, 0)
        return

    def on_editable_toggled(self, button):
        value = button.get_active()
        self.entry.set_editable(value)

    def on_visible_toggled(self, button):
        value = button.get_active()
        self.entry.set_visibility(value)

    def on_pulse_toggled(self, button):
        if button.get_active():
            self.entry.set_progress_pulse_step(0.2)
            # Call self.do_pulse every 100 ms
            self.timeout_id = GLib.timeout_add(100, self.do_pulse, None)
        else:
            # Don't call self.do_pulse anymore
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
            self.entry.set_progress_pulse_step(0)

    def on_click(self, widget, callback_data=None):
        # print(win.entry.get_text())
        Gtk.main_quit()
        return self.entry.get_text()

    def do_pulse(self, user_data):
        self.entry.progress_pulse()
        return True

    def on_icon_toggled(self, button):
        if button.get_active():
            icon_name = "system-search-symbolic"
        else:
            icon_name = None
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY,
            icon_name)


def main():
    win = EntryWindow()
    try:
        win.show_all()
        win.connect("destroy", Gtk.main_quit)
        Gtk.main()
    finally:
        # Gtk.main_level()
        Gtk.main_quit()
        return win.entry.get_text()


if __name__ == '__main__':
    main()
