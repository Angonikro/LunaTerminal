#!/usr/bin/python3
import os
import sys
import json
import signal
import subprocess
import shutil
import gi
import cairo
from urllib.parse import unquote, urlparse

gi.require_version("Gtk", "4.0")
gi.require_version("Vte", "3.91")
from gi.repository import Gtk, Gdk, Gio, GLib, Vte, Pango, PangoCairo

APP_ID = "de.goldisoft.LunaTerminal"
VERSION = "0.5.0"

CSS = """
/* X11/Compiz: alpha is enabled only along the terminal content path.
   The titlebar, menu bar, notebook tabs and popovers retain solid dark colors. */
window {
    background-color: rgba(0, 0, 0, 0);
    background-image: none;
}
window > box, window > box > notebook, notebook > stack,
notebook > stack > *, scrolledwindow, viewport, terminal {
    background-color: rgba(0, 0, 0, 0);
    background-image: none;
}
headerbar {
    background-color: #202333;
}
notebook > header, menubar {
    background-color: #1b1e2b;
}
headerbar { background: #202333; color: #e8eaff; border-bottom: 1px solid #343a52; }
.luna-mark { color: #ffd700; font-size: 32px; font-weight: 900; padding: 0 9px 1px 2px; }
headerbar button, headerbar menubutton > button, headerbar .flat {
    background: #292e43; color: #e8eaff; border: 1px solid #3a4260;
    border-radius: 8px; box-shadow: none; min-width: 34px; min-height: 30px;
}
headerbar button:hover, headerbar menubutton > button:hover, headerbar .flat:hover {
    background: #394365; color: #ffffff; border-color: #6676b8;
}
notebook > header {
    background: #1b1e2b;
    border-bottom: 1px solid #343b55;
    padding: 5px 8px 0 8px;
}
notebook > header > tabs {
    background: transparent;
}
notebook > header tab {
    background: #222637;
    color: #aeb8d2;
    border: 1px solid transparent;
    border-radius: 7px 7px 0 0;
    padding: 4px 6px;
    margin: 0 3px 0 0;
    min-height: 30px;
}
notebook > header tab:checked {
    background: #303b59;
    color: #ffffff;
    border-color: #465579;
    border-bottom: 2px solid #4d91ff;
}
notebook > header tab:hover:not(:checked) {
    background: #2a3045;
    color: #eef2ff;
}
.terminal-tab-title {
    color: #d9e0f5;
    font-size: 12px;
}
notebook > header tab:checked .terminal-tab-title {
    color: #ffffff;
}
.terminal-tab-close-zone {
    background: #252c40;
    border-left: 1px solid #485573;
    border-radius: 4px;
    min-width: 25px;
    min-height: 25px;
    margin-left: 8px;
    padding: 0;
}
.terminal-tab-close-zone:hover {
    background: #9f4056;
}
button.terminal-tab-close {
    background: transparent;
    color: #dce4fa;
    border: 0;
    box-shadow: none;
    min-width: 25px;
    min-height: 25px;
    padding: 0;
    margin: 0;
}
button.terminal-tab-close image {
    color: #e5ebff;
    opacity: 1;
}
button.terminal-tab-close:hover image {
    color: #ffffff;
}
button.notebook-new-tab {
    background: #252d43;
    color: #eaf0ff;
    border: 1px solid #465579;
    border-radius: 7px;
    min-width: 30px;
    min-height: 30px;
    padding: 0;
    margin: 0 0 2px 6px;
    box-shadow: none;
}
button.notebook-new-tab:hover {
    background: #3a4b72;
    border-color: #6c8bc9;
    color: #ffffff;
}
/* High-contrast menu bar and drop-down menus */
menubar {
    background-color: #202333;
    color: #edf0ff;
    border-bottom: 1px solid #343a52;
    padding: 3px 6px;
}
menubar > item {
    background: transparent;
    color: #edf0ff;
    border-radius: 6px;
    padding: 6px 10px;
}
menubar > item label {
    color: #edf0ff;
}
menubar > item:hover,
menubar > item:selected {
    background: #394365;
    color: #ffffff;
}
menubar > item:hover label,
menubar > item:selected label {
    color: #ffffff;
}
popover.menu,
popover contents {
    background-color: #202333;
    color: #edf0ff;
    border: 1px solid #465071;
}
popover.menu modelbutton,
popover modelbutton {
    background: transparent;
    color: #edf0ff;
    padding: 7px 12px;
}
popover.menu modelbutton label,
popover modelbutton label {
    color: #edf0ff;
}
popover.menu modelbutton:hover,
popover modelbutton:hover {
    background: #394365;
    color: #ffffff;
}
popover.menu modelbutton:hover label,
popover modelbutton:hover label {
    color: #ffffff;
}
terminal { padding: 10px; }
box.tab-close-area {
    background-color: #303750;
    border-left: 1px solid #69769b;
    border-radius: 0 5px 5px 0;
    min-width: 34px;
    min-height: 30px;
    padding: 2px 3px;
    margin-left: 9px;
}
button.tab-close-button {
    opacity: 1;
    display: block;
    min-width: 27px;
    min-height: 26px;
    padding: 0;
    margin: 0;
    background-color: #3d4663;
    color: #ffffff;
    border: 1px solid #8290b8;
    border-radius: 4px;
    box-shadow: none;
}
button.tab-close-button label {
    color: #ffffff;
    font-size: 17px;
    font-weight: bold;
}
button.tab-close-button image {
    opacity: 1;
    color: #ffffff;
}
button.tab-close-button:hover {
    background-color: #a83e55;
    color: #ffffff;
    border-color: #f08a9e;
}
button.tab-close-button:hover label,
button.tab-close-button:hover image {
    color: #ffffff;
}
.settings-panel, .about-content { background: #202333; color: #edf0ff; padding: 18px; }
.settings-label { color: #edf0ff; font-weight: 600; }
.settings-hint { color: #c5cde8; font-size: 12px; }
.settings-entry, .settings-spin, .settings-drop {
    background: #171923; color: #f3f5ff; caret-color: #ffffff;
    border: 1px solid #465071; border-radius: 6px; padding: 6px 8px;
}
.settings-entry:focus, .settings-spin:focus, .settings-drop:focus {
    border-color: #8295e8; box-shadow: 0 0 0 1px #8295e8;
}
.settings-entry selection { background: #5367a8; color: #ffffff; }
.settings-spin button, .settings-button {
    background: #292e43; color: #e8eaff; border: 1px solid #465071;
    border-radius: 7px; box-shadow: none;
}
.settings-spin button:hover, .settings-button:hover {
    background: #394365; color: #ffffff; border-color: #7184ce;
}
.settings-spin button image { color: #e8eaff; }
.settings-button label { color: inherit; }
.about-title { color: #ffffff; font-size: 20px; font-weight: bold; }
.about-version { color: #c3cbea; font-size: 13px; }
.about-description { color: #e1e6fa; font-size: 14px; }
.about-footer { color: #aeb9df; font-size: 12px; padding-top: 18px; }
.searchbar { background: #202333; padding: 7px; border-bottom: 1px solid #343a52; }
.searchbar entry { background: #171923; color: #f3f5ff; border: 1px solid #465071; }
"""

