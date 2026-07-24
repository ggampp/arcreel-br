# timeline-virtual-scroll Specification

## Purpose
A lista de storyboards da timeline usa virtual scroll (`useVirtualizer` de `@tanstack/react-virtual`), montando no DOM apenas as linhas de storyboard próximas ao viewport, com suporte a altura dinâmica e lazy loading nativo de imagens, garantindo rolagem fluida com muitos storyboards. Implementado em `frontend/src/components/canvas/timeline/ShotList.tsx`.

## Requirements
### Requirement: Renderização com virtual scroll
A lista de storyboards (`ShotList`) MUST renderizar as linhas com virtual scroll, montando no DOM apenas as linhas próximas ao viewport.

#### Scenario: Carga inicial com muitos storyboards
- **WHEN** o usuário abre um episódio com 50 storyboards
- **THEN** o DOM renderiza apenas as linhas visíveis no viewport mais o overscan (overscan = 6), e não os 50

#### Scenario: Rolagem para navegar
- **WHEN** o usuário rola a timeline para baixo
- **THEN** os SegmentCards que entram no alcance do viewport são renderizados e os que saem são desmontados

### Requirement: Suporte a altura dinâmica
O virtual scroll MUST suportar altura dinâmica do SegmentCard, incluindo mudanças por expandir/recolher.

#### Scenario: Expandir/recolher cartão
- **WHEN** o usuário expande um SegmentCard e a altura muda
- **THEN** a lista de virtual scroll ajusta corretamente a posição dos itens seguintes, sem saltos ou sobreposição

#### Scenario: Diferença entre altura estimada e real
- **WHEN** a altura real renderizada do SegmentCard difere da estimativa
- **THEN** o virtualizer corrige automaticamente via measureElement e a posição de rolagem permanece suave

### Requirement: Lazy loading de imagens
As tags `<img>` dentro do viewport MUST usar o atributo nativo de lazy loading do navegador.

#### Scenario: Imagens na região de overscan
- **WHEN** o SegmentCard está na região de overscan (já renderizado, mas ainda fora do viewport visível)
- **THEN** suas tags `<img>` têm `loading="lazy"`, e o navegador atrasa o carregamento até se aproximarem da área visível

### Requirement: Adaptação do posicionamento por rolagem
O posicionamento por rolagem disparado pelo Agent ou pelo sistema (scrollTarget) MUST funcionar no ambiente de virtual scroll.

#### Scenario: Agent rola até um storyboard fora do DOM
- **WHEN** scrollTarget aponta para um segment ID que não está no DOM
- **THEN** o sistema rola até a posição alvo via virtualizer.scrollToIndex e o SegmentCard alvo é renderizado e fica visível

#### Scenario: Destaque após posicionamento por rolagem
- **WHEN** a rolagem posiciona no segment alvo
- **THEN** o SegmentCard alvo executa a animação de flash de destaque, igual ao comportamento atual
