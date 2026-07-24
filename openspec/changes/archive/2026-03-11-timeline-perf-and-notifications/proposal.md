## Why

O painel de storyboards (Timeline) em episódios com 30–100 storyboards tem problemas graves de performance e experiência: renderização DOM completa faz imagens/vídeos carregarem ao mesmo tempo e estourar a largura de banda; qualquer mudança de recurso dispara invalidação global de cache e recarrega toda a mídia; em operações em lote do Agent, a notificação mostra só uma mudança e o usuário não percebe o conjunto.

## What Changes

- **Virtual scroll**: TimelineCanvas passa a usar @tanstack/react-virtual, renderizando só SegmentCards próximos ao viewport e reduzindo na raiz o número de requisições concorrentes
- **Lazy loading**: `<img>` com `loading="lazy"`; `<video>` só define `src` ao entrar no viewport
- **Invalidação precisa de cache**: substituir o `mediaRevision: number` global por `entityRevisions: Record<string, number>` (chave `entity_type:entity_id`), construindo a chave direto de `entity_type` + `entity_id` do evento SSE e incrementando só a entidade alterada. Cobre todos os 7 consumidores: SegmentCard, CharacterCard, ClueCard, OverviewCanvas, AssetSidebar, AvatarStack, VersionTimeMachine
- **Adaptação do posicionamento por rolagem**: `useScrollTarget` adapta ao virtual scroll, usando `virtualizer.scrollToIndex()` no lugar de `scrollIntoView()`
- **Agregação de notificações**: em `useProjectEventsSSE`, agrupar mudanças do mesmo tipo por `entity_type:action`; toast e workspace notification mostram texto agregado (ex.: "A IA adicionou 3 personagens: Zhang San, Li Si, Wang Wu")

## Capabilities

### New Capabilities
- `timeline-virtual-scroll`: virtual scroll e lazy loading de mídia na timeline, reduzindo requisições de rede concorrentes e quantidade de DOM
- `precise-cache-invalidation`: invalidação de cache por granularidade de entidade, em substituição a mediaRevision global, cobrindo todos os 7 componentes consumidores de mídia
- `batch-notification-aggregation`: agregação de notificações de mudanças SSE, unindo mudanças do mesmo tipo no mesmo lote em uma notificação legível

### Modified Capabilities
(não é necessário alterar comportamento de specs existentes)

## Impact

- **Dependência frontend**: adicionar `@tanstack/react-virtual`
- **Componentes frontend**: TimelineCanvas, SegmentCard (MediaColumn), CharacterCard, ClueCard, OverviewCanvas, AssetSidebar, AvatarStack, VersionTimeMachine, hook useScrollTarget
- **Store frontend**: app-store (entityRevisions substitui mediaRevision)
- **Hooks frontend**: useProjectEventsSSE (invalidação precisa + agregação de notificações), useProjectAssetSync (mantém invalidação total como fallback)
- **Backend**: sem mudanças (eventos SSE já carregam informação suficiente)
