## ADDED Requirements

### Requirement: Cada template de subagent deve definir contrato claro de entrada/saída

Cada arquivo de definição de subagent (`.claude/agents/*.md`) SHALL declarar explicitamente, na description e no system prompt, seus parâmetros de entrada, formato de saída e skills/scripts chamados internamente.

#### Scenario: Contrato do subagent analyze-assets
- **WHEN** esse subagent é despachado (dispatch)
- **THEN** ele recebe o nome do projeto e o caminho do diretório source como entrada, lê sozinho o texto original do romance, analisa e extrai três classes de ativos (personagens / cenas / props), grava em project.json via Bash com o script `add_assets.py` e retorna uma lista-resumo dos ativos

#### Scenario: Contrato do subagent split-narration-segments
- **WHEN** esse subagent é despachado
- **THEN** ele recebe nome do projeto, número do episódio e o trecho de texto do romance daquele episódio; divide em segmentos pelo ritmo de narração (~4 s/segmento), marca segment_break, salva `drafts/episode_{N}/step1_segments.md` e retorna resumo com quantidade de segmentos e duração total

#### Scenario: Contrato do subagent normalize-drama-script
- **WHEN** esse subagent é despachado
- **THEN** ele recebe nome do projeto e número do episódio; na primeira geração chama a ferramenta MCP in-process `mcp__arcreel__normalize_drama_script` (modelo de texto configurado no projeto) para gerar roteiro normalizado e orçamento de planos, salva `drafts/episode_{N}/step1_normalized_script.md` e `step2_shot_budget.md`, e retorna resumo de quantidade de cenas e distribuição de planos; em edições posteriores o subagent edita diretamente os Markdown existentes

#### Scenario: Contrato do subagent create-episode-script
- **WHEN** esse subagent é despachado
- **THEN** ele recebe nome do projeto e número do episódio, pré-carrega a skill generate-script, chama a ferramenta MCP in-process `mcp__arcreel__generate_episode_script` para gerar JSON, valida a saída e retorna um resumo do resultado

### Requirement: Cada subagent deve ser focado em uma única tarefa

Cada subagent SHALL completar apenas uma tarefa focada e retornar; não pode incluir internamente fluxos multi-etapas que exijam confirmação do usuário.

#### Scenario: Subagent não deve usar AskUserQuestion para confirmações entre etapas
- **WHEN** o subagent executa sua tarefa focada
- **THEN** o subagent conclui todo o trabalho de forma independente e retorna o resultado, sem usar AskUserQuestion no meio para esperar confirmação do usuário

#### Scenario: Subagent pode pedir esclarecimento em ambiguidade
- **WHEN** durante a execução o subagent encontra ambiguidade crítica que não consegue resolver sozinho (ex.: nome de personagem pouco claro no romance)
- **THEN** o subagent pode usar AskUserQuestion uma única vez para pedir esclarecimento, mas não para controle de fluxo multi-etapas

### Requirement: Subagents de pré-processamento devem ser definidos por content_mode

Os modos narration (narração) e drama (série animada) SHALL usar definições de subagent independentes, em vez de um único subagent com parâmetro de alternância.

#### Scenario: Modo narration usa split-narration-segments
- **WHEN** o content_mode do project é "narration"
- **THEN** a skill de orquestração orienta o agente principal a despachar o subagent `split-narration-segments`, executar a divisão de segmentos (ritmo de narração, marcar segment_break, marcar segmentos de diálogo) e gerar step1_segments.md

#### Scenario: Modo drama usa normalize-drama-script
- **WHEN** o content_mode do project é "drama"
- **THEN** a skill de orquestração orienta o agente principal a despachar o subagent `normalize-drama-script`, executar roteiro normalizado (cenas estruturadas, tempo, local, personagens) + orçamento de planos (estimativa de planos, marcar segment_break) e gerar step1_normalized_script.md e step2_shot_budget.md

### Requirement: create-episode-script deve pré-carregar a skill generate-script

O frontmatter do subagent `create-episode-script` SHALL pré-carregar a skill `generate-script` via campo `skills`.

#### Scenario: Conteúdo da skill injetado ao iniciar o subagent
- **WHEN** o subagent é despachado
- **THEN** o conteúdo completo da skill generate-script já está no context do subagent, que pode chamar a ferramenta `mcp__arcreel__generate_episode_script` conforme as instruções da skill

#### Scenario: Subagent valida o resultado gerado
- **WHEN** a ferramenta `mcp__arcreel__generate_episode_script` termina
- **THEN** o subagent valida que scripts/episode_{N}.json existe e passa na validação de dados; se houver erros, tenta corrigir e regenerar

### Requirement: Remover definições antigas de subagent multi-etapas

`novel-to-narration-script.md` e `novel-to-storyboard-script.md` SHALL ser removidos e substituídos pelos novos templates de subagent focados.

#### Scenario: Arquivos antigos de agent removidos
- **WHEN** a refatoração é concluída
- **THEN** o diretório `agent_runtime_profile/.claude/agents/` não contém mais `novel-to-narration-script.md` nem `novel-to-storyboard-script.md`

#### Scenario: Novos arquivos de agent no lugar
- **WHEN** a refatoração é concluída
- **THEN** o diretório `agent_runtime_profile/.claude/agents/` contém definições focadas como `analyze-assets.md`, `split-narration-segments.md`, `normalize-drama-script.md`, `create-episode-script.md`

### Requirement: Deve existir script CLI para gravação de ativos

SHALL existir o script `add_assets.py` (em scripts/ da skill manage-project), encapsulando gravação em lote de personagens / cenas / props via `ProjectManager` + `validate_project()`, para o subagent chamar via ferramenta Bash.

#### Scenario: Adicionar personagens / cenas / props em lote
- **WHEN** o subagent chama `add_assets.py` via Bash, passando JSON compacto com `--characters` / `--scenes` / `--props`
- **THEN** o script grava os três tipos de ativos em project.json, chama validate_project e imprime resumo de sucesso/falha

#### Scenario: Ativos já existentes são ignorados automaticamente
- **WHEN** o nome do ativo já existe em project.json
- **THEN** o script ignora esse ativo (sem sobrescrever dados existentes) e marca na saída "já existe, ignorado"

### Requirement: Deve existir ferramenta MCP in-process de normalização de roteiro no modo drama

SHALL existir a ferramenta MCP in-process `mcp__arcreel__normalize_drama_script` (implementada em `server/agent_runtime/sdk_tools/text_generation.py`), usando o modelo de texto configurado no projeto para transformar o romance original em roteiro normalizado em Markdown e orçamento de planos.

#### Scenario: Primeira geração do roteiro normalizado
- **WHEN** o subagent `normalize-drama-script` chama essa ferramenta
- **THEN** a ferramenta lê o romance em source/, chama o modelo de texto do projeto para gerar roteiro estruturado e grava `drafts/episode_{N}/step1_normalized_script.md` e `step2_shot_budget.md`

#### Scenario: Formato de saída compatível com a etapa de geração de script
- **WHEN** a geração do roteiro normalizado termina
- **THEN** o formato de `step1_normalized_script.md` é compatível com a entrada esperada por `mcp__arcreel__generate_episode_script`, permitindo consumo contínuo na geração do roteiro JSON
