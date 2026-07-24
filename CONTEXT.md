# ArcReel

Plataforma de geração de vídeo com IA: transforma romances em short videos. Este arquivo é o glossário de domínio (ubiquitous language): só define conceitos, sem detalhes de implementação.

## Language

### Fornecedores e backends

**provider (fornecedor)**:
Uma fonte de capacidade de geração de mídia, identificada por provider id (ex.: `gemini-aistudio`, `gemini-vertex`, `ark`, `custom-{id}`). O provider é a **identidade**, não o objeto de conexão.
_Avoid_: vendor, channel.

**backend (backend)**:
O objeto cliente de fato construído para um provider + model, que chama a API. Um provider pode derivar vários backends. O backend é o **artefato construído**, distinto da identidade do provider — «qual provider escolher» e «qual backend construir» são decisões independentes.
_Avoid_: client (demasiado genérico), adapter (já tem outro sentido arquitetural).

**built-in provider (provider embutido)**:
Fornecedor registrado estaticamente em `PROVIDER_REGISTRY` na subida do ArcReel (ex.: `gemini-aistudio` / `gemini-vertex` / `ark` / `openai` / `grok` / `vidu`). O usuário preenche credenciais + escolhe model e usa; campos de credencial podem ser customizados por fornecedor (ex.: Vertex AI usa caminho de JSON de service account; Kling usa JWT access_key + secret_key).
_Avoid_: preset (confunde com model preset), official (soa como «autorizado oficialmente pelo vendor»).

**custom provider (provider customizado)**:
Fornecedor criado em runtime pela UI, com `provider_id` no formato `custom-{id}`. Liga-se a um endpoint que define a forma do protocolo; o modelo de credencial é fixo: `api_key` (campo único) + `base_url`. Cobre principalmente cenários de proxy/relay. Protocolos que exigem multi-campo (service account JSON, AKSK, JWT access+secret) **não** podem ser custom provider — só built-in.

**endpoint (porta de protocolo)**:
Uma forma de protocolo que um custom provider pode ligar — template de URL HTTP + convenção de auth + semântica de campos («slot de protocolo», ex.: `openai-video` → protocolo OpenAI Sora `/v1/videos`, `newapi-video` → protocolo NewAPI `/v1/video/generations`). O endpoint decide como o backend é construído e chamado; é a fonte única de verdade da afiliação de protocolo, registrada em `ENDPOINT_REGISTRY`. Um backend embutido pode servir ao mesmo tempo built-in provider e fechamento de endpoint, com código compartilhado.
_Avoid_: protocol (demasiado genérico, confunde com HTTP/JSON), format (confunde com image format / formato de arquivo), porta (sobrepõe network port).

**canonical provider id (id canônico de provider)**:
Forma da key de `PROVIDER_REGISTRY`; fonte única de verdade da identidade do provider e a única forma de escrita aceita em todo o sistema.
_Avoid_: nomes legacy de provider.

**legacy provider name (nome legacy de provider)**:
Aliases não canônicos gravados em `project.json` por versões antigas (ex.: `gemini`, `aistudio`, `vertex`, `seedance`). Dados históricos a limpar, **não** identidade válida; após migração one-shot para id canônico deixam de ser aceitos (ver `docs/adr/0001`).

**registry key ↔ `api_model_name` (nome de modelo na API)**:
A key de `PROVIDER_REGISTRY[provider].models` (string model_id) é o **identificador interno único** do modelo — também id de UI/persistência e chave de billing e lookup de capabilities; a única forma de escrita de modelo aceita no sistema. `ModelInfo.api_model_name` (padrão `None`) é o **nome de modelo realmente enviado à API do fornecedor** — só se preenche quando precisa diferir da key (modelos anfíbios); se `None`, cai de volta para a key (ver `docs/adr/0038`).
_Avoid_: tratar a key do registry como o nome enviado ao fornecedor (em modelos anfíbios envia errado).

**amphibious model (modelo anfíbio)**:
Modelo em que o mesmo nome de API do fornecedor carrega dois media_type (imagem e vídeo) (ex.: Kling `kling-v3-omni` — image e video com o mesmo nome na API Kling). Como a key do registry e `ModelInfo.media_type` são univalorados, o modelo anfíbio vira duas entradas de registry: um media_type usa **alias key** + `api_model_name` apontando o nome real da API; o outro ocupa a key primária. Qual ocupa a primária é escolha de engenharia por modelo, não regra rígida (em Kling v3-omni, imagem usa alias `kling-v3-omni-image`, vídeo ocupa primária `kling-v3-omni`; ver `docs/adr/0038`).
_Avoid_: tratar alias key como nome real do modelo; dar key composta `(model_id, media_type)` a anfíbios (ADR 0038 rejeitou).

**discovery_format**:
Campo de nível de provider no custom provider (valores `openai` / `google`); só decide qual API de listagem usar para «descoberta de modelos» e «teste de conectividade»; **não decide o protocolo de chamada de nenhum modelo** — o protocolo de chamada vem do endpoint de cada modelo.
_Avoid_: api_format (nome antigo, inclusive valor `newapi` removido; sugeria «um provider = um protocolo»); usá-lo como switch de protocolo de chamada. (A descoberta ainda aceita probe `anthropic`, mas não persiste nem participa do despacho de protocolo.)

**active credential (credencial ativa)**:
Quando há várias credenciais no mesmo fornecedor (ou na config Agent Anthropic), a que está em vigor, trocada manualmente na UI, com efeito global; no máximo uma ativa por fornecedor. Ao apagar a ativa, o fornecedor escolhe automaticamente a mais antiga restante; credenciais Agent não se apagam direto — é preciso trocar antes (ver `docs/adr/0016`).
_Avoid_: default credential (confunde com «default model / default backend»); interpretar a troca como rotação automática ou load balancing — o sistema só troca manualmente.

**agent credential / Anthropic credential (credencial Agent / Anthropic)**:
Credencial de gateway compatível com Anthropic para o Claude Agent SDK (base_url + api_key + routing model), em tabela própria de credenciais Agent, **armazenamento separado e incomunicável** das credenciais de custom provider (ver `docs/adr/0017`).
_Avoid_: tratá-la como custom provider (`custom-{id}`) — credencial Agent não entra em `ENDPOINT_REGISTRY` nem na geração de mídia; custom provider também não é injetado no Agent SDK.

### Tarefas e cancelamento

