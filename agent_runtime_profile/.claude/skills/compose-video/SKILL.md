---
name: compose-video
description: Concatena os clipes de vídeo já gerados na ordem do script em um filme final do episódio, com opção de misturar BGM e transições entre cenas. Use quando o usuário disser "montar o filme", "compor o vídeo deste episódio" ou "adicionar trilha".
---

# Compor vídeo

Concatena os clipes de vídeo já gerados do episódio (`videos/*.mp4`) na ordem do script em um filme único e grava em `output/`. Opcionalmente mistura BGM e aplica transições entre cenas conforme `transition_to_next`.

## Escopo de aplicação (importante)

- **drama + ad** — lê `scenes[]` (drama) ou `shots[]` (ad) no topo do script; narration (`segments[]`) e reference_video puro (`video_units[]`) ainda devem ir pelo export de rascunho CapCut/Jianying no Web
- **timeline ad** — pode ler `ad_timeline.text_overlays` de `project.json` (overlays de legenda queimada) e `ad_timeline.music_track` (ou CLI `--music`); o arquivo de música deve estar dentro do diretório do projeto (sugerido: `music/`)
- **Concatenação de um episódio** — processa um arquivo de script por vez; não suporta merge multi-episódio
- **Não implementa intro/outro / timeline fina de BGM** — timeline avançada ainda via export de rascunho CapCut/Jianying no Web

## Uso CLI

O script deve rodar no cwd do projeto que contém `project.json`, usando o nome do arquivo de script **relativo à raiz do projeto (cwd)**:

```bash
# Forma mínima: concatena na ordem do script + transições automáticas (conforme transition_to_next)
python .claude/skills/compose-video/scripts/compose_video.py scripts/episode_1.json

# Misturar BGM (arquivo de música relativo à raiz do projeto ou caminho absoluto)
python .claude/skills/compose-video/scripts/compose_video.py scripts/episode_1.json --music background_music.mp3

# Desligar transições (sempre cut; útil para contornar inconsistência de codec xfade)
python .claude/skills/compose-video/scripts/compose_video.py scripts/episode_1.json --no-transitions

# Nome de saída customizado (saída fixa sob output/)
python .claude/skills/compose-video/scripts/compose_video.py scripts/episode_1.json --output episode_1_final.mp4
```

Parâmetros completos:

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `script` | posicional (obrigatório) | Nome do arquivo de script (relativo ao cwd do projeto) |
| `--output OUTPUT` | opcional | Nome do arquivo de saída; se omitido, gerado a partir do campo `novel.chapter` do script. Qualquer valor, o arquivo final cai em `output/` |
| `--music MUSIC` | opcional | Caminho do BGM (relativo ao cwd do projeto ou absoluto), mas **após resolução deve ficar dentro do diretório do projeto** |
| `--no-transitions` | flag | Tudo em cut direto, ignora `transition_to_next` do script |

## Fluxo de trabalho

1. **Ler o script** — carrega de `scripts/` via `ProjectManager.load_script()` (filtro de caminho reutiliza `_safe_subpath` em lib)
2. **Coletar clipes** — resolve um a um `scenes[i].generated_assets.video_clip` e valida existência
3. **Concatenar** — padrão: normalize → concat (normaliza cada trecho para H.264/AAC unificado e codifica com concat filter); com necessidade de transição `xfade`, aplica filtro conforme `transition_to_next`
4. **Mix de áudio** — se `--music` for passado, faz mais um audio mix; o nome de saída ganha sufixo `_with_music`

## Tipos de transição suportados

Mapeados a partir do campo do script `scenes[i].transition_to_next`:

| Valor do campo | Comportamento ffmpeg |
|---|---|
| `cut` (padrão) | Concatenação direta, sem fade |
| `fade` | `xfade=transition=fade:duration=0.5` |
| `dissolve` | `xfade=transition=dissolve:duration=0.5` |
| `wipe` | `xfade=transition=wipeleft:duration=0.5` |

## Checagens prévias

- [ ] O cwd atual é a raiz do projeto (contém `project.json`)
- [ ] content_mode do script é drama (topo tem `scenes[]`)
- [ ] `generated_assets.video_clip` de cada cena já foi gerado
- [ ] `ffmpeg` / `ffprobe` estão no PATH (o script pré-checa)
- [ ] Arquivo de BGM existe (se `--music` for passado)

## Limitações / capacidades ausentes

As capacidades abaixo **não estão implementadas**; use o export de rascunho CapCut/Jianying no Web:

- modos narration / ad / reference_video (o script só reconhece `scenes[]`)
- merge multi-episódio / recorte em fatias de um episódio
- ajuste de volume de BGM, timeline de BGM independente
- intro/outro
- renderização de legendas
