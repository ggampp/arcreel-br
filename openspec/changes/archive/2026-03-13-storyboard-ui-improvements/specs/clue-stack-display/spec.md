## ADDED Requirements

### Requirement: Pilha de miniaturas de pistas

O cabeçalho do SegmentCard SHALL, à esquerda da pilha de avatares de personagens, exibir miniaturas das imagens das pistas associadas ao storyboard atual (`clues_in_segment` / `clues_in_scene`), em formato quadrado arredondado, empilhadas no mesmo estilo da pilha de avatares, mostrando no máximo 4, com o excedente indicado por badge de overflow `+n`.

#### Scenario: Exibir miniatura quando a pista tem imagem

- **WHEN** o objeto de pista possui caminho `clue_sheet`
- **THEN** a imagem correspondente é exibida em formato quadrado arredondado (`rounded`), com tamanho igual ao avatar de personagem (`h-7 w-7`)

#### Scenario: Placeholder com inicial quando a pista não tem imagem

- **WHEN** o objeto de pista não possui caminho `clue_sheet`
- **THEN** é exibido um bloco colorido com a inicial do nome da pista (quadrado arredondado), com cor determinada pelo hash do nome, seguindo a mesma regra de fallback dos avatares de personagem

#### Scenario: Não renderizar quando o storyboard não tem pistas associadas

- **WHEN** `clues_in_segment` / `clues_in_scene` do storyboard são arrays vazios
- **THEN** a pilha de miniaturas de pistas não é renderizada; o lado direito do cabeçalho mostra só a pilha de avatares de personagens

#### Scenario: Exibir quantidade de overflow quando há mais de 4 pistas

- **WHEN** o storyboard tem mais de 4 pistas associadas
- **THEN** apenas as 4 primeiras miniaturas são exibidas; as restantes são representadas por um badge cinza `+n`

### Requirement: Popover de hover da pista

Ao passar o mouse sobre a miniatura da pista, SHALL aparecer um popover com a imagem da pista, nome, etiqueta de tipo (cena/prop) e resumo da descrição, com layout consistente com o popover de personagem.

#### Scenario: Hover exibe detalhes da pista

- **WHEN** o usuário passa o mouse sobre a miniatura de uma pista
- **THEN** aparece um popover com a imagem da pista à esquerda (ou ícone placeholder se não houver imagem) e, à direita, o nome da pista e um resumo de uma linha da descrição

#### Scenario: Popover exibe etiqueta de tipo cena

- **WHEN** no popover o `type` da pista é `"location"`
- **THEN** ao lado do nome é exibida a etiqueta "Cena" (tom amber)

#### Scenario: Popover exibe etiqueta de prop

- **WHEN** no popover o `type` da pista é `"prop"`
- **THEN** ao lado do nome é exibida a etiqueta "Prop" (tom emerald)

### Requirement: Popover de personagem ganha etiqueta de tipo "Personagem"

AvatarPopover SHALL exibir a etiqueta de tipo "Personagem" ao lado do nome do personagem, no mesmo estilo das etiquetas do popover de pistas, para facilitar a distinção entre os dois tipos de entidade.

#### Scenario: Hover no avatar de personagem exibe etiqueta "Personagem"

- **WHEN** o usuário passa o mouse sobre o avatar de um personagem
- **THEN** no popover, ao lado do nome do personagem, é exibida a etiqueta "Personagem" (tom indigo)
