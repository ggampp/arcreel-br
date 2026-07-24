---
status: accepted
---

# Secrets de provider proibidos no env do processo: asserção no startup + override de env do agent + limpeza Bash env -u

Se secrets de provider entram em `os.environ`, o subprocesso do agent herda o conjunto inteiro — superfície de vazamento grande — e o valor único no nível do processo conflita com multi-credencial / troca por sessão. Decidimos que secrets só ficam no DB, com três camadas forçadas: ① asserção no startup — se `os.environ` contiver qualquer secret real de provider (`PROVIDER_SECRET_KEYS`), fail-fast e recusa subir; deploys que configuram key por variável de ambiente não sobem — deliberado; ② env do subprocesso do agent — credencial Anthropic injetada por sessão a partir do DB (ver `docs/adr/0017`); demais variáveis de provider sobrescritas com string vazia; ③ comando Bash embrulhado pelo PreToolUse hook em `env -u … sh -c`, unset dinâmico por lista fixa + padrões `*_API_KEY`/`*_AUTH_TOKEN` etc., interceptando qualquer variável sensível ainda herdada do ambiente host.

## Consequences

- Ao adicionar provider, o nome da variável de env deve ser registrado em `lib/config/env_keys.py` (asserção de startup / override de env / limpeza Bash compartilham esta lista; o scan por padrão só cobre variáveis com nome regular).
- ③ é mecanismo POSIX (depende de `env`/`sh`), só executa o wrap quando o sandbox está disponível (macOS/Linux); o hook só reescreve o comando, não decide permissão — a liberação fica nos passos seguintes da cadeia (allowed_tools). No fallback nativo Windows o hook pula o wrap; o comando original vai para o julgamento da whitelist Bash de `can_use_tool`, com três regras de recusa: match de fronteira de token (bloqueia colisão de prefixo tipo `ffmpegX`), interceptação de metachar de shell (ponto e vírgula, `&`, pipe, ângulos, backtick, `$`, newline — bloqueia cadeia/pipe/redirecionamento/substituição de comando), interceptação de path traversal `..` (incluindo formas ofuscadas com aspas `".."` e backslash `.\.` — bloqueia sair do diretório skills para rodar script arbitrário); a entrada `python` se restringe ainda mais a `.claude/skills/<skill>/scripts/<script>.py`. Em troubleshooting de ops, o texto de recusa indica qual regra bateu. As camadas ①② não dependem de plataforma.
- Complementa `docs/adr/0017`: 0017 fala de «como injetar» a credencial Anthropic; este fala de «como não vazar» secrets de todos os providers.
