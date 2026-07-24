---
name: generate-video
description: Gera clipes de vídeo para cenas do script. Use quando o usuário disser "gerar vídeo", "transformar storyboard em vídeo", quiser regenerar o vídeo de uma cena, ou precisar retomar geração de vídeo interrompida. Suporta lote do episódio inteiro, cena única, retomada por checkpoint etc.
---

# Gerar vídeo

## Despacho automático de modo

Após ler o script, a ferramenta MCP detecta a estrutura de topo e roteia para o executor correspondente:

| Característica do script | Rota | Diretório de saída |
|---|---|---|
| `generation_mode == "reference_video"` ou existe `video_units[]` | `task_type="reference_video"` → `execute_reference_video_task` | `reference_videos/{unit_id}.mp4` |
| `shots[]` + projeto `generation_mode == "reference_video"` (ad, saída direta por referência) | a ferramenta deriva o agrupamento e segue `task_type="reference_video"` | `reference_videos/{unit_id}.mp4` |
| `segments[]` (narration) | `task_type="video"` → `execute_video_task` | `videos/scene_{segment_id}.mp4` |
| `scenes[]` (drama) | idem | `videos/scene_{scene_id}.mp4` |
| `shots[]` (ad, caminho storyboard) | idem | `videos/scene_{shot_id}.mp4` |

O modo referência pula a exigência de storyboard e entrega `{script_file}` direto ao executor; o executor lê unit.references → resolve as sheets nos três buckets characters/scenes/props → comprime em memória → renderiza o prompt → chama VideoBackend.

Cria vídeo para cada cena/segmento/unit. Nos modos storyboard/grid a storyboard é o frame inicial; no modo reference_video as imagens de referência de personagem/cena/prop viram `reference_images`, pulando o passo de storyboard.

### ad saída direta por referência (agrupamento derivado)

O esqueleto do script ad é único (lista plana `shots[]`, sem `video_units`). Com `generation_mode == "reference_video"` do projeto, as ferramentas `generate_video_*` automaticamente:

1. **Agrupam em grupos derivados** shots consecutivos em video_units (cada unit ≤4 shots; duração total da unit limitada pelo teto de geração única do provedor); o índice (unit → shot_ids + conjunto de referência) vai para o campo `reference_units` do script — só cita shot_id; shots continuam sendo a única fonte de verdade de conteúdo
2. O conjunto de referência de cada unit herda dos shots membros: referência de produto injetada por completo e com prioridade absoluta (com sheet: sheet + original; sem sheet: original direto; instrução de alta fidelidade anexada), depois sheets de personagem/cena/prop
3. Enfileira tarefas `reference_video` por unit; o prompt é montado automaticamente a partir de image_prompt/video_prompt dos shots (com estrutura de corte `Shot N (Xs):`); a copy de locução **não** entra no prompt de imagem

Após editar shots (incluir/remover/mudar duração/reordenar), chamar de novo a ferramenta de geração rederiva automaticamente; units cujos membros e conjunto de referência não mudaram mantêm o vídeo já gerado, sem consumir de novo.

Em projetos anúncio/curta, shots de produto (`products_in_shot` não vazio) recebem automaticamente uma segunda injeção de referência de produto na camada de vídeo: se o backend de vídeo suportar sobrepor referência no request do primeiro frame, a referência de produto vai no request com instrução de alta fidelidade; se não suportar, degrada normalmente — sem especificar à mão e sem o video_prompt precisar repetir a aparência do produto.

> Proporção, duração etc. são definidos pela config do projeto e pelas capacidades do modelo de vídeo; a ferramenta MCP trata automaticamente.

## Chamadas de ferramentas

**Importante: a geração de vídeo deve enfileirar via as ferramentas MCP abaixo. Este skill não fornece scripts Python/Shell; não use BASH para chamar `python .../scripts/*.py`.**

Enfileirar via ferramenta MCP:

| Operação | Ferramenta |
|------|------|
| Gerar o episódio inteiro (padrão) | `mcp__arcreel__generate_video_episode({"script": "episode_1.json"})` |
| Retomada por checkpoint | `mcp__arcreel__generate_video_episode({"script": "episode_1.json", "resume": true})` |
| Cena única | `mcp__arcreel__generate_video_scene({"script": "episode_1.json", "scene_id": "E1S01"})` |
| Lote à escolha | `mcp__arcreel__generate_video_selected({"script": "episode_1.json", "scene_ids": ["E1S01", "E1S05", "E1S10"]})` |
| À escolha + retomada | `mcp__arcreel__generate_video_selected({"script": "episode_1.json", "scene_ids": [...], "resume": true})` |
| Todos os pendentes (modo independente) | `mcp__arcreel__generate_video_all({"script": "episode_1.json"})` |

> Todas as tarefas são submetidas de uma vez à fila de geração; o Worker agenda automaticamente conforme a config de concorrência per-provider.
> O número do episódio é derivado do `episode` de topo do script ou do nome do arquivo; não precisa passar à mão.
> No modo `reference_video`, `scene_id` / `scene_ids` são ignorados e vira geração do episódio inteiro.

## Fluxo de trabalho

1. **Carregar projeto e script** — confirmar que todas as cenas têm `storyboard_image`
2. **Gerar vídeo** — a ferramenta MCP monta o Prompt, chama a API e salva checkpoint automaticamente
3. **Checkpoint de revisão** — mostrar resultados; o usuário pode regenerar cenas insatisfatórias
4. **Atualizar o script** — atualiza automaticamente o caminho `video_clip` e o status da cena

## Construção do Prompt

O Prompt é montado internamente pela ferramenta MCP, com estratégias diferentes conforme content_mode. Campos lidos do JSON do script:

**image_prompt** (referência da storyboard): scene, composition (shot_type, lighting, ambiance)

**video_prompt** (geração de vídeo): action, camera_motion, ambiance_audio, dialogue, narration (somente drama)

- Modo narração: `novel_text` não participa da geração de vídeo (a narração é dublada à parte via `generate-narration-audio`); `dialogue` só contém diálogos de personagem do original
- Modo animação de série: inclui diálogo, narração e efeitos sonoros completos
- Negative prompt exclui BGM automaticamente

## Checagem pré-geração

- [ ] Todas as cenas têm storyboard aprovada
- [ ] Comprimento do texto de diálogo adequado
- [ ] Descrição de ação clara e simples

### Modo reference_video

- [ ] Personagens / cenas / props citados por todas as units estão registrados nos três buckets de project.json e o arquivo `*_sheet` existe
- [ ] nº de shots por unit ≤ 4, duração total ≤ teto do modelo
- [ ] nº de references ≤ `max_reference_images` do modelo

> No modo referência→vídeo, a saída se chama `{unit_id}.mp4` e fica em `reference_videos/`.
> A saída direta ad por referência trata referências com critério soft: sheet/original ausente é
> pulado com aviso no resultado da tarefa (não falha rígida como narration/drama); shot de
> produto sem imagem de produto degrada a injeção de fidelidade para texto puro —
> antes de gerar, confirme que a original do produto foi enviada.
