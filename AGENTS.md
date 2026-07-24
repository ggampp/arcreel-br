# ArcReel

ArcReel é uma plataforma de geração de vídeo com IA que transforma romances em short videos. Arquitetura em três camadas:

```
frontend/ (React SPA)  →  server/ (FastAPI)  →  lib/ (biblioteca core)
  React 19 + Tailwind       roteamento + SSE
  roteamento wouter         agent_runtime/
  estado zustand            (Claude Agent SDK)
```

## Idioma / Language
- **Respostas ao usuário em português brasileiro (pt-BR)**: todas as respostas, listas de tarefas e arquivos de plano devem ser em português do Brasil.
- **UI i18n da plataforma**: apenas `pt` (padrão) e `en` — ver `lib/i18n/` e `frontend/src/i18n/`.
- Código, identificadores e commits seguem as convenções do repositório (Conventional Commits em inglês quando aplicável ao fluxo do projeto).

## Comandos de desenvolvimento

```bash
# Backend
# Subir o servidor de desenvolvimento (use --reload-dir para limitar a vigilância; senão o watchfiles
# varre node_modules / .venv / .git / .worktrees e centenas de milhares de arquivos, CPU ~50%+ em um núcleo)
uv run uvicorn server.app:app --reload --reload-dir server --reload-dir lib --port 1241

uv run python -m pytest                              # testes (-v arquivo único / -k keyword / --cov cobertura)
uv run ruff check . && uv run ruff format .          # lint + format
uv run basedpyright                                  # typecheck (CI exige 0 error)
uv sync                                              # instalar deps
uv run alembic upgrade head                          # migrações de banco
uv run alembic revision --autogenerate -m "desc"     # gerar migração

# Frontend — primeiro cd frontend
pnpm lint        # ESLint, 1ª etapa do CI frontend-tests, inclui jsx-a11y
pnpm check       # typecheck + vitest
pnpm build       # build de produção, com typecheck
# Equivalente CI: pnpm lint && pnpm check — ambos verdes antes do push
```

## Pontos de arquitetura

### Rotas da API de backend

Todas as APIs sob `/api/v1`, definidas em `server/routers/`:
- `projects.py` — CRUD de projetos, geração de overview
- `generate.py` — geração de storyboard/vídeo/personagem/cena/prop (enfileira na fila de tarefas)
- `assistant.py` — gestão de sessões Claude Agent SDK (stream SSE)
- `agent_chat.py` — interação de chat do agente
- `tasks.py` — status da fila de tarefas (stream SSE)
- `project_events.py` — push SSE de eventos do projeto
- `files.py` — upload de arquivos e assets estáticos
- `versions.py` — histórico de versões de recursos e rollback
- `characters.py` / `scenes.py` / `props.py` — CRUD de ativos de projeto (**gerados unificadamente por `_asset_router_factory.build_asset_router()`**, dirigidos por `lib/asset_types.ASSET_SPECS`; para novo tipo de ativo, basta registrar no spec)
- `assets.py` — biblioteca global de ativos (character/scene/prop reutilizáveis entre projetos; DB na tabela `assets`)
- `reference_videos.py` — reference-video→vídeo (parse por take + enfileirar)
- `usage.py` — estatísticas de uso de API
- `cost_estimation.py` — estimativa de custo (projeto/episódio/take)
- `grids.py` — geração, listagem, detalhe e regeneração de grid
- `auth.py` / `api_keys.py` — autenticação e gestão de API keys
- `system_config.py` — configuração do sistema
- `system.py` — endpoints de sistema: download de pacote de logs de diagnóstico (`/system/logs/download`)
- `agent_config.py` — credenciais Anthropic do Agent + catálogo de fornecedores pré-definidos (prefixo `/api/v1/agent`)
- `providers.py` — gestão de config de fornecedores pré-definidos (lista, leitura/escrita, teste de conexão)
- `custom_providers.py` — CRUD de fornecedores customizados, gestão e descoberta de modelos, teste de conexão

### server/services/ — camada de serviços de negócio

- `generation_tasks.py` — orquestração de tarefas de geração storyboard/vídeo/personagem/cena/prop
- `reference_video_tasks.py` — orquestração de reference-video→vídeo
- `project_archive.py` — exportação de projeto (ZIP)
- `project_cover.py` — geração de capa do projeto
- `project_events.py` — publicação de eventos de mudança do projeto
- `jianying_draft_service.py` — exportação de rascunho CapCut/Jianying
- `cost_estimation.py` — cálculo de estimativa e agregação de custo real
- `resolution_resolver.py` — resolução de resolução de vídeo (adaptação por capacidade do provider)
- `resume_executor.py` — entrada do worker `_process_resume_task`; poll de jobs no lado do provider (não passa pelo pipeline de vídeo normal; só reutiliza helpers de finalize para gravar ativos)
- `diagnostics.py` — coleta de diagnóstico do sistema com dados sensíveis redigidos, para o pacote de `/system/logs/download`