**task (tarefa)**:
Um registro na GenerationQueue que carrega um pedido de geração de mídia. Máquina de estados: `queued → running → succeeded | failed | cancelling → cancelled`.
_Avoid_: job (conceito inexistente).

**cancelling (em cancelamento)**:
Estado intermediário: o sinal de cancel foi emitido, mas o asyncio task dentro do worker ainda não terminou o finally. A API de cancel muda o DB de `running` para `cancelling` e retorna de imediato; no finally, o worker só pode ir de `cancelling` para `cancelled` (não passa por succeeded/failed). É o único **não-terminal que parte de `running` e é reescrito por código fora do worker** — `queued` (API de enqueue) e `cancelled` (caminho cancel de queued) também são escritas externas, mas a primeira não parte de running e a segunda é terminal.

**slot (slot de execução)**:
Capacidade de execução concorrente de tasks no GenerationWorker, na dimensão **provider × media_type** (não só duas vias globais image/video). O slot se decompõe em duas coisas distintas: **capacidade** é o escalar de teto vindo da provider config (fonte única; só muda quando o usuário altera settings), padrão `IMAGE_MAX_WORKERS=5` / `VIDEO_MAX_WORKERS=3`, sobrescrevível na provider config; cada lane resolve em três camadas — **valor configurado pelo usuário > default de fábrica do fornecedor no registry (`ProviderMeta.default_concurrency`) > default global**; o default declarado é a camada intermediária para fornecedores com capacidade limitada na origem (serial/limitado de fábrica); sem declaração, cai no global; **ocupação** é a contabilidade em memória do worker de tasks em execução / fila (muda o tempo todo com as tasks). Após TTS, surge em paralelo a capacidade audio (`AUDIO_MAX_WORKERS`, default definido na implementação — TTS barato e rápido, tendência a afrouxar; ver `docs/adr/0010`). Se o pool de video de um provider enche, **só bloqueia tasks de video daquele provider**, sem afetar outros; mas se o projeto só tem um video provider, isso bloqueia todo video. O teto configurável pelo usuário é **inteiro ≥1, ou vazio (= fallback para default)**; `0` não é input válido do usuário — só sentinela interna de CapacityTable para «lane não suportada» (produzida por `_lane_limits` projetando `media_types`); ver `docs/adr/0043`.
_Avoid_: concurrency limit (demasiado genérico).

**CapacityTable / SlotTable**:
Duas estruturas independentes no worker que carregam o slot (`lib/generation_worker.py`), separando capacidade e ocupação de ponta a ponta.
- **CapacityTable** — tabela pura de tetos escalares (`provider_id × media_type → teto`). A provider config é a fonte única; reload só troca os números da tabela (`replace`), sem tocar a contabilidade de ocupação. Semântica tri-estado de `get`: conhecido + lane na tabela → valor registrado (`0` = lane não suportada); conhecido sem lane → `0`; provider desconhecido → default preguiçoso (consulta pura, sem write-back).
- **SlotTable** — contabilidade passiva só em memória (`(provider_id, media_type) → {task_id: ocupação}`). Conta inflight + pending (transiente da fila do video sem distinguido por flag de phase; promote só vira a flag); responsabilidades: há vaga? (capacidade vem do caller; a estrutura em si é agnóstica de capacidade), achar o executável por task (cancel), reportar conclusão (contabilidade do worker). **Não escreve DB, não resolve provider, não decide política de órfãos, não toca a guarda da máquina de estados de `docs/adr/0006`**. Bucket vazio é podado junto com a última liberação de ocupação (pilar de correção da blacklist de pool cheio `occupied_providers`).

A contabilidade de ocupação é **estado em memória do worker** e deve ser mantida em par com `status='running'` no DB — no cancel, o worker acha o asyncio.Task via `find_by_task`, chama `cancel()`, e no finally faz `release` e move o DB de `cancelling` para `cancelled` (ver `docs/adr/0006`). As duas usam `media_type` como dimensão de chave para a lane audio: SlotTable já contabiliza `(provider, "audio")`, CapacityTable carrega capacidade fechada em `_lane_limits`; mas o claim loop (hoje hardcoded `("image","video")`) e a resolução de provider de `_extract_provider` ainda precisam incluir audio (intencionalmente fora do escopo desta rodada; ver `docs/adr/0010`).

**worker (GenerationWorker)**:
Background asyncio task **sempre amarrado no mesmo processo uvicorn do server** no ArcReel — **não** é processo separado, **não** é membro de cluster. `lease` / `heartbeat` / `requeue_running` no código são andaimes legados de «coordenação multi-worker», nunca usados multi-processo. Desenhos que envolvem o worker devem pensar «coordenação in-process single-process».

**orphan task (tarefa órfã)**:
Task com status `running` no DB sem asyncio.Task correspondente na memória do worker. A única causa realista é **restart do serviço** (deploy / recuperação de crash). Princípio de tratamento: **não re-disparar a geração** (evitar cobrança duplicada); tasks submit-poll com `provider_job_id` em teoria podem retomar o poll; caso contrário, marcar failed.

**cancel (cancelar)**:
Caminho **cotidiano** do usuário para parar um task, com resposta em segundos — não só mudar status no DB e esperar o próximo checkpoint, e sim interromper de verdade o asyncio task correspondente no worker e liberar o slot na hora. Aberto para `queued` e `running`.
_Avoid_: abort (ambíguo, pode ser falha do sistema), stop (não distingue ativo/passivo).

**cancelled_by**:
Marcação da origem do cancelamento. `user` = disparado pelo usuário na UI; `cascade` = dependências downstream de um task cancelado também canceladas. Timeout/recuperação interna do sistema **não** conta como cancel (ver hang e timeout).

### Resolução

**provider resolve (resolução de provider)**:
Dado um task de geração, decidir qual **ProviderModel** usar. Prioridade do mais alto ao mais baixo: pedido atual (payload) > nível de projeto (project.json) > default global. É «escolher identidade», sem construir backend.
_Avoid_: usar "resolution" para este processo — `resolution` é reservado para resolução de imagem/vídeo (ver «Tamanho e proporção»); a ambiguidade confunde.

**ProviderModel**:
Resultado da resolução de provider — o par `(provider_id, model_id)` (provider_id canônico). Value object de «qual provider e model foram escolhidos», **não** é backend (nenhum cliente construído).
_Avoid_: ResolvedBackend, BackendSelection (confundem com backend).

