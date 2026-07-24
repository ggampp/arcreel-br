# Espaço de trabalho de geração de vídeo com IA
<!-- mode: drama -->

---

## Regras gerais importantes

As regras abaixo se aplicam a **todas** as operações do projeto:

### Especificações de vídeo
- **Proporção do vídeo**: definida por `aspect_ratio` do projeto; não é necessário especificar no prompt
- **Duração por segmento/cena**: definida pelas capacidades do modelo de vídeo e por `default_duration` do projeto
  - modos storyboard / grid: definidos por `default_duration` do projeto
  - modo reference_video: definidos por `supported_durations` do modelo de vídeo escolhido; o subagent consulta o valor real em runtime via `mcp__arcreel__get_video_capabilities`
- **Resolução de imagem**: 1K
- **Resolução de vídeo**: 1080p
- **Forma de geração**: cada segmento/cena é gerado de forma independente, usando a storyboard como frame inicial

> **Sobre a função extend**: o extend do Veo 3.1 serve apenas para alongar um único segmento/cena,
> +7 segundos fixos por vez, e **não** serve para encadear shots diferentes. Entre segmentos/cenas diferentes use concatenação com ffmpeg.

### Normas de áudio
- **BGM proibido automaticamente**: ao final do prompt de vídeo, acrescentar sempre «proibido: BGM, legendas de texto, marcas d'água»

### Chamadas de ferramentas

- **Fila de negócio / geração de texto / consulta de capacidades**: sempre via ferramentas MCP in-process `mcp__arcreel__*` (personagem/cena/prop/storyboard/vídeo/grid/script de episódio/script normalizado/planejamento e replanejamento de episódios/consulta de capacidades de vídeo). Rodam no processo principal do server, sem restrição da whitelist de rede do sandbox; o agent chama como tool.
- **Edição de JSON do projeto**: alterar scripts (`scripts/*.json`) ou personagens/cenas/props (`project.json`) **sempre via ferramentas de edição `mcp__arcreel__*`** — campos do script com `patch_episode_script` (batch-native: mapa `{id_do_segmento: {caminho_do_campo: valor}}`, uma chamada altera vários segmentos × vários campos; edição unitária = mapa de tamanho 1; atômico all-or-nothing: qualquer edição inválida descarta o lote inteiro e o erro aponta segment id e campo; erros de validação estrutural reportam o caminho do campo; antes de edições em lote, faça Read do script para confirmar o estado atual), título do episódio com `patch_episode_meta`, inserir/remover/dividir segmentos com `insert_segment` / `remove_segment` / `split_segment`, personagens/cenas/props com `patch_project`. **Proibido** usar Write / Edit / Bash para alterar esses dois tipos de arquivo (bloqueados por sandbox `denyWrite` e hook PreToolUse). **Prompt alterado exige regeneração**: após mudar `image_prompt` / `video_prompt` de segmentos com `patch_episode_script`, a ferramenta **não** invalida imagem/vídeo antigos — chame em seguida a geração correspondente desses segmentos, senão fica «prompt novo + imagem antiga».
- **Uso do Bash**: apenas diagnóstico e navegação de arquivos (`ls` / `cat` / `jq` / `python` / `curl` etc.), e scripts Python ainda presentes no skill `compose-video`.
- **Proteção de arquivos sensíveis**: `.env` / `vertex_keys/` / `.system_config.json*` / `.arcreel.db*` / `.claude/settings.json` são bloqueados em nível de kernel pelo sandbox profile (`filesystem.denyRead`) e pelo hook PreToolUse de acesso a arquivos; arquivos de código (`.py`/`.js`/`.ts`/`.tsx`/`.sh`/`.yaml`/`.yml`/`.toml`) têm escrita bloqueada por hook em runtime.

### Normas de caminho

O diretório de trabalho atual (cwd) da sessão do agent já está ligado à raiz do projeto atual. **Todos os caminhos em parâmetros de ferramentas devem seguir**:

- **Read / Edit / Write / Glob / Grep**: `file_path` com **caminho absoluto**
- **Bash chamando scripts de skill**: caminhos **relativos à raiz do projeto (cwd)**, por exemplo:
  - ✅ `source/episode_1.txt`, `drafts/episode_1/step1_normalized_script.json`, `scripts/episode_1.json`
  - ❌ `projects/{nome_do_projeto}/source/episode_1.txt` (prefixo duplo; placeholder ou concatenação errada cai na raiz de projects)
- **Proibido** aparecer o prefixo `projects/{...}/` em parâmetros de ferramentas; esse prefixo só documenta a estrutura de pastas e **não** deve ser passado a nenhuma ferramenta
- Scripts de skill validam o cwd e recusam execução se o cwd não for a raiz do projeto atual
- **Sobre formas relativas em agent.md / SKILL.md**: caminhos relativos nas instruções de subagent (ex.: «ler `project.json`», «ler `source/episode_{N}.txt`») são **localização dentro do projeto**, não valores de `file_path` prontos. Em Read/Edit/Write/Glob/Grep, monte o caminho absoluto a partir do cwd da sessão

---

## Modo de conteúdo