### lib/ — módulos core

- **{gemini,ark,grok,openai,vidu,dashscope}_shared** + **httpx_shared** — factories de SDK e utilitários compartilhados por fornecedor
- **image_backends/** / **video_backends/** / **text_backends/** — backends de mídia multi-fornecedor, padrão Registry + Factory (vidu só image/video; video ainda tem relay newapi)
- **custom_provider/** — suporte a fornecedor customizado: wrapper de backend, descoberta de modelos, factory (compatível OpenAI/Google)
- **MediaGenerator** (`media_generator.py`) — compõe backend + VersionManager + UsageTracker
- **GenerationQueue** (`generation_queue.py`) — fila assíncrona, backend SQLAlchemy ORM, controle de concorrência lease-based
- **GenerationWorker** (`generation_worker.py`) — worker em background, dois canais de concorrência image/video
- **ProjectManager** (`project_manager.py`) — operações de filesystem e dados do projeto
- **StatusCalculator** (`status_calculator.py`) — calcula campos de status na leitura, sem estado redundante armazenado
- **UsageTracker** (`usage_tracker.py`) / **CostCalculator** (`cost_calculator.py`) — rastreio de uso e cálculo de custo
- **TextGenerator** (`text_generator.py`) / **ScriptGenerator** (`script_generator.py`) — geração de texto e roteiro
- **asset_types.py** — spec unificado das três classes character/scene/prop (`ASSET_SPECS`), dirige factory de rotas, bucket key, campos de sheet, whitelist de PATCH
- **source_loader/** — importação de fontes de romance (txt/docx/epub/pdf), interface unificada `loader`
- **reference_video/** — reference-video→vídeo: `shot_parser` parseia prompt por take + `limits` de capacidade
- **grid/** — sistema de grid: layout (grid_4/6/9), construção de prompt, corte
- **agent_session_store/** — espelho de transcript do Claude Agent SDK no DB (store + import_local)
- **retry** (`retry.py`) — decorator genérico de retry com backoff exponencial, reutilizado pelos backends

### lib/config/ — sistema de config de fornecedores

ConfigService (`service.py`) → Repository (persistência + redaction de secrets) → Resolver. `registry.py` mantém o registro de pré-definidos (`PROVIDER_REGISTRY`).

### lib/db/ — camada SQLAlchemy Async ORM

- `engine.py` — engine assíncrono + session factory (`DATABASE_URL` padrão `sqlite+aiosqlite`)
- `models/` — modelos ORM: Task / ApiCall / ApiKey / AgentSession (`session.py`) / Config / Credential / User / CustomProvider (com subtabela de modelos) / **Asset** (biblioteca global)
- `repositories/` — Repository assíncrono: Task / Usage / Session / ApiKey / Credential (multi API Key + chave ativa) / CustomProvider / **Asset**

Banco: desenvolvimento SQLite (`projects/.arcreel.db`), produção PostgreSQL (`asyncpg`)

### Agent Runtime (integração Claude Agent SDK)

`server/agent_runtime/` encapsula o Claude Agent SDK:
- `AssistantService` (`service.py`) — orquestra sessões do Claude SDK
- `SessionManager` — ciclo de vida da sessão + padrão de assinantes SSE
- `SessionActor` (`session_actor.py`) — um asyncio task dedicado por sessão, serializa todas as chamadas ClaudeSDKClient (spec: `docs/superpowers/specs/2026-04-13-session-actor-design.md`)
- `SessionStore` (`session_store.py`) — metadados de sessão + espelho de transcript no DB (controlado por `ARCREEL_SDK_SESSION_STORE`: `db`/`off`; off volta ao caminho jsonl do SDK)
- `StreamProjector` — constrói a resposta do assistente em tempo real a partir dos eventos de stream
- `sdk_transcript_adapter` / `turn_schema` — leitura de transcript e normalização de Turn (replay de histórico)
- `sdk_tools/` — ferramentas MCP in-process do SDK (enqueue_assets/grid/storyboards/videos + text_generation), para Skills, injetadas pelo agent profile manifest

### lib/i18n/ — internacionalização

Camada de tradução do backend, idiomas `pt` (Português Brasil) / `en`. Em `{pt,en}/` os arquivos são namespaces: `errors` (erros e validação), `providers` (nomes/descrições de fornecedores), `assets` (mensagens de ativos), `emails` (templates de e-mail), `system` (mensagens de sistema), `templates` (mensagens de template).
- Tipo `Translator` = `Annotated[Callable[..., str], Depends(get_translator)]`, idioma a partir de `Accept-Language`
- Nas rotas, injete `_t: Translator` e chame `_t("key", param=value)`

### Frontend

- React 19 + TypeScript + Tailwind CSS 4
- Roteamento: `wouter` (não React Router)
- Estado: `zustand` (stores em `frontend/src/stores/`)
- Alias de path: `@/` → `frontend/src/`
- Proxy Vite: `/api` → `http://127.0.0.1:1241`
- i18n: `i18next` + `react-i18next`, arquivos em `frontend/src/i18n/{pt,en}/` (padrão pt-BR), namespaces `common`/`dashboard`/`auth`/`errors`/`assets`/`templates`

## Padrões de design-chave

### Camadas de dados

| Tipo de dado | Onde fica | Estratégia |
|---------|---------|------|
| Definições de personagem/cena/prop | `project.json` (projeto) + tabela `assets` (biblioteca global) | Fonte única de verdade; o roteiro só referencia nomes; as três classes compartilham a abstração `lib/asset_types.ASSET_SPECS` |
| Metadados de episódio (episode/title/script_file) | `project.json` | sincronizados na escrita ao salvar o roteiro |
| Campos estatísticos (scenes_count / status / progress) | não armazenados | `StatusCalculator` injeta na leitura |

### Comunicação em tempo real

- Assistente: `/api/v1/assistant/sessions/{id}/stream` — resposta em stream SSE
- Eventos de projeto: `/api/v1/projects/{name}/events/stream` — push SSE de mudanças
- Fila de tarefas: o frontend faz poll em `/api/v1/tasks` para status

### Fila de tarefas

Todas as tarefas de geração (storyboard/vídeo/personagem/cena/prop/reference-video) entram na GenerationQueue e são processadas assincronamente pelo GenerationWorker (canais independentes image / video).
`generation_queue_client.py` → `enqueue_and_wait()` encapsula enfileirar + aguardar conclusão.

### Modelos Pydantic

`lib/script_models.py` define `NarrationSegment` e `DramaScene` para validação de roteiro.
`lib/data_validator.py` valida a estrutura e a integridade de referências de `project.json` e JSON de episódio.

### content_mode e generation_mode

Duas dimensões independentes — «tipo de conteúdo» e «origem do vídeo»:

- **content_mode** — `narration` (narração, divide segmentos pelo ritmo de leitura) / `drama` (animação seriada, organiza por cena/diálogo). Define a estrutura de roteiro em `lib/script_models.py` (`NarrationSegment` vs `DramaScene`) e qual variante `CLAUDE.*.md` o agent profile carrega
- **generation_mode** — `reference_video` etc. Define o caminho de geração de vídeo: imagem→vídeo (padrão, storyboard-driven) / grid→vídeo (grid_4/6/9 como frames inicial/final) / reference→vídeo (imagens de ativos direto, sem storyboard; ver `lib/reference_video/`)
- Ambos os campos ficam ocultos ao LLM (`SkipJsonSchema`) e são injetados pela camada de orquestração; não deixe Skill/Subagent inferirem sozinhos

## Sandbox do Agent

Em Linux/macOS, por padrão o bwrap isola as chamadas de ferramentas do Agent (whitelist de filesystem/rede/subprocessos),
detectado e habilitado por `server/app.py::check_sandbox_available`. Ao escrever novas ferramentas de Agent, assuma o sandbox **ligado por padrão**:
paths fora do permitido e requests de saída serão rejeitados; declare permissões quando necessário.

Windows nativo não tem bwrap e rebaixa automaticamente:

- `check_sandbox_available` retorna False; a ferramenta Bash do Agent usa a whitelist de código `_WINDOWS_BASH_PREFIX_WHITELIST`
  (mais grossa que o sandbox; poucos prefixos passam). Deploy em WSL2/Docker mantém o sandbox completo
- Se a nova ferramenta depender de capacidades só no sandbox (ex.: bind mount isolando cwd), documente o caminho de rebaixamento no Windows
  ou recuse explicitamente quando `check_sandbox_available()` falhar, em vez de liberar em silêncio

## Runtime do agente

Config dedicada do agente fica em `agent_runtime_profile/`, fisicamente separada do `.claude/` de desenvolvimento:

- `.claude/skills/` `.claude/agents/` — definições de Skill e Subagent
- `CLAUDE.narration.md` / `CLAUDE.drama.md` — variantes de system prompt por `content_mode`, injetadas dinamicamente no runtime
- sincronização do profile por `lib/profile_manifest.py` via manifest + sha256: só copia arquivos declarados e validados, evitando sujeira local no projeto

Criação, avaliação e manutenção de Skills: skill `/skill-creator`.

- **SKILL.md e scripts em sincronia**: ao mudar scripts da skill, atualize o SKILL.md e vice-versa; os dois devem permanecer consistentes

## Normas de i18n

- Proibido hardcode de strings voltadas ao usuário; texto novo precisa de key `pt`/`en` (UI só português do Brasil e inglês)
- **Só texto voltado ao usuário precisa de i18n**: respostas de router / e-mail / frontend passam pelo Translator; strings só para o agent (retorno de MCP tool, agent prompt, exceções de service, logger) estão isentas — não crie key de tradução para elas
- Backend: injeção `_t: Translator`; frontend: `useTranslation("namespace")`
- CI: `tests/test_i18n_consistency.py` garante que keys pt/en não divergem

## Configuração de ambiente

Copie `.env.example` para `.env` e defina parâmetros de auth (`AUTH_USERNAME`/`AUTH_PASSWORD`/`AUTH_TOKEN_SECRET`).
API Key, escolha de backend, modelos etc. são geridos na página WebUI (`/settings`).
Dependência externa: `ffmpeg` (concatenação e pós-processamento de vídeo).

## Compatibilidade Windows

A plataforma principal de desenvolvimento é macOS / Linux, mas o server deve conseguir criar projetos e fluxos básicos no Windows. Código novo que toque filesystem, subprocessos, paths tmp ou permissões deve seguir:

- **Constantes POSIX-only de `os`** — `O_NOFOLLOW` / `O_DIRECT` etc. com `getattr(os, "O_NOFOLLOW", 0)`, fallback Python `is_symlink()` (ex.: `lib/profile_manifest.py::_project_lock`)
- **`os.chmod(0o600)`** — envolva em `if os.name == "posix":`; no Windows a proteção de credenciais fica com ACL (`%LOCALAPPDATA%` do usuário)
- **I/O de arquivo com `encoding="utf-8"` explícito** — senão o padrão Windows cp936/cp1252 corrompe texto UTF-8
- **tmp com `tempfile.gettempdir()`** — não hardcode `/tmp`; ao casar saídas tmp do Claude SDK, liste tempdir e aliases POSIX
- **subprocess com `create_subprocess_exec` (forma de lista)** — evite `shell=True`; ffmpeg/ffprobe: primeiro `shutil.which()`, rebaixe se ausente em vez de falhar duro
- **Sandbox Windows rebaixado automaticamente** — Bash volta para whitelist `_WINDOWS_BASH_PREFIX_WHITELIST`; em produção ainda se recomenda WSL2/Docker
- **Paths longos** — Windows 10 1607+ precisa de `LongPathsEnabled=1` para levantar o limite MAX_PATH (260)

### Qualidade de código

- **ruff**: line-length 120; antes do commit, nos arquivos Python alterados: `uv run ruff check <files> && uv run ruff format <files>`
- **basedpyright**: modo standard + `reportMissingTypeStubs = false`, CI exige 0 error, pre-push hook roda scan completo; localmente `uv run basedpyright`. Em tests/, `reportOptional*` e série `unknown*` rebaixados a warning para reduzir ruído de mocks; libs de terceiros sem tipos (ffmpeg-python, pyJianYingDraft, volcenginesdkarkruntime, xai_sdk.chat, docx2txt/mammoth/ebooklib) com `# pyright: ignore[...]` por linha
- **pytest**: `asyncio_mode = "auto"`, cobertura CI ≥80%, fixtures compartilhadas em `tests/conftest.py`
- **consistência i18n**: `tests/test_i18n_consistency.py` garante keys pt/en; novas keys precisam dos dois idiomas
- **gestão de deps**: novas/atualizações de deps sempre com `uv add` / `pnpm add` (não edite versões à mão em pyproject.toml / package.json); após adicionar, sincronize patterns de `.github/dependabot.yml` no grupo certo, evitando o fallback all-other
- **commits e PRs**: títulos em Conventional Commits (`type(scope): resumo`; types e categorias de changelog em `CONTRIBUTING.md` / `.release-please-config.json`). Com squash merge o título vira a entrada do changelog — escreva benefício perceptível ao usuário, termos de produto no scope, sem jargão de implementação (status_code, nomes de classes internas) e com escopo honesto; ao corrigir, mude só o título, não faça amend do commit

## Agent skills

### Issue tracker

Issues e Specs são rastreados nos GitHub Issues de `ArcReel/ArcReel`, sempre via CLI `gh`. Specs usam label `Spec` + prefixo de título `Spec:`; issues de implementação terminam com `[Spec #N]` e viram sub-issue nativa. Detalhes em `docs/agents/issue-tracker.md`.

### Triage labels

A máquina de estados de triage usa cinco labels padrão: `needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`, mais `parked` para issues deliberadamente postergadas. Detalhes em `docs/agents/triage-labels.md`.

### Domain docs

Layout de contexto único: `CONTEXT.md` na raiz + `docs/adr/`. Detalhes em `docs/agents/domain.md`.