**capability (t2i / i2i)**:
As duas formas de task de imagem — t2i text-to-image (sem ref), i2i image-to-image (com ref). Qual se aplica a um take só se sabe no «momento de abrir o quadro», se montou ou não as refs — **só na execução** (ver `docs/adr/0001`); enqueue e claim do worker (pré-execução) não sabem. Tasks de vídeo não têm dimensão capability.

### Tamanho e proporção

**aspect_ratio (proporção)**:
Razão de aspecto da saída (ex.: `9:16` / `16:9` / `1:1`), setting de projeto. **Fonte única de verdade da proporção de saída, sempre prioritária** — storyboard/vídeo com proporção errada é inutilizável.
_Avoid_: misturar proporção em campos de resolução ou tamanho.

**resolution (resolução)**:
Faixa de nitidez — **só decide a escala de nitidez, não a proporção**. Faixas de imagem `512px`/`1K`/`2K`/`4K`, de vídeo `480p`/`720p`/`1080p`/`4K`, ou valor customizado. Se o customizado trouxer proporção embutida (ex.: `1920x1080`), só se usa o **lado curto** como escala de nitidez e se descarta a proporção embutida — a proporção continua vindo de aspect_ratio. Sem resolução mas com necessidade de tamanho para controlar proporção, fallback 720P (ver `docs/adr/0011`).
_Avoid_: usar resolution para resolução de provider (ver «provider resolve»); deixar a proporção embutida no valor de resolução sobrescrever aspect_ratio.

**size (tamanho)**:
Largura×altura em pixels efetivamente enviada ao backend, derivada de **proporção × faixa de resolução** dentro das restrições de pixels de cada backend (mecanismo unificado em `lib/aspect_size.py`). Backends que aceitam pixels arbitrários têm desvio zero de proporção; backends com faixas limitadas (ex.: sora-2 com enum fixo, ark com piso de orçamento de pixels) escolhem a faixa mais próxima em proporção, desvio como exceção inerente.
_Avoid_: tratar size como sinônimo de proporção ou nitidez — é o resultado derivado dos dois.

**supported_durations**:
Conjunto discreto de durações (segundos) permitidas por um modelo de vídeo; fonte única de verdade da duração daquele modelo; intervalos contínuos também se expandem inteiros em conjunto discreto (modelos first-party sempre não vazios). Consumido em três lugares homólogos: prompt de roteiro, seletor do frontend, body do pedido de vídeo (ver `docs/adr/0018`).
_Avoid_: `VALID_DURATIONS` / whitelist global de duração (hardcode `[4,6,8]` removido, oposto ao conceito per-model); tratá-lo como «tabela oficial de capacidade de duração» de cada casa (no lado custom provider é só pré-preenchimento heurístico, precisa de review do usuário).

**default_duration**:
Duração preferida de projeto (int); null ou ausente é um nível semântico de «auto» — a IA decide sozinha dentro de supported_durations pelo ritmo do conteúdo, **não** «não configurado / a preencher».
_Avoid_: ler null como «não configurado» e preencher default por conta própria; misturar com escolha de duração take a take no storyboard.

**semântica de «não enviar» (resolution = None)**:
Quando a resolução é **só nitidez** e o SDK não exige o parâmetro, não configurado resolve para None — significa «não carregar o parâmetro na chamada do SDK», deixar o default do próprio SDK, em vez de preencher um default nosso; tabelas nossas como `DEFAULT_VIDEO_RESOLUTION` já foram removidas (ver `docs/adr/0019`).
_Avoid_: tratar None como «usar tal resolução default» e preencher. Quando o tamanho precisa **carregar a proporção**, não se aplica — nesse caso `aspect_size` sempre calcula e envia (ver `docs/adr/0011` e entradas «size» / «resolution»).

### Imagens de referência e compressão

**reference image (imagem de referência)**:
Imagem alimentada a I2I / I2V / R2V como **entrada de condicionamento (conditioning)**, guiando identidade/estilo/composição. É **entrada** da geração do modelo, não o **produto**. Uma geração pode levar várias (sheets de character/scene/prop + refs extras + storyboard anterior etc.).
_Avoid_: usar «imagem de referência» para o produto gerado ou para o arquivo-fonte do ativo.

**reference upload copy (cópia de upload de referência)**:
Os **bytes usados no momento de codificar a imagem de referência no body da requisição do fornecedor**. Cópia temporária (buffer em memória / arquivo temp), apagada ao terminar; não é o arquivo-fonte do ativo no disco, nem o produto gerado. Os três devem ficar claros: **arquivo-fonte do ativo** (ex.: `character_sheet.png` 4K, somente leitura), **produto gerado** (saída do modelo, gravada em qualidade total, sem compressão na gravação), **cópia de upload de referência** (único objeto que sofre compressão).
_Avoid_: ler «comprimir imagem de referência» como comprimir o fonte ou o produto.

**reference image compression (compressão de imagem de referência)**:
Só sobre a **cópia de upload de referência**: redimensionamento proporcional + re-encode, para caber no teto de tamanho do body do fornecedor sem degradar demais o condicionamento. Como só mexe na cópia que morre após o envio, **zero impacto** em fonte e produto — «gerar 4K e não receber 4K» não acontece por este mecanismo. Até quanto comprimir é decisão de «modelo-alvo», fora deste glossário (ver `docs/adr/0012`).
_Avoid_: misturar com compressão no save de upload (`normalize_uploaded_image`, para uploads do usuário).

### Billing

**cost snapshot (snapshot de custo)**:
Quando uma chamada de API termina (`ApiCall` de `pending` para `success`), o `CostCalculator` calcula o valor com o modelo e os parâmetros de billing **de então**, e **congela** em `cost_amount` + `currency` daquele registro. Toda agregação de uso e custo faz `SUM(cost_amount)` nesse valor congelado, **sem recalcular na leitura**. Duas corolários: ① ajustar preço só afeta **chamadas novas** depois, sem reescrever histórico; ② gastos passados de modelos descontinuados ficam travados — dados de preço não precisam reter tarifas antigas para billing histórico.
_Avoid_: billing em tempo real, recálculo de custo na leitura.

### Tipos de mídia e narração (TTS)

**media_type / call_type**:
Dimensão de mídia que atravessa o sistema, valores `image` / `video` / `text` / `audio`. Resolução de provider, família de backend, uso e billing todos «faneiam por media_type». O mesmo token deve ser consistente em `ModelInfo.media_type`, `CallType`, UsageTracker, CostCalculator e consultas de pricing.
_Avoid_: modality (demasiado genérico), media kind.

