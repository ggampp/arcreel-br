## 1. Seletor de duração do storyboard (DurationSelector)

- [x] 1.1 Transformar `DurationBadge` em `SegmentCard.tsx` em `DurationSelector`: clicável quando `onUpdatePrompt` existe, abrindo Popover; sem `onUpdatePrompt`, manter aparência somente leitura
- [x] 1.2 No Popover, renderizar três botões de opção 4s / 6s / 8s, com o valor atual em destaque
- [x] 1.3 Ao selecionar o novo valor, chamar `onUpdatePrompt(segmentId, "duration_seconds", newValue)` e fechar o Popover
- [x] 1.4 Ao clicar fora do Popover, fechar o Popover sem alterar o valor da duração

## 2. Componente ClueStack

- [x] 2.1 Criar `frontend/src/components/ui/ClueStack.tsx`, implementando a pilha de miniaturas de pistas com base na estrutura do AvatarStack
- [x] 2.2 Formato da imagem de pista: quadrado arredondado (`rounded`), tamanho igual ao avatar de personagem (`h-7 w-7`), empilhamento com `-space-x-2`
- [x] 2.3 Sem `clue_sheet`, exibir bloco colorido com a inicial (quadrado arredondado), cor determinada pelo hash do nome
- [x] 2.4 Com mais de 4 pistas, exibir badge de overflow `+n`
- [x] 2.5 Quando o storyboard não tem pistas associadas, não renderizar ClueStack

## 3. Popover de hover da pista (CluePopover)

- [x] 3.1 Em `ClueStack.tsx`, implementar `CluePopover`: à esquerda a imagem da pista (ou ícone placeholder sem imagem); à direita nome + etiqueta de tipo + resumo da descrição
- [x] 3.2 Com `type === "location"`, etiqueta "Cena" (tom amber); com `type === "prop"`, etiqueta "Prop" (tom emerald)
- [x] 3.3 Layout, tamanho e layer do popover alinhados ao AvatarPopover

## 4. Popover de personagem com etiqueta de tipo

- [x] 4.1 Alterar `AvatarPopover` em `AvatarStack.tsx`: ao lado do nome do personagem, adicionar a etiqueta "Personagem" (tom indigo), no mesmo estilo das etiquetas do popover de pistas

## 5. Integração no cabeçalho do SegmentCard

- [x] 5.1 Em `SegmentCard.tsx`, obter os nomes das pistas associadas (ler de `clues_in_segment` / `clues_in_scene`, no mesmo padrão de `getCharacterNames`)
- [x] 5.2 Renomear o parâmetro `_clues` para `clues` e renderizar `ClueStack` no cabeçalho; layout do lado direito: AvatarStack (esquerda) + divisor vertical + ClueStack (direita), separados por linha vertical (`border-l border-gray-700`)
- [x] 5.3 Substituir `DurationBadge` por `DurationSelector`, conectando o callback `onUpdatePrompt`

## 6. Verificação

- [x] 6.1 Rodar `pnpm test` confirmando que todos os testes passam
- [x] 6.2 Rodar `pnpm typecheck` confirmando zero erros de tipo no TypeScript
