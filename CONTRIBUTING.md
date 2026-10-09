# Contribuir para o FontEasy

Obrigado pelo interesse! O projeto é MIT — qualquer contribuição aceite é
licenciada nos mesmos termos.

## Como contribuir

1. Faz fork e cria um branch (`git checkout -b feat/minha-melhoria`).
2. Corre os testes antes de submeter: `python3 -m pytest -q`.
3. Valida os builds se mexeste em packaging: `sh packaging/build-deb.sh`.
4. Abre um Pull Request com descrição clara do que muda e porquê.

## Regras

- Python 3.10+, linha ≤ 100 colunas.
- Lógica nova de instalação/validação deve vir com testes em `tests/`.
- Sem dependências novas sem justificação (o projeto evita peso extra).
- Textos da UI em pt-PT (a infraestrutura gettext está pronta para traduções).

## Reportar problemas

Abre um Issue com: versão (`0.2.0`), distro, passos para reproduzir e o
output relevante do terminal.