**audio (tipo de mídia)**:
O 4º media_type, carrega text-to-speech (TTS). No mesmo nível de image/video/text, **agendado via GenerationQueue/Worker** (como image/video, não como geração de text síncrona inline) — porque áudio de narração é um por segment, N por episódio, regenerável em lote, com a mesma cardinalidade de geração de image/video, não o «uma vez por episódio» de text. Há uma assimetria: a **chamada do backend de audio em si é síncrona one-shot** (no estilo text_backends, resposta em segundos, sem submit-poll), mas a **orquestração da tarefa ainda passa pela fila** (worker claim → chama backend síncrono → marca terminal), de modo que audio entra no painel de tarefas (progresso/cancel/retomada) sem precisar do mecanismo resume/`provider_job_id` de video (ver `docs/adr/0010`).
_Avoid_: tts (reservado a capability), voice, speech.

**text_to_speech (capability)**:
Identificador de capacidade do media_type audio: «sintetizar texto em fala». Declarado em `ModelInfo.capabilities` do modelo audio, na mesma dimensão capability que t2i/i2i de imagem.
_Avoid_: tts, voice_synthesis.

**narration voiceover / narration_audio (narração por voz)**:
Um trecho de fala gerado a partir do `novel_text` (texto original do romance) de cada NarrationSegment no modo narração; único produto do media_type audio nesta fase. Um por segment, arquivo de áudio no disco, caminho em `GeneratedAssets.narration_audio` daquele segment.
_Avoid_: dub (confunde com dublagem cinematográfica), áudio TTS (demasiado genérico).

**três significados de "audio" (alerta de ambiguidade)**:
- **audio (tipo de mídia)** = dimensão TTS definida nesta tabela.
- **`generate_audio` (capability/campo)** = switch de **trilha embutida** do modelo de vídeo (Veo/Kling etc.), dimensão video, sem relação com TTS.
- **`ambiance_audio` (campo de script)** = **prompt de som ambiente** para o modelo de vídeo — texto, não arquivo de áudio.
Nomes novos de TTS devem evitar `generate_audio` / `ambiance_audio` / `resolution_audio` (dimensão de billing de vídeo Veo), para não colidir com o media_type audio.

### Projeto e ativos

**sheet (design / ficha)**:
Imagem de tipificação gerada por IA de character/scene/prop (`character_sheet` / `scene_sheet` / `prop_sheet`); **produto** da fase de geração de ativos, depois entrada de reference image no storyboard/grid/reference-video downstream para ancorar consistência.
_Avoid_: misturar com «reference image (entrada de condicionamento da geração)» — a direção é oposta: sheet é produto depois reutilizado; reference image é entrada. Também não confundir com o campo `reference_image` de upload do usuário em character (arquivo de referência do usuário, não ficha de IA).

**global asset library (biblioteca global de ativos)**:
Repositório global único de character/scene/prop reutilizáveis entre projetos (persistência em DB + diretório de imagens `_global_assets/`), ligado a projetos por **cópia em snapshot**, não por referência.
_Avoid_: tratá-la como «acoplamento por referência» com o projeto — entrada / aplicação ao projeto copiam a imagem fisicamente; mudar um lado não mexe no outro; achar que renomear/apagar no library propaga a projetos já usados; colocar product aqui — ativos multi-imagem em lista não cabem no modelo de coluna única da library; o spec isenta com `in_global_library=False`.

**product (ativo de produto)**:
4º item de ASSET_SPECS (bucket `products`, campo sheet `product_sheet`, subdiretório `products/`), carrega o sujeito de venda de projetos de anúncio/curta. Tem o campo-lista `reference_images` (várias fotos originais do usuário; no save mantém o original sem compressão — **âncora de aceitação de fidelidade** de «o produto no filme final fiel ao real»; após upload pode-se acrescentar opcionalmente ref derivada `*_isolated.png` sem fundo, sem sobrescrever o original) e `selling_points` (lista de argumentos de venda, agent pode rascunhar, usuário pode editar), mais texto livre `brand`. O product sheet é referência derivada multiângulo padronizada opcional (na geração as originais entram em peso total), e só segue downstream após confirmação humana (soft gate do workflow do agent, sem máquina de estados). Injeção downstream binária: se `products_in_shot` do take não está vazio, é take de produto — refs de produto entram em peso total, antes de todas as outras, com instrução de alta fidelidade (com sheet: «multiângulo do sheet + originais de lastro»; sem sheet: originais diretas); a camada de vídeo reinjeta com gate de capacidade de reference do backend, rebaixando se o backend não suporta; takes de atmosfera têm zero imagem de produto (ver `docs/adr/0034`).
_Avoid_: deixar o agent reescrever `reference_images` — campo de sistema fora da whitelist do agent; updates vão por API de upload dedicada; inverter a prioridade âncora entre originais e sheet — originais sempre existem e são o critério de aceitação; sheet só é derivado purificado; aplicar compressão de save 2MB/q85 nas originais — isso é normalização de upload de outros ativos, agressiva demais para a âncora; inventar nível intermediário de «injeção fraca» — dar a imagem e pedir para não se parecer demais é contraditório no mecanismo; unificação de estilo fica no style de projeto + `brand_profile.style_prefix`.

**style template (template de estilo)**:
Texto de prompt de estilo de quadro inteiro pré-definido (duas classes: live-action / animação, um id por escolha). Ao selecionar, o prompt expandido vai para o campo `style` de project.json (snapshot para injeção), mantendo `style_template_id` (pode ser re-resolvido em PATCH / migração na leitura); mudanças no registry não reescrevem projetos antigos de forma proativa (ver `docs/adr/0023`).
_Avoid_: tratar style como label curto (valores antigos Photographic/Anime/3D aposentados, só aliases legacy de migração preguiçosa); empilhar com imagem de referência de estilo (`style_image`, ref de estilo enviada pelo usuário) — são mutuamente exclusivos; escrever um limpa o outro.

**clue (pista) — termo de ativo legacy**:
No início do ArcReel, termo guarda-chuva para «cena + prop» (distintos por type location/prop); hoje divididos em scene e prop independentes; clue e o campo `importance` não fazem parte do modelo de dados atual.
_Avoid_: usar clue/pista em código/docs novos para cena ou prop — os termos canônicos são scene e prop; clue só aparece ao ler project.json histórico, código de migração e designs arquivados.

### Roteiro e storyboard

