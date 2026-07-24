---
name: manage-project
description: Kit de ferramentas de gestão de projeto. Cenários: incluir/modificar personagem/cena/prop em project.json (via patch_project, upsert por table+name), gravar campos de settings de topo, editar overview do projeto e consultar capacidades do modelo de vídeo (get_video_capabilities). Planejamento de episódios não está neste skill: use as ferramentas de servidor mcp__arcreel__plan_episodes / replan_episodes.
user-invocable: false
---

# Kit de ferramentas de gestão de projeto

Oferece escrita em lote de personagem/cena/prop em project.json, edição de settings e overview no nível do projeto, e consulta de capacidades do modelo de vídeo.

## Visão geral das ferramentas

| Ferramenta | Função | Quem chama |
|------|------|--------|
| `mcp__arcreel__patch_project` (SDK tool) | Incluir/modificar personagem/cena/prop de project.json (upsert por table+name), campos de settings de topo ou overview do projeto (ramo overview) | subagent / agent principal |
| `mcp__arcreel__get_video_capabilities` (SDK tool) | Consultar capacidades do modelo de vídeo do projeto atual (granularidade de model; comum a todos os modos de geração) | **subagent** (consulta sozinho ao executar a tarefa) |

> Planejamento de episódios (dividir/reordenar) é feito pelas ferramentas de servidor `mcp__arcreel__plan_episodes` / `mcp__arcreel__replan_episodes`; o fluxo está na etapa 2 do manga-workflow.

## Escrita de personagem/cena/prop

Gravar via ferramenta `mcp__arcreel__patch_project` (nome do projeto ligado à sessão, sem parâmetro). Chame uma vez por table;
cada entry faz upsert pela chave name: se name não existir, inclui; se existir, faz merge dos campos. **Revisar descrição de ativo existente exige intenção explícita do usuário**
(evita sobrescrever em silêncio campos editados manualmente); extração de novos ativos fica a cargo do subagent analyze-assets, que por padrão pula os já existentes.

```text
mcp__arcreel__patch_project({"table": "characters", "entries": {"nome_do_personagem": {"description": "...", "voice_style": "..."}}})
mcp__arcreel__patch_project({"table": "scenes", "entries": {"nome_da_cena": {"description": "..."}}})
mcp__arcreel__patch_project({"table": "props", "entries": {"nome_do_prop": {"description": "..."}}})
mcp__arcreel__patch_project({"settings": {"episode_target_units": 1000}})
mcp__arcreel__patch_project({"settings": {"source_language": "en"}})
mcp__arcreel__patch_project({"settings": {"narration_voice": "Ethan", "narration_speed": 1.2}})
mcp__arcreel__patch_project({"overview": {"genre": "suspense", "theme": "vingança e redenção"}})
```

**Três formas de chamada, escolha uma**: `{"table", "entries"}` faz upsert de ativo, `{"settings"}` grava campos de topo,
`{"overview"}` edita o overview do projeto; passar várias ao mesmo tempo ou nenhuma é rejeitado. Campos na whitelist de `settings`:

- `episode_target_units`: `int >= 1` define / `null` limpa. Volume-alvo por episódio (interpretado como unidade de leitura conforme `source_language`); a ferramenta de planejamento de episódios usa isso para calibrar o corte por episódio
- `source_language`: `"zh" / "en" / "vi"` define / `null` limpa. Prioridade: **config explícita do usuário > inferência automática** — se o usuário especificar a língua com clareza, pode gravar (não se limita a overview pulado ou falho); sem confirmação explícita do usuário, não adivinhe e grave sozinho; o caminho normal é o overview gravar automaticamente. Se a config explícita divergir da inferência / língua real do original, avise o usuário (WARN) e continue com a config explícita, sem bloquear o fluxo
- `brief`: string define / `null` limpa. Texto curto de briefing criativo; só gravável em projetos anúncio/curta (`content_mode=ad`); outros tipos de projeto rejeitam
- `planning_window_chars`: `int >= 1` define / `null` limpa e volta ao default interno. Nº de caracteres da janela de original lida por lote no planejamento de episódios
- `planning_max_episodes`: `int >= 1` define / `null` limpa e volta ao default interno. Nº máximo de episódios produzidos por lote no planejamento
- `narration_voice`: string não vazia (id de timbre conforme doc do provedor) define / `null` limpa. Override de timbre de narração no nível do projeto; prevalece sobre as settings globais e só afeta o projeto atual
- `narration_speed`: número finito positivo (ex.: `1.2`) define / `null` limpa. Override de velocidade de narração no nível do projeto; prevalece sobre as settings globais e só afeta o projeto atual

Campos na whitelist de `overview`: `synopsis` / `genre` / `theme` / `world_setting`, **semântica de merge** (só altera campos passados;
se o overview não existir, cria). **Revisar o overview exige intenção explícita do usuário** (evita sobrescrever em silêncio campos editados manualmente).

O retorno da ferramenta distingue **N novos / N merge de campos** e lista explicitamente os campos ignorados (``reference_image`` /
``character_sheet`` e outros campos geridos pelo sistema, ``type`` / ``importance`` e outros campos deprecados). Estrutura ilegal (ex.: falta
description) não grava e retorna `is_error: true`.
**Proibido** usar Write/Edit/Bash para alterar `project.json` diretamente — só via patch_project.

## Consultar capacidades do modelo de vídeo

Consulta via ferramenta MCP (nome do projeto ligado à sessão, sem parâmetro):

```text
mcp__arcreel__get_video_capabilities({})
```

**Retorno**: texto JSON com `provider_id` / `model` / `supported_durations[]` / `max_duration` / `max_reference_images` / `source` / `default_duration` / `content_mode` / `generation_mode`.

**Uso**: subagents de pré-processamento de todos os generation_mode (storyboard / grid / reference_video) consultam sozinhos na execução para decidir duração por segmento / shot. **Prioridade de decisão** (alta→baixa): restrição rígida (duração deve vir de `supported_durations`; duração total da unit em reference_video ≤ `max_duration`) > preferência `default_duration` (se não null, use como padrão) > eficiência de empacotamento / necessidade de conteúdo (reference_video combina shots para aproximar `max_duration`; narration / drama com frases longas ou quadro complexo podem tomar valor mais longo). Se estourar, redivida a unit; não viole a duração.

**Erro**: se o projeto não for encontrado ou as capacidades do modelo não puderem ser resolvidas, retorna `is_error: true` com o motivo no texto.
