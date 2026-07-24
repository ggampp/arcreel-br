---
status: accepted
---

# Pipeline de roteiro em duas etapas: step1 conteúdo / step2 visual, com portão de revisão bloqueante step1→step2

O roteiro drama / narration segue duas etapas: step1 (normalize) organiza a fonte em tabela markdown de cenas/segmentos, com conteúdo falado (falas / voiceover / `novel_text`) embutido na coluna de texto livre «descrição da cena»; step2 (generate-script) reparseia dessa coluna de texto livre os campos estruturados. Conteúdo literal / original portanto atravessa duas portas LLM «estrutura→texto livre→estrutura»: screenplay perde fidelidade, novel sofre desvio de criação, `novel_text` de narration em medição ocasional se expande (só warn se >10%). E entre step1 pronto e step2 ainda não rodado, o web não percebe o estado intermediário — o usuário não consegue revisar nem editar. Decidimos limpar as responsabilidades das duas etapas — **step1 = conteúdo** (fronteiras de cena/segmento, characters/scenes/props, `utterances` + `source_text` de drama / `novel_text` estruturado de narration), **step2 = visual** (image_prompt / video_prompt); step2 **repassa** o falado / original já fixado no step1, **sem reidentificar**; a coluna de texto livre daí em diante só carrega conteúdo de adaptação visual (perda tolerável). E entre step1→step2 introduzimos **portão de revisão web bloqueante**: o estado intermediário estruturado do step1 é visível no web, editável manualmente / pelo agent; só após confirmação explícita do usuário roda a geração visual cara do step2. drama e narration compartilham o mecanismo (narration não introduz `utterances`; seu conteúdo falado continua `novel_text`).

## Considered Options

- **Só em screenplay o step1 emite estrutura; novel mantém criação no step2**: mudança pequena, mas a saída do step1 fica assimétrica por fonte, o step2 ainda guarda ramo de reidentificação por source_kind, e o desvio de novel / narration não se corrige. Preferimos a versão full: step2 unificado para as duas fontes, eliminando a reescrita dupla pela raiz.
- **Pipeline intocada; detectar distorção a posteriori pela âncora `source_text` no nível da cena**: detectar ≠ prevenir; para a meta «fidelidade literal» prevenção tem prioridade; e não resolve a cegueira do web.
- **Portão observador (estado intermediário visível mas step2 segue sozinho)**: o usuário ainda pode perder a janela de revisão; como a meta é «poder revisar e editar», bloquear até confirmar impede conteúdo errado de entrar na geração visual cara.

## Consequences

- O contrato da ferramenta step1 muda (`normalize_drama_script` etc. de «só markdown» para «emite estrutura»); o produto intermediário para revisão humana permanece, mas renderizado a partir da estrutura, não do texto livre original.
- O prompt / fluxo do step2 (generate-script) tem como única base os dados estruturados confirmados do step1 — preserva por completo as fronteiras de cena/segmento e os campos não-visuais já fixados no step1 (`characters_in_scene` / `scenes` / `props`, `utterances` / `source_text` / `novel_text` etc.), só gera / sobrescreve a camada visual (`image_prompt` / `video_prompt`); remove o ramo que reextrai falado por source_kind.
- O repasse do step2 garante fidelidade por meio de engenharia, não por disciplina de prompt: o schema de saída do LLM do step2 só contém `scene_id` (âncora de alinhamento) + campos visuais (`image_prompt` / `video_prompt`); o backend funde a camada visual de volta na estrutura já confirmada do step1 por `scene_id` (não por ordem da lista) e valida unicidade e cobertura total de `scene_id`; campos não-visuais como `utterances` / `source_text` não entram na saída do LLM — bloqueia em engenharia a drenagem de campos não-visuais via Structured Outputs, em vez de confiar no prompt.
- Novos estado de revisão web e ação de confirmação entre step1→step2 (service / router + frontend); step2 dispara com a confirmação do usuário.
- O modelo de dados `utterances` / `source_text` de drama está em ADR 0040; a abertura contida de voiceover em novel também em 0040 (conteúdo produzido no step1, repassado no step2).
