#!/bin/sh
# Constrói um tarball portátil + instalador.
# Uso: ./packaging/build-tarball.sh   -> dist/fonteasy-0.2.0.tar.gz
set -eu

ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
VERSION="0.2.0"
STAGE="$ROOT/packaging/tarball-stage/fonteasy-$VERSION"

rm -rf "$STAGE" "$ROOT/dist/fonteasy-$VERSION.tar.gz"
mkdir -p "$STAGE" "$ROOT/dist"

cp -r "$ROOT/src" "$STAGE/src"
cp -r "$ROOT/assets" "$STAGE/assets"
cp "$ROOT/packaging/install.sh" "$STAGE/install.sh"
cp "$ROOT/README.md" "$STAGE/README.md"
cp "$ROOT/LICENSE" "$STAGE/LICENSE"
cp "$ROOT/requirements.txt" "$STAGE/requirements.txt"
find "$STAGE" -name "__pycache__" -type d -prune -exec rm -rf {} +

tar -czf "$ROOT/dist/fonteasy-$VERSION.tar.gz" -C "$ROOT/packaging/tarball-stage" "fonteasy-$VERSION"
echo "OK: $ROOT/dist/fonteasy-$VERSION.tar.gz"
tar -tzf "$ROOT/dist/fonteasy-$VERSION.tar.gz"
