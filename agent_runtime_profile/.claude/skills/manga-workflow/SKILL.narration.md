---
name: manga-workflow
description: Orquestrador de fluxo ponta a ponta que transforma romance em vídeo curto. Use este skill sempre que o usuário falar em fazer vídeo, criar projeto, continuar o projeto ou ver progresso. Gatilhos incluem, sem se limitar a: "me ajuda a transformar o romance em vídeo", "abrir um projeto novo", "continuar", "próximo passo", "ver o progresso do projeto", "começar do zero", "dividir episódios", "rodar o fluxo inteiro sozinho" etc. Mesmo se o usuário só disser "continuar" ou "próximo passo", se o contexto atual for de projeto de vídeo, dispare. Não use para geração isolada de ativo (ex.: só redesenhar uma storyboard ou só regenerar a arte de um personagem — isso tem skill próprio).
---
<!-- mode: narration -->

# Orquestração do fluxo de vídeo

Você (agent principal) é o hub de orquestração. Você **não** processa o original do romance nem gera o script diretamente; em vez disso:
1. Detecta o estado do projeto → 2. Decide a próxima etapa → 3. Faz dispatch do subagent adequado → 4. Mostra o resultado → 5. Obtém confirmação do usuário → 6. Loop

**Restrições centrais**:
- O original do romance **nunca** entra no context do agent principal; o subagent lê sozinho
- Cada dispatch só passa **caminhos de arquivo e parâmetros-chave**, sem blocos grandes de conteúdo
- Cada subagent completa uma tarefa focada e retorna; o agent principal cuida da costura entre etapas

> Caminhos de dados e ramificações de etapa dos três modos de geração (imagem→vídeo / grid→vídeo / referência→vídeo) em `.claude/references/generation-modes.md`.

---

## Etapa 0: Configuração do projeto

**Importante**: a criação do diretório do projeto é feita pelo Web via `POST /api/v1/projects`, que dispara `ProjectManager.create_project()` (inclui todos os subdiretórios e `project.json`, e materializa o agent profile correspondente ao content_mode). **O agent principal não cria diretórios nem grava campos iniciais de project.json** — no start da sessão o cwd já está ligado à raiz do projeto existente.

### Projeto novo

1. Oriente o usuário a criar o projeto primeiro no Web, **especificando content_mode na criação** (narration / drama); após o start da sessão o cwd já está na raiz do projeto correspondente
2. Use Read em `project.json` e confirme os campos `title`, `content_mode`, `generation_mode` (nesta sessão o content_mode atual é `narration`, imutável após a criação)
3. Se `generation_mode` não foi definido na criação, pergunte com AskUserQuestion e o usuário completa no Web (ou grava via ferramenta de config mcp__arcreel__)
4. Peça ao usuário colocar o texto do romance em `source/`
5. **Após o upload, overview do projeto é gerado automaticamente** (synopsis, genre, theme, world_setting)

> Subdiretórios padrão do projeto são criados automaticamente por `create_project()`: `source/`, `scripts/`, `drafts/`, `characters/`, `scenes/`, `props/`, `storyboards/`, `grids/`, `videos/`, `reference_videos/`, `thumbnails/`, `output/`.

### Projeto existente

1. O cwd da sessão já está ligado à raiz do projeto-alvo
2. Com Read em `project.json` + Glob no sistema de arquivos, determine o resumo de estado
3. Continue a partir da última etapa incompleta

---

## Detecção de estado

Ao entrar no fluxo, use Read em `project.json` e Glob no sistema de arquivos. Verifique em ordem; o primeiro item faltante define a etapa atual:

1. characters / scenes / props **qualquer um** vazio (definição faltando)? → **Etapa 1**
2. O episódio-alvo não tem entrada no ledger (`episodes[]` de project.json)? → **Etapa 2**. O estado de continuidade de episódios **só lê o ledger**: `ledger_status` de cada entrada marca o estado do episódio (planned já planejado / consumed já consumido / stale invalidado após reordenação e precisa refazer / unanchored âncora perdida e travado); o topo `planning_cursor` marca o início do próximo lote de planejamento; **não use Glob de nomes de arquivo para inferir o número do episódio** (`source/episode_{N}.txt` é só derivado do ledger)
3. O episódio-alvo tem `ledger_status` `stale` (invalidado após reordenação — step1/script/mídia antigos contam como inválidos; mesmo com arquivos ainda presentes, refaça a partir desta etapa; produtos são substituídos pelo mecanismo de versão), ou o arquivo intermediário step1 da **combinação atual** do episódio-alvo não existe? → **Etapa 3**. Verifique o arquivo correspondente nos três ramos `effective_mode(project, episode)` × `content_mode` (note que effective_mode inclui o override `episodes[i].generation_mode` do episódio; não olhe só o campo de topo do projeto):
   - effective_mode == reference_video (qualquer content_mode): `drafts/episode_{N}/step1_reference_units.md`
   - effective_mode ∈ {storyboard, grid} e content_mode == narration: `drafts/episode_{N}/step1_segments.json`
   - effective_mode ∈ {storyboard, grid} e content_mode == drama: `drafts/episode_{N}/step1_normalized_script.json` (conteúdo estruturado)

   Neste projeto content_mode é fixo em narration (imutável após a criação), então só acerta o 1º ou o 2º ramo, conforme o effective_mode do episódio. Só reconheça o arquivo da combinação atual: **outros `step1_*` de outros modos** no diretório são resíduo e não contam como etapa 3 concluída.
4. scripts/episode_{N}.json não existe? → **Etapa 4** (ver também gatilhos da etapa 4: se o intermediário da etapa 3 for modificado/redividido nesta sessão, mesmo com JSON existente é preciso regenerar)
5. Qualquer classe de ativo ainda tem item sem sheet (character sem character_sheet / scene sem scene_sheet / prop sem prop_sheet)? → **Etapa 5** (três classes em paralelo)
6. **modos storyboard / grid**: há cena sem storyboard? → **Etapa 6** (modo reference_video pula)
7. Há cena/unit sem vídeo? → **Etapa 7**
8. **modos storyboard / grid**: há segmento sem `narration_audio`? → **Etapa 8 (narração TTS)** (modo reference_video sem segments, pula)
9. Tudo concluído → fim do fluxo; oriente o usuário a exportar o rascunho CapCut/Jianying no Web

> A etapa 8 só depende do `novel_text` de cada segmento do script, independente de storyboard/vídeo — pode avançar assim que o script da etapa 4 existir.
> Se o usuário pedir dublagem cedo, entre direto na etapa 8; não precisa esperar storyboard/vídeo.

**Determinar o número do episódio-alvo**: se o usuário não especificou, leia o ledger — o menor número de episódio com `ledger_status` `planned` (ou `stale`) é o próximo a produzir; se todos os episódios do ledger já foram consumidos e o original ainda não foi planejado por completo, entre na etapa 2 para planejar o próximo lote.

---

## Protocolo de confirmação entre etapas

**Após cada retorno de subagent**, o agent principal:

1. **Mostra o resumo**: apresenta ao usuário o resumo devolvido pelo subagent
2. **Obtém confirmação**: com AskUserQuestion oferece opções:
   - **Continuar para a próxima etapa** (recomendado)
   - **Refazer esta etapa** (redispatch com requisitos de edição anexados)
   - **Pular esta etapa**
3. **Age conforme a escolha do usuário**

---

## Etapa 1: Extração global de personagem/cena/prop

**Gatilho**: em project.json, characters / scenes / props **qualquer um** vazio (definição faltando)

**dispatch do subagent `analyze-assets`**:

```text
Nome do projeto: {project_name}
Escopo da análise: {romance inteiro / escopo indicado pelo usuário}
Personagens já existentes: {lista de nomes, ou "nenhum"}
Cenas já existentes: {lista de nomes, ou "nenhuma"}
Props já existentes: {lista de nomes, ou "nenhum"}

Analise o original do romance, extraia informações de personagem / cena / prop, grave em project.json e retorne o resumo.
```

---

## Etapa 2: Planejamento de episódios