DEFAULT_PROFILE = {
    "background": "#171923",
    "foreground": "#e8eaff",
    "font": "Monospace 11",
    "opacity": 100,
    "cursor": "block",
    "audible_bell": False,
    "scrollbar": True,
    "scrollback_lines": 10000,
    "history_entries": 1000,
}

class TerminalPage(Gtk.Box):
    def __init__(self, app, window_state, profile_name=None, cwd=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app = app
        self.window_state = window_state
        self.window = window_state["window"]
        self.profile_name = profile_name or app.settings.get("active_profile", "Standard")
        self.profile = app.get_profile(self.profile_name)
        self.initial_cwd = cwd or app.settings.get("working_directory") or os.path.expanduser("~")
        self.search_revealer = Gtk.Revealer()
        self.search_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.search_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.search_bar.add_css_class("searchbar")
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Im Terminal suchen …")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("activate", lambda *_: self.search_next())
        self.search_bar.append(self.search_entry)
        prev_btn = Gtk.Button(label="↑")
        prev_btn.set_tooltip_text("Vorheriger Treffer")
        prev_btn.connect("clicked", lambda *_: self.search_previous())
        self.search_bar.append(prev_btn)
        next_btn = Gtk.Button(label="↓")
        next_btn.set_tooltip_text("Nächster Treffer")
        next_btn.connect("clicked", lambda *_: self.search_next())
        self.search_bar.append(next_btn)
        close_search = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_search.connect("clicked", lambda *_: self.hide_search())
        self.search_bar.append(close_search)
        self.search_revealer.set_child(self.search_bar)
        self.append(self.search_revealer)

        self.terminal = Vte.Terminal()
        self.terminal.set_hexpand(True)
        self.terminal.set_vexpand(True)
        self.terminal.set_scrollback_lines(int(self.profile["scrollback_lines"]))
        self.terminal.set_mouse_autohide(True)
        self.terminal.connect("bell", self.on_bell)
        # VTE must paint its configured RGBA background. With clearing disabled,
        # GTK4 can expose its default white widget backing instead of alpha blending.
        if hasattr(self.terminal, "set_clear_background"):
            self.terminal.set_clear_background(True)
        self.apply_profile()
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_hexpand(True)
        self.scroller.set_vexpand(True)
        self.scroller.set_policy(
            Gtk.PolicyType.AUTOMATIC if self.profile.get("scrollbar", True) else Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC
        )
        self.scroller.set_child(self.terminal)
        self.append(self.scroller)

        self.terminal.connect("child-exited", self.on_child_exited)
        self.terminal.connect("window-title-changed", self.on_title_changed)
        self.install_url_matching()
        self.install_context_menu()
        self.install_url_click()
        self.start_shell()

    def on_bell(self, *_args):
        if self.profile.get("audible_bell", False):
            self.app.play_bell()

    def apply_profile(self):
        p = self.profile
        fg = self.app.parse_color(p.get("foreground", DEFAULT_PROFILE["foreground"]))
        bg = self.app.parse_color(p.get("background", DEFAULT_PROFILE["background"]))
        opacity = max(0, min(100, int(p.get("opacity", 100)))) / 100.0
        bg.alpha = opacity
        palette_values = [
            "#1f2430", "#e06c75", "#98c379", "#e5c07b",
            "#61afef", "#c678dd", "#56b6c2", "#dcdfe4",
            "#5c6370", "#e06c75", "#98c379", "#e5c07b",
            "#61afef", "#c678dd", "#56b6c2", "#ffffff",
        ]
        palette = [self.app.parse_color(c) for c in palette_values]
        self.terminal.set_colors(fg, bg, palette)
        self.terminal.set_font(Pango.FontDescription(p.get("font", "Monospace 11")))
        self.terminal.set_scrollback_lines(int(p.get("scrollback_lines", 10000)))
        self.terminal.set_audible_bell(False)  # Play the bundled sound inside LunaTerminal instead.
        cursor = p.get("cursor", "block")
        cursor_map = {
            "block": Vte.CursorShape.BLOCK,
            "ibeam": Vte.CursorShape.IBEAM,
            "underline": Vte.CursorShape.UNDERLINE,
        }
        self.terminal.set_cursor_shape(cursor_map.get(cursor, Vte.CursorShape.BLOCK))
        self.scroller_policy()

    def scroller_policy(self):
        if hasattr(self, "scroller"):
            self.scroller.set_policy(
                Gtk.PolicyType.AUTOMATIC if self.profile.get("scrollbar", True) else Gtk.PolicyType.NEVER,
                Gtk.PolicyType.AUTOMATIC
            )

    def install_url_matching(self):
        try:
            regex = GLib.Regex.new('https?://[^\\s<>"]+', GLib.RegexCompileFlags.CASELESS, GLib.RegexMatchFlags.DEFAULT)
            self.url_tag = self.terminal.match_add_regex(regex, 0)
        except Exception:
            self.url_tag = None

    def install_url_click(self):
        gesture = Gtk.GestureClick.new()
        gesture.set_button(1)
        gesture.connect("released", self.on_terminal_url_click)
        self.terminal.add_controller(gesture)

    def on_terminal_url_click(self, gesture, n_press, x, y):
        try:
            result = self.terminal.match_check(x, y)
            match = result[0] if isinstance(result, tuple) else result
            if match and str(match).startswith(("http://", "https://")):
                Gio.AppInfo.launch_default_for_uri(str(match), None)
        except Exception:
            pass

    def install_context_menu(self):
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)
        gesture.connect("pressed", self.show_context_menu)
        self.terminal.add_controller(gesture)

    def show_context_menu(self, gesture, n_press, x, y):
        menu = Gio.Menu()
        menu.append("Kopieren", "win.copy")
        menu.append("Einfügen", "win.paste")
        menu.append("Alles markieren", "win.select-all")
        menu.append("Suchen …", "win.search")
        menu.append("Neuer Tab", "app.new-tab")
        menu.append("Tab schließen", "app.close-tab")
        popover = Gtk.PopoverMenu.new_from_model(menu)
        popover.set_parent(self.terminal)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        popover.set_pointing_to(rect)
        popover.popup()
        self._context_popover = popover

    def start_shell(self):
        shell = self.app.settings.get("shell") or os.environ.get("SHELL") or "/bin/bash"
        if not os.path.isfile(shell):
            shell = "/bin/bash"
        login = bool(self.app.settings.get("login_shell", True))
        argv = [shell, "--login"] if login and os.path.basename(shell) == "bash" else ([shell, "-l"] if login else [shell])
        env = dict(os.environ)
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"
        env["HISTSIZE"] = str(self.profile.get("history_entries", 1000))
        env["HISTFILESIZE"] = str(self.profile.get("history_entries", 1000))
        env["LUNATERMINAL_PROFILE"] = self.profile_name
        envv = [f"{k}={v}" for k, v in env.items()]
        cwd = self.initial_cwd if os.path.isdir(self.initial_cwd) else os.path.expanduser("~")
        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT, cwd, argv, envv, GLib.SpawnFlags.DEFAULT,
            None, None, -1, None, self.on_spawn_done, None
        )

    def on_spawn_done(self, terminal, pid, error, user_data):
        if error:
            self.terminal.feed(f"\\r\\nLunaTerminal: Shell konnte nicht gestartet werden: {error}\\r\\n".encode())
            return
        self.child_pid = pid
        startup = self.app.settings.get("startup_command", "").strip()
        if startup:
            GLib.idle_add(lambda: self.terminal.feed_child((startup + "\\n").encode("utf-8")) or GLib.SOURCE_REMOVE)

    def on_child_exited(self, terminal, status):
        if self.app.settings.get("close_on_exit", True):
            self.app.close_page(self)
        else:
            self.terminal.feed(b"\\r\\n[Shell beendet. Mit Strg+Umschalt+T ein neues Terminal oeffnen.]\\r\\n")

    def on_title_changed(self, terminal):
        title = terminal.get_window_title() or os.path.basename(self.initial_cwd.rstrip("/")) or "Terminal"
        # Update only the title label. set_tab_label_text() replaces the complete
        # custom tab widget and therefore removes the dedicated close-button area.
        if hasattr(self, "tab_label") and self.tab_label:
            self.tab_label.set_text(title[:40])
        else:
            self.window_state["notebook"].set_tab_label_text(self, title[:40])

    def show_search(self):
        self.search_revealer.set_reveal_child(True)
        self.search_entry.grab_focus()
        self.search_entry.select_region(0, -1)

    def hide_search(self):
        self.search_revealer.set_reveal_child(False)
        self.terminal.grab_focus()

    def do_search(self, direction=1):
        text = self.search_entry.get_text()
        if not text:
            return
        try:
            regex = GLib.Regex.new(GLib.Regex.escape_string(text), GLib.RegexCompileFlags.CASELESS, GLib.RegexMatchFlags.DEFAULT)
            self.terminal.search_set_regex(regex, 0)
            if direction > 0:
                self.terminal.search_find_next()
            else:
                self.terminal.search_find_previous()
        except Exception:
            pass

    def search_next(self):
        self.do_search(1)

    def search_previous(self):
        self.do_search(-1)

    def current_directory(self):
        try:
            uri = self.terminal.get_current_directory_uri()
            if uri:
                parsed = urlparse(uri)
                path = unquote(parsed.path)
                if os.path.isdir(path):
                    return path
        except Exception:
            pass
        try:
            pid = getattr(self, "child_pid", None)
            if pid:
                path = os.readlink(f"/proc/{pid}/cwd")
                if os.path.isdir(path):
                    return path
        except Exception:
            pass
        return self.initial_cwd


