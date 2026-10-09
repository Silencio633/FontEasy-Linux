#!/bin/sh
# Constrói o pacote .deb (não requer root).
# Uso: ./packaging/build-deb.sh   -> dist/fonteasy_0.2.0-1_all.deb
set -eu

ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
VERSION="0.2.0"
REVISION="1"
PKGDIR="$ROOT/packaging/deb-stage/fonteasy_${VERSION}-${REVISION}_all"

rm -rf "$PKGDIR"
mkdir -p \
  "$PKGDIR/DEBIAN" \
  "$PKGDIR/usr/lib/python3/dist-packages" \
  "$PKGDIR/usr/bin" \
  "$PKGDIR/usr/share/applications" \
  "$PKGDIR/usr/share/icons/hicolor/scalable/apps" \
  "$PKGDIR/usr/share/metainfo" \
  "$ROOT/dist"

cp -r "$ROOT/src/fonteasy" "$PKGDIR/usr/lib/python3/dist-packages/fonteasy"
find "$PKGDIR/usr/lib/python3/dist-packages/fonteasy" -name "__pycache__" -type d -prune -exec rm -rf {} +

cat > "$PKGDIR/usr/bin/fonteasy" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 -m fonteasy "$@"
EOF
chmod 755 "$PKGDIR/usr/bin/fonteasy"

cp "$ROOT/assets/io.github.Silencio633.FontEasy.desktop" "$PKGDIR/usr/share/applications/"
cp "$ROOT/assets/io.github.Silencio633.FontEasy.svg" "$PKGDIR/usr/share/icons/hicolor/scalable/apps/"
cp "$ROOT/assets/io.github.Silencio633.FontEasy.metainfo.xml" "$PKGDIR/usr/share/metainfo/"

cat > "$PKGDIR/DEBIAN/control" <<EOF
Package: fonteasy
Version: ${VERSION}-${REVISION}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0, fontconfig, xdg-utils
Maintainer: silenciosiquela <silenciosiquela@gmail.com>
Description: Instala fontes no Linux sem complicações
 Escolhe ficheiros .ttf/.otf/.ttc/.otc, pré-visualiza a família e o
 estilo via Fontconfig e instala em ~/.local/share/fonts.
 .
 Interface GTK3 em Python.
EOF

dpkg-deb --build "$PKGDIR" "$ROOT/dist/fonteasy_${VERSION}-${REVISION}_all.deb"
echo "OK: $ROOT/dist/fonteasy_${VERSION}-${REVISION}_all.deb"
dpkg-deb -c "$ROOT/dist/fonteasy_${VERSION}-${REVISION}_all.deb"
