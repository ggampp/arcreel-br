# batch-notification-aggregation Specification

## Purpose
Quando um lote de mudanças SSE contém várias mudanças do mesmo tipo, agregá-las em uma única notificação (toast / notificação persistente do workspace), evitando spam de toasts individuais. A lógica de agregação está em `frontend/src/utils/project-changes.ts` (`groupChangesByType` agrupa por `entity_type:action`, `formatGroupedNotificationText` gera o texto).

## Requirements
### Requirement: Agregar notificações de mudanças do mesmo tipo
Quando um lote de mudanças SSE contém várias mudanças do mesmo tipo, o sistema MUST agregá-las em uma única notificação, em vez de exibir apenas uma delas.

#### Scenario: Adicionar personagens em lote

- **WHEN** o Agent adiciona em lote 3 personagens (Zhang San, Li Si, Wang Wu) e o lote SSE contém 3 mudanças `character:created`
- **THEN** o sistema exibe um toast agregado: "Foram adicionados 3 personagens: Zhang San, Li Si, Wang Wu"

#### Scenario: Adicionar props em lote

- **WHEN** o Agent adiciona em lote 2 props (arma do crime, diário) e o lote SSE contém 2 mudanças `prop:created`
- **THEN** o sistema exibe um toast agregado: "Foram adicionados 2 props: arma do crime, diário"

#### Scenario: Mudança única mantém o formato original

- **WHEN** o lote SSE contém apenas 1 mudança `character:created`
- **THEN** o texto da notificação mantém o formato atual (ex.: "Personagem «Zhang San» criado")

### Requirement: Exibir mudanças agrupadas por tipo
Mudanças de tipos diferentes MUST ser exibidas em grupos, gerando uma notificação independente por grupo.

#### Scenario: Lote com tipos mistos

- **WHEN** um lote SSE contém 2 mudanças `character:created` e 1 mudança `episode:created`
- **THEN** o sistema gera dois toasts: um sobre personagens e outro sobre episódios

### Requirement: Agregar notificações do workspace
Notificações do workspace (persistentes, não toast) também MUST ser agregadas, navegando para a posição da primeira mudança do grupo.

#### Scenario: Workspace notification de criação de personagens em lote

- **WHEN** o Agent adiciona em lote 3 personagens e a source não é "webui"
- **THEN** é gerada uma workspace notification com texto agregado; o clique navega para o primeiro personagem

### Requirement: Truncar listas longas
Quando a quantidade de mudanças do mesmo tipo excede o limiar, o texto da notificação MUST ser truncado para manter legibilidade.

#### Scenario: Mais de 5 mudanças do mesmo tipo

- **WHEN** um lote SSE contém 8 mudanças `segment:updated`
- **THEN** o texto da notificação é truncado, ex.: "Foram atualizados 8 storyboards: seg_001, seg_002… etc."