**skeleton / skeleton kind (esqueleto / tipo de esqueleto)**:
Tipo de estrutura do array de itens do roteiro, quatro valores: `segments` (segmentos de narração) / `scenes` (cenas de drama) / `shots` (takes de anúncio) / `video_units` (unidades de reference-video). O esqueleto é **derivado** dos eixos content_mode e generation_mode, não é um terceiro eixo: narration/drama/ad correspondem aos três primeiros; em generation_mode=reference_video, narration/drama trocam o conjunto para video_units; o esqueleto ad é sempre shots e não muda com o caminho de geração (ver `docs/adr/0033`). Há duas perguntas legítimas sobre o esqueleto — **normativa** (pela config de modos do projeto/episódio, *qual* esqueleto este roteiro *deveria* ter) e **forense** (pelos dados do roteiro, *qual* esqueleto ele *de fato* tem); em estados intermediários de migração as duas podem divergir, e a forense prioriza a forma dos dados. O conhecimento de esqueleto fica no módulo-folha sem dependências `lib/script_skeleton.py`: tabela estreita `SKELETONS` indexada por tipo de esqueleto (a key é a key do array de itens, linha `Skeleton(id_field, chars_field)`; `video_units` não tem elenco por item, logo `chars_field=None`) + **resolve normativa** `resolve_declared_kind(content_mode, generation_mode)` (para consumidores com a config do projeto; content_mode desconhecido/ausente lança `ValueError`) + **resolve forense** `resolve_script_kind(script)` (para consumidores com os dados do roteiro, com a escada de tolerância que prioriza a forma dos dados); os dois resolvers são a entrada única de despacho de esqueleto de todos os consumidores; fundamento em `docs/adr/0045`.
_Avoid_: tratar o esqueleto como quarto content_mode ou sinônimo de content_mode (eixo de três valores não produz quatro esqueletos); misturar as perguntas normativa e forense (config já em reference_video mas dados ainda em segments → a edição segue os dados); fallback binário «não-narration = drama» para modos desconhecidos (proibido por `docs/adr/0033`).

**grid (grade / grid)**:
Caminho de geração de storyboard que junta várias cenas do mesmo trecho em uma imagem conjunta de N células (grid_4/6/9) e depois recorta frames inicial/final de cada cena; com image→vídeo take a take (storyboard) é o outro caminho «storyboard→vídeo» sob generation_mode; o valor central é garantir estilo/personagem consistentes em uma só geração.
_Avoid_: tratar reference_video como terceiro valor no mesmo nível de grid/storyboard — ele pula o storyboard e é um esqueleto independente acima de content_mode, não esse caminho «storyboard→vídeo»; o valor canônico do modo take a take é storyboard, não o termo antigo single.

**ad (modo anúncio/curta)**:
Terceiro valor de content_mode; produz um único short de cerca de `target_duration` segundos, não uma série multi-episódio. Esqueleto de roteiro: `shots[]` plano (`shot_id` no formato E1S{n}), cada take carrega `section` (rótulo de seção do framework de venda, oito valores de orientação sem enum rígido) e texto de locução de primeira classe `voiceover_text`; o projeto é sempre mono-episódio (episodes sempre a única 1ª entrada), com campos de projeto `target_duration` (segundos inteiros positivos), `brief` (texto curto de briefing criativo, não passa por source_loader), `brand_profile` (saída do Brand Analyzer: visual_description / tone / audience / colors / keywords / style_prefix; o prefixo é injetado em todos os prompts de storyboard e vídeo), `ad_timeline` (timeline de filme final text_overlays + music_track), `ad_continuation` (padrão true: frame final do vídeo do take anterior como start i2v do próximo), `ad_video_takes` (número de takes por shot 1–3, padrão 1; multi-take via VersionManager); não tem `default_duration`; generation_mode só abre storyboard e reference_video (ver `docs/adr/0033`). A geração one-shot de roteiro não usa arquivo intermediário step1: o prompt vem direto de brief + brand_profile + info de produto (com selling_points) + tabela de proporções do framework de oito seções de venda aprovada (15/30/60/90, faixa mais próxima; fundamento em `docs/research/arcreel-ad-section-timing-research.md`); products vazio desvia automaticamente para prompt genérico de curta; a restrição de duração do take muda com o caminho de geração — storyboard: enum rígido supported_durations; reference_video: inteiro livre 1–15 s; desvio do total do roteiro além do limiar de `target_duration` só warn, não bloqueia. Upload de originais de produto pode anexar ref opcional `*_isolated.png` sem fundo (depende de rembg, sem sobrescrever a âncora original). Review de consistência via `critique_ad_consistency` (estrutura + similaridade de histograma opcional). O compose-video in-app já suporta ad `shots[]` e camadas/BGM de ad_timeline.
_Avoid_: deixar ad cair no fallback binário «não-narration = drama» — todo mecanismo que despacha por content_mode deve tratar o terceiro valor explicitamente; misturar AdShot com shot interno de video_unit (reference-video) — o primeiro é take plano do esqueleto de roteiro, o segundo é sub-take temporal dentro da unit; tratar a não-integração de ad no gate de review step1→step2 como lacuna a preencher — geração one-shot sem estado intermediário step1 é contrato intencional; condições de revisitação em `.out-of-scope/ad-step1-step2-review-gate.md`; misturar `brand` livre de produto com `brand_profile` de projeto — o primeiro é rótulo de um produto, o segundo é o dossiê Brand Analyzer do filme inteiro.

**video_unit / shot (unidade de reference-video)**:
Unidade de geração no modo reference-video: um video_unit contém 1–4 shots (sub-takes), a unit inteira compartilha um conjunto de refs numeradas em ordem (`[图N]` / `[imgN]`), pula o storyboard e gera direto a partir das imagens de ativos. Em narration/drama o roteiro se organiza em `video_units[]` em vez de `segments[]` / `scenes[]` (conteúdo da unit autocontido); em ad o esqueleto não muda — a unit é um índice leve **agrupado por derivação** a partir de `shots[]` (roteiro `reference_units[]`, só cita shot_id + conjunto de refs herdado, refs de produto com prioridade absoluta) — takes contíguos, ≤4 shots por unit, duração total sob o teto do fornecedor; agrupamento é função pura (`lib/reference_video/ad_units.py`), reproduzível; units cujo membro e conjunto de refs não mudaram preservam o produto na re-derivação. **O produto se ancora na unit**: no caminho ad+reference, o filme final (`generated_assets.video_clip` etc.) fica em cada unit de `reference_units[]`; `shots` não carrega produto desse caminho; todos os consumidores (score `StatusCalculator`, export CapCut/Jianying, diff de eventos de projeto) leem o produto da unit após despachar pelo generation_mode declarado do projeto, sem ler shots nem cheirar a forma dos dados (índices residuais não podem poluir o comportamento do caminho storyboard).
_Avoid_: misturar shot com segment (segmento de narração) / DramaScene (cena de drama); «scene» no modo reference tem três sentidos a distinguir — ativo de cena (scene_sheet), cena de storyboard do roteiro (DramaScene), take (shot); editar manualmente reference_units de ad — é derivado; shots é a única fonte de verdade de conteúdo.

