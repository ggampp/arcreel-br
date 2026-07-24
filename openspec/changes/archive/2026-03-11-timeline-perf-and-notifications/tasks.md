## 1. Dependências e infraestrutura do frontend

- [x] 1.1 Instalar a dependência @tanstack/react-virtual
- [x] 1.2 No app-store, implementar `entityRevisions: Record<string, number>` no lugar de `mediaRevision: number`, com métodos `invalidateEntities(keys: string[])` e `getEntityRevision(key: string)`, mantendo `invalidateAllEntities()` como invalidação total de fallback

## 2. Virtual scroll

- [x] 2.1 Em TimelineCanvas, introduzir `useVirtualizer` com `estimateSize`(200px), `overscan`(5), `measureElement`
- [x] 2.2 Trocar a lista de SegmentCard de renderização completa com `segments.map()` para renderização com posicionamento absoluto via `virtualItems.map()`
- [x] 2.3 Adaptar `useScrollTarget`: manter o mapeamento `segmentId → virtualIndex`; ao disparar scrollTarget, chamar `virtualizer.scrollToIndex()` e, após a rolagem, executar o flash de destaque

## 3. Migrar todos os consumidores para assinatura precisa

- [x] 3.1 SegmentCard: trocar assinatura de `mediaRevision` por `entityRevisions["segment:{segment_id}"]`; em `<img>` adicionar `loading="lazy"`
- [x] 3.2 CharacterCard: trocar assinatura de `mediaRevision` por `entityRevisions["character:{name}"]`
- [x] 3.3 ClueCard: trocar assinatura de `mediaRevision` por `entityRevisions["clue:{name}"]`
- [x] 3.4 OverviewCanvas: trocar assinatura de `mediaRevision` por `entityRevisions["project:project"]`
- [x] 3.5 AssetSidebar: remover o repasse de props `mediaRevision`; cada subcomponente (CharacterSheetCard, ClueSheetCard) assina diretamente a chave de entidade correspondente no store
- [x] 3.6 AvatarStack: trocar assinatura de `mediaRevision` por cada avatar assinando `character:{name}` / `clue:{name}`
- [x] 3.7 VersionTimeMachine: trocar assinatura de `mediaRevision` por `entityRevisions["{resourceType}:{resourceId}"]`

## 4. Invalidação precisa de cache

- [x] 4.1 Alterar o callback `onChanges` de useProjectEventsSSE: construir a chave a partir de `entity_type` + `entity_id` do evento de mudança SSE e chamar `invalidateEntities(keys)` no lugar de `invalidateMediaAssets()`
- [x] 4.2 Alterar `refreshProject` de useProjectEventsSSE: não chamar mais `invalidateMediaAssets()` (a invalidação precisa já é tratada em onChanges)
- [x] 4.3 Alterar useProjectAssetSync: ao concluir a task, chamar `invalidateAllEntities()` como fallback
- [x] 4.4 Limpar o campo `mediaRevision` e o método `invalidateMediaAssets()` obsoletos no app-store (após confirmar que não há outros consumidores)

## 5. Agregação de notificações

- [x] 5.1 Implementar a função utilitária `groupChangesByType(changes)`: agrupar mudanças por `entity_type:action`
- [x] 5.2 Implementar as funções de texto agregado `formatGroupedNotificationText(group)` e `formatGroupedDeferredText(group)`, com truncamento (mais de 5 itens → "… etc.")
- [x] 5.3 Alterar o callback `onChanges` de useProjectEventsSSE: substituir `selectNotificationChange` → um toast por grupo após agrupar; substituir `selectPrimaryChange` → uma workspace notification por grupo após agrupar (navega para o primeiro do grupo)

## 6. Testes e verificação

- [x] 6.1 Escrever testes unitários das funções de agregação de notificações (groupChangesByType, formatGroupedNotificationText)
- [x] 6.2 Escrever testes unitários da lógica de invalidação precisa de cache (invalidateEntities / invalidateAllEntities de entityRevisions)
- [x] 6.3 Atualizar referências a `mediaRevision` nos testes existentes (stores.test.ts, useProjectAssetSync.test.tsx, OverviewCanvas.test.tsx)
- [x] 6.4 Rodar a suíte completa de testes do frontend (pnpm check) garantindo sem regressão
- [x] 6.5 Rodar a suíte completa de testes do backend (pytest) garantindo sem regressão
