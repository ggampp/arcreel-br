---
status: proposed
---

# TTS (tipo de mídia audio) passa por GenerationQueue/Worker, como image/video; o backend continua síncrono, diferente do text inline

A geração de mídia no ArcReel se espalha no eixo `media_type`: image/video passam por **GenerationQueue + GenerationWorker** (slots por provider×media_type, com progresso/cancel/resume/órfãs); text é **chamada síncrona inline** (`TextGenerator` = TextBackend + UsageTracker, não enfileira; o worker só faz `for media_type in ("image","video")`, sem task). Ao integrar narração com voz (TTS), a primeira bifurcação é: audio segue text (inline síncrono) ou image/video (fila).

A inclinação inicial era inline síncrono «como chamada de texto, sem controle de concorrência», porque a chamada do backend TTS **já é um POST síncrono de uma vez** (no estilo `text_backends`, sem submit-poll, resposta em segundos) — parece mais próxima de text. Depois confirmamos que **geração em lote é necessidade rígida no web e no agent**, e o fato crítico: **a base de geração de áudio de narração (um trecho por segment, N segmentos por episódio, loteável, regenerável) é a de image/video, não a de text («uma vez por episódio»)**. Em inline síncrono o lote só se orquestra em série no frontend, progresso preso à aba do browser, sem painel de tarefas, sem cancel/resume/cross-device — experiência partida da de imagem/vídeo; a fila existe justamente para «tarefa longa em lote + progresso + cancel + resume», e image/video já a usam.

Decidimos que **audio passa por GenerationQueue/Worker, igual a image/video**: um segmento = uma entrada na fila; lote = N entradas; reutiliza o painel de tarefas `/api/v1/tasks` existente. Mantemos uma **assimetria deliberada** — o **backend de audio continua síncrono de uma vez** (estilo `text_backends`, não o submit→poll→resume do video): o worker no claim chama o backend síncrono e, em segundos, marca estado final. Ou seja: **«entrar na fila ou não» é decidido pela base de geração (se é lote por segment), não por o backend ser assíncrono** — ponto que confunde leitores futuros («o backend de audio é síncrono como text; por que audio entra na fila e text não?»), daí este ADR.

## Considered Options

- **Inline síncrono (como text) + lote serial no frontend** — menos código, worker intocado. Rejeitado: progresso de lote preso à aba do browser, sem painel de tarefas, sem cancel/resume/cross-device, partido de image/video; e a base de geração de audio é a de image/video, não de text — a analogia não se sustenta.
- **Passar pela fila (como image/video)** — adotado.

## Consequences

- **Worker ganha terceira lane**: `ProviderPool` com `audio_max` / `has_audio_room`; o loop de claim amplia `for media_type in ("image","video")` para incluir `"audio"`; toca pontos de lane como `_resolve_dispatch_provider` / `_any_pool_has_room` / `_pool_full_providers` / `_load_pools_from_db` / `_build_default_pools` (mudanças mecânicas). TTS é barato e rápido; `AUDIO_MAX_WORKERS` default generoso — a lane não deve ser gargalo.
- **Ferramenta do agent é `enqueue_tts(segment_ids?)`** (enfileira, estilo `enqueue_storyboards`), não `generate_*` síncrono; omitido = todos os segmentos faltantes; list = faixa de lote; um único = um segmento.
- **Web enfileira + reutiliza o painel de tarefas**: single e lote enqueue; frontend polla `/api/v1/tasks` para progresso; reutiliza UI de cancel/resume existente.
- **Backend de audio fica síncrono, sem resume/`provider_job_id`**: claim do worker → chama backend síncrono (segundos) → marca final. O tratamento de órfãs do `docs/adr/0007` para audio degenera em «marca failed, sem resume», porque é síncrono e regenerar é barato — sem o mecanismo submit-poll-resume do video.
- **«Síncrono» é escolha para «segment curto + API síncrona»; assíncrono é ponto de extensão reservado**: v1 escolhe síncrono porque (a) as APIs TTS dos providers escolhidos já devolvem bytes síncronos (HTTP sync DashScope Qwen-TTS, OpenAI-compat `/v1/audio/speech` retorna na hora), (b) narração por segment é curta (`duration_seconds ≤ 60`, texto limitado) e termina em segundos. **Mas APIs TTS de texto longo na indústria são assíncronas** (MiniMax T2A async, long-text assíncrono Doubao ≤100k chars, Google long-audio LRO, Azure batch). Se no futuro entrarem providers só com API assíncrona, ou a síntese virar «texto longo de episódio inteiro de uma vez», será preciso ciclo de vida submit-poll estilo video — por isso o Protocol `AudioBackend` **reserva** a possibilidade assíncrona (como text/video permitem formas próprias de backend), mas v1 só implementa síncrono.
- **Task sem migração**: `task.task_type` / `media_type` são colunas String livres; linhas audio caem no DB direto.
- **Versionamento inalterado**: audio, como image/video, versiona via VersionManager (ver «narração com voz» e entrada de tipo de mídia audio em `CONTEXT.md`).
- **A assimetria com text é contrato**: text gera uma vez por episódio, inline síncrono, sem fila; audio gera N segmentos por episódio, entra na fila. Qualquer PR futuro que queira devolver audio a inline síncrono (ou meter text na fila) precisa deprecar este ADR e justificar mudança na base de geração.