**utterance (item de fala)**:
Unidade unificada de «o que é dito» em uma cena drama — cada item é fala de personagem (com falante) ou voice-over / narração (sem falante). Um `DramaScene` tem uma sequência **ordenada** de falas (`utterances`); a ordem de inserção é a ordem dentro da cena (intercalação de falas e voice-over). O tipo define o destino: falas entram na geração de vídeo e o fornecedor gera trilha de lip-sync; voice-over não entra no vídeo, fica para legendas do filme final e TTS futuro. O conteúdo falado de drama tem nisso a fonte única de verdade; o falado de narration não usa utterances — continua sendo o `novel_text` lido em voz alta.
_Avoid_: tratar fala e voice-over como dois campos independentes sem ordem (a ordem se perde e o downstream tem de juntar duas fontes); misturar utterance com `novel_text` de narração — o segundo é o trecho inteiro lido (cardinalidade um), o primeiro é fala item a item na cena (cardinalidade muitos); empurrar voice-over para a trilha do fornecedor de vídeo — a trilha do fornecedor só carrega fala de lip-sync; voice-over vai para legenda / TTS.

**source_text (âncora de texto-fonte da cena)**:
Excerto literal de texto-fonte no nível da cena drama — registra o trecho original de onde a cena veio, para revisão humana, regeneração de cena única e localização de distorção. É âncora de rastreio best-effort (copiada pelo LLM, pode desviar levemente), não ground truth de fidelidade literal (a fidelidade vem do pipeline de extração); em si não é lida em voz alta nem soa; é assunto separado das utterances que são o falado. No papel se assemelha ao `novel_text` de narração, mas `novel_text` é ao mesmo tempo original e falado lido, enquanto `source_text` é só âncora de original.
_Avoid_: tratar source_text como conteúdo a dublagem/leitura; misturar com `source_range` de episódio (intervalo de offset do original no nível do episódio) — um é texto literal de cena, o outro é offset de caracteres de episódio.

**source_kind / screenplay source (natureza do arquivo-fonte / fonte de roteiro)**:
Campo de topo de project.json, valores `novel` (romance, padrão — comportamento atual) / `screenplay` (roteiro finalizado enviado pelo usuário). Marca que o arquivo-fonte **já é o roteiro finalizado do autor**, não um romance a adaptar. Com `screenplay`, a cadeia drama inteira vira de «criação» para «extração em primeiro lugar»: limites de episódio, cenas, falas, hooks de fim de episódio são **extraídos como estão** do roteiro (autor é autoridade); o LLM só preenche a camada de produção visual que o roteiro não escreveu (image_prompt / video_prompt). É um terceiro eixo ortogonal a content_mode (narration/drama/ad) e generation_mode — «natureza do arquivo-fonte», nem tipo de conteúdo nem origem do vídeo.
**Fidelidade literal só ancora o «conteúdo audível»** — texto de fala de personagem e de voice-over (itens de fala em `DramaScene.utterances`; fala com falante, voice-over sem) não se reescreve, não se perde, não se polui; layout/labels (`△`/`【画外音】`/markdown), dicas de câmera e palco (`（航拍，全景）`/`（压低声音）`), descrições visuais, extras genéricos (`老人甲` / plano vazio) ficam a critério do LLM para reescrever ou remover; speaker genérico não vira ativo (ver `docs/adr/0036`).
_Avoid_: usar «roteiro» para o upload-fonte e para o produto gerado ao mesmo tempo — o upload é «fonte de roteiro (screenplay)», o produto é «roteiro (script JSON)», dois conceitos; tratar screenplay como novo content_mode; ainda rodar «step1 no estilo adaptação» ou «plan_episodes no estilo re-planejamento» em screenplay — exatamente a reescrita secundária a eliminar (perda de falas, adulteração das divisões do autor); ler «literal» como copiar também layout/dicas de palco/extras — literal só amarra «o que é dito», não «o que se vê na produção» nem «o layout do papel».

**episode ledger (livro-razão de episódios)**:
`episodes[]` de project.json é a fonte única de verdade de episódios: além de episode/title/script_file, a entrada estende `source_range` (faixa do material original), `hook` (gancho de fim de episódio), `outline` (outline de episódio em drama) e `ledger_status` (estado de consumo); o físico `source/episode_N.txt` é derivado (ver `docs/adr/0031`). Campos do livro podem estar todos ausentes — ausência = entrada antiga, preenchida pelo backfill reexecutável (`lib/episode_ledger.backfill_episode_ledger`).
_Avoid_: inferir estado ou contagem de episódios pela existência de arquivos físicos de episódio (inferência por Glob é o padrão antigo substituído); misturar campos do livro com campos estatísticos injetados na leitura pelo StatusCalculator — o livro persiste em project.json, os estatísticos não caem em disco.

**ledger_status (estado de consumo)**:
Ciclo de vida em quatro estados da entrada do livro: planned (planejado, ainda não consumido) / consumed (já tem produto downstream: arquivo intermediário step1, roteiro ou mídia) / stale (invalidado após reordenação, marca em vez de apagar) / unanchored (backfill não conseguiu ancorar: conteúdo não casa com o original, ou arquivo de episódio ausente/ilegível; trava e não participa de reordenação; consumo downstream não é afetado — se o arquivo físico de episódio existe, ele é o registro final).
_Avoid_: misturar com `status` injetado na leitura (draft/in_production/completed) — as duas keys coexistem na mesma entrada com semânticas diferentes; tratar unanchored como falha (é degradação honesta; matching de substring exato, sem âncora fuzzy).

**normalized source coordinates (coordenadas normalizadas de fonte)**:
Todos os offsets de caracteres de source_range e planning_cursor vivem no espaço de saída de `lib/episode_ledger.normalize_source_text` (Unicode NFC + unificação de quebras de linha); antes de fatiar o original por offset, rode a mesma função no texto-fonte.
_Avoid_: fatiar o conteúdo bruto do arquivo com o offset — NFD (import macOS/vietnamita) ou fonte CRLF desalinha.

