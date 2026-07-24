## Why

O SegmentCard do painel de storyboards tem duas lacunas de informação: a duração do storyboard (4/6/8s) hoje é somente leitura e não pode ser alterada direto na interface, forçando o usuário a outros caminhos; o campo de pistas associadas (cenas/props) já existe no modelo de dados, mas nunca foi exibido no cabeçalho do cartão, deixando o contexto de criação incompleto.

## What Changes

- **DurationBadge → DurationSelector**: o rótulo de duração do storyboard deixa de ser somente leitura e passa a ser interativo; o clique abre um Popover com 4s / 6s / 8s; após a seleção, o novo valor é gravado no backend pelo canal existente `onUpdatePrompt`; a duração total no header do episódio atualiza com o refresh dos dados.
- **Novo componente ClueStack**: no lado direito do cabeçalho do SegmentCard, exibir miniaturas das pistas associadas (quadrado arredondado, no estilo das imagens do Lorebook à esquerda); no hover, popover com nome da pista, imagem e etiqueta de tipo (cena / prop).
- **Popover de personagem com etiqueta "Personagem"**: AvatarPopover ganha a etiqueta de tipo `Personagem` ao lado do nome, no mesmo estilo do popover de pistas, para facilitar a distinção.

## Capabilities

### New Capabilities

- `segment-duration-selector`: a duração do storyboard no cabeçalho do SegmentCard pode ser trocada pelo seletor em popover (4/6/8s), com atualização vinculada da duração total do episódio.
- `clue-stack-display`: o cabeçalho do SegmentCard exibe a pilha de miniaturas das pistas associadas; no hover, o popover mostra nome, imagem e etiqueta de tipo (cena/prop); o popover de personagem ganha em sincronia a etiqueta de tipo "Personagem".

### Modified Capabilities

(nenhum spec existente a alterar)

## Impact

- Só mudanças no frontend; sem alteração de API de backend nem de modelo de dados
- Arquivos modificados: `frontend/src/components/canvas/timeline/SegmentCard.tsx`, `frontend/src/components/ui/AvatarStack.tsx`
- Arquivo novo: `frontend/src/components/ui/ClueStack.tsx`
- O PATCH de backend `/projects/{name}/segments/{segment_id}` já suporta o campo `duration_seconds`; sem mudanças necessárias
