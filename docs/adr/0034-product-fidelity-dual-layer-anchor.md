---
status: accepted
---

# Âncora de fidelidade de produto em duas camadas: imagem original do usuário é âncora de aceitação; sheet padronizado de produto é referência derivada opcional

O produto no material de venda precisa ser fiel ao real (distorção = risco de publicidade enganosa), mas as imagens de produto enviadas pelo usuário costumam ter fundo bagunçado, luz ruim e ângulos faltando. Os três tipos de asset atuais (character/scene/prop) usam sheet gerado por IA como âncora de consistência downstream; redesenho por IA de produto fixa na origem o desvio de logo, texto da embalagem e textura do material. Decidimos: asset de produto em duas camadas — a imagem original do usuário é obrigatória e é sempre a âncora de aceitação de fidelidade; o sheet padronizado de produto é referência derivada opcional de limpeza, e só entra no downstream após confirmação humana.

## Decisão

- **Original como âncora**: o asset de produto mantém várias imagens originais enviadas pelo usuário (`reference_images`); é o critério de aceitação de «produto no material fiel ao real»; reverte a limitação anterior «upload ad-hoc de referência do usuário fora de escopo» — o original entra direto na referência de geração downstream.
- **product sheet opcional, portão humano**: a entrada de upload de imagem de produto oferece o checkbox «gerar imagem de referência padrão do produto», que dispara geração de sheet multi-ângulo padronizado (fila de geração de asset; revisão/regeneração na página de assets); o fluxo do agent agenda o olhar do usuário antes de começar o storyboard. O risco de desvio do redesenho por IA é controlado pelo portão «sheet só após confirmação»; sem confirmação, não entra no downstream.
- **Injeção binária, sem «injeção fraca»**: o shot se marca com `products_in_shot` (referência por nome); não vazio = shot de produto — referência de produto injetada por completo, ordenação com prioridade absoluta, instrução de alta fidelidade anexa; shot de atmosfera zero imagens de produto. Imagem de referência é conditioning forte; «dar a imagem e pedir para não parecer demais» é mecanicamente contraditório e causa desvio; unificação de estilo fica no mecanismo de style do projeto, não via imagem de produto.
- **Segunda trava na camada de vídeo: primeiro injeção de referência**: em shot de produto, backends de vídeo que suportam entrada de referência injetam a imagem do produto no request de vídeo (zero custo extra de imagem, superfície de suporte ampla); âncora de frame inicial/final como reforço capability-gated futuro (o slot da pipeline já existe), elevando se o desvio medido for inaceitável.
- **Produto como 4º item de ASSET_SPECS**: a abstração de spec estende formalmente a capacidade de campos de lista (várias originais, lista de selling points) — extensão de princípio, não caso especial de produto; por ora não entra na biblioteca global de assets (o modelo de coluna de imagem única é incompatível; reutilização cross-projeto é trabalho futuro).

## Consequences

- É o primeiro tipo de asset centrado em «várias imagens enviadas pelo usuário» e com a imagem de upload entrando direto na referência downstream; a política de compressão na gravação do upload (limites 2MB/q85 de normalize_uploaded_image) tensiona a pureza da âncora — na implementação avaliar à parte (subir o teto de qualidade ou manter o original). Atenção: é etapa independente da compressão da cópia de upload de referência (ADR 0012, no envio, faixa visualmente lossless).
- Com sheet, o conjunto de injeção downstream é «vários ângulos do sheet + original como reserva»; a proporção exata fica para afinar com medição real, sem fixar na camada de desenho.
