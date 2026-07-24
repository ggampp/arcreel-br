---
name: generate-grid
description: Gera storyboards em grid. Use quando o usuário disser "gerar grid", "imagem em grid", "gerar storyboard no modo grid". Agrupa automaticamente por segment_break, escolhe o tamanho ótimo de grid, gera a imagem encadeada de primeiro/último frame e recorta/atribui.
---

# Gerar storyboard em grid

Gera storyboards em grid para projetos no modo grid. Agrupa automaticamente por segment_break; cada grupo gera uma imagem grande de grid que, após o recorte, forma a cadeia de primeiro/último frame.

## Pré-condições

- `generation_mode` do projeto é `"grid"`
- Script já gerado (`scripts/episode_N.json` existe)
- Artes de personagem/cena/prop já geradas (usadas como referência)

## Chamadas de ferramentas

| Operação | Ferramenta |
|------|------|
| Gerar o episódio inteiro | `mcp__arcreel__generate_grid({"script": "episode_1.json"})` |
| Grupo das cenas indicadas | `mcp__arcreel__generate_grid({"script": "episode_1.json", "scene_ids": ["E1S01", "E1S02", "E1S03"]})` |
| Só listar agrupamento atual | `mcp__arcreel__generate_grid({"script": "episode_1.json", "list_only": true})` |

## Saída

- Imagem grande de grid em `grids/grid_{id}.png`
- Primeiro/último frame recortados em `storyboards/scene_{id}_first.png` / `scene_{id}_last.png`
- Metadados da cadeia de frames em `grids/grid_{id}.json`
