## ADDED Requirements

### Requirement: Pilha de miniaturas de cenas/props

`ReferencesSection` SHALL exibir, via componente `ClueStack`, miniaturas das imagens de cenas (`sceneNames`) e props (`propNames`) associadas ao storyboard atual, em formato quadrado arredondado, empilhadas no mesmo estilo da pilha de avatares de personagens, mostrando no máximo 4, com o excedente indicado por badge de overflow `+n`.

#### Scenario: Exibir miniatura quando o ativo tem imagem

- **WHEN** o objeto de cena possui caminho `scene_sheet`, ou o objeto de prop possui caminho `prop_sheet`
- **THEN** a imagem correspondente é exibida em formato quadrado arredondado (`rounded`), com tamanho igual ao avatar de personagem (`h-7 w-7`)

#### Scenario: Placeholder com inicial quando o ativo não tem imagem

- **WHEN** o objeto de cena/prop não possui o caminho de sheet correspondente
- **THEN** é exibido um bloco colorido com a inicial do nome do ativo (quadrado arredondado), com cor determinada pelo hash do nome, seguindo a mesma regra de fallback dos avatares de personagem

#### Scenario: Não renderizar quando o storyboard não tem cenas/props associadas

- **WHEN** `sceneNames` e `propNames` estão ambos vazios
- **THEN** a pilha de miniaturas não é renderizada (`ClueStack` retorna null)

#### Scenario: Exibir quantidade de overflow quando há mais de 4 ativos

- **WHEN** o total de cenas + props associadas excede 4
- **THEN** apenas as 4 primeiras miniaturas são exibidas; as restantes são representadas por um badge cinza `+n`

### Requirement: Popover de hover do ativo

Ao passar o mouse sobre a miniatura de cena/prop (`RefThumbnail`), SHALL aparecer um popover (`RefPopover`) com a imagem do ativo, nome, etiqueta de tipo (cena/prop) e resumo da descrição, com layout consistente com o popover de personagem.

#### Scenario: Hover exibe detalhes do ativo

- **WHEN** o usuário passa o mouse sobre a miniatura de uma cena/prop
- **THEN** aparece um popover com a imagem do ativo à esquerda (ou ícone placeholder se não houver imagem) e, à direita, o nome do ativo e o resumo da primeira linha de description

#### Scenario: Popover exibe etiqueta de cena

- **WHEN** o ativo exibido no popover tem `kind` igual a `"scene"`
- **THEN** ao lado do nome é exibida a etiqueta "Cena" (tom amber)

#### Scenario: Popover exibe etiqueta de prop

- **WHEN** o ativo exibido no popover tem `kind` igual a `"prop"`
- **THEN** ao lado do nome é exibida a etiqueta "Prop" (tom emerald)

### Requirement: Popover de personagem exibe etiqueta de tipo "Personagem"

O popover da miniatura de personagem (`RefThumbnail`, `kind` igual a `"character"`) SHALL exibir a etiqueta de tipo "Personagem" ao lado do nome, no mesmo estilo das etiquetas de cena/prop, para facilitar a distinção do tipo de entidade.

#### Scenario: Hover no avatar de personagem exibe etiqueta "Personagem"

- **WHEN** o usuário passa o mouse sobre o avatar de um personagem
- **THEN** no popover, ao lado do nome do personagem, é exibida a etiqueta "Personagem" (tom indigo)
