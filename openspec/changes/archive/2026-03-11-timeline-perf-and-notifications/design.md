## Context

O painel de storyboards do frontend do ArcReel (TimelineCanvas) empilha todos os SegmentCards com `overflow-y-auto` simples, sem virtual scroll nem lazy loading. Um episódio costuma ter 30–100 storyboards; na carga da página todas as requisições de imagem e vídeo disparam ao mesmo tempo.

Quando qualquer recurso muda, `invalidateMediaAssets()` incrementa o contador global `mediaRevision`, fazendo todos os componentes que assinam esse valor (SegmentCard, CharacterCard, ClueCard, OverviewCanvas, AssetSidebar, AvatarStack, VersionTimeMachine) dispararem mudança de URL de mídia `?v=N` e o navegador recarregar todos os recursos.

Em operações em lote do Agent (ex.: adicionar 5 personagens de uma vez), o diff do backend gera corretamente várias mudanças, mas no frontend `selectPrimaryChange()` / `selectNotificationChange()` escolhem só 1 item do array para exibir.

## Goals / Non-Goals

**Goals:**
- Reduzir o número de requisições de mídia concorrentes da Timeline de N (total de storyboards) para a quantidade visível no viewport + overscan (~8–12)
- Quando uma entidade muda, a mídia de outras entidades não é recarregada (cobrindo todos os 7 componentes consumidores)
- Em operações em lote do Agent, o usuário percebe todas as mudanças (notificação agregada)

**Non-Goals:**
- Mudança no protocolo SSE do backend (a informação atual dos eventos já basta)
- Otimização de headers de cache no servidor (ETag/Last-Modified)
- Paginação / infinite scroll
- Centro de notificações / histórico de notificações

## Decisions

### 1. Escolha de virtual scroll: @tanstack/react-virtual

**Escolha**: @tanstack/react-virtual v3  
**Alternativas**: react-window, react-virtuoso  
**Justificativa**:
- Suporte nativo a altura dinâmica (`measureElement` + ResizeObserver); SegmentCard tem estados expandido/recolhido
- Sem invasão de UI; só fornece o hook virtualizer, compatível com o sistema de estilos Tailwind existente
- O projeto já usa o ecossistema @tanstack (react-query etc.); mantém consistência de stack
- `estimateSize` em 200px de altura estimada; overscan em 5

### 2. Estratégia de lazy loading: nativo + virtual scroll

**Escolha**: o virtual scroll já implementa lazy loading naturalmente (SegmentCard fora do viewport não renderiza); `<img>` dentro do viewport ganha `loading="lazy"` como segunda camada  
**Justificativa**: o virtual scroll resolve o problema na raiz; `loading="lazy"` só otimiza imagens na região de overscan, sem lógica extra de IntersectionObserver

### 3. Invalidação de cache: número de versão por entidade (chave entity_type:entity_id)

**Escolha**: `entityRevisions: Record<string, number>`, chave no formato `entity_type:entity_id` (ex.: `segment:seg_001`, `character:Zhang San`, `clue:arma do crime`, `project:project`)  
**Alternativas**:
- Versão por caminho de arquivo — caminho de personagem/pista é incerto e exige lógica extra de derivação
- Diff no frontend dos dados de scripts antes/depois — alta complexidade, pouco confiável  
**Justificativa**:
- `entity_type` + `entity_id` no evento SSE já estão prontos, sem derivação
- Cobre de forma unificada os 7 consumidores; cada um assina a chave da própria entidade
- O caminho de envio em lote do Worker (`emit_project_change_batch`) trata corretamente primeira geração e regeneração
- Manter `invalidateAllEntities()` como fallback (quando o canal de polling de tasks conclui sem chave concreta)

**Lista de migração dos consumidores:**

| Componente | Assinatura antiga | Nova chave de assinatura |
|------|--------|-----------|
| SegmentCard | `mediaRevision` | `segment:{segment_id}` |
| CharacterCard | `mediaRevision` | `character:{character_name}` |
| ClueCard | `mediaRevision` | `clue:{clue_name}` |
| OverviewCanvas | `mediaRevision` | `project:project` |
| AssetSidebar | `mediaRevision` (via props) | `character:{name}` / `clue:{name}` (cada subcomponente assina sozinho) |
| AvatarStack | `mediaRevision` | `character:{name}` / `clue:{name}` |
| VersionTimeMachine | `mediaRevision` | `{resourceType}:{resourceId}` (chave dinâmica) |

### 4. Adaptação do posicionamento por rolagem

**Escolha**: manter o mapeamento `segmentId → virtualIndex`; ao disparar scrollTarget, chamar `virtualizer.scrollToIndex()`  
**Justificativa**: com virtual scroll o segment alvo pode não estar no DOM; não dá para usar `getElementById` + `scrollIntoView()`

### 5. Agregação de notificações: agrupar por entity_type:action

**Escolha**: agrupar as changes do mesmo lote por `entity_type:action` e gerar um texto agregado por grupo  
**Alternativa**: um toast por mudança  
**Justificativa**: 5 toasts para 5 personagens é má experiência; agregar em "A IA adicionou 3 personagens: Zhang San, Li Si, Wang Wu" é mais amigável

## Risks / Trade-offs

- **[Desvio na estimativa de altura dinâmica]** → `estimateSize` impreciso pode causar saltos na rolagem; mitigar com correção em tempo real via `measureElement`
- **[Crescimento de memória de entityRevisions]** → projetos grandes podem ter muitas chaves; na prática 100 storyboards + 20 personagens + 10 pistas ≈ 130 chaves, desprezável
- **[Experiência do caminho de fallback de invalidação total]** → em `useProjectAssetSync`, ao concluir a task ainda há invalidação total; é caso raro (compensação quando o SSE desconecta), aceitável
- **[Refatoração de props do AssetSidebar]** → hoje o AssetSidebar recebe `mediaRevision` por props; precisa que cada subcomponente assine o store; mudança um pouco maior, mas alinhada às melhores práticas do zustand
- **[Truncamento do texto de notificação agregada]** → com mais de 5 mudanças do mesmo tipo, truncar em "A IA adicionou 5 personagens: Zhang San, Li Si… etc."
