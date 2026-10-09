"""FontEasy — instala fontes no Linux sem complicações (GTK3)."""

from __future__ import annotations

import gettext
import locale
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from fonteasy import __app_id__, __version__  # noqa: E402
from fonteasy import installer  # noqa: E402
from fonteasy.installer import get_default_font_dir  # noqa: E402

# ---------------------------------------------------------------------------
# i18n: por agora os textos estão em pt-PT; a infraestrutura gettext fica
# pronta para futuras traduções (pasta locale/ + ficheiros .po).
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
        self.file_labels: dict[str, str] = {}  # nome -> "Família — Estilo"

        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(layout)

        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>FontEasy</span>")
        layout.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label=_("Instala as tuas fontes no Linux sem complicações."))
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
            label=_("Seleciona ficheiros .TTF, .OTF, .TTC ou .OTC (ou arrasta-os para aqui).")
        )
        self.status.set_line_wrap(True)
        layout.pack_start(self.status, False, False, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        layout.pack_start(buttons, False, False, 0)

        choose_button = Gtk.Button(label=_("Escolher fontes"))
        choose_button.connect("clicked", self.choose_fonts)
        buttons.pack_start(choose_button, True, True, 0)

        clear_button = Gtk.Button(label=_("Limpar"))
        clear_button.connect("clicked", self.clear_selection)
        buttons.pack_start(clear_button, True, True, 0)

        install_button = Gtk.Button(label=_("Instalar fontes"))
        install_button.get_style_context().add_class("suggested-action")
        install_button.connect("clicked", self.install_fonts)
        buttons.pack_start(install_button, True, True, 0)

        folder_button = Gtk.Button(label=_("Abrir pasta de fontes"))
        folder_button.connect("clicked", self.open_font_folder)
        buttons.pack_start(folder_button, True, True, 0)

    # -- diálogos ---------------------------------------------------------
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

    # -- seleção ----------------------------------------------------------
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
            title=_("Selecionar fontes"),
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            _("Cancelar"), Gtk.ResponseType.CANCEL,
            _("Selecionar"), Gtk.ResponseType.ACCEPT,
        )
        dialog.set_select_multiple(True)

        file_filter = Gtk.FileFilter()
        file_filter.set_name(_("Ficheiros de fontes"))
        for extension in sorted(SUPPORTED_EXTENSIONS):
            file_filter.add_pattern(f"*{extension}")
            file_filter.add_pattern(f"*{extension.upper()}")
        dialog.add_filter(file_filter)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            self.add_files([Path(n) for n in dialog.get_filenames()])
        dialog.destroy()

    def add_files(self, candidates: list[Path]):
        """Valida com fc-scan e adiciona apenas fontes reais."""
        added, invalid, duplicated = 0, [], 0
        known = {p.resolve() if p.exists() else p for p in self.selected_files}

        for candidate in candidates:
            key = candidate.resolve() if candidate.exists() else candidate
            if key in known:
                duplicated += 1
                continue
            ok, info = installer.validate_source(candidate)
            if not ok:
                invalid.append(f"{candidate.name}: {info}")
                continue
            self.selected_files.append(candidate)
            self.file_labels[candidate.name] = info
            known.add(key)
            added += 1

        self.refresh_list()

        parts = []
        if added:
            parts.append(_(f"{added} fonte(s) adicionada(s)."))
        if duplicated:
            parts.append(_(f"{duplicated} já estava(m) na lista."))
        if invalid:
            parts.append(_(f"{len(invalid)} ficheiro(s) inválido(s) — ver detalhes."))
        self.status.set_text(" ".join(parts) if parts else _("Nenhum ficheiro novo."))

        if invalid:
            self.show_message(
                _("Os seguintes ficheiros foram ignorados:\n\n") + "\n".join(invalid),
                error=True,
            )

    def remove_file(self, file_path: Path):
        self.selected_files = [p for p in self.selected_files if p != file_path]
        self.file_labels.pop(file_path.name, None)
        self.refresh_list()
        self.status.set_text(_(f"{len(self.selected_files)} fonte(s) na lista."))

    def clear_selection(self, _button=None):
        if not self.selected_files:
            return
        if self.confirm(_("Limpar a lista de fontes selecionadas?")):
            self.selected_files = []
            self.file_labels = {}
            self.refresh_list()
            self.status.set_text(_("Lista limpa."))

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
                # escape manual para evitar injeção de Pango Markup
                import html

                label.set_markup(
                    f"<b>{html.escape(file_path.name)}</b>\n"
                    f"<small>{html.escape(info)}</small>"
                )
            else:
                label.set_text(file_path.name)
            box.pack_start(label, True, True, 0)

            remove = Gtk.Button(label="✕")
            remove.set_tooltip_text(_("Remover da lista"))
            remove.connect("clicked", lambda _b, p=file_path: self.remove_file(p))
            box.pack_start(remove, False, False, 0)

            row.add(box)
            self.list_box.add(row)

        self.list_box.show_all()

    # -- instalação --------------------------------------------------------
    def install_fonts(self, _button):
        if not self.selected_files:
            self.show_message(
                _("Primeiro, seleciona pelo menos uma fonte."),
                error=True,
            )
            return

        font_dir = get_default_font_dir()
        result = installer.install_font_files(list(self.selected_files), font_dir)

        # Mantém na lista apenas o que falhou, para permitir nova tentativa.
        failed_names = set()
        for err in result.errors:
            # erros de cache não têm prefixo de ficheiro
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
            _(f"Instaladas: {len(result.installed)} | "
              f"Ignoradas: {len(result.skipped)} | "
              f"Erros: {len(result.errors)}")
        )

        report = [
            _(f"Fontes instaladas: {len(result.installed)}"),
            _(f"Fontes já existentes: {len(result.skipped)}"),
            _(f"Erros: {len(result.errors)}"),
        ]
        if result.installed:
            report.append(_("\nInstaladas:\n") + "\n".join(result.installed))
        if result.skipped:
            report.append(_("\nJá existentes:\n") + "\n".join(result.skipped))
        if result.errors:
            report.append(_("\nProblemas:\n") + "\n".join(result.errors))

        self.show_message("\n".join(report), error=bool(result.errors))

    def open_font_folder(self, _button):
        folder = get_default_font_dir()
        folder.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["xdg-open", str(folder)],
                check=False,
                capture_output=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
            self.show_message(f"{folder}\n\n{exc}", error=True)


def main():
    window = FontEasy()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
