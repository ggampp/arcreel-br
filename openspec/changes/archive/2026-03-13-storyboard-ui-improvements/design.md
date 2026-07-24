## Context

SegmentCard é o cartão central do painel de storyboards, renderizado na lista de virtual scroll do TimelineCanvas. Hoje a área de cabeçalho só exibe o ID do storyboard, o badge de duração somente leitura e a pilha de avatares de personagens. O `duration_seconds` do storyboard (4/6/8s) já é suportado de ponta a ponta no modelo de dados e na API PATCH do backend, mas o frontend não oferece ponto de edição. O campo de pistas (`clues_in_segment` / `clues_in_scene`) também existe no modelo, mas o `SegmentCard` o recebe como `_clues` e nunca o renderiza.

## Goals / Non-Goals

**Goals:**
- Permitir que o usuário troque a duração do storyboard (4/6/8s) direto no cabeçalho do cartão, com a duração total do episódio vinculada
- Exibir no cabeçalho do cartão as miniaturas das pistas associadas, lado a lado com a pilha de avatares de personagens
- Nos popovers de hover, unificar etiquetas de tipo para distinguir "Personagem" e "Cena/Prop"

**Non-Goals:**
- Não alterar API de backend nem modelo de dados
- Não mudar a lógica de virtual scroll do TimelineCanvas
- Não adicionar nenhuma informação nova na área de conteúdo (três colunas) do SegmentCard

## Decisions

### Decisão 1: Seletor de duração usa Popover, não ciclo por clique

**Escolha**: clicar no badge de duração abre um Popover com três botões 4s / 6s / 8s, com o valor atual em destaque.

**Justificativa**: ciclar (4→6→8→4) não é intuitivo; o usuário não vê todas as opções de uma vez. O Popover reutiliza o componente `Popover` existente, com baixo custo de implementação e estilo alinhado às outras interações em popover do projeto.

**Alternativa**: Segmented Control de três opções sempre visível em linha — consome espaço horizontal e, com largura limitada no cabeçalho, comprime o badge de ID e a área de avatares.

### Decisão 2: Mudança de duração pelo canal existente onUpdatePrompt

**Escolha**: chamar `onUpdatePrompt(segmentId, "duration_seconds", newValue)`, reutilizando o encadeamento completo `StudioCanvasRouter` → `API.updateSegment` / `API.updateScene` → `refreshProject()`.

**Justificativa**: sem nova prop nem novo callback; a API PATCH do backend já suporta `duration_seconds`; a duração total é reaggregada a partir dos segments após `refreshProject()`.

### Decisão 3: ClueStack como componente independente, lado a lado com AvatarStack

**Escolha**: criar `ClueStack.tsx` (em `frontend/src/components/ui/`), sem generalizar o AvatarStack. Layout do cabeçalho do SegmentCard: AvatarStack (personagens) à esquerda, divisor vertical, ClueStack (pistas) à direita.

**Justificativa**: personagens e pistas têm semântica diferente (personagem tem character_sheet, pista tem clue_sheet; conteúdo do popover de hover é diferente); unificar forçaria complexidade no AvatarStack. Replicar o padrão estrutural do AvatarStack (imagem + fallback de inicial + hover popover + overflow badge) tem baixo custo e não interfere.

**Formato**: miniaturas de pista usam `rounded` (quadrado arredondado), não `rounded-full`, alinhadas ao estilo das imagens dos cartões de pista no Lorebook à esquerda.

### Decisão 4: Estilo unificado das etiquetas de tipo no popover

O popover de personagem (AvatarPopover) ganha a etiqueta `Personagem` (indigo) à direita do nome; o popover de pista mostra `Cena` (amber) ou `Prop` (emerald) conforme `Clue.type`. Ambos são Badges pequenos, mantendo a estrutura de conteúdo do popover.

## Risks / Trade-offs

- **Vinculação da duração total depende do refresh do backend**: após mudar a duração, é preciso esperar `refreshProject()` para atualizar a duração total no cabeçalho (~200–500 ms de atraso). Como a troca de duração de storyboard é operação de baixa frequência, não se faz atualização otimista.
- **Taxa alta de imagens de pista ausentes**: em projetos iniciais as pistas costumam não ter `clue_sheet`; o fallback é bloco colorido com a inicial — a função está completa, mas o visual depende de o usuário ter enviado imagens de pista.
