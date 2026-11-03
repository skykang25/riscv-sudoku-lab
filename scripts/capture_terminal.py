#!/usr/bin/env python3
"""Capture an actual GTK/VTE terminal window running the SIRVE measurement.

Uses an isolated Xvfb display, not the user's desktop. The screenshot contains
real terminal pixels; output is never retyped into HTML or drawn onto an image.
Requires Xvfb, GTK/VTE Python bindings, xwininfo, Pillow, and pexpect.
"""
import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]


def terminal_window(source):
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    gi.require_version("Vte", "2.91")
    from gi.repository import Gdk, GLib, Gtk, Pango, Vte

    title = "SIRVE measurement - " + source
    window = Gtk.Window(title=title)
    window.set_titlebar(Gtk.HeaderBar(title=title, show_close_button=True))
    terminal = Vte.Terminal()
    terminal.set_font(Pango.FontDescription("Monospace 11"))
    foreground, background = Gdk.RGBA(), Gdk.RGBA()
    foreground.parse("#eeeeec")
    background.parse("#222222")
    terminal.set_colors(foreground, background, [])
    terminal.set_size(132, 62)
    terminal.set_scrollback_lines(1000)
    window.add(terminal)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    log = ROOT / "assets" / (Path(source).stem + "-measurement.txt")
    command = ["/bin/bash", "--noprofile", "--norc", "-c",
               'python3 scripts/measure.py "$1" --log "$2"; read -r -p "Press Enter to close."',
               "capture", source, str(log)]
    terminal.spawn_async(Vte.PtyFlags.DEFAULT, str(ROOT), command, None,
                         GLib.SpawnFlags.DEFAULT, None, None, -1, None, None, None)
    Gtk.main()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=("sudoku_baseline.s", "sudoku_bitmask.s"))
    parser.add_argument("--window", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.window:
        terminal_window(args.source)
        return
    stem = Path(args.source).stem
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    log = assets / (stem + "-measurement.txt")
    screenshot = assets / (stem + "-terminal.png")
    title = "SIRVE measurement - " + args.source
    xvfb = subprocess.Popen(["Xvfb", "-displayfd", "1", "-screen", "0",
                             "1800x1800x24", "-nolisten", "tcp"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    terminal = None
    try:
        display = ":" + xvfb.stdout.readline().strip()
        assert display != ":", "Xvfb did not provide a display number"
        env = os.environ.copy()
        for key in ("WAYLAND_DISPLAY", "GNOME_TERMINAL_SERVICE", "GNOME_TERMINAL_SCREEN"):
            env.pop(key, None)
        env.update(DISPLAY=display, GDK_BACKEND="x11", XDG_SESSION_TYPE="x11")
        started_ns = time.time_ns()
        terminal = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                     "--window", args.source],
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if (log.exists() and log.stat().st_mtime_ns >= started_ns
                    and "this is not elapsed time." in log.read_text()):
                break
            if terminal.poll() is not None:
                out, err = terminal.communicate()
                raise RuntimeError("Terminal closed before the measurement finished: " + out + err)
            time.sleep(0.2)
        else:
            ImageGrab.grab(xdisplay=display).save(assets / (stem + "-capture-debug.png"))
            raise TimeoutError("Terminal measurement did not finish on " + display)
        time.sleep(1)
        tree = subprocess.run(["xwininfo", "-display", display, "-root", "-tree"],
                              capture_output=True, text=True, check=True).stdout
        matches = [line for line in tree.splitlines()
                   if title in line or '"gnome-terminal-server"' in line]
        window = next((re.search(r"(\d+)x(\d+)\+\d+\+\d+\s+\+(-?\d+)\+(-?\d+)", line)
                       for line in matches if re.search(r"\d+x\d+", line)), None)
        if not window:
            raise RuntimeError("Could not locate the terminal window: " + tree)
        width, height, x, y = map(int, window.groups())
        assert width > 500 and height > 500
        ImageGrab.grab(bbox=(x, y, x + width, y + height), xdisplay=display).save(screenshot)
        print(f"Captured actual GTK/VTE terminal pixels: {screenshot}")
        print(f"Raw debugger log: {log}")
    finally:
        if terminal is not None and terminal.poll() is None:
            terminal.terminate()
            try:
                terminal.wait(timeout=3)
            except subprocess.TimeoutExpired:
                terminal.kill()
        xvfb.terminate()
        xvfb.wait(timeout=3)


if __name__ == "__main__":
    main()