**planning_cursor**:
Campo de topo de project.json; início da próxima rodada de planejamento de episódios no original (`{source_file, offset}`, null = sem progresso de planejamento), avançado pela ferramenta de planejamento a cada commit. O arquivo residual `source/_remaining.txt` foi abolido: o backfill de migração ainda lê seu conteúdo para converter o cursor; a ferramenta de planejamento o limpa no primeiro commit.
_Avoid_: tratar `_remaining.txt` como fonte de verdade do progresso (corrupção = irrecuperável, exatamente o padrão antigo que o livro elimina); tratar cursor não vazio como o mais recente absoluto — reexecutar o backfill só preenche faixas de novos episódios, não avança valores não vazios; o ponto de partida do planejamento é o maior entre o fim da faixa ancorada no livro e o cursor.

**plan / replan (planejamento de episódios)**:
Capacidade de planejamento de episódios no servidor (`lib/episode_planner.EpisodePlanner` + ferramentas SDK `plan_episodes` / `replan_episodes`): a partir de planning_cursor lê uma janela do original, chama o modelo de texto da config do projeto uma vez para planejar todos os episódios com arco completo na janela (título/gancho/faixa; em drama inclui outline), schema forte + validação mecânica de âncora existente/única/contínua com retry automático em falha; dentro do mesmo lock de projeto escreve o livro, deriva arquivos de episódio e limpa resíduos. plan aceita `instructions` opcional persistente (preferências de divisão do usuário, ex. alinhar por capítulo): se não vazio, injeta no prompt de planejamento com força «deve cumprir tudo», prioritário sobre a integridade de arco default; não persiste — em planejamento multi-lote o agent deve re-carregar a cada lote; vazio/em branco = comportamento puro de arco de hoje, literalmente. replan reordena localmente a partir de from_episode com opinião em texto livre do usuário: se a faixa cruza vários arquivos-fonte, quebra por arquivo em vários re-cortes independentes (um episódio não cruza arquivo; fronteira de arquivo = fronteira de episódio; numeração de episódio contínua entre segmentos); se atinge episódios já consumidos, exige confirmação explícita (marca stale); opinião global (volume por episódio) reescreve settings do projeto como opinião global estruturada, herdada automaticamente pelos lotes seguintes (em contraste com `instructions` de plan, que se carrega por lote e não persiste; ver `docs/adr/0032`).
_Avoid_: deixar o agent principal ler o original e escolher pontos de corte sozinho (scripts peek/split são o padrão antigo substituído); hardcode de tamanho de janela / episódios por lote nas instruções — são defaults internos da ferramenta; `planning_window_chars` / `planning_max_episodes` nas settings do projeto podem sobrescrever.

### Runtime do agente

**SessionActor**:
Um asyncio task dedicado por sessão Claude, que serializa todas as chamadas de protocolo daquela sessão ao `ClaudeSDKClient` (connect / query / interrupt / disconnect); chamadas concorrentes ao cliente SDK não são seguras — o actor é essa fronteira de serialização (ver `docs/adr/0028`).
_Avoid_: misturar com ManagedSession (container de estado em memória da sessão) — o actor é o canal de execução, ManagedSession é o estado; chamar `client.disconnect()` / consumer_task diretamente é o padrão antigo substituído.

**SDK transcript (memória do agent)**:
Registro de sessão escrito pelo SDK no próprio protocolo (espelho em DB ou jsonl); única responsabilidade: o resume do SDK reconstruir o contexto do agent — é a **memória do agent**, formato e timing de escrita decididos pelo SDK; o ArcReel não tem o direito de reformar nem misturar entradas só de UI (seriam alimentadas de volta ao agent no resume e poluiriam).
_Avoid_: tratar o transcript como fonte de dados da timeline de diálogo da UI — a única fonte de leitura da UI é o session event log; gravar no transcript eventos sintetizados pelo servidor.

**session event log (log de eventos de sessão)**:
**Única fonte de leitura** da timeline de diálogo da UI: por sessão, uma sequência de eventos com cursor monotônico crescente; stream em tempo real, reconexão e replay de histórico leem a mesma coisa. As entradas se **tipam no ponto de escrita** — o stream de mensagens do SDK e eventos sintetizados pelo servidor (aceitação de mensagem do usuário, interrupção, progresso de subtarefa etc.) completam o reconhecimento semântico e a normalização no momento de entrar no log. O posicionamento é de **visão materializada** do transcript: pode ser reconstruída por replay do transcript (lazy na primeira visita de sessões antigas); apagar não perde a verdade. Mensagens do usuário: o servidor **escreve no log e atribui identidade antes de ecoar**; o frontend não renderiza nenhuma mensagem sintética local. Entradas de chamada de skill só registram nome da skill e args; o texto completo injetado não entra no log (só vive no transcript).
_Avoid_: tratá-lo como segunda fonte de verdade a reconciliar com o transcript — o meio de reparar drift é reconstruir por replay, não sincronização bidirecional; queimar conceitos de projeção de UI (agrupamento de turn etc.) na entrada do log — o log guarda fatos estáveis, a projeção fica no lado da leitura; deduplicar ou cheirar semântica no lado da leitura — a tipagem só ocorre no ponto de escrita.

**draft (estado de pré-visualização em stream)**:
A única representação de pré-visualização em memória do servidor de uma mensagem de assistente ainda em stream, ainda não concluída; a identidade é seu `message_id`; ao concluir, é **substituída exatamente** pela entrada autoritativa do log com o mesmo `message_id`. Não entra no log, não cai em disco — se o serviço cair, some, alinhado à memória do agent (o SDK também não lembra mensagens incompletas). Na reconexão, o snapshot do primeiro frame carrega o estado acumulado atual.
_Avoid_: usar comparação de conteúdo para julgar duplicata entre draft e conteúdo já commitado — a correspondência só reconhece `message_id`; fazer do draft um estado pending de entrada de log (quebra o append-only do log).

**subagent timeline (sub-timeline)**:
Sequência de mensagens de subagent agrupada por parent_tool_use_id na mesma sessão. Chamadas de ferramenta e respostas do subagent entram **por completo** como entradas de log com marcação parent, mas na timeline principal só aparece um card de subtarefa colapsável (fechado por padrão, mostra descrição+status+progresso); expandir revela a sub-timeline.
_Avoid_: espalhar mensagens de subagent na timeline principal; só registrar eventos de progresso sem as mensagens internas — expandir a sub-timeline pressupõe que as mensagens internas estão no log.

