# Guia de contribuição

Contribuições de código, reportes de bugs e sugestões de features são bem-vindas!

## Ambiente de desenvolvimento local

```bash
# Pré-requisitos: Python 3.12+, Node.js 20+, uv, pnpm, ffmpeg
# SO: Linux / macOS / Windows WSL2 (Windows nativo não é suportado para este fluxo)

# Instalar dependências
uv sync
cd frontend && pnpm install && cd ..

# Instalar hooks pre-commit uma vez (ruff / eslint / pull_request_target tripwire)
uv run pre-commit install

# Inicializar o banco
uv run alembic upgrade head

# Subir o backend (terminal 1)
# Atenção: use --reload-dir para limitar a vigilância; senão o watchfiles varre
# node_modules / .venv / .git / .worktrees e centenas de milhares de arquivos (CPU ~50%+ em um núcleo)
uv run uvicorn server.app:app --reload --reload-dir server --reload-dir lib --port 1241

# Subir o frontend (terminal 2)
cd frontend && pnpm dev

# Acesse http://localhost:5173
```

## Rodar testes

```bash
# Testes de backend
python -m pytest

# Typecheck + testes de frontend
cd frontend && pnpm check
```

## Qualidade de código

**Lint e format (ruff):**

```bash
uv run ruff check . && uv run ruff format .
```

- Conjunto de regras: `E`/`F`/`I`/`UP`, ignora `E402` e `E501`
- line-length: 120
- CI força: `ruff check . && ruff format --check .`

**Lint (ESLint do frontend):**

```bash
cd frontend && pnpm lint          # checar
cd frontend && pnpm lint:fix      # auto-corrigir o que for possível
```

- Config: `frontend/eslint.config.js` (flat config)
- Regras: `typescript-eslint/recommendedTypeChecked` + `react/recommended` + `react-hooks/recommended` + `jsx-a11y/recommended`
- Typed linting com `projectService: true`, cobre `no-floating-promises`, `no-misused-promises` etc.
- CI força no job `frontend-tests`, step `Lint`

### Normas de uso de eslint-disable

