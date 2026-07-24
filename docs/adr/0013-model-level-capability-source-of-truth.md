---
status: accepted
---

# Declaração de capacidade de provider converge no nível do modelo; capacidade do provider é visão somente-leitura derivada

Modelos diferentes do mesmo provider têm capacidades diferentes (ex.: modelo de texto Ark lite não suporta structured_output, mas a declaração de topo cobria e a chamada nativa quebrava). Declarar `media_types` / `capabilities` no topo do provider leva inevitavelmente a descompasso entre a declaração e a capacidade real de modelos individuais. Decidimos declarar capacidades (enums de capability de text/image/video) em `ModelInfo` (nível de modelo); `media_types` / `capabilities` de `ProviderMeta` viram `@property` somente-leitura agregadas a partir de todos os modelos abaixo, sem armazenamento próprio — a fonte de verdade da capacidade é o modelo; a capacidade no nível do provider é derived view, não gravável.

## Consequences

- Toda consulta de capacidade agrega a partir de models, em troca de uma única fonte de verdade; resolução de provider, inferência automática, seletor de modelo no frontend e despacho de cobrança dependem dessa forma de dados.
- A declaração de capacidade no registry é **metadado descritivo**; o conjunto de capacidades construído em runtime pelo backend é que decide os parâmetros realmente enviados ao SDK upstream — os dois podem divergir de propósito (mesma linhagem de «declaração vs execução» de `docs/adr/0001`).
- Novo modelo = uma declaração de capacidade no seu `ModelInfo`, sem mudar o topo do provider.
