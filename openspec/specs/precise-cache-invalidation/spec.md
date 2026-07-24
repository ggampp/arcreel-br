# precise-cache-invalidation Specification

## Purpose
Manter um número de revisão de mídia independente por entidade (chave no formato `entity_type:entity_id`), em substituição ao contador global, de modo que, ao concluir geração de storyboard/vídeo/imagem de design de ativo, apenas a URL de mídia da entidade correspondente seja atualizada, sem re-render completo. As revisões ficam no app-store (`getEntityRevision`), incrementadas por `useProjectEventsSSE` conforme eventos SSE (`buildEntityRevisionKey`); consumidores (`StudioCanvasRouter`, `PreprocessingView` etc.) assinam por chave de entidade.

## Requirements
### Requirement: Rastreamento de versão por granularidade de entidade
O sistema MUST manter um número de versão independente por entidade (chave no formato `entity_type:entity_id`), em substituição ao contador global de mídia. Todos os consumidores de ativos de mídia (cartões de storyboard/vídeo, CharacterCard, miniaturas de cena/prop, OverviewCanvas, AssetSidebar, AvatarStack, VersionTimeMachine) devem migrar para o novo mecanismo.

#### Scenario: Geração de um storyboard concluída

- **WHEN** o evento SSE reporta storyboard_ready do segment "seg_001"
- **THEN** apenas a revisão de `segment:seg_001` é incrementada; as de outras entidades permanecem iguais

#### Scenario: Geração de um vídeo concluída

- **WHEN** o evento SSE reporta video_ready do segment "seg_003"
- **THEN** apenas a revisão de `segment:seg_003` é incrementada; as de outras entidades permanecem iguais

#### Scenario: Geração da imagem de design de personagem concluída

- **WHEN** o evento SSE reporta updated do character "Zhang San"
- **THEN** apenas a revisão de `character:Zhang San` é incrementada; as de outras entidades permanecem iguais

#### Scenario: Geração da imagem de design de prop concluída

- **WHEN** o evento SSE reporta updated do prop "arma do crime"
- **THEN** apenas a revisão de `prop:arma do crime` é incrementada; as de outras entidades permanecem iguais

#### Scenario: Atualização de metadados do projeto

- **WHEN** o evento SSE reporta updated do project
- **THEN** a revisão de `project:project` é incrementada

### Requirement: Construir chave de versão diretamente a partir do evento SSE
O sistema MUST construir a chave de versão a partir dos campos `entity_type` e `entity_id` do evento de mudança SSE, sem derivar caminho de arquivo.

#### Scenario: Evento storyboard_ready

- **WHEN** chega um evento com `entity_type: "segment"`, `entity_id: "seg_005"`, `action: "storyboard_ready"`
- **THEN** incrementa a revisão da chave `segment:seg_005`

#### Scenario: Evento character updated

- **WHEN** chega um evento com `entity_type: "character"`, `entity_id: "Zhang San"`, `action: "updated"`
- **THEN** incrementa a revisão da chave `character:Zhang San`

#### Scenario: Evento prop updated

- **WHEN** chega um evento com `entity_type: "prop"`, `entity_id: "arma do crime"`, `action: "updated"`
- **THEN** incrementa a revisão da chave `prop:arma do crime`

### Requirement: Assinatura precisa por componente
Cada componente consumidor de mídia MUST assinar apenas a revisão da entidade relevante.

#### Scenario: SegmentCard com assinatura precisa

- **WHEN** a geração do storyboard do segment "seg_001" conclui
- **THEN** apenas o SegmentCard de "seg_001" dispara mudança de URL de mídia e re-render; outros SegmentCards não são afetados

#### Scenario: CharacterCard com assinatura precisa

- **WHEN** a geração da imagem de design do character "Zhang San" conclui
- **THEN** apenas o CharacterCard de "Zhang San", o avatar correspondente no AvatarStack e a entrada no AssetSidebar re-renderizam; outros personagens não são afetados

#### Scenario: Miniatura de prop com assinatura precisa

- **WHEN** a geração da imagem de design do prop "arma do crime" conclui
- **THEN** apenas a miniatura de cena/prop e a entrada no AssetSidebar de "arma do crime" re-renderizam

#### Scenario: OverviewCanvas com assinatura precisa

- **WHEN** a imagem de estilo do projeto é atualizada
- **THEN** apenas a imagem de estilo no OverviewCanvas re-renderiza

#### Scenario: VersionTimeMachine com assinatura precisa

- **WHEN** uma nova versão de um recurso é gerada
- **THEN** o VersionTimeMachine assina a chave da entidade do recurso em exibição e só rebusca a lista de versões quando essa entidade muda

### Requirement: Invalidação total como fallback
Quando não for possível determinar a entidade alterada (ex.: canal de polling de tasks), o sistema MUST manter invalidação total de cache como mecanismo de fallback.

#### Scenario: Task concluída sem evento SSE

- **WHEN** useProjectAssetSync detecta que a task passou de não-succeeded para succeeded
- **THEN** chama o método de invalidação total e incrementa unificadamente as revisões de todas as entidades rastreadas

### Requirement: Regeneração de ativos
Ao regenerar ativos, o mecanismo de invalidação de cache MUST disparar corretamente.

#### Scenario: Regeneração de storyboard

- **WHEN** o usuário regenera o storyboard do segment "seg_001" (caminho do arquivo igual, conteúdo atualizado)
- **THEN** o Worker envia evento storyboard_ready, o frontend incrementa a revisão de `segment:seg_001` e o navegador carrega o novo conteúdo

#### Scenario: Regeneração da imagem de design de personagem

- **WHEN** o usuário regenera a imagem de design do character "Zhang San"
- **THEN** o Worker envia evento character updated, o frontend incrementa a revisão de `character:Zhang San` e o navegador carrega o novo conteúdo