**Gatilho**: o episódio-alvo não tem entrada no ledger (`episodes[]` de project.json)

O planejamento de episódios é feito pela ferramenta de servidor: internamente, a partir de `planning_cursor`, lê uma janela do original, chama o modelo de texto do projeto uma vez e planeja todos os episódios com arco narrativo completo dentro da janela (título/gancho/faixa do original), e na mesma trava do projeto grava o ledger, deriva `source/episode_{N}.txt` e limpa arquivos derivados residuais. **O agent principal só chama a ferramenta uma vez e só recebe o resumo** — não lê o original do romance e não escolhe pontos de corte sozinho:

1. Antes de planejar, confira rapidamente `project.json`:
   - `source_language` está alinhado à língua real do original? Prioridade: **config explícita do usuário > inferência automática** (caminho normal: overview grava automaticamente); se divergir, **avise o usuário (WARN), explique a consequência e sugira correção** (config errada distorce a métrica de volume e a premissa linguística do planejamento); se o usuário não corrigir, continue com a config explícita, sem bloquear. Se o campo faltar ou o usuário confirmar que está errado, grave via `mcp__arcreel__patch_project({"settings": {"source_language": "en"|"vi"|"zh"}})`
   - `episode_target_units` (volume-alvo por episódio, interpretado como unidade de leitura conforme `source_language`): se já definido, use; se faltar e o usuário deu contagem de caracteres/palavras na conversa → grave via `mcp__arcreel__patch_project({"settings": {"episode_target_units": N}})` ; se nenhum dos dois, pode planejar direto (a ferramenta calibra o volume pelo ritmo de vídeo curto), sem forçar pergunta
2. Chame `mcp__arcreel__plan_episodes({})`. Janela de caracteres e teto de episódios por lote são defaults internos da ferramenta; as settings do projeto `planning_window_chars` / `planning_max_episodes` podem sobrescrever (via patch_project settings). **Se o usuário der preferência permanente de divisão antes de planejar** (ex.: "dividir estritamente por capítulo, um capítulo por episódio" "cada episódio fecha em tal lugar"), passe o texto da preferência em `instructions`: `mcp__arcreel__plan_episodes({"instructions": "texto da preferência do usuário"})`; o planejador alinha essa preferência com força «deve cumprir tudo», prioridade sobre a integridade padrão do arco narrativo. Obras longas planejam em vários lotes (uma chamada de ferramenta por lote); essa preferência **não é persistida** — deve ser **repetida com o mesmo `instructions` em cada chamada de lote** até o fim do planejamento
3. **Revisão por lote**: mostre ao usuário o resumo do ledger devolvido pela ferramenta (título+gancho+volume de cada episódio) e peça opinião
4. Se o usuário der feedback (uma frase pode conter várias opiniões, inclusive preferência global) → chame `mcp__arcreel__replan_episodes({"from_episode": N, "instructions": "texto da opinião do usuário"})`, com `from_episode` = o episódio mais cedo afetado pela opinião; mostre de novo o resultado da reordenação. Opiniões globais (ex.: volume por episódio) a ferramenta regrava automaticamente nas settings do projeto e os lotes seguintes herdam
5. **Confirmação de aviso de episódios já consumidos**: se a reordenação atingir episódios já consumidos (já com produtos step1/script/mídia), a ferramenta devolve a lista afetada e **não** executa — informe o escopo do impacto, obtenha confirmação explícita e chame de novo com `"confirm_consumed": true`; esses episódios ficam stale (produtos não são apagados; o refazer substitui pelo mecanismo de cobertura/versão existente)
6. Quando o usuário estiver satisfeito com o lote, entre na etapa 3. **Com autorização total de autonomia do usuário** (ex.: "roda o fluxo inteiro sem confirmar etapa a etapa"), pode pular a revisão por lote e seguir direto

---

## Etapa 3: Pré-processamento do episódio

**Gatilho**: o arquivo intermediário em drafts/ do episódio-alvo não existe

Escolha o subagent conforme `effective_mode(project, episode)`:

- `effective_mode == reference_video` → dispatch `split-reference-video-units` (produz `drafts/episode_{N}/step1_reference_units.md`)
- caso contrário (neste projeto content_mode == narration) → dispatch `split-narration-segments` (produz `drafts/episode_{N}/step1_segments.json`)

Parâmetros comuns do prompt de dispatch: nome do projeto, caminho do projeto, número do episódio, caminho do arquivo do romance deste episódio.

(Os dois subagents de pré-processamento leem project.json sozinhos + chamam
`mcp__arcreel__get_video_capabilities({})`
para obter capacidades do modelo e preferências do usuário; o agent principal não precisa injetar de antemão a lista de personagem/cena/prop nem
dados como `supported_durations` / `max_duration` / `max_reference_images` / `default_duration`.)

**Mudança no intermediário exige regenerar o script JSON**: se o intermediário da etapa 3 for modificado ou redividido (qualquer modo de geração, primeira vez ou refazer), mesmo com `scripts/episode_{N}.json` já existente, **reexecute a etapa 4** — o JSON do script não acompanha o intermediário automaticamente; pular deixa «intermediário novo + JSON antigo».

---

## Etapa 4: Geração de script JSON

**Gatilho** (qualquer um):
- `scripts/episode_{N}.json` não existe
- o intermediário da etapa 3 foi modificado ou redividido nesta sessão (mesmo com JSON já existente, é preciso regenerar)

**Gate de revisão step1→step2 (bloqueante)**: o estado intermediário estruturado step1 da etapa 3 precisa de **confirmação explícita** para liberar esta etapa (só se aplica a step1 estruturado; o step1 do caminho `reference_video` é md de texto livre e **não** passa por este gate — não confirme e não chame `confirm_script_review` nele). Duas vias equivalentes de confirmação — o usuário revisa / edita e confirma no Web, ou você chama `mcp__arcreel__confirm_script_review({"episode": N})` após o usuário concordar na conversa em seguir para a geração visual (no modo de autonomia total, confirme com a autorização geral do usuário). Sem confirmação (ou com step1 alterado após confirmação) `generate_episode_script` é rejeitado pelo gate; **projetos legados** (que já geraram o script deste episódio antes do upgrade) estão grandfathered e não precisam confirmar de novo.

**dispatch do subagent `create-episode-script`**: passe nome do projeto, caminho do projeto, número do episódio.

---

## Etapa 5: Design de ativos (character / scene / prop em paralelo)

**Pré-condição**: as definições das três classes de ativos (characters / scenes / props) já foram gravadas em project.json pela etapa 1. Se qualquer definição estiver vazia (array ausente), volte à etapa 1 para completar a extração; não fique parado na etapa 5.

**Gatilho**: em qualquer das três classes há item sem sheet:
- character sem character_sheet
- scene sem scene_sheet
- prop sem prop_sheet

**Regra de despacho (julgamento de condição explícito, decisão independente por tipo)**:

```text
Para type ∈ {character, scene, prop}:
  se a classe tem item sem *_sheet → dispatch do subagent `generate-assets` correspondente
  se a classe já está completa      → pular, sem dispatch

Os três julgamentos são independentes; o resultado pode ser dispatch de 0~3 subagents.
Após o retorno de todos os subagents despachados, una os resumos, mostre ao usuário e entre na confirmação entre etapas.
```

Os três blocos de dispatch abaixo são templates; instancie só os que satisfazem a condição:

### subagent — design de personagem

**Gatilho**: há personagem sem character_sheet

```text
dispatch do subagent `generate-assets`:
  tipo de tarefa: character
  nome do projeto: {project_name}
  itens a gerar: {lista de nomes de personagens faltantes}
  chamada de ferramenta:
    mcp__arcreel__generate_assets({"type": "character"})
  forma de validação: reler project.json e checar o campo character_sheet dos personagens correspondentes
```

### subagent — design de cena

**Gatilho**: há cena sem scene_sheet

```text
dispatch do subagent `generate-assets`:
  tipo de tarefa: scene
  nome do projeto: {project_name}
  itens a gerar: {lista de nomes de cenas faltantes}
  chamada de ferramenta:
    mcp__arcreel__generate_assets({"type": "scene"})
  forma de validação: reler project.json e checar o campo scene_sheet das cenas correspondentes
```

