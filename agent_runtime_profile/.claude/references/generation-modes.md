# Referência de modos de geração

O ArcReel separa «que tipo de conteúdo» e «como gerar o vídeo» em duas dimensões independentes. `content_mode` expressa estritamente o **tipo de conteúdo** (narration / drama); `generation_mode` expressa a **fonte / caminho de geração do vídeo** (storyboard / grid / reference_video). As combinações enumeráveis estão abaixo; no caminho referência→vídeo o tipo de conteúdo só influencia decisões secundárias como proporção da imagem / duração padrão.

## Matriz de modos

| generation_mode | content_mode | Estrutura principal de dados | Subagent de pré-processamento | Arquivo intermediário step1 | Schema do script | Fonte de referência visual |
|---|---|---|---|---|---|---|
| `storyboard` | `narration` | `segments[]` | split-narration-segments | `step1_segments.json` | NarrationEpisodeScript | Uma storyboard por segmento como frame inicial |
| `storyboard` | `drama` | `scenes[]` | normalize-drama-script | `step1_normalized_script.json` | DramaNormalizedScript (step1) → DramaVisualScript (step2) → DramaEpisodeScript (merge) | Uma storyboard por cena como frame inicial |
| `grid` | `narration` | `segments[]` + grupos de grid | split-narration-segments | `step1_segments.json` | NarrationEpisodeScript | Recortes da imagem de grid |
| `grid` | `drama` | `scenes[]` + grupos de grid | normalize-drama-script | `step1_normalized_script.json` | DramaNormalizedScript (step1) → DramaVisualScript (step2) → DramaEpisodeScript (merge) | Recortes da imagem de grid |
| `reference_video` | `narration` / `drama` | `video_units[]` | split-reference-video-units | `step1_reference_units.md` | ReferenceVideoScript | Sheets de personagem / cena / prop como `reference_images` |

> `effective_mode(project, episode) = episode.generation_mode or project.generation_mode or "storyboard"`. O fallback padrão é imagem→vídeo (storyboard).
>
> drama usa pipeline em duas etapas (ver ADR 0041): step1 (normalize-drama-script) produz **conteúdo estruturado** `step1_normalized_script.json` (limites de cena / ativos em cena / utterances de locução palavra por palavra / âncora source_text / descrição visual adaptada); step2 (create-episode-script) o LLM só emite a camada visual `DramaVisualScript` (scene_id + image_prompt + video_prompt); o backend faz merge por scene_id com o conteúdo do step1 e obtém `DramaEpisodeScript`, repassando campos não visuais.
>
> Arquivos intermediários step1 ficam unificados em `drafts/episode_{N}/`. Detecção de estado e geração de script **só reconhecem o arquivo da combinação atual**: outros `step1_*` no diretório são resíduo histórico — não contam como pré-processamento concluído nem substituem a entrada da geração de script. `step1_normalized_script.md` residual de projetos drama antigos (rascunho livre pré-estruturação) não conta como step1 válido; rode normalize de novo para produzir `.json`.

## Mapeamento de etapas

```
Step 3 pré-processamento (despacha por effective_mode(project, episode); intermediários em drafts/episode_{N}/)
  effective_mode = reference_video        → dispatch split-reference-video-units → step1_reference_units.md
  effective_mode ∈ {storyboard, grid}:
    content_mode = narration               → dispatch split-narration-segments   → step1_segments.json
    content_mode = drama                   → dispatch normalize-drama-script     → step1_normalized_script.json (conteúdo estruturado)

Step 4 script JSON
  → dispatch create-episode-script (escolhe schema por generation_mode)
  Se o intermediário do Step 3 for modificado / redividido, reexecute este passo — o JSON do script não acompanha o intermediário automaticamente

Step 5 ativos (characters / scenes / props)
  Os três modos compartilham o skill `generate-assets` (--characters/--scenes/--props)

Step 6 storyboard
  storyboard         → dispatch generate-assets (storyboard)
  grid               → dispatch generate-assets (grid)
  reference_video    → pular

Step 7 vídeo
  storyboard / grid  → dispatch generate-assets (video)
  reference_video    → dispatch generate-assets (video)
                       mcp__arcreel__generate_video_episode detecta video_units e roteia para task_type="reference_video"

Step 8 narração TTS (somente content_mode narration)
  storyboard / grid  → dispatch generate-assets (narration_audio)
                       mcp__arcreel__generate_narration_audio sintetiza por segmento a partir de novel_text
  reference_video    → pular (sem segments)
```

## Especificações de vídeo

- **Resolução**: imagem 1K, vídeo 1080p
- **Duração por segmento** (storyboard / grid): valor deve estar em `supported_durations` do modelo; se `default_duration` do projeto não for null, use como padrão (gravado em project.json na criação conforme content_mode); se null, o pré-processamento escolhe pelo ritmo do conteúdo
- **Duração por unit** (reference_video): soma de todos os shots ≤ `max_duration` e **alvo próximo desse valor**; cada shot deve estar em `supported_durations` do modelo; se não couber, redivida a unit, sem violar a duração. Valores concretos o subagent consulta em execução via `mcp__arcreel__get_video_capabilities` — **não fixar neste documento**
- **Concatenação**: todos os modos usam ffmpeg concat; Veo extend só para **alongar um único segmento**, não para encadear shots diferentes
- **BGM**: ao final do prompt de vídeo, acrescentar sempre «proibido: BGM, legendas de texto, marcas d'água»

## Idioma do prompt

- Prompts de geração de imagem/vídeo em **português**
- Descrição narrativa, sem lista de palavras-chave
- Regras extras no modo reference_video: citar ativos com `@[personagem]`/`@[cena]`/`@[prop]`; **proibido** descrever aparência, traje ou detalhes de cena (as referências fornecem)

## Diferenças de diretório

> A árvore abaixo só ilustra a estrutura do projeto; o cwd da sessão já está em `projects/{name}/`. **Ao chamar ferramentas use caminhos relativos ao cwd** (ex.: `videos/`, `reference_videos/`); não use o prefixo `projects/{name}/`.

```text
projects/{name}/          # ← cwd da sessão já está aqui
├── storyboards/          # modos storyboard / grid (imagens de storyboard)
├── grids/                # modo grid (imagens de grid)
├── reference_videos/     # saída de vídeo do modo reference_video
├── videos/               # saída de vídeo dos modos storyboard / grid
└── audio/                # áudio de narração (somente content_mode narration; criado na primeira geração)
```

> Consulte o Prompting guide and strategies a partir da linha 365 de `docs/google-genai-docs/nano-banana.md`.
