---
name: generate-script
description: Chama o modelo de texto configurado no projeto para gerar o script JSON (produz image_prompt e video_prompt de cada storyboard). Chamado pelo subagent create-episode-script. Lê o arquivo intermediário step1 e project.json e emite script conforme o schema Pydantic.
user-invocable: false
---

# generate-script

Chama o modelo de geração de texto configurado no projeto (Gemini / Ark / OpenAI / provedor customizado, definido por project.json)
e, a partir do arquivo intermediário do Step 1, produz o script JSON final. Os `image_prompt` / `video_prompt` do script
são a «semente» da geração posterior de imagem / vídeo — **a qualidade do prompt basicamente decide a qualidade da imagem** — por isso este skill é
o elo mais importante de otimizar em toda a pipeline do ArcReel.

## Pré-condições

1. Existe `project.json` no diretório do projeto (com style / overview / characters / scenes / props)
2. Pré-processamento Step 1 concluído (um arquivo intermediário conforme `effective_mode`):
   - narration (imagem→vídeo / grid→vídeo + narração): `drafts/episode_N/step1_segments.json` (segmentos estruturados: novel_text palavra por palavra + duração + segment_break + personagens / cenas / props em cena)
   - drama (imagem→vídeo / grid→vídeo + animação de série): `drafts/episode_N/step1_normalized_script.json` (conteúdo estruturado; step1 já fixou utterances de locução / âncora source_text / descrição visual adaptada; step2 repassa + completa visual — ver ADR 0041)
   - reference_video (referência→vídeo): `drafts/episode_N/step1_reference_units.md`
   - **exceção ad (anúncio/curta)**: não precisa de nenhum intermediário step1 — a entrada criativa é `brief` + `products`
     (com selling_points) + `target_duration` de `project.json`; o prompt é montado no backend pela tabela de proporção
     do framework de oito seções de venda aprovado (`products` vazio desvia automaticamente para prompt de curta genérico)
3. **drama / narration (imagem→ / grid→) exigem confirmação prévia do gate de revisão web**: o estado intermediário estruturado step1 é revisado no Web, editável manualmente / por agent, e **só após confirmação explícita** esta ferramenta gera a camada visual step2. Duas vias equivalentes de confirmação: o usuário clica confirmar no Web, ou o agent principal chama `mcp__arcreel__confirm_script_review({"episode": N})` após o usuário concordar na conversa. Sem confirmação (ou com conteúdo alterado após confirmação) esta ferramenta recusa; projetos legados (que já geraram o script deste episódio) estão grandfathered e passam. ad e reference_video não passam por este gate.

## Uso

Chamada via ferramenta MCP (nome do projeto ligado à sessão, não precisa passar):

```text
mcp__arcreel__generate_episode_script({"episode": N})
mcp__arcreel__generate_episode_script({"episode": N, "dry_run": true})   # só pré-visualiza o prompt
```

O caminho de saída é fixo internamente em `{project}/scripts/episode_{N}.json`; customização não é suportada;
para renomear ou arquivar, opere no Web.

**Importante: a geração de script deve chamar a ferramenta MCP acima. Este skill não fornece scripts Python/Shell; não use BASH para chamar `python .../scripts/*.py`.**

## Fluxo de geração

A ferramenta MCP completa os passos abaixo via `ScriptGenerator`:

1. **Carregar project.json** — lê content_mode, characters, scenes, props, overview, style
2. **Carregar o intermediário Step 1** — escolhe o arquivo conforme effective_mode
3. **Construir o Prompt** — gerado por `lib.prompt_builders_script` ou `lib.prompt_builders_reference`
4. **Chamar TextBackend** — `TextGenerator` escolhe o modelo de texto conforme a config do projeto e passa o schema Pydantic como `response_schema` para forçar a estrutura JSON
5. **Validação Pydantic** — schema conforme content_mode / effective_mode:
   - ad → `AdEpisodeScript` (lista plana `shots[]`; o esqueleto não muda com o caminho de geração; no caminho storyboard
     duration é restrição rígida de enum de supported_durations; no caminho reference_video é inteiro livre 1–15 s)
   - reference_video (sob narration/drama) → `ReferenceVideoScript` (com `video_units[]`)
   - narration → step2 em duas etapas: `response_schema` do LLM é `NarrationVisualEpisodeScript` (só `segment_id` + image_prompt + video_prompt); o backend faz merge da camada visual de volta nos segmentos estruturados do step1 por `segment_id` (novel_text / duração / segment_break / personagens / cenas / props repassados) e obtém o `NarrationEpisodeScript` completo. novel_text não entra na saída do LLM → sem drift de expansão
   - drama (storyboard / grid) → **duas etapas**: o LLM emite `DramaVisualScript` (só `scene_id` + image_prompt + video_prompt); o backend faz merge da camada visual de volta no conteúdo já fixado do step1 (`step1_normalized_script.json`: utterances / source_text / ativos em cena / duração / limites repassados sem mudança); o resultado do merge é `DramaEpisodeScript`. Campos não visuais não entram na saída do LLM, o que impede de raiz o drift via Structured Outputs (ver ADR 0041)
6. **Completar metadados** — `episode`, `content_mode`, `novel` (title do projeto + `Episódio N`), estatísticas (nº de segmentos / cenas / units, duração total), timestamps. Esses campos ficam ocultos do LLM (SkipJsonSchema) e são injetados pelo backend a partir de `project.json`, evitando alucinação que contamine consumidores downstream (nome do mp4 do compose-video, rascunho CapCut/Jianying etc.).
   - Nota: o `generation_mode` de topo só é gravado em scripts de referência→vídeo de narration/drama (valor fixo `reference_video`); o esqueleto de script ad é único (só `shots[]` + `content_mode`) e **não grava `generation_mode` de topo** — consumidores não devem despachar script ad por esse campo.

## Formato de saída

O JSON gerado é salvo em `scripts/episode_N.json`, estrutura principal:

- `title`: título do episódio escrito pelo LLM
- `episode` / `content_mode` / `novel` (com title, chapter): injetados pelo backend `_add_metadata`, sem depender da saída do LLM
- modo narration: `segments[]` (cada segmento com novel_text, duration_seconds, segment_break, personagens / cenas / props em cena — repassados do step1; image_prompt, video_prompt — gerados no step2)
- modo drama: `scenes[]` (cada cena com image_prompt, video_prompt, duration_seconds, e utterances, source_text, characters_in_scene etc. repassados do step1)
- modo ad: `shots[]` (cada shot com section, voiceover_text, products_in_shot, image_prompt, video_prompt, duration_seconds etc.), `metadata.total_shots`; desvio da duração total em relação a `target_duration` só gera log de aviso, não bloqueia o save; qualquer que seja o caminho de geração, **não** contém `generation_mode` de topo
- modo reference_video: `video_units[]` (cada unit com `shots[]`, `references[]`, `duration_seconds` etc.), `metadata.total_units`, e grava `generation_mode: "reference_video"` no topo
- `metadata`: total_segments / total_scenes, created_at, generator
- `duration_seconds`: duração total do episódio (segundos), recalculada no backend pela soma das durações dos storyboards

## Saída de `--dry-run`

Imprime o texto completo do prompt que seria enviado ao modelo de texto, sem chamar a API e sem gravar arquivo. Serve para checar qualidade e comprimento do prompt.

> Caminhos de dados, subagents de pré-processamento e escolha de schema dos três modos de geração em `.claude/references/generation-modes.md`.
