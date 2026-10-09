# Publicar no Flathub — guia

## Estado atual (2026-10-09)

| Requisito | Estado |
|---|---|
| ID `io.github.Silencio633.FontEasy` (prefixo code-hosting, 4 componentes) | OK — revê nota abaixo sobre `FontEasy` vs repo `FontEasy-Linux` |
| UI em inglês | OK |
| Metainfo válido (`appstreamcli validate`) | OK (só infos + 1 pedantic não-fatal) |
| `.desktop` válido | OK |
| Ícone SVG nomeado pelo ID | OK |
| Screenshot real no metainfo (via tag, não branch) | OK após push da tag `v0.2.0` |
| Manifesto `packaging/io.github.Silencio633.FontEasy.json` (runtime GNOME 50, permissões mínimas) | OK — `sha256` da release v0.2.0 preenchido e verificado; **requer revisão humana antes de submeter (ver "Nota sobre IA")** |
| Permissões: `wayland`, `fallback-x11`, `ipc`, `xdg-data/fonts` | OK (sem `--share=network`; "abrir pasta" usa portal `Gtk.show_uri`) |
| Release estável com tag (`v0.2.0`) | POR FAZER |
| Build local testado (`org.flatpak.Builder`) | POR FAZER — sem `flatpak-builder` nesta máquina |
| Linter (`flatpak-builder-lint`) | POR FAZER |
| Histórico de desenvolvimento significativo | RISCO — repo novo, poucos commits; a decisão é dos revisores caso a caso |

Nota sobre o ID: o Flathub calcula `https://github.com/Silencio633/FontEasy` a
partir do ID, mas o repo chama-se `FontEasy-Linux`. Os revisores costumam aceitar
após verificação manual — menciona isto no PR.

## Nota sobre IA (política do Flathub)

Os revisores exigem que **manifestos Flathub não contenham conteúdo gerado por IA**
e que o PR de submissão seja aberto e descrito por um humano. Este manifesto foi
preparado com assistência de IA: **revê linha a linha, assume a autoria e abre o
PR tu mesmo**. Não declarar isto pode levar a rejeição ou ban.

## Passo 1 — Release v0.2.0 no GitHub

```bash
git tag -a v0.2.0 -m "FontEasy 0.2.0"
git push origin v0.2.0
# GitHub → Releases → Draft a new release → tag v0.2.0
```

## Passo 2 — sha256 no manifesto

```bash
curl -sL https://github.com/Silencio633/FontEasy-Linux/archive/refs/tags/v0.2.0.tar.gz \
  | sha256sum
# colar o hash em packaging/io.github.Silencio633.FontEasy.json (campo sha256)
```

## Passo 3 — Build + teste local

```bash
flatpak install -y flathub org.flatpak.Builder
flatpak run --command=flathub-build org.flatpak.Builder --install \
  packaging/io.github.Silencio633.FontEasy.json
flatpak run io.github.Silencio633.FontEasy
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest \
  packaging/io.github.Silencio633.FontEasy.json
```

## Passo 4 — PR de submissão

1. Fork de `flathub/flathub` (**sem** "Copy the master branch only").
2. `git clone --branch=new-pr <teu-fork> && cd flathub && git checkout -b fonteasy new-pr`.
3. Copiar o manifesto revisto para a raiz como
   `io.github.Silencio633.FontEasy.json`, commit, push.
4. Abrir PR contra o branch **`new-pr`** com título
   `Add io.github.Silencio633.FontEasy` (descrição escrita por ti).
5. Responder aos revisores; para test build comentar `bot, build`.
6. Após aprovação e merge, aceitar o convite de escrita (2FA ativo) e ler
   https://docs.flathub.org/docs/for-app-authors/maintenance.
