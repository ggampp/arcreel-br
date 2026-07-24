## ADDED Requirements

### Requirement: Duração do storyboard com troca interativa

O elemento de exibição de duração no cabeçalho do SegmentCard SHALL permitir que o usuário clique e abra um seletor para alternar entre as três opções 4s, 6s e 8s; após a seleção, o novo valor é gravado no backend via callback `onUpdatePrompt` e, ao concluir o salvamento, a duração total do episódio é atualizada.

#### Scenario: Clicar no badge de duração abre o seletor

- **WHEN** o usuário clica no badge de duração no cabeçalho do SegmentCard (ex.: "4s")
- **THEN** abre um Popover listando os três botões "4s", "6s" e "8s", com o valor atual em destaque

#### Scenario: Selecionar nova duração e salvar

- **WHEN** o usuário clica em uma opção de duração no seletor (ex.: "6s")
- **THEN** o Popover fecha, o badge mostra imediatamente "6s" e dispara o salvamento no backend via `onUpdatePrompt(segmentId, "duration_seconds", 6)`

#### Scenario: Cancelar seleção

- **WHEN** o usuário clica fora do Popover
- **THEN** o Popover fecha e o badge de duração mantém o valor original

#### Scenario: Somente leitura sem onUpdatePrompt

- **WHEN** o SegmentCard não fornece a prop `onUpdatePrompt` (modo somente leitura)
- **THEN** o badge de duração não é clicável e a aparência é a de estado somente leitura (sem efeito de hover)

### Requirement: Atualização vinculada da duração total do episódio

A duração total exibida no cabeçalho do TimelineCanvas SHALL atualizar automaticamente após qualquer mudança de duração de storyboard e o refresh dos dados do projeto, sem operação extra.

#### Scenario: Duração total atualiza após alterar duração do storyboard

- **WHEN** o usuário altera a duração de um storyboard, o backend salva com sucesso e `refreshProject()` conclui
- **THEN** a duração total no cabeçalho do TimelineCanvas é recalculada somando `duration_seconds` de todos os storyboards, refletindo o valor mais recente
