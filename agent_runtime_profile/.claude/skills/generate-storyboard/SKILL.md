---
name: generate-storyboard
description: Gera imagens de storyboard para cenas do script. Use quando o usuário disser "gerar storyboard", "pré-visualizar o quadro da cena", quiser regenerar certas storyboards, ou houver cenas no script sem storyboard. Mantém automaticamente consistência de personagem e continuidade de quadro.
---

# Gerar storyboard

Cria storyboards via fila de geração; a proporção da imagem é definida automaticamente conforme content_mode.

> Especificações dos modos de geração em `.claude/references/generation-modes.md`.

## Chamadas de ferramentas

**Importante: a geração de storyboard deve enfileirar via as ferramentas MCP abaixo. Este skill não fornece scripts Python/Shell; não use BASH para chamar `python .../scripts/*.py`.**

Enfileirar via ferramenta MCP:

| Operação | Ferramenta |
|------|------|
| Enviar todas as storyboards faltantes | `mcp__arcreel__generate_storyboards({"script": "episode_1.json"})` |
| Regenerar IDs específicos | `mcp__arcreel__generate_storyboards({"script": "episode_1.json", "segment_ids": ["E1S05"]})` |
| Regenerar vários IDs | `mcp__arcreel__generate_storyboards({"script": "episode_1.json", "segment_ids": ["E1S01", "E1S02"]})` |

> **Regra de seleção**: `segment_ids` aceita segment_id de narration e scene_id de drama; se omitido, envia todos os faltantes.
>
> **Dependência**: o generation worker deve estar online (canais independentes de imagem/vídeo); o worker cuida da geração real e do rate control.

## Fluxo de trabalho

1. **Carregar projeto e script** — confirmar que todos os personagens têm imagem `character_sheet`
2. **Gerar storyboards** — a ferramenta MCP detecta content_mode automaticamente e encadeia tarefas dependentes pela relação de vizinhança
3. **Checkpoint de revisão** — mostrar cada storyboard; o usuário aprova ou pede regeneração
4. **Atualizar o script** — atualizar caminho `storyboard_image` e status da cena

## Mecanismo de consistência de personagem

A ferramenta MCP trata automaticamente as referências abaixo; não é preciso especificar à mão:
- **character_sheet**: arte do personagem em cena, mantém aparência consistente
- **scene_sheet / prop_sheet**: artes de cena / prop que aparecem na cena
- **Referência de produto (projetos anúncio/curta)**: se o shot tem `products_in_shot` não vazio, injeta automaticamente a referência de produto **antes** de todas as outras (com product sheet: sheet + original; sem sheet: original direto) e anexa instrução de restauração em alta fidelidade — image_prompt não precisa repetir a aparência do produto
- **Storyboard anterior**: segmentos adjacentes citam por padrão, melhorando a continuidade de quadro
- Quando o segmento marca `segment_break=true`, pula a referência da storyboard anterior

## Template de prompt

Montar o prompt a partir dos campos do JSON do script:

```
Storyboard da cena [scene_id/segment_id]:

- Descrição do quadro: [visual.description]
- Composição do shot: [visual.shot_type]
- Ponto de partida do movimento de câmera: [visual.camera_movement]
- Condições de luz: [visual.lighting]
- Atmosfera do quadro: [visual.mood]
- Personagens: [characters_in_scene]
- Ação: [action]

Requisito de estilo: estilo de storyboard cinematográfico, conforme o style do projeto.
Os personagens devem ser totalmente consistentes com as imagens de referência fornecidas.
```

> A proporção da imagem é definida por parâmetro da API, não no prompt.

## Checagem pré-geração

- [ ] Todos os personagens têm imagem character_sheet aprovada
- [ ] Descrição visual da cena completa
- [ ] Ação do personagem especificada

## Tratamento de erros

- Falha de uma cena não afeta o lote; registre a cena falha e continue
- Ao fim da geração, resuma todas as cenas falhas e os motivos
- Suporta geração incremental (pula cenas que já têm imagem)
- Use `mcp__arcreel__generate_storyboards({"script": "...", "segment_ids": [...]})` para regenerar cenas falhas