Este projeto é **modo animação de série** (`drama`). A estrutura de dados do script é `scenes[]`; cada cena corresponde a um quadro visual independente (com diálogo, ação e emoção).

> Os modos de geração (storyboard / grid / reference_video) são configurados pelo campo `generation_mode` em `project.json`, independentes do modo de conteúdo. Especificações detalhadas em `.claude/references/generation-modes.md`.

---

## Modos de geração

O sistema suporta três **modos de geração** (`generation_mode`), via campo de topo em `project.json` + `episodes[i].generation_mode` por episódio:

| generation_mode | Nome (UI) | Estrutura principal de dados | Fonte de referência visual |
|---|---|---|---|
| `storyboard` (padrão) | Imagem→vídeo | `segments[]` ou `scenes[]` + storyboard | Uma storyboard por segmento como frame inicial |
| `grid` | Grid→vídeo | `segments[]` ou `scenes[]` + grupos de grid | Recortes da imagem de grid |
| `reference_video` | Referência→vídeo | `video_units[]` | Sheets de personagem/cena/prop como referência |

Regra de resolução: `effective_mode(project, episode) = episode.generation_mode or project.generation_mode or "storyboard"`.

> Matriz completa de modos e ramificações de etapas em `.claude/references/generation-modes.md`.

---

## Estrutura do projeto

- `projects/{nome_do_projeto}` — workspace do projeto de vídeo
- `lib/` — biblioteca Python compartilhada (camada de abstração multi-provedor de imagem / vídeo / texto, gestão de projetos)
- `agent_runtime_profile/.claude/skills/` — skills disponíveis

## Arquitetura: Skill de orquestração + Subagents focados

```
Agent principal (camada de orquestração — extremamente leve)
  │  Mantém apenas: resumo do estado do projeto + histórico de diálogo
  │  Responsabilidades: detecção de estado, decisões de fluxo, confirmação do usuário, dispatch de subagent
  │
  ├─ dispatch → analyze-assets               extração global de personagem/cena/prop
  ├─ dispatch → split-narration-segments     divisão de segmentos no modo narration
  ├─ dispatch → normalize-drama-script       normalização de script no modo drama
  ├─ dispatch → split-reference-video-units  divisão de video_unit no modo reference
  ├─ dispatch → create-episode-script        geração de script JSON (pré-carrega skill generate-script)
  └─ dispatch → generate-assets              geração de ativos (personagem/cena/prop/storyboard/vídeo)
```

### Princípios de fronteira Skill/Agent

| Tipo | Uso | Exemplo |
|------|------|------|
| **Subagent (tarefa focada)** | Precisa de muito contexto ou raciocínio → protege o context do agent principal | analyze-assets, split-narration-segments |
| **Skill (chamado dentro do subagent)** | Execução determinística de scripts → chamadas de API, geração de arquivos | generate-script, generate-assets |
| **Operação direta do agent principal** | Apenas operações leves | ler estado do projeto, ops simples de arquivo, interação com o usuário |

### Restrições-chave

- **Subagent não pode spawn de subagent**: fluxos multi-etapa só via dispatch em cadeia do agent principal
- **Texto original do romance não entra no agent principal**: o subagent lê sozinho; o agent principal só passa caminhos de arquivo
- **Um subagent = uma tarefa focada**: conclui e retorna; não faz confirmações multi-etapa com o usuário por dentro

### Limites de responsabilidade

- **Proibido escrever código**: não criar nem modificar arquivos de código (`.py`/`.js`/`.sh` etc.); processamento de dados via ferramentas `mcp__arcreel__*` ou scripts existentes de `manage-project` / `compose-video`
- **Reportar bug de código**: se ficar claro que o erro do MCP tool ou do script do skill é bug de código (não de parâmetro ou ambiente), reportar ao usuário e sugerir feedback aos desenvolvedores

## Skills disponíveis

| Skill | Comando de gatilho | Função |
|-------|---------|------|
| manga-workflow | `/manga-workflow` | Skill de orquestração: detecção de estado + dispatch de subagent + confirmação do usuário |
| manage-project | — | Kit de gestão de projeto: escrita em lote de personagem/cena/prop, settings e overview |
| generate-script | — | Gera script JSON com o modelo de texto do projeto (chamado por subagent) |
| generate-assets | `/generate-assets` | Geração unificada de ativos: pode especificar `type=character\|scene\|prop`; omitir = três classes em paralelo |
| generate-storyboard | `/generate-storyboard` | Gera imagens de storyboard (modo storyboard) |
| generate-grid | `/generate-grid` | Gera storyboard em grid (modo grid: grids encadeados agrupados por segment_break) |
| generate-video | `/generate-video` | Gera vídeo |
| compose-video | `/compose-video` | Pós-produção de vídeo (BGM, intro/outro, concatenação multi-episódio, ffmpeg) |

## Início rápido

Novos usuários devem usar `/manga-workflow` para o fluxo completo de criação de vídeo.

## Visão geral do fluxo de trabalho

O skill de orquestração `/manga-workflow` avança automaticamente pelas etapas abaixo (após cada etapa, aguarda confirmação do usuário):

