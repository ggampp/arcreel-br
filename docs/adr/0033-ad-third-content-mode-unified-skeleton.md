---
status: accepted
---

# Ad/curta-metragem como terceiro tipo de conteúdo: esqueleto de roteiro único, caminhos de geração ortogonais

O modo ad/curta (principalmente short video de venda) produz um único vídeo, não série multi-episódio, e precisa entrar no sistema de tipos. Antes, reference_video como valor de generation_mode trocava o esqueleto de roteiro inteiro (video_units no lugar de segments/scenes; content_mode não participava da escolha de estrutura) — as duas dimensões não eram de fato ortogonais; se o modo ad também aterrissasse «trocando o esqueleto», texto de voiceover, export de legendas, estimativa de custo e cálculo de status viveriam em duplicata nas duas estruturas. Decidimos: `ad` aterrissa como terceiro valor de content_mode, e o esqueleto de roteiro de ad é único, sem trocar conforme o caminho de geração.

## Decisão

- **`ad` como terceiro valor de content_mode**: reutiliza todos os mecanismos despachados por content_mode (variante de profile `CLAUDE.ad.md`, SCRIPT_SHAPES, imutável após criar, despacho do StatusCalculator).
- **Esqueleto de roteiro único**: o roteiro ad é `shots[]` plano (`shot_id`, E1S{n}); cada shot carrega rótulo `section` (o framework de venda hook→…→cta é atributo do shot, não estrutura aninhada) e texto de voiceover de primeira classe `voiceover_text`. Os dois caminhos de geração consomem o mesmo roteiro: o caminho storyboard gera imagem e vídeo shot a shot; o caminho reference_video **deriva grupos** dos shots em video_unit (índice leve que só referencia shot_id e o conjunto de referências, sem copiar conteúdo); shots ad e R2V Shot correspondem 1:1. generation_mode sob ad vira de fato a dimensão ortogonal «origem do vídeo».
- **ad só abre storyboard e reference_video**: grid não abre — a resolução por célula do grid conflita com o objetivo de alta fidelidade do produto; o valor de consistência de estilo em ad é carregado por produto/referência de estilo.
- **Sempre um único episódio**: episodes de projeto ad é sempre `[{episode: 1, …}]`, o roteiro é `scripts/episode_1.json`; a maquinaria por episódio (status/arquivo/versão/custo/export) zero mudança estrutural; o frontend esconde a semântica de episódio em ad. No futuro, «um produto, várias variantes» estende com cada episódio = uma variante.
- **Restrição de duração do shot injetada dinamicamente por generation_mode**: caminho storyboard enumera duro por supported_durations (restrição de capacidade do modelo); caminho reference inteiro livre 1–15s (ritmo de corte curto depende disso). Esqueleto unificado; restrição de valor segue o caminho.

## Por que não reutilizar a semântica «trocar esqueleto» nem elevar reference_video primeiro

O texto de voiceover precisa de fonte única cross-caminho (export de legendas e entrada futura de TTS); esqueleto duplo o duplicaria nas duas estruturas e forçaria ramo duplo em todo o downstream. Elevar reference_video a tipo de topo e só então aterrissar ad misturaria no enum de topo «semântica de conteúdo» (narration/drama/ad) e «esqueleto de geração» (reference_video) — exatamente a confusão de dimensões pela qual generation_mode foi criticado, subindo uma camada, e bloquearia o lançamento de ad atrás de uma grande refatoração. A forma «não engolir o esqueleto» de ad, por outro lado, vira modelo de reforma do problema legado: reference_video sob narration/drama pode voltar a generation_mode puro nessa forma; o plano de elevação precisa ser reavaliado à luz disso.

## Consequences

- VALID_CONTENT_MODES, SCRIPT_SHAPES, profile manifest, validador de dados e assistente de criação se estendem com o terceiro valor; campos exclusivos de ad (`target_duration`, `brief`, bucket `products`) estão na proposta e no ADR 0034.
- O redesenho do ledger de episódios precisa tratar ad como ledger de uma única entrada / isento de planejamento de split, sem assumir content_mode binário.
- O índice derivado de video_unit persiste no JSON do roteiro; shots são a única verdade de conteúdo; ao regenerar um unit, o agrupamento é reproduzível.
