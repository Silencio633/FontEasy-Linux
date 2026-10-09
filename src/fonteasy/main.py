"""FontEasy — install fonts on Linux the easy way (GTK3)."""

from __future__ import annotations

import gettext
import locale
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from fonteasy import __version__  # noqa: E402, F401
from fonteasy import installer  # noqa: E402
from fonteasy.installer import get_default_font_dir  # noqa: E402

# ---------------------------------------------------------------------------
# i18n: UI strings default to English (Flathub requirement); gettext stays
# ready for translations (locale/ + .po files, e.g. pt-PT).
# ---------------------------------------------------------------------------
try:
    locale.setlocale(locale.LC_ALL, "")
except locale.Error:  # pragma: no cover
    pass

try:
    gettext.bindtextdomain("fonteasy", str(Path(__file__).resolve().parent.parent.parent / "locale"))
    gettext.textdomain("fonteasy")
    _ = gettext.gettext
except OSError:  # pragma: no cover
    _ = lambda s: s  # noqa: E731

APP_NAME = "FontEasy"
SUPPORTED_EXTENSIONS = installer.SUPPORTED_EXTENSIONS


class FontEasy(Gtk.Window):
    def __init__(self):
        super().__init__(title=_("FontEasy Linux"))
        self.set_default_size(620, 480)
        self.set_border_width(20)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.selected_files: list[Path] = []
        self.file_labels: dict[str, str] = {}  # name -> "Family — Style"

        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(layout)

        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>FontEasy</span>")
        layout.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label=_("Install your fonts on Linux the easy way."))
        subtitle.set_line_wrap(True)
        layout.pack_start(subtitle, False, False, 0)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)

        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(200)
        scroll.add(self.list_box)
        layout.pack_start(scroll, True, True, 0)
        self._enable_drag_and_drop(scroll)

        self.status = Gtk.Label(
            label=_("Select .TTF, .OTF, .TTC or .OTC files (or drag them here).")
        )
        self.status.set_line_wrap(True)
        layout.pack_start(self.status, False, False, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        layout.pack_start(buttons, False, False, 0)

        choose_button = Gtk.Button(label=_("Choose fonts"))
        choose_button.connect("clicked", self.choose_fonts)
        buttons.pack_start(choose_button, True, True, 0)

        clear_button = Gtk.Button(label=_("Clear"))
        clear_button.connect("clicked", self.clear_selection)
        buttons.pack_start(clear_button, True, True, 0)

        install_button = Gtk.Button(label=_("Install fonts"))
        install_button.get_style_context().add_class("suggested-action")
        install_button.connect("clicked", self.install_fonts)
        buttons.pack_start(install_button, True, True, 0)

        folder_button = Gtk.Button(label=_("Open font folder"))
        folder_button.connect("clicked", self.open_font_folder)
        buttons.pack_start(folder_button, True, True, 0)

    # -- dialogs ----------------------------------------------------------
    def show_message(self, message: str, error: bool = False):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

    def confirm(self, message: str) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=message,
        )
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES

    # -- selection ----------------------------------------------------------
    def _enable_drag_and_drop(self, widget: Gtk.Widget):
        target = Gtk.TargetEntry.new("text/uri-list", 0, 0)
        widget.drag_dest_set(
            Gtk.DestDefaults.ALL, [target], Gdk.DragAction.COPY
        )
        widget.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_data_received(self, _widget, _context, _x, _y, data, _info, _time):
        paths: list[Path] = []
        for uri in data.get_uris():
            parsed = urlparse(uri)
            if parsed.scheme != "file":
                continue
            paths.append(Path(url2pathname(unquote(parsed.path))))
        if paths:
            self.add_files(paths)

    def choose_fonts(self, _button):
        dialog = Gtk.FileChooserDialog(
            title=_("Select fonts"),
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Select"), Gtk.ResponseType.ACCEPT,
        )
        dialog.set_select_multiple(True)

        file_filter = Gtk.FileFilter()
        file_filter.set_name(_("Font files"))
        for extension in sorted(SUPPORTED_EXTENSIONS):
            file_filter.add_pattern(f"*{extension}")
            file_filter.add_pattern(f"*{extension.upper()}")
        dialog.add_filter(file_filter)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            self.add_files([Path(n) for n in dialog.get_filenames()])
        dialog.destroy()

    def add_files(self, candidates: list[Path]):
        """Validate with fc-scan and add only real fonts."""
        added, invalid, duplicated = 0, [], 0
        known = {p.resolve() if p.exists() else p for p in self.selected_files}

        for candidate in candidates:
            key = candidate.resolve() if candidate.exists() else candidate
            if key in known:
                duplicated += 1
                continue
            ok, info = installer.validate_source(candidate)
            if not ok:
                invalid.append("{}: {}".format(candidate.name, info))
                continue
            self.selected_files.append(candidate)
            self.file_labels[candidate.name] = info
            known.add(key)
            added += 1

        self.refresh_list()

        parts = []
        if added:
            parts.append(_("{} font(s) added.").format(added))
        if duplicated:
            parts.append(_("{} already in the list.").format(duplicated))
        if invalid:
            parts.append(_("{} invalid file(s) — see details.").format(len(invalid)))
        self.status.set_text(" ".join(parts) if parts else _("No new files."))

        if invalid:
            self.show_message(
                _("The following files were skipped:\n\n") + "\n".join(invalid),
                error=True,
            )

    def remove_file(self, file_path: Path):
        self.selected_files = [p for p in self.selected_files if p != file_path]
        self.file_labels.pop(file_path.name, None)
        self.refresh_list()
        self.status.set_text(_("{} font(s) in the list.").format(len(self.selected_files)))

    def clear_selection(self, _button=None):
        if not self.selected_files:
            return
        if self.confirm(_("Clear the selected font list?")):
            self.selected_files = []
            self.file_labels = {}
            self.refresh_list()
            self.status.set_text(_("List cleared."))

    def refresh_list(self):
        for child in self.list_box.get_children():
            self.list_box.remove(child)

        for file_path in self.selected_files:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.set_margin_top(6)
            box.set_margin_bottom(6)
            box.set_margin_start(8)
            box.set_margin_end(8)

            info = self.file_labels.get(file_path.name, "")
            label = Gtk.Label(xalign=0)
            label.set_hexpand(True)
            if info:
                # manual escaping to avoid Pango markup injection
                import html

                label.set_markup(
                    "<b>{}</b>\n<small>{}</small>".format(
                        html.escape(file_path.name), html.escape(info)
                    )
                )
            else:
                label.set_text(file_path.name)
            box.pack_start(label, True, True, 0)

            remove = Gtk.Button(label="✕")
            remove.set_tooltip_text(_("Remove from the list"))
            remove.connect("clicked", lambda _b, p=file_path: self.remove_file(p))
            box.pack_start(remove, False, False, 0)

            row.add(box)
            self.list_box.add(row)

        self.list_box.show_all()

    # -- installation -------------------------------------------------------
    def install_fonts(self, _button):
        if not self.selected_files:
            self.show_message(
                _("First, select at least one font."),
                error=True,
            )
            return

        font_dir = get_default_font_dir()
        result = installer.install_font_files(list(self.selected_files), font_dir)

        # Keep only failures in the list so the user can retry.
        failed_names = set()
        for err in result.errors:
            # cache errors carry no file prefix
            name = err.split(":", 1)[0].strip()
            if name.endswith(tuple(SUPPORTED_EXTENSIONS)) or "." in name:
                failed_names.add(name)
        cache_only_error = bool(result.errors) and not failed_names and result.installed

        if cache_only_error or not failed_names:
            self.selected_files = []
            self.file_labels = {}
        else:
            keep = [p for p in self.selected_files if p.name in failed_names]
            removed_labels = {p.name for p in self.selected_files} - {p.name for p in keep}
            for name in removed_labels:
                self.file_labels.pop(name, None)
            self.selected_files = keep
        self.refresh_list()

        self.status.set_text(
            _("Installed: {} | Skipped: {} | Errors: {}").format(
                len(result.installed), len(result.skipped), len(result.errors)
            )
        )

        report = [
            _("Installed fonts: {}").format(len(result.installed)),
            _("Already existing: {}").format(len(result.skipped)),
            _("Errors: {}").format(len(result.errors)),
        ]
        if result.installed:
            report.append(_("\nInstalled:\n") + "\n".join(result.installed))
        if result.skipped:
            report.append(_("\nAlready existing:\n") + "\n".join(result.skipped))
        if result.errors:
            report.append(_("\nProblems:\n") + "\n".join(result.errors))

        self.show_message("\n".join(report), error=bool(result.errors))

    def open_font_folder(self, _button):
        folder = get_default_font_dir()
        folder.mkdir(parents=True, exist_ok=True)
        try:
            # Uses the OpenURI portal under Flatpak — no xdg-open needed.
            Gtk.show_uri_on_window(
                self, folder.as_uri(), Gtk.get_current_event_time()
            )
        except Exception as exc:  # noqa: BLE001 — show any failure to the user
            self.show_message("{}\n\n{}".format(folder, exc), error=True)


def main():
    window = FontEasy()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
