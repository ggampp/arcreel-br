# Modo ad não integra o gate de review step1→step2

O modo de conteúdo ad (anúncio/curta) não integra o pipeline de roteiro em duas etapas step1→step2 nem o gate de review web bloqueante. O escopo do gate permanece content_mode ∈ {drama, narration} e effective_mode ≠ reference_video.

## Por que isso está fora de escopo

Os dois problemas centrais que o gate de review step1→step2 (docs/adr/0041) resolve **não se sustentam estruturalmente** em ad:

- **Distorção por reescrita secundária**: em drama / narration, o conteúdo falado literal precisa atravessar as duas etapas step1→step2, com risco de reescrita entre etapas; o roteiro ad é gerado em uma única passagem e produz a estrutura final direto (`shots[]` plano + texto de locução de primeira classe `voiceover_text`) — não há fronteira entre etapas, logo não há reescrita entre etapas.
- **Estado intermediário não revisável**: em drama / narration, entre o fim do step1 e o step2 ainda não rodado, o usuário não tem visibilidade na web; o roteiro ad grava direto em `scripts/episode_1.json`, e a timeline web fica visível e editável o tempo todo.

O único ponto que se sustenta em parte — «falta de checkpoint duro antes da geração visual cara» — é coberto por dois lados: ad é sempre mono-episódio, com poucos takes (filme final 15–90 s), e o raio de explosão de custo é muito menor que um episódio drama; o workflow do agent já tem o acordo de confirmação por estágio — após gerar o roteiro, apresenta ao usuário a lista de takes e o texto de locução, soft gate de `product_sheet`, e review de fidelidade de produto após o storyboard (intercepta antes do custo de vídeo).

«Geração one-shot de roteiro ad sem arquivo intermediário step1» é design intencional do ADR 0033; a entrada «ad (modo anúncio/curta)» de CONTEXT.md registra esse contrato. Construir um pipeline em duas etapas só para ad por simetria do gate tem retorno desproporcional.

## Condições de revisitação

- ad apresentar dor real de fidelidade: o texto publicitário literal fornecido pelo usuário no brief for reescrito pelo LLM e a origem não puder ser localizada;
- a geração de roteiro ad evoluir para duas etapas por outros motivos — aí o gate entra em sincronia (após a consolidação do registry de nomes de arquivo step1, basta registrar em um só lugar; ver #985).

## Pedidos anteriores

- #987 — modo de conteúdo ad sem integração ao gate de review step1→step2 (lacuna de contrato)