**agent runtime profile (profile de runtime do agent)**:
Árvore de config de runtime dedicada ao agente (`agent_runtime_profile/`: variantes de system prompt + Skill/Subagent de negócio), **fisicamente separada** do `.claude/` local do desenvolvedor; no runtime materializada em cada diretório de projeto via manifest.
_Avoid_: usar «.claude» / «CLAUDE.md» de forma genérica — `.claude/` de desenvolvimento e agent profile são dois conjuntos; também não chamar de agent config (colide com a rota agent_config de credenciais Anthropic).

**materialization (materialização de profile)**:
O processo de copiar o agent profile em cada diretório de projeto por manifest + sha256; só sincroniza arquivos declarados e validados, e escolhe a variante `CLAUDE.{narration,drama,ad}.md` pelo content_mode do projeto, gravando como único `CLAUDE.md`.
_Avoid_: usar «sync / copy / deploy» de forma genérica — materialização é especificamente a escrita controlada de manifest + projeção de variante + tri-estado sha256; o nome do arquivo-fonte da variante (`CLAUDE.narration.md`) ≠ o nome lógico no lado do projeto (`CLAUDE.md`).

**agent sandbox (sandbox do agent)**:
Camada de isolamento em nível de kernel em torno das chamadas de ferramentas do Agent (macOS Seatbelt / Linux bwrap), restringindo leitura/escrita de arquivos e rede de **todos os subprocessos dentro do sandbox** (Bash e seus derivados); Read/Write/Edit/Glob/Grep embutidos do SDK rodam no processo principal, fora do sandbox, interceptados pelo hook PreToolUse da camada de aplicação (ver `docs/adr/0025`, `docs/adr/0026`).
_Avoid_: usar «sandbox» para o hook de cerca de paths da camada de aplicação — sandbox é especificamente a camada de kernel; Windows sem sandbox de kernel rebaixa Bash para whitelist de prefixos.

**AgentAccessPolicy (regras de acesso do agent)**:
Fonte única de verdade das regras de «o que o agent pode tocar» (`server/agent_runtime/agent_access_policy.py`): construída de forma pura a partir de paths raiz de processo + `sandbox_enabled`, zero I/O; o mesmo conjunto de regras tem duas projeções — compila SandboxSettings para o sandbox de kernel (denyRead/denyWrite/lista de domínios de rede) e fornece decisão de leitura/escrita/comando por chamada e wrapper de stripping de secrets Bash para o hook da aplicação; o rebaixamento Windows (whitelist de prefixos Bash) fica na classe, junto com a restrição mútua «o wrapping quebra o matching da whitelist» (ver `docs/adr/0046`). A casca do SDK (assinatura de hook, tipos de resultado de permissão, ordem da cadeia de permissão) fica no thin adapter do SessionManager.
_Avoid_: SandboxPolicy — «agent sandbox» é a camada de isolamento de kernel; esta classe também serve hooks da aplicação que não são sandbox; puxar injeção de credenciais para a classe (injeção lê DB, quebra construção pura); importar tipos do SDK dentro da classe.

**SseChannel (canal de broadcast de assinatura)**:
Componente de broadcast de assinatura SSE parametrizado (`server/sse_channel.py`), compartilhado pelo stream de mensagens de sessão e pelo stream de eventos de projeto; responsabilidades limitadas a assinar/desassinar, broadcast, heartbeat ocioso, tratamento de overflow; as diferenças entre os dois se expressam todas por parâmetros: política de overflow (stream de sessão «expulsa mensagens não críticas + sinal de overflow; fim do stream = sinal de reconexão» vs. stream de eventos de projeto «remove assinante, sem sinal; desconexão se autoverifica por heartbeat») e hooks opcionais de ciclo de vida do primeiro/último assinante (stream de eventos de projeto usa para ligar/desligar o scan em background). O prólogo (replay de buffer no stream de sessão, snapshot inicial no de eventos de projeto) não entra no componente; a atomicidade entre assinatura e prólogo é garantida pelo consumidor na seção crítica síncrona do lado da assinatura (ver `docs/adr/0046`).
_Avoid_: enfiar a produção do prólogo no componente — replay de buffer e snapshot de scan não têm uma linha de implementação em comum; parametrizar seria falsa abstração; unificar à força as duas semânticas de overflow; ligar o endpoint de stream de tarefas já aposentado (poll de banco).

### Auth e credenciais

**download token (token de download)**:
JWT de curta duração (~5 min), amarrado ao nome do projeto, one-shot, só para exportação de projeto (`purpose=download`); única forma de auth do endpoint de exportação como query param — o endpoint valida sozinho, não lê Authorization header, para a URL de download nativa do browser não carregar credencial de longa duração.
_Avoid_: misturar com JWT de sessão de longa duração ou API Key; colocar o JWT de login na URL de download.

## Diálogos de exemplo

> **Dev**: quando o worker reclama um task de imagem, como ele sabe qual provider usar no rate limit?
> **Expert**: ele faz resolução de provider, mas só até «escolher identidade» — pega o provider, não o backend, e não gera de verdade.
> **Dev**: e ele sabe se é t2i ou i2i? E se o usuário configurou providers diferentes para os dois?
> **Expert**: não sabe. capability só se fixa na execução; o worker só pega um provider representativo por t2i para rate limit. Qual se usa de verdade, a camada de execução resolve de novo com precisão.
> **Dev**: e se project.json tiver `seedance`?
> **Expert**: isso é nome legacy de provider; após a migração não deveria mais aparecer. O sistema só reconhece o id canônico `ark`.
>
> **Dev**: o backend TTS de narração é um POST síncrono one-shot, como a geração de text, sem async — então também não entra na fila e chama direto como text?
> **Expert**: não. Entrar ou não na fila olha a **cardinalidade de geração**, não se o backend é síncrono ou não. text gera uma vez por episódio, inline síncrono basta; áudio de narração é um por segment, N por episódio, em lote — mesma cardinalidade de image/video, então vai para a fila e para o painel de tarefas (ver `docs/adr/0010`).
> **Dev**: backend síncrono e ainda assim na fila — não é contraditório?
> **Expert**: não. O worker claima o task de audio, chama aquele backend síncrono, marca terminal em segundos — só poupa o submit-poll-resume de video. Ocupa o audio pool daquele provider, em paralelo aos pools image/video; TTS é barato, `AUDIO_MAX_WORKERS` default afrouxado, em geral não é gargalo.