class LunaTerminal(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.windows = []
        self.active_state = None
        self.settings_path = os.path.join(GLib.get_user_config_dir(), "lunaterminal", "settings.json")
        self.settings = {
            "profiles": {"Standard": dict(DEFAULT_PROFILE)},
            "active_profile": "Standard",
            "shell": "",
            "login_shell": True,
            "working_directory": os.path.expanduser("~"),
            "startup_command": "",
            "close_on_exit": True,
            "restore_session": False,
            "menu_bar_visible": True,
            "window_width": 1050,
            "window_height": 680,
            "saved_session": [],
        }
        self.load_settings()

    def play_bell(self):
        """Play LunaTerminal's bundled BEL sound without changing desktop settings."""
        sound = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "bell.wav")
        if not os.path.isfile(sound):
            return
        players = [
            ("paplay", [sound]),
            ("pw-play", [sound]),
            ("canberra-gtk-play", ["--file", sound]),
            ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet", sound]),
            ("aplay", [sound]),
        ]
        for name, arguments in players:
            executable = shutil.which(name)
            if not executable:
                continue
            try:
                subprocess.Popen(
                    [executable, *arguments],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return
            except OSError:
                continue

    def load_settings(self):
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Migrate the 0.1.x flat preferences into the Standard profile.
            old_profile = dict(DEFAULT_PROFILE)
            old_profile.update({
                "background": saved.get("background", DEFAULT_PROFILE["background"]),
                "foreground": saved.get("foreground", DEFAULT_PROFILE["foreground"]),
                "scrollback_lines": saved.get("scrollback_lines", DEFAULT_PROFILE["scrollback_lines"]),
                "history_entries": saved.get("history_entries", DEFAULT_PROFILE["history_entries"]),
            })
            self.settings.update(saved)
            profiles = self.settings.get("profiles")
            if not isinstance(profiles, dict) or not profiles:
                profiles = {"Standard": old_profile}
            elif "Standard" not in profiles:
                profiles["Standard"] = old_profile
            for name, profile in list(profiles.items()):
                merged = dict(DEFAULT_PROFILE)
                if isinstance(profile, dict):
                    merged.update(profile)
                profiles[name] = merged
            self.settings["profiles"] = profiles
            if self.settings.get("active_profile") not in profiles:
                self.settings["active_profile"] = next(iter(profiles))
        except (OSError, ValueError, TypeError):
            pass

    def save_settings(self):
        os.makedirs(os.path.dirname(self.settings_path), mode=0o700, exist_ok=True)
        tmp = self.settings_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.settings_path)

    @staticmethod
    def parse_color(value):
        color = Gdk.RGBA()
        if not color.parse(value):
            raise ValueError(f"Ungültiger Farbwert: {value}")
        return color

    def get_profile(self, name=None):
        name = name or self.settings.get("active_profile", "Standard")
        return self.settings["profiles"].get(name, self.settings["profiles"]["Standard"])

    def do_activate(self):
        if self.windows:
            self.windows[-1]["window"].present()
            return
        saved = self.settings.get("saved_session", []) if self.settings.get("restore_session") else []
        if saved:
            state = self.create_window(present=False, restore=saved)
        else:
            state = self.create_window(present=False)
            self.new_tab()
        state["window"].present()

    def create_window(self, present=True, restore=None):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("LunaTerminal")
        window.set_default_size(int(self.settings.get("window_width", 1050)), int(self.settings.get("window_height", 680)))
        header = Gtk.HeaderBar()
        moon = Gtk.Label(label="☾")
        moon.add_css_class("luna-mark")
        moon.set_tooltip_text("LunaTerminal")
        header.pack_start(moon)
        title = Gtk.Label(label="LunaTerminal")
        title.add_css_class("title")
        header.set_title_widget(title)
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_menu_model(self.build_menu_model())
        header.pack_end(menu_btn)
        window.set_titlebar(header)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        menubar = Gtk.PopoverMenuBar.new_from_model(self.build_menubar_model())
        menubar.set_visible(bool(self.settings.get("menu_bar_visible", True)))
        outer.append(menubar)
        notebook = Gtk.Notebook()
        notebook.set_scrollable(True)
        notebook.set_show_border(False)
        notebook.set_hexpand(True)
        notebook.set_vexpand(True)
        new_tab_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
        new_tab_btn.add_css_class("notebook-new-tab")
        new_tab_btn.set_tooltip_text("Neuer Tab (Strg+Umschalt+T)")
        new_tab_btn.connect("clicked", lambda *_: self.new_tab(state=state))
        notebook.set_action_widget(new_tab_btn, Gtk.PackType.END)
        outer.append(notebook)
        window.set_child(outer)
        # GTK4/X11: explicitly declare an EMPTY opaque region. Passing None
        # resets to the default (the whole surface is opaque), which prevents
        # the compositor from blending the window with the desktop.
        def clear_opaque_region(widget, *_args):
            surface = widget.get_surface()
            if surface is not None and hasattr(surface, "set_opaque_region"):
                try:
                    surface.set_opaque_region(cairo.Region())
                except (TypeError, RuntimeError):
                    pass
        window.connect("realize", clear_opaque_region)
        window.connect("map", clear_opaque_region)
        state = {"window": window, "notebook": notebook, "menubar": menubar, "pages": [], "fullscreen": False}
        self.windows.append(state)
        self.active_state = state
        self.install_page_actions(state)
        window.connect("notify::is-active", lambda *_: self.set_active_state(state))
        window.connect("close-request", lambda *_: self.on_window_close(state))
        self.add_window_shortcuts(window)
        if restore:
            for item in restore:
                self.new_tab(state=state, profile_name=item.get("profile"), cwd=item.get("cwd"))
        if present:
            window.present()
        return state

    def set_active_state(self, state):
        self.active_state = state

    def build_menu_model(self):
        menu = Gio.Menu()
        menu.append("Neuer Tab", "app.new-tab")
        menu.append("Neues Fenster", "app.new-window")
        menu.append("Tab schließen", "app.close-tab")
        menu.append("Menüleiste anzeigen / ausblenden", "app.toggle-menubar")
        menu.append("Einstellungen", "app.settings")
        menu.append("Info", "app.about")
        return menu

    def build_menubar_model(self):
        bar = Gio.Menu()
        file_menu = Gio.Menu()
        file_menu.append("Neuer Tab", "app.new-tab")
        file_menu.append("Neues Fenster", "app.new-window")
        file_menu.append("Tab schließen", "app.close-tab")
        file_menu.append("Fenster schließen", "app.close-window")
        bar.append_submenu("Datei", file_menu)
        edit = Gio.Menu()
        edit.append("Kopieren", "win.copy")
        edit.append("Einfügen", "win.paste")
        edit.append("Alles markieren", "win.select-all")
        edit.append("Suchen", "win.search")
        bar.append_submenu("Bearbeiten", edit)
        view = Gio.Menu()
        view.append("Vollbild", "app.fullscreen")
        view.append("Menüleiste ein-/ausblenden", "app.toggle-menubar")
        view.append("Schrift vergrößern", "app.font-up")
        view.append("Schrift verkleinern", "app.font-down")
        view.append("Normale Schriftgröße", "app.font-reset")
        bar.append_submenu("Ansicht", view)
        terminal = Gio.Menu()
        terminal.append("Neuer Tab", "app.new-tab")
        terminal.append("Shell neu starten", "app.restart-shell")
        terminal.append("Einstellungen", "app.settings")
        bar.append_submenu("Terminal", terminal)
        help_menu = Gio.Menu()
        help_menu.append("Info", "app.about")
        bar.append_submenu("Hilfe", help_menu)
        return bar

    def install_page_actions(self, state):
        for name, callback in {
            "copy": lambda *_: self.page_action("copy"),
            "paste": lambda *_: self.page_action("paste"),
            "select-all": lambda *_: self.page_action("select-all"),
            "search": lambda *_: self.page_action("search"),
        }.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            state["window"].add_action(action)

    def add_app_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def add_window_shortcuts(self, window):
        shortcuts = [
            ("<Control><Shift>t", "app.new-tab"),
            ("<Control><Shift>w", "app.close-tab"),
            ("<Control><Shift>n", "app.new-window"),
            ("<Control><Shift>f", "win.search"),
            ("<Control><Shift>c", "win.copy"),
            ("<Control><Shift>v", "win.paste"),
            ("<Control><Shift>a", "win.select-all"),
            ("<Control>plus", "app.font-up"),
            ("<Control>minus", "app.font-down"),
            ("<Control>0", "app.font-reset"),
            ("F11", "app.fullscreen"),
            ("<Control>Page_Up", "app.previous-tab"),
            ("<Control>Page_Down", "app.next-tab"),
            ("<Control>m", "app.toggle-menubar"),
        ]
        controller = Gtk.ShortcutController()
        for accelerator, action_name in shortcuts:
            shortcut = Gtk.Shortcut.new(
                Gtk.ShortcutTrigger.parse_string(accelerator),
                Gtk.ShortcutAction.parse_string(f"action({action_name})")
            )
            controller.add_shortcut(shortcut)
        window.add_controller(controller)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        actions = {
            "new-tab": self.new_tab,
            "new-window": self.new_window,
            "close-tab": self.close_tab,
            "close-window": self.close_window,
            "settings": self.show_settings,
            "about": self.show_about,
            "font-up": lambda *_: self.change_font(1),
            "font-down": lambda *_: self.change_font(-1),
            "font-reset": self.reset_font,
            "fullscreen": self.toggle_fullscreen,
            "toggle-menubar": self.toggle_menubar,
            "previous-tab": lambda *_: self.switch_tab(-1),
            "next-tab": lambda *_: self.switch_tab(1),
            "restart-shell": self.restart_shell,
        }
        for name, callback in actions.items():
            self.add_app_action(name, callback)

    def current_state(self):
        if self.active_state in self.windows:
            return self.active_state
        return self.windows[-1] if self.windows else None

    def current_page(self, state=None):
        state = state or self.current_state()
        if not state:
            return None
        idx = state["notebook"].get_current_page()
        return state["notebook"].get_nth_page(idx) if idx >= 0 else None

    def new_window(self, *_):
        state = self.create_window(present=True)
        self.new_tab(state=state)

    def new_tab(self, *_args, state=None, profile_name=None, cwd=None):
        state = state or self.current_state()
        if not state:
            state = self.create_window()
        page = TerminalPage(self, state, profile_name=profile_name, cwd=cwd)
        label = Gtk.Label(label="Terminal")
        label.add_css_class("terminal-tab-title")
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.FILL)
        label.set_xalign(0.0)
        # Let the title use the available tab width up to the fixed close zone.
        # It may shrink only when the window contains many tabs.
        label.set_width_chars(18)
        label.set_max_width_chars(40)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_single_line_mode(True)

        close = Gtk.Button()
        close.add_css_class("terminal-tab-close")
        close.set_child(Gtk.Image.new_from_icon_name("window-close-symbolic"))
        close.set_size_request(25, 25)
        close.set_opacity(1.0)
        close.set_tooltip_text("Tab schließen")

        # The close button owns a fixed trailing compartment. The title can
        # shrink/ellipsize but can never take the close button's reserved space.
        close_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        close_area.add_css_class("terminal-tab-close-zone")
        close_area.set_size_request(27, 27)
        close_area.set_hexpand(False)
        close_area.set_vexpand(False)
        close_area.set_valign(Gtk.Align.CENTER)
        close_area.append(close)

        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        tab_box.add_css_class("terminal-tab")
        # Each tab keeps a sensible fixed width instead of stretching across
        # the whole notebook. The title expands inside this width, while the
        # close compartment keeps its reserved position at the far right.
        tab_box.set_size_request(250, 34)
        tab_box.set_hexpand(False)
        tab_box.set_valign(Gtk.Align.CENTER)
        tab_box.append(label)
        tab_box.append(close_area)
        page.tab_label = label
        idx = state["notebook"].append_page(page, tab_box)
        state["notebook"].set_tab_reorderable(page, True)
        close.connect("clicked", lambda *_: self.close_page(page))
        state["pages"].append(page)
        state["notebook"].set_current_page(idx)
        page.terminal.grab_focus()
        self.active_state = state
        return page

    def close_page(self, page, close_empty=True):
        state = page.window_state
        idx = state["notebook"].page_num(page)
        if idx >= 0:
            try:
                pty = page.terminal.get_pty()
                if pty:
                    page.terminal.feed_child(b"exit\\n")
            except Exception:
                pass
            state["notebook"].remove_page(idx)
        if page in state["pages"]:
            state["pages"].remove(page)
        if close_empty and state["notebook"].get_n_pages() == 0:
            state["window"].close()

    def close_tab(self, *_):
        page = self.current_page()
        if page:
            self.close_page(page)

    def on_window_close(self, state):
        self.save_session()
        if state in self.windows:
            self.windows.remove(state)
        if self.active_state is state:
            self.active_state = self.windows[-1] if self.windows else None
        return False

    def close_window(self, *_):
        state = self.current_state()
        if state:
            state["window"].close()

    def save_session(self):
        saved = []
        for state in self.windows:
            for page in state["pages"]:
                saved.append({"profile": page.profile_name, "cwd": page.current_directory()})
        self.settings["saved_session"] = saved
        if self.windows:
            w = self.windows[-1]["window"]
            if not w.is_maximized() and not self.windows[-1].get("fullscreen", False):
                self.settings["window_width"] = max(600, w.get_width())
                self.settings["window_height"] = max(400, w.get_height())
        self.save_settings()

    def page_action(self, action):
        page = self.current_page()
        if not page:
            return
        if action == "copy":
            page.terminal.copy_clipboard_format(Vte.Format.TEXT)
        elif action == "paste":
            page.terminal.paste_clipboard()
        elif action == "select-all":
            page.terminal.select_all()
        elif action == "search":
            page.show_search()

    def change_font(self, delta):
        page = self.current_page()
        if not page:
            return
        desc = page.terminal.get_font() or Pango.FontDescription("Monospace 11")
        size = max(7, min(40, int(desc.get_size() / Pango.SCALE) + delta))
        desc.set_size(size * Pango.SCALE)
        page.terminal.set_font(desc)

    def reset_font(self, *_):
        page = self.current_page()
        if page:
            page.terminal.set_font(Pango.FontDescription(page.profile.get("font", "Monospace 11")))

    def switch_tab(self, delta):
        state = self.current_state()
        if not state:
            return
        nb = state["notebook"]
        count = nb.get_n_pages()
        if count:
            nb.set_current_page((nb.get_current_page() + delta) % count)

    def toggle_fullscreen(self, *_):
        state = self.current_state()
        if not state:
            return
        w = state["window"]
        if state.get("fullscreen", False):
            w.unfullscreen()
            state["fullscreen"] = False
        else:
            w.fullscreen()
            state["fullscreen"] = True

    def toggle_menubar(self, *_):
        state = self.current_state()
        if state:
            visible = not state["menubar"].get_visible()
            state["menubar"].set_visible(visible)
            self.settings["menu_bar_visible"] = visible
            self.save_settings()

    def restart_shell(self, *_):
        page = self.current_page()
        if page:
            state, profile, cwd = page.window_state, page.profile_name, page.current_directory()
            self.close_page(page, close_empty=False)
            self.new_tab(state=state, profile_name=profile, cwd=cwd)

    def show_settings(self, *_):
        dialog = Gtk.Dialog(transient_for=self.current_state()["window"], modal=True)
        dialog.set_title("LunaTerminal – Einstellungen")
        dialog.set_default_size(760, 760)
        dialog.set_resizable(True)
        cancel = dialog.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        cancel.add_css_class("settings-button")
        save = dialog.add_button("Speichern", Gtk.ResponseType.ACCEPT)
        save.add_css_class("settings-button")
        content = dialog.get_content_area()
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        panel.add_css_class("settings-panel")
        scroll.set_child(panel)
        content.append(scroll)

        # Use a vertical settings layout instead of a Gtk.Grid. This avoids
        # GTK theme/layout combinations collapsing the grid rows in the dialog.
        grid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        panel.append(grid)

        def label(text):
            w = Gtk.Label(label=text)
            w.add_css_class("settings-label")
            w.set_halign(Gtk.Align.START)
            return w

        def hint(text):
            w = Gtk.Label(label=text)
            w.add_css_class("settings-hint")
            w.set_halign(Gtk.Align.START)
            w.set_wrap(True)
            return w

        def entry(value="", placeholder=""):
            w = Gtk.Entry()
            w.add_css_class("settings-entry")
            w.set_text(str(value))
            w.set_placeholder_text(placeholder)
            w.set_hexpand(True)
            return w

        def spin(value, low, high, step=1):
            w = Gtk.SpinButton.new_with_range(low, high, step)
            w.add_css_class("settings-spin")
            w.set_value(value)
            w.set_digits(0)
            return w

        def drop(options, selected):
            w = Gtk.DropDown.new_from_strings(options)
            w.add_css_class("settings-drop")
            try:
                w.set_selected(options.index(selected))
            except ValueError:
                w.set_selected(0)
            return w

        def row(r, title, widget, tip=None):
            group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            title_label = label(title)
            title_label.set_size_request(190, -1)
            title_label.set_valign(Gtk.Align.CENTER)
            line.append(title_label)
            widget.set_hexpand(True)
            line.append(widget)
            group.append(line)
            if tip:
                tip_label = hint(tip)
                tip_label.set_margin_start(204)
                group.append(tip_label)
            group.set_margin_bottom(5)
            grid.append(group)

        profile_names = list(self.settings["profiles"].keys())
        active_profile = self.settings.get("active_profile", "Standard")
        profile_drop = drop(profile_names, active_profile)
        row(0, "Profil", profile_drop, "Profile speichern unterschiedliche Farben, Schrift und Terminalverhalten.")
        profile_name_entry = entry(active_profile, "Profilname")
        row(2, "Profilname", profile_name_entry)
        profile_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        create_profile = Gtk.Button(label="Neues Profil")
        create_profile.add_css_class("settings-button")
        delete_profile = Gtk.Button(label="Profil löschen")
        delete_profile.add_css_class("settings-button")
        profile_actions.append(create_profile)
        profile_actions.append(delete_profile)
        grid.append(profile_actions)

        profile = dict(self.get_profile(active_profile))
        bg = entry(profile["background"])
        fg = entry(profile["foreground"])
        font = entry(profile["font"])

        # Real selectable color palette plus custom HEX entry.
        def color_control(value_entry, fallback):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            value_entry.set_hexpand(True)
            choose = Gtk.Button(label="Farbpalette …")
            choose.add_css_class("settings-button")
            choose.set_size_request(145, -1)
            def choose_color(_button):
                chooser = Gtk.Dialog(transient_for=dialog, modal=True)
                chooser.set_title("Farbe auswählen")
                chooser.set_default_size(470, 390)
                chooser.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
                chooser.add_button("Übernehmen", Gtk.ResponseType.ACCEPT)
                area = chooser.get_content_area()
                body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                body.set_margin_top(14); body.set_margin_bottom(14)
                body.set_margin_start(14); body.set_margin_end(14)
                body.append(Gtk.Label(label="Farbe direkt auswählen", xalign=0))
                colors = [
                    "#000000", "#202020", "#404040", "#606060", "#808080", "#A0A0A0", "#C0C0C0", "#FFFFFF",
                    "#7F0000", "#FF0000", "#FF6666", "#FF9999", "#7F3F00", "#FF8000", "#FFC000", "#FFFF00",
                    "#006000", "#00A000", "#00CC66", "#80FF80", "#003366", "#0066CC", "#3399FF", "#80CCFF",
                    "#000066", "#3333CC", "#6666FF", "#9999FF", "#660066", "#993399", "#CC66CC", "#FF99FF",
                    "#171923", "#202333", "#292E43", "#394365", "#5367A8", "#8295E8", "#E8EAFF", "#D9E0F5",
                ]
                palette_grid = Gtk.Grid(column_spacing=7, row_spacing=7)
                selected = {"value": value_entry.get_text() or fallback}
                for index, color_value in enumerate(colors):
                    swatch = Gtk.Button()
                    swatch.set_size_request(42, 34)
                    swatch.set_tooltip_text(color_value)
                    swatch.add_css_class("luna-color-swatch")
                    # A dedicated drawing area fills the complete swatch with
                    # the actual color instead of showing a colored dot.
                    swatch_area = Gtk.DrawingArea()
                    swatch_area.set_content_width(42)
                    swatch_area.set_content_height(34)
                    rgba = Gdk.RGBA()
                    rgba.parse(color_value)
                    def draw_swatch(_area, cr, width, height, color=rgba):
                        cr.set_source_rgba(color.red, color.green, color.blue, 1.0)
                        cr.rectangle(0, 0, width, height)
                        cr.fill()
                        cr.set_source_rgba(0.15, 0.17, 0.22, 0.9)
                        cr.set_line_width(1)
                        cr.rectangle(0.5, 0.5, max(0, width-1), max(0, height-1))
                        cr.stroke()
                    swatch_area.set_draw_func(draw_swatch)
                    swatch.set_child(swatch_area)
                    swatch.connect("clicked", lambda _b, c=color_value: (selected.__setitem__("value", c), hex_entry.set_text(c)))
                    palette_grid.attach(swatch, index % 8, index // 8, 1, 1)
                body.append(palette_grid)
                body.append(Gtk.Label(label="Eigener Farbwert (HEX)", xalign=0))
                hex_entry = Gtk.Entry()
                hex_entry.set_text(selected["value"])
                hex_entry.set_placeholder_text("#336699")
                hex_entry.connect("changed", lambda e: selected.__setitem__("value", e.get_text().strip()))
                body.append(hex_entry)
                area.append(body)
                def finish(dlg, response_id):
                    if response_id == Gtk.ResponseType.ACCEPT:
                        candidate = selected["value"].strip()
                        try:
                            self.parse_color(candidate)
                            value_entry.set_text(candidate)
                        except ValueError:
                            alert = Gtk.AlertDialog()
                            alert.set_message("Ungültiger Farbwert")
                            alert.set_detail("Bitte eine Farbe aus der Palette wählen oder einen gültigen HEX-Wert eingeben.")
                            alert.show(dlg)
                            return
                    dlg.close()
                chooser.connect("response", finish)
                chooser.present()
            choose.connect("clicked", choose_color)
            box.append(value_entry); box.append(choose)
            return box

        # List fonts installed on this machine, with independent style and size.
        def font_control(value_entry):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            value_entry.set_hexpand(True)
            choose = Gtk.Button(label="Schrift auswählen …")
            choose.add_css_class("settings-button")
            choose.set_size_request(165, -1)
            def choose_font(_button):
                desc = Pango.FontDescription.from_string(value_entry.get_text() or "Monospace 11")
                chooser = Gtk.Dialog(transient_for=dialog, modal=True)
                chooser.set_title("Schriftart, Stil und Größe")
                chooser.set_default_size(520, 330)
                chooser.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
                chooser.add_button("Übernehmen", Gtk.ResponseType.ACCEPT)
                area = chooser.get_content_area()
                body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                body.set_margin_top(16); body.set_margin_bottom(16)
                body.set_margin_start(16); body.set_margin_end(16)
                body.append(Gtk.Label(label="Installierte Schriftfamilie", xalign=0))
                families = []
                try:
                    result = subprocess.run(
                        ["fc-list", "--format", "%{family}\\n"],
                        capture_output=True, text=True, timeout=5, check=False
                    )
                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            for family_name in line.split(","):
                                family_name = family_name.strip()
                                if family_name and family_name not in families:
                                    families.append(family_name)
                except (OSError, subprocess.SubprocessError):
                    pass
                if not families:
                    font_map = PangoCairo.FontMap.get_default()
                    families = [f.get_name() for f in font_map.list_families()]
                families = sorted(set(families), key=str.casefold)
                if not families:
                    families = ["Monospace", "DejaVu Sans Mono", "Liberation Mono"]
                family_model = Gtk.StringList.new(families)
                family_drop = Gtk.DropDown.new(family_model, None)
                current_family = desc.get_family() or "Monospace"
                try: family_drop.set_selected(families.index(current_family))
                except ValueError: family_drop.set_selected(0)
                body.append(family_drop)
                body.append(Gtk.Label(label="Schriftstil", xalign=0))
                style_names = ["Normal", "Fett", "Kursiv", "Fett Kursiv"]
                style_drop = Gtk.DropDown.new_from_strings(style_names)
                if desc.get_weight() >= Pango.Weight.BOLD and desc.get_style() == Pango.Style.ITALIC:
                    style_drop.set_selected(3)
                elif desc.get_weight() >= Pango.Weight.BOLD:
                    style_drop.set_selected(1)
                elif desc.get_style() == Pango.Style.ITALIC:
                    style_drop.set_selected(2)
                body.append(style_drop)
                body.append(Gtk.Label(label="Schriftgröße", xalign=0))
                size = Gtk.SpinButton.new_with_range(6, 32, 1)
                current_size = desc.get_size() / Pango.SCALE if desc.get_size() else 11
                size.set_value(max(6, min(32, current_size)))
                body.append(size)
                preview = Gtk.Label(label="Vorschau: pi@raspberrypi:~$ ls -la")
                preview.set_wrap(True)
                preview.set_margin_top(8)
                body.append(preview)
                def make_desc():
                    d = Pango.FontDescription()
                    d.set_family(families[family_drop.get_selected()])
                    d.set_size(int(size.get_value()) * Pango.SCALE)
                    style_index = style_drop.get_selected()
                    d.set_weight(Pango.Weight.BOLD if style_index in (1,3) else Pango.Weight.NORMAL)
                    d.set_style(Pango.Style.ITALIC if style_index in (2,3) else Pango.Style.NORMAL)
                    return d
                def refresh_preview(*_args):
                    # Gtk4 Gtk.Label has no set_font_desc(); apply a Pango
                    # attribute list instead. The old call raised AttributeError
                    # before chooser.present(), so the font dialog never appeared.
                    attributes = Pango.AttrList()
                    attributes.insert(Pango.attr_font_desc_new(make_desc()))
                    preview.set_attributes(attributes)
                family_drop.connect("notify::selected", refresh_preview)
                style_drop.connect("notify::selected", refresh_preview)
                size.connect("value-changed", refresh_preview)
                refresh_preview()
                area.append(body)
                def finish(dlg, response_id):
                    if response_id == Gtk.ResponseType.ACCEPT:
                        value_entry.set_text(make_desc().to_string())
                    dlg.close()
                chooser.connect("response", finish)
                chooser.present()
            choose.connect("clicked", choose_font)
            box.append(value_entry); box.append(choose)
            return box

        bg_control = color_control(bg, "#171923")
        fg_control = color_control(fg, "#e8eaff")
        font_control_widget = font_control(font)
        opacity = spin(profile["opacity"], 0, 100, 5)
        cursor = drop(["block", "ibeam", "underline"], profile["cursor"])
        scrollback = spin(profile["scrollback_lines"], 100, 1000000, 100)
        history = spin(profile["history_entries"], 1, 100000, 100)
        bell = Gtk.CheckButton(label="Akustisches Signal aktivieren")
        bell.set_active(profile["audible_bell"])
        scrollbar = Gtk.CheckButton(label="Scrollleiste anzeigen")
        scrollbar.set_active(profile["scrollbar"])
        row(4, "Hintergrundfarbe", bg_control, "Farbe über den Dialog auswählen oder HEX-Wert direkt eingeben.")
        row(6, "Schriftfarbe", fg_control, "Farbe über den Dialog auswählen oder HEX-Wert direkt eingeben.")
        row(8, "Schriftart und Größe", font_control_widget, "Schriftfamilie und Größe bequem in getrennten Feldern auswählen.")
        row(10, "Transparenz", opacity, "0 = vollständig transparent, 100 = deckend (abhängig vom Compositor).")
        row(12, "Cursorform", cursor)
        row(13, "Gespeicherte Zeilen", scrollback)
        row(14, "Befehlshistorie", history)
        grid.append(bell)
        grid.append(scrollbar)

        shell = entry(self.settings.get("shell", ""), "/bin/bash")
        row(18, "Shell", shell, "Leer lassen für die Standard-Shell des Benutzers. Beispiel: /bin/bash oder /usr/bin/zsh.")
        login = Gtk.CheckButton(label="Shell als Login-Shell starten")
        login.set_active(self.settings.get("login_shell", True))
        grid.append(login)
        cwd = entry(self.settings.get("working_directory", os.path.expanduser("~")))
        row(21, "Startverzeichnis", cwd, "Wird für neu geöffnete Tabs und Fenster verwendet.")
        startup = entry(self.settings.get("startup_command", ""))
        row(23, "Startbefehl", startup, "Optionaler Befehl, der nach dem Start der Shell ausgeführt wird.")
        close_exit = Gtk.CheckButton(label="Terminal-Tab bei Shell-Ende schließen")
        close_exit.set_active(self.settings.get("close_on_exit", True))
        grid.append(close_exit)
        restore = Gtk.CheckButton(label="Tabs und Arbeitsverzeichnisse beim nächsten Start wiederherstellen")
        restore.set_active(self.settings.get("restore_session", False))
        grid.append(restore)

        menu_visible = Gtk.CheckButton(label="Menüleiste anzeigen (Datei, Bearbeiten, Ansicht, Terminal, Hilfe)")
        menu_visible.set_active(self.settings.get("menu_bar_visible", True))
        grid.append(menu_visible)

        def load_profile_fields(name):
            p = self.settings["profiles"].get(name, dict(DEFAULT_PROFILE))
            profile_name_entry.set_text(name)
            bg.set_text(p.get("background", DEFAULT_PROFILE["background"]))
            fg.set_text(p.get("foreground", DEFAULT_PROFILE["foreground"]))
            font.set_text(p.get("font", DEFAULT_PROFILE["font"]))
            opacity.set_value(int(p.get("opacity", DEFAULT_PROFILE["opacity"])))
            cursor_values = ["block", "ibeam", "underline"]
            cursor.set_selected(cursor_values.index(p.get("cursor", "block"))
                                 if p.get("cursor", "block") in cursor_values else 0)
            scrollback.set_value(int(p.get("scrollback_lines", DEFAULT_PROFILE["scrollback_lines"])))
            history.set_value(int(p.get("history_entries", DEFAULT_PROFILE["history_entries"])))
            bell.set_active(bool(p.get("audible_bell", False)))
            scrollbar.set_active(bool(p.get("scrollbar", True)))

        def selected_profile_name():
            # Read the selected string from Gtk.StringList itself. This avoids
            # stale Python-side indices after the model is replaced.
            index = profile_drop.get_selected()
            model = profile_drop.get_model()
            if model is not None and index != Gtk.INVALID_LIST_POSITION:
                try:
                    value = model.get_string(index)
                    if value:
                        return value
                except (AttributeError, TypeError, IndexError):
                    pass
            if 0 <= index < len(profile_names):
                return profile_names[index]
            return "Standard"

        def select_profile(_dropdown, _param=None):
            name = selected_profile_name()
            load_profile_fields(name)

        # GtkDropDown selection changes are exposed as property notifications.
        # Connect both selected and selected-item for GTK minor-version
        # differences; duplicate notifications only reload the same fields.
        profile_drop.connect("notify::selected", select_profile)
        profile_drop.connect("notify::selected-item", select_profile)

        def refresh_profile_list(select_name="Standard"):
            if "Standard" not in profile_names:
                profile_names.insert(0, "Standard")
                self.settings["profiles"].setdefault("Standard", dict(DEFAULT_PROFILE))
            model = Gtk.StringList.new(profile_names)
            profile_drop.set_model(model)
            target_index = profile_names.index(select_name) if select_name in profile_names else 0
            profile_drop.set_selected(target_index)
            load_profile_fields(model.get_string(target_index))

        def make_profile(_button):
            base_name = profile_name_entry.get_text().strip() or f"Profil {len(profile_names) + 1}"
            name = base_name
            suffix = 2
            while name in profile_names:
                name = f"{base_name} {suffix}"
                suffix += 1
            self.settings["profiles"][name] = dict(DEFAULT_PROFILE)
            profile_names.append(name)
            refresh_profile_list(name)

        def remove_profile(_button):
            name = selected_profile_name()
            if name == "Standard" or len(profile_names) <= 1:
                return
            self.settings["profiles"].pop(name, None)
            if name in profile_names:
                profile_names.remove(name)
            # Immediately switch the editor to Standard so the Save handler
            # cannot recreate the just-deleted profile from stale entry text.
            refresh_profile_list("Standard")

        create_profile.connect("clicked", make_profile)
        delete_profile.connect("clicked", remove_profile)

        def response(dlg, result):
            if result != Gtk.ResponseType.ACCEPT:
                dlg.close()
                return
            try:
                name = profile_name_entry.get_text().strip() or "Standard"
                if name not in profile_names:
                    name = selected_profile_name()
                self.parse_color(bg.get_text().strip())
                self.parse_color(fg.get_text().strip())
                profile_data = {
                    "background": bg.get_text().strip(),
                    "foreground": fg.get_text().strip(),
                    "font": font.get_text().strip() or "Monospace 11",
                    "opacity": int(opacity.get_value()),
                    "cursor": ["block", "ibeam", "underline"][cursor.get_selected()],
                    "scrollback_lines": int(scrollback.get_value()),
                    "history_entries": int(history.get_value()),
                    "audible_bell": bell.get_active(),
                    "scrollbar": scrollbar.get_active(),
                }
                self.settings["profiles"][name] = profile_data
                self.settings["active_profile"] = name
                for stale_name in list(self.settings["profiles"]):
                    if stale_name not in profile_names:
                        self.settings["profiles"].pop(stale_name, None)
                self.settings["shell"] = shell.get_text().strip()
                self.settings["login_shell"] = login.get_active()
                self.settings["working_directory"] = cwd.get_text().strip() or os.path.expanduser("~")
                self.settings["startup_command"] = startup.get_text().strip()
                self.settings["close_on_exit"] = close_exit.get_active()
                self.settings["restore_session"] = restore.get_active()
                self.settings["menu_bar_visible"] = menu_visible.get_active()
                self.save_settings()
                for window_state in self.windows:
                    window_state["menubar"].set_visible(menu_visible.get_active())
                # A profile selected in Settings is the active profile for
                # the running application, not only for tabs that were already
                # created with that profile. Update every open terminal now so
                # the change takes effect without restarting LunaTerminal.
                for state in self.windows:
                    for page in state["pages"]:
                        page.profile_name = name
                        page.profile = dict(profile_data)
                        page.apply_profile()
                dlg.close()
            except (ValueError, OSError) as exc:
                alert = Gtk.AlertDialog()
                alert.set_message("Einstellungen konnten nicht gespeichert werden")
                alert.set_detail(str(exc))
                alert.show(dlg)

        dialog.connect("response", response)
        dialog.present()

    def show_about(self, *_):
        state = self.current_state()
        if not state:
            return
        dialog = Gtk.Dialog(transient_for=state["window"], modal=True)
        dialog.set_title("Über LunaTerminal")
        dialog.set_default_size(390, 300)
        close = dialog.add_button("Schließen", Gtk.ResponseType.CLOSE)
        close.add_css_class("settings-button")
        dialog.connect("response", lambda d, _r: d.close())
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        panel.add_css_class("about-content")
        title = Gtk.Label(label="LunaTerminal")
        title.add_css_class("about-title")
        panel.append(title)
        version = Gtk.Label(label=f"Version {VERSION}")
        version.add_css_class("about-version")
        panel.append(version)
        desc = Gtk.Label(label="Leistungsfähige Linux-Kommandozeile mit GTK 4 und VTE.")
        desc.add_css_class("about-description")
        desc.set_wrap(True)
        panel.append(desc)
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        panel.append(spacer)
        footer = Gtk.Label(label="Goldisoft 2026")
        footer.add_css_class("about-footer")
        panel.append(footer)
        dialog.get_content_area().append(panel)
        dialog.present()


app = LunaTerminal()
css = Gtk.CssProvider()
css.load_from_data(CSS.encode())
Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)
raise SystemExit(app.run(sys.argv))
