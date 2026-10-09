#!/bin/sh
# Instalador do tarball FontEasy. Não requer root no modo --user (predefinição).
#
#   ./install.sh              instala em ~/.local
#   ./install.sh --system     instala em /usr/local (requer root)
#   ./install.sh --uninstall  remove a instalação --user
set -eu

MODE="user"
if [ "${1:-}" = "--system" ]; then MODE="system"; fi
if [ "${1:-}" = "--uninstall" ]; then MODE="uninstall"; fi

if [ "$MODE" = "system" ]; then
  PREFIX="/usr/local"
  LIBDIR="$PREFIX/lib/fonteasy"
  BINDIR="$PREFIX/bin"
  APPDIR="$PREFIX/share/applications"
  ICONDIR="$PREFIX/share/icons/hicolor/scalable/apps"
else
  PREFIX="$HOME/.local"
  LIBDIR="$PREFIX/lib/fonteasy"
  BINDIR="$PREFIX/bin"
  APPDIR="$PREFIX/share/applications"
  ICONDIR="$PREFIX/share/icons/hicolor/scalable/apps"
fi

if [ "$MODE" = "uninstall" ]; then
  rm -rf "$HOME/.local/lib/fonteasy" "$HOME/.local/bin/fonteasy" \
    "$HOME/.local/share/applications/io.github.Silencio633.FontEasy.desktop" \
    "$HOME/.local/share/icons/hicolor/scalable/apps/io.github.Silencio633.FontEasy.svg"
  echo "FontEasy removido de $HOME/.local."
  exit 0
fi

# Dependências de sistema (informativo; não instala sem root).
for cmd in python3 fc-scan fc-cache; do
  command -v "$cmd" >/dev/null 2>&1 || echo "AVISO: '$cmd' não encontrado (pacote fontconfig/python3)."
done
python3 -c "import gi" 2>/dev/null || echo "AVISO: python3-gi em falta (apt: python3-gi gir1.2-gtk-3.0)."

mkdir -p "$LIBDIR" "$BINDIR" "$APPDIR" "$ICONDIR"
cp -r src/fonteasy "$LIBDIR/"
find "$LIBDIR" -name "__pycache__" -type d -prune -exec rm -rf {} +

cat > "$BINDIR/fonteasy" <<EOF
#!/bin/sh
exec /usr/bin/python3 -c "import sys; sys.path.insert(0, '$LIBDIR'); from fonteasy.main import main; main()" "\$@"
EOF
chmod 755 "$BINDIR/fonteasy"

cp assets/io.github.Silencio633.FontEasy.desktop "$APPDIR/"
cp assets/io.github.Silencio633.FontEasy.svg "$ICONDIR/"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPDIR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t "$PREFIX/share/icons/hicolor" || true

echo "FontEasy instalado em $PREFIX. Executa: fonteasy"
case ":$PATH:" in
  *":$BINDIR:"*) ;;
  *) echo "NOTA: $BINDIR não está no PATH. Adiciona: export PATH=\"\$PATH:$BINDIR\"" ;;
esac
