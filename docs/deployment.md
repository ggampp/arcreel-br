# Notas complementares de deploy

Este documento complementa detalhes de deploy não cobertos em [`getting-started.md`](getting-started.md), voltado principalmente a ops e desenvolvedores que já sobem o ArcReel com Docker / localmente.

## Dependências do sandbox do Agent

Na subida, o ArcReel faz checagem estrita de segurança — se a ferramenta de sandbox estiver ausente, a subida é recusada.

| Ambiente | Ferramenta | Instalação |
|---|---|---|
| macOS | `sandbox-exec` | Já vem no sistema; nada a instalar |
| Desenvolvimento local Linux | `bwrap` + `socat` | `sudo apt install bubblewrap socat` (Ubuntu/Debian) / `sudo dnf install bubblewrap socat` (Fedora) / `sudo pacman -S bubblewrap socat` (Arch) |
| Docker | `bwrap` + `socat` | Já inclusos no Dockerfile |

Se a subida falhar, o server imprime mensagem de erro clara; instale conforme o aviso.

**Nota de migração de `.env`**: o design do sandbox exige que o `os.environ` do processo pai **não** contenha nenhuma chave de provider.
Mova as keys abaixo do `.env` para a página de configuração do sistema na WebUI:

- `ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` e demais ANTHROPIC_*
- `ARK_API_KEY` / `XAI_API_KEY` / `GEMINI_API_KEY` / `VIDU_API_KEY` / `DASHSCOPE_API_KEY` / `MINIMAX_API_KEY` / `OPENAI_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS` (credenciais Vertex continuam em `vertex_keys/`)

Se a checagem de subida achar essas keys ainda no env, o server recusa subir e pede a limpeza.
