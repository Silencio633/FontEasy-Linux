# FontEasy

Instala fontes no Linux sem complicações. Escolhe ficheiros `.ttf`, `.otf`, `.ttc` ou `.otc`
(ou arrasta-os para a janela), pré-visualiza a família/estilo via Fontconfig e instala em
`~/.local/share/fonts` com atualização da cache (`fc-cache -f`).

![GTK3 + Python + Fontconfig](https://img.shields.io/badge/GTK3-Python-fontconfig-blue)

## Dependências (Ubuntu/Debian)

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 fontconfig xdg-utils
pip install -r requirements.txt
```

## Correr (a partir do código)

```bash
PYTHONPATH=src python3 -m fonteasy
```

## Distribuição — instalar noutros sistemas

Gera os artefactos (não requer root):

```bash
./packaging/build-deb.sh       # dist/fonteasy_0.2.0-1_all.deb
./packaging/build-tarball.sh   # dist/fonteasy-0.2.0.tar.gz
```

| Artefacto | Para quem | Como instalar |
|---|---|---|
| `.deb` | Debian/Ubuntu e derivados | `sudo apt install ./dist/fonteasy_0.2.0-1_all.deb` (traz `python3-gi`, `gir1.2-gtk-3.0`, `fontconfig` como dependências) |
| `.tar.gz` + `install.sh` | Qualquer distro com Python 3.10+, GTK3 e fontconfig | `tar -xzf fonteasy-0.2.0.tar.gz && cd fonteasy-0.2.0 && ./install.sh` (modo `--user`, sem root; `--system` com root; `--uninstall` remove) |
| Manifesto Flatpak | Qualquer distro com Flatpak (Flathub) | `flatpak-builder --install build-dir packaging/org.fonteasy.FontEasy.json` (requer `flatpak-builder` + SDK GNOME 45; **build ainda não executado nesta máquina**) |

Todos os formatos instalam o lançador `fonteasy`, a entrada de menu
(`org.fonteasy.FontEasy.desktop`), o ícone e os metadados AppStream.

## Funcionalidades

- Seleção múltipla + arrastar-e-largar (`text/uri-list`).
- Validação real com `fc-scan` (não só a extensão): rejeita ficheiros corruptos, vazios,
  > 50 MiB e symlinks.
- Mostra `Família — Estilo` por ficheiro na lista.
- Nunca sobrescreve: destinos existentes vão para "Ignoradas".
- Sanitiza pelo nome base (`Path.name`), sem path traversal.
- Botões Limpar (com confirmação), remover por linha e "Abrir pasta de fontes".
- Após copiar, corre `fc-cache -f`; falhas da cache são reportadas sem esconder o sucesso da cópia.
- Mantém na lista os ficheiros com erro para nova tentativa.

## Estrutura

```
src/fonteasy/         pacote Python (main.py = UI GTK3, installer.py, font_validator.py)
tests/                pytest (15 testes)
assets/               .desktop, ícone SVG, metainfo AppStream
packaging/            build-deb.sh, build-tarball.sh, install.sh, manifesto Flatpak
locale/               traduções gettext (futuro)
```

## Testes

```bash
python3 -m pytest -q
```

## i18n

Textos em pt-PT com infraestrutura `gettext` pronta (`domínio fonteasy`, pasta `locale/`).
Para traduzir: `xgettext -o locale/fonteasy.pot src/fonteasy/main.py` e criar `locale/<lang>/LC_MESSAGES/fonteasy.po`.

## Licença

MIT — ver `LICENSE`.