1. **Configuração do projeto**: criar projeto (define `content_mode` na criação, imutável depois), escolher `generation_mode`, enviar romance, gerar overview do projeto
2. **Extração global de personagem/cena/prop** → dispatch do subagent `analyze-assets`
3. **Planejamento de episódios** → agent principal chama a ferramenta de servidor `mcp__arcreel__plan_episodes` para planejar um lote de episódios (ledger + arquivos derivados mantidos pela ferramenta) + revisão por lote; feedback via `mcp__arcreel__replan_episodes` para reordenar de uma vez. Preferências permanentes de divisão (ex.: alinhar por capítulos) devem ir em `instructions` de `plan_episodes` e ser **repetidas em cada chamada de lote** até o fim do planejamento (preferências não são persistidas)
4. **Pré-processamento do episódio** → três ramos por `effective_mode` × `content_mode` (arquivos intermediários em `drafts/episode_{N}/`):
   - reference_video (qualquer content_mode) → `split-reference-video-units` (produz `step1_reference_units.md`)
   - storyboard / grid + narration → `split-narration-segments` (produz `step1_segments.json`)
   - storyboard / grid + drama → `normalize-drama-script` (produz conteúdo estruturado `step1_normalized_script.json`)
5. **Geração de script JSON** → dispatch do subagent `create-episode-script`; se o arquivo intermediário for modificado/redividido, **reexecutar** esta etapa
6. **Design de ativos (character/scene/prop em paralelo)** → dispatch do subagent `generate-assets`
7. **Geração de storyboard**: só modos `storyboard` / `grid`; `reference_video` pula → dispatch do subagent `generate-assets`
8. **Geração de vídeo** → dispatch do subagent `generate-assets` (o script despacha automaticamente por video_units/segments/scenes)

O fluxo tem **entrada flexível**: a detecção de estado localiza a primeira etapa incompleta e suporta retomada após interrupção.
Após a geração de vídeo, o usuário pode exportar rascunho CapCut/Jianying no Web.

## Princípios-chave

- **Consistência de personagem**: cada cena usa a storyboard como frame inicial, mantendo a aparência do personagem
- **Consistência de cena/prop**: ambientes e props marcantes são fixados via mecanismo `scenes` / `props`, garantindo consistência visual entre cenas
- **Continuidade de storyboard**: use `segment_break` para marcar pontos de troca de cena; na pós-produção dá para adicionar transições
- **Controle de qualidade**: após cada cena, revisar qualidade; regenerar individualmente cenas insatisfatórias

## Estrutura de diretórios do projeto

> A árvore abaixo é só ilustrativa; o cwd da sessão já está na raiz do projeto. **Bash chamando scripts de skill** usa caminhos relativos ao cwd (ex.: `source/`, `scripts/`); **Read / Edit / Write / Glob / Grep** usam **caminho absoluto** conforme «Normas de caminho». Em nenhuma ferramenta use o prefixo `projects/{nome_do_projeto}/`.

```text
projects/{nome_do_projeto}/      # ← cwd da sessão já está aqui; abaixo são relativos ao cwd
├── project.json       # metadados (personagens, cenas, props, episódios, estilo)
├── source/            # conteúdo original do romance
├── scripts/           # scripts de storyboard (JSON)
├── drafts/            # arquivos intermediários do Step 1
├── characters/        # artes de personagem
├── scenes/            # artes de cena
├── props/             # artes de prop
├── storyboards/       # imagens de storyboard (modos storyboard / grid)
├── grids/             # imagens de grid (modo grid)
├── videos/            # clipes de vídeo gerados (modos storyboard / grid)
├── reference_videos/  # video_units gerados (modo reference_video)
├── thumbnails/        # thumbnails do primeiro frame
└── output/            # saída final
```

### Campos principais de project.json

- `schema_version`: versão do formato de dados do projeto (atual 1)
- `title`, `content_mode` (`narration`/`drama`), `generation_mode` (`storyboard`/`grid`/`reference_video`), `style`, `style_description`
- `overview`: overview do projeto (synopsis, genre, theme, world_setting)
- `episodes`: ledger de episódios (fonte única de verdade): episode, title, script_file, `generation_mode` opcional de override, e campos de ledger `source_range` (faixa do original) / `hook` (gancho do fim do episódio) / `outline` (outline de episódio em drama) / `ledger_status` (planned/consumed/stale/unanchored); o topo `planning_cursor` marca o início do próximo lote de planejamento. `source/episode_N.txt` é derivado do ledger, mantido pelas ferramentas de planejamento — **não** editar ou renomear à mão
- `characters`: definição completa do personagem (description, voice_style, character_sheet)
- `scenes`: definição completa da cena (description, scene_sheet)
- `props`: definição completa do prop (description, prop_sheet)

### Princípios de camadas de dados

- Definições completas de personagem/cena/prop **só em project.json**; o script só referencia nomes
- Campos estatísticos (`scenes_count`, `status`, `progress` etc.) são **calculados na leitura** por StatusCalculator, não armazenados
- Metadados de episódio (episode/title/script_file) são **sincronizados na escrita** ao salvar o script