Após o PR 3 (#219) o projeto adota política de zero warning; todas as regras são error. Se for preciso desabilitar:

- **Formato**: `// eslint-disable-next-line <rule> -- <motivo em português ou inglês claro>`; o motivo após `--` é **obrigatório**
- **Proibido**: `/* eslint-disable */` em nível de arquivo, `// eslint-disable-line` sem motivo, combinação com `@ts-ignore`
- **PR**: novos disables devem aparecer no body do PR em tabela `rule | file:line | motivo`
- **Fechamento em nível de arquivo** só via override `files` em `eslint.config.js`, com comentário explicando o porquê
- **Motivos inaceitáveis**: «muito trabalhoso», «por enquanto», «later fix»
- **Motivos aceitáveis (exemplos)**: «referência de setter React é estável», «init só no mount», «vídeo de pré-visualização gerativo sem fonte de legenda»

**Sugestão de IDE local (não versionar no repo):**

`.vscode/` já está no `.gitignore`. Adicione `frontend/.vscode/settings.json` para o VS Code / Cursor mostrar lint em tempo real e auto-fix on save:

```json
{
  "eslint.workingDirectories": [{ "pattern": "./frontend" }],
  "editor.codeActionsOnSave": { "source.fixAll.eslint": "explicit" }
}
```

**Restrições conhecidas:**

- Lock de versão TypeScript: peer de `typescript-eslint@8.x` é `typescript <6.1`; ao subir TS para 6.1+ é preciso sincronizar `typescript-eslint`

**Cobertura de testes:**

- CI exige ≥80%
- `asyncio_mode = "auto"` (sem marcar async tests manualmente)

### Disciplina de markers do pytest

Novos testes devem ser marcados por tipo; o CI padrão roda `-m "not e2e"`:

| Marker | Significado | Proibido |
|--------|------|------|
| `unit` | Rápido, isolado, sem I/O real / serviços externos | — |
| `integration` | Colaboração entre módulos, deps reais (DB in-memory, filesystem tmp etc.) | **Proibido mockar a entrada pública do módulo sob teste** (ex.: integração de `MediaGenerator` não pode mockar `MediaGenerator.generate`, senão testa o mock) |
| `e2e` | Ponta a ponta, depende de recursos externos reais (API remota, LLM, ffmpeg pesado) | CI pula por padrão; rode local sob demanda |

Testes existentes não precisam de remarcação retroativa; a regra vale só para novos.

## Fluxo de trabalho

### Estratégia de branches (trunk-based)

- Só `main` é branch de longo prazo. Todo trabalho sai do `main` atual em branches curtas e volta via PR
- Proibido `git push origin main` direto. Mesmo branches pessoais passam por PR; revise o diff e o checklist de aceitação antes

### Convenção de nomes de branch

`<type>/<slug>`, com `type` de conventional commit:

- `feat/` — nova feature (ex.: `feat/reference-video-backend`)
- `fix/` — correção de bug (ex.: `fix/queue-lease-timeout`)
- `refactor/` — refatoração (ex.: `refactor/session-actor`)
- `docs/` — só documentação (ex.: `docs/contribution-infra`)
- `chore/` — build / tooling / versão / limpeza (ex.: `chore/freeze-versions`)
- `ci/` — config de CI (ex.: `ci/testing-discipline`)
- `test/` — só testes

`slug` em minúsculas + hífen, descrevendo o foco da branch.

### Vida curta da branch

Da criação ao merge ≤ 3 dias. Se passar, quebre o trabalho ou rebase na main — **não** arraste uma branch de 1 mês para review.

### Squash merge

Cada PR vira 1 commit em `main`, com mensagem em conventional commits (ver abaixo). No GitHub use "Squash and merge".

### Defer conhecidos

O template de PR tem a seção "known defer". Antes do merge, abra **follow-up issue** para cada item e coloque o link na descrição do PR; não deixe como «depois a gente vê».

## Convenção de commits

Mensagens no formato [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: descrição da nova funcionalidade
fix: descrição da correção
refactor: descrição da refatoração
docs: alteração de documentação
chore: alteração de build/tooling
```

## Fluxo de release

Versão e changelog são mantidos automaticamente pelo [release-please](https://github.com/googleapis/release-please) (config em `.release-please-config.json`, workflow em `.github/workflows/release-please.yml`). **Desenvolvedores não fazem bump manual de versão** — basta commits conventional válidos.

### Fluxo

1. PR squash-merged em `main` com conventional commits
2. release-please varre commits desde o último release e abre/atualiza um Release PR com título no estilo `chore(main): release X.Y.Z`, contendo o bump e o `CHANGELOG.md` atualizado
3. Merging o Release PR cria a tag `vX.Y.Z` e publica o GitHub Release

### commit type → passo de versão

| commit type | passo de versão | changelog |
|-------------|---------|-----------|
| `feat`      | minor   | ✨ Features |
| `fix`       | patch   | 🐛 Bug Fixes |
| `feat!` / qualquer type + `!` / footer com `BREAKING CHANGE:` | **major** | ⚠️ BREAKING CHANGES (topo do changelog) |
| `perf` / `refactor` / `docs` / `revert` | sem passo | exibidos (⚡ / ♻️ / 📚 / ↩️) |
| `chore` / `ci` / `build` / `test` / `style` | sem passo | ocultos |

> Por padrão o release-please só faz bump com `feat` e `fix` (e breaking changes). Marcar `perf`/`refactor`/`docs`/`revert` como `hidden: false` só afeta a apresentação do changelog, não dispara patch. Se um ciclo só tiver esses tipos, não haverá Release PR até o próximo `fix`/`feat`.

Os campos `version` de `pyproject.toml` e `frontend/package.json` são geridos pelo release-please (ver comentário `# managed by release-please` em `pyproject.toml`) e devem ser tratados como **somente leitura** pelos desenvolvedores. O `uv.lock` também é sincronizado com `uv lock` no branch do Release PR. A fonte de verdade da versão é git tag + `.release-please-manifest.json`.

### Exemplos de commit

```
# Nova feature (minor bump)
feat(image-backends): suporte ao backend OpenAI DALL-E 3

# Correção de bug (patch bump)
fix(queue): corrigir lease de tarefa não devolvida após timeout

# Com scope e corpo
feat(grid): suporte a layout grid_12

Estende o sistema de grid para 12 células, útil para pré-visualização em lote de séries longas.
```

**Breaking changes** têm duas formas equivalentes; o release-please faz major em ambas:

```
# Forma 1: ! após o type
feat(api)!: remover endpoint /api/v1/legacy

# Forma 2: footer BREAKING CHANGE (mais comum, permite várias linhas)
feat(auth): unificar lógica de validação de API Key

BREAKING CHANGE: a resposta de /api/v1/api-keys passa a ser { items: [...] };
clientes antigos precisam se adaptar.
```

Em ambos os casos o release-please:
- faz bump major da versão
- insere no topo do changelog um bloco **⚠️ BREAKING CHANGES** com as descrições
- mantém a entrada normal na seção do type (ex.: `✨ Features`)