### subagent — design de prop

**Gatilho**: há prop sem prop_sheet

```text
dispatch do subagent `generate-assets`:
  tipo de tarefa: prop
  nome do projeto: {project_name}
  itens a gerar: {lista de nomes de props faltantes}
  chamada de ferramenta:
    mcp__arcreel__generate_assets({"type": "prop"})
  forma de validação: reler project.json e checar o campo prop_sheet dos props correspondentes
```

---

## Etapa 6: Geração de storyboard (somente modos storyboard / grid)

**Gatilho**: há cena sem storyboard; **modo referência→vídeo pula esta etapa**

Verifique `effective_mode(project, episode)`:

- `"storyboard"` → dispatch `generate-assets`, chame `mcp__arcreel__generate_storyboards`
- `"grid"` → dispatch `generate-assets`, chame `mcp__arcreel__generate_grid`
- `"reference_video"` → não dispara; pule direto para a etapa 7

### modo storyboard (padrão)

**dispatch do subagent `generate-assets`**:

```text
dispatch do subagent `generate-assets`:
  tipo de tarefa: storyboard
  nome do projeto: {project_name}
  chamada de ferramenta:
    mcp__arcreel__generate_storyboards({"script": "episode_{N}.json"})
  forma de validação: reler scripts/episode_{N}.json e checar o campo storyboard_image de cada cena
```

### modo grid

**dispatch do subagent `generate-assets`**:

```text
dispatch do subagent `generate-assets`:
  tipo de tarefa: storyboard
  nome do projeto: {project_name}
  chamada de ferramenta:
    mcp__arcreel__generate_grid({"script": "episode_{N}.json"})
  forma de validação: reler scripts/episode_{N}.json e checar o campo storyboard_image de cada cena
```

---

## Etapa 7: Geração de vídeo

**Gatilho**: há cena sem vídeo

**dispatch do subagent `generate-assets`**:

```text
dispatch do subagent `generate-assets`:
  tipo de tarefa: video
  nome do projeto: {project_name}
  chamada de ferramenta:
    mcp__arcreel__generate_video_episode({"script": "episode_{N}.json"})
  forma de validação: reler scripts/episode_{N}.json e checar o campo video_clip de cada cena
```

---

## Etapa 8: Narração TTS (somente modos storyboard / grid)

**Gatilho**: há segmento sem `narration_audio`; **modo referência→vídeo pula esta etapa** (sem segments)

A narração TTS sintetiza voz segmento a segmento a partir do `novel_text` original de cada segmento; depende só do script, independente de storyboard/vídeo:
na ordem do fluxo fica depois do vídeo, mas se o usuário pedir pode rodar a qualquer momento após o script da etapa 4.

**dispatch do subagent `generate-assets`**:

```text
dispatch do subagent `generate-assets`:
  tipo de tarefa: narration_audio
  nome do projeto: {project_name}
  chamada de ferramenta:
    mcp__arcreel__generate_narration_audio({"script": "episode_{N}.json"})
  forma de validação: reler scripts/episode_{N}.json e checar o campo generated_assets.narration_audio de cada segmento
```

Após interrupção, redispatch a mesma chamada de ferramenta para retomar por checkpoint — segmentos com áudio são pulados automaticamente; só completa os faltantes.

---

## Entrada flexível

O fluxo **não força começar do zero**. Conforme o resultado da detecção de estado, começa automaticamente na etapa correta:

- "analisar personagens do romance" → só executa a etapa 1
- "criar o script do episódio 2" → começa na etapa 2 (se os personagens já existirem)
- "continuar" → a detecção de estado acha o primeiro item faltante
- etapa específica (ex.: "gerar storyboard") → pula direto para essa etapa

---

## Camadas de dados

- Definições completas de personagem / cena / prop **só em project.json**; o script só referencia nomes
- Campos estatísticos (scenes_count, status, progress) são **calculados na leitura**, não armazenados
- Metadados de episódio são **sincronizados na escrita** ao salvar o script
