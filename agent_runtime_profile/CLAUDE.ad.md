# Espaço de trabalho de geração de vídeo com IA
<!-- mode: ad -->

---

## Regras gerais importantes

As regras abaixo se aplicam a **todas** as operações do projeto:

### Especificações de vídeo
- **Proporção do vídeo**: definida por `aspect_ratio` do projeto (anúncios/curtas padrão 9:16 vertical); não é necessário especificar no prompt
- **Duração por shot**: projetos ad/curta **não** usam preferência `default_duration` — a duração de cada shot é planejada em função de `target_duration` (duração total alvo, em segundos)
  - modo storyboard: a duração de cada shot deve ser um valor de `supported_durations` do modelo de vídeo escolhido; o subagent consulta o valor real em runtime via `mcp__arcreel__get_video_capabilities`
  - modo reference_video: duração por shot é inteiro livre de 1–15 segundos, sem restrição de `supported_durations` do provedor (ritmo de cortes curtos depende disso)
- **Resolução de imagem**: 1K
- **Resolução de vídeo**: 1080p
- **Forma de geração**: conforme `generation_mode` — storyboard gera cada shot de forma independente com a storyboard como frame inicial; reference_video gera por grupos derivados (video_unit), pulando storyboard (ver «Modos de geração» abaixo)

> **Sobre a função extend**: o extend do Veo 3.1 serve apenas para alongar um único shot,
> +7 segundos fixos por vez, e **não** serve para encadear shots diferentes. Entre shots diferentes use concatenação com ffmpeg.

### Normas de áudio
- **BGM proibido automaticamente**: ao final do prompt de vídeo, acrescentar sempre «proibido: BGM, legendas de texto, marcas d'água»

### Chamadas de ferramentas

- **Fila de negócio / geração de texto / consulta de capacidades**: sempre via ferramentas MCP in-process `mcp__arcreel__*` (personagem/cena/prop/storyboard/vídeo/grid/script de episódio/script normalizado/consulta de capacidades de vídeo). Rodam no processo principal do server, sem restrição da whitelist de rede do sandbox; o agent chama como tool.
- **Edição de JSON do projeto**: alterar scripts (`scripts/*.json`) ou personagens/cenas/props (`project.json`) **sempre via ferramentas de edição `mcp__arcreel__*`** — campos do script com `patch_episode_script` (batch-native: mapa `{id_do_shot: {caminho_do_campo: valor}}`, uma chamada altera vários shots × vários campos; edição unitária = mapa de tamanho 1; atômico all-or-nothing: qualquer edição inválida descarta o lote inteiro e o erro aponta shot id e campo; erros de validação estrutural reportam o caminho do campo; antes de edições em lote, faça Read do script para confirmar o estado atual), título do episódio com `patch_episode_meta`, inserir/remover/dividir shots com `insert_segment` / `remove_segment` / `split_segment`, personagens/cenas/props com `patch_project`. **Proibido** usar Write / Edit / Bash para alterar esses dois tipos de arquivo (bloqueados por sandbox `denyWrite` e hook PreToolUse). **Prompt alterado exige regeneração**: após mudar `image_prompt` / `video_prompt` de shots com `patch_episode_script`, a ferramenta **não** invalida imagem/vídeo antigos — chame em seguida a geração correspondente desses shots, senão fica «prompt novo + imagem antiga».
- **Uso do Bash**: apenas diagnóstico e navegação de arquivos (`ls` / `cat` / `jq` / `python` / `curl` etc.), e scripts Python ainda presentes nos skills `manage-project` / `compose-video`.
- **Proteção de arquivos sensíveis**: `.env` / `vertex_keys/` / `.system_config.json*` / `.arcreel.db*` / `.claude/settings.json` são bloqueados em nível de kernel pelo sandbox profile (`filesystem.denyRead`) e pelo hook PreToolUse de acesso a arquivos; arquivos de código (`.py`/`.js`/`.ts`/`.tsx`/`.sh`/`.yaml`/`.yml`/`.toml`) têm escrita bloqueada por hook em runtime.

### Normas de caminho

O diretório de trabalho atual (cwd) da sessão do agent já está ligado à raiz do projeto atual. **Todos os caminhos em parâmetros de ferramentas devem seguir**:

- **Read / Edit / Write / Glob / Grep**: `file_path` com **caminho absoluto**
- **Bash chamando scripts de skill**: caminhos **relativos à raiz do projeto (cwd)**, por exemplo:
  - ✅ `scripts/episode_1.json`, `storyboards/E1S01.png`
  - ❌ `projects/{nome_do_projeto}/scripts/episode_1.json` (prefixo duplo; placeholder ou concatenação errada cai na raiz de projects)
- **Proibido** aparecer o prefixo `projects/{...}/` em parâmetros de ferramentas; esse prefixo só documenta a estrutura de pastas e **não** deve ser passado a nenhuma ferramenta
- Scripts de skill validam o cwd e recusam execução se o cwd não for a raiz do projeto atual
- **Sobre formas relativas em agent.md / SKILL.md**: caminhos relativos nas instruções de subagent (ex.: «ler `project.json`») são **localização dentro do projeto**, não valores de `file_path` prontos. Em Read/Edit/Write/Glob/Grep, monte o caminho absoluto a partir do cwd da sessão

---

## Modo de conteúdo

Este projeto é **modo anúncio/curta** (`ad`), produzindo **um único** vídeo curto de cerca de `target_duration` segundos, e não uma série multi-episódio:

- Estrutura do script: lista plana `shots[]`, `shot_id` no formato `E1S{n}`; cada shot carrega `section` (rótulo de seção do framework de venda, ex.: hook/pain_point/product_reveal/selling_point/demo/trust/price_promo/cta) e copy de locução de primeira classe `voiceover_text` (única fonte para export de legendas e dublagem posterior)
- Projeto **sempre de um episódio**: `episodes` tem sempre só o item do episódio 1; o script é `scripts/episode_1.json`; **não existe conceito de divisão em episódios** — não planeje nem divida episódios
- Entrada criativa: `brief` (texto curto de briefing) e `target_duration` (duração total alvo, segundos) no topo de `project.json`; não usa fluxo de importação de arquivo de romance/fonte
- A duração total do script deve se aproximar de `target_duration`; desvio grande → avisar o usuário, não recusar o save

> O modo de geração é configurado pelo campo `generation_mode` em `project.json`, independente do modo de conteúdo.

---

## Modos de geração

O modo anúncio/curta libera apenas dois **modos de geração** (`generation_mode`):

| generation_mode | Nome (UI) | Estrutura principal de dados | Fonte de referência visual |
|---|---|---|---|
| `storyboard` (padrão) | Imagem→vídeo | `shots[]` + imagens de storyboard | Uma storyboard por shot como frame inicial |
| `reference_video` | Referência→vídeo | grupos derivados de `shots[]` | Referência de produto + sheets de ativos |

`grid` (vídeo por grid) **não** está disponível para projetos ad/curta: resolução por célula do grid conflita com o objetivo de alta fidelidade do produto.

### Agrupamento derivado do reference_video

- O esqueleto do script não muda (continua lista plana `shots[]`); as ferramentas `generate_video_*` agrupam automaticamente **shots consecutivos** em video_units (cada unit ≤4 shots; duração total do unit limitada pelo teto de geração única do provedor), geram vídeo por unit em `reference_videos/{unit_id}.mp4` e **pulam** o passo de storyboard
- O índice de agrupamento fica no campo `reference_units` do script (só referências a shot_id e conjuntos de referência) — mantido pelas ferramentas, **não editar à mão**; `shots` é a única fonte de verdade de conteúdo; após editar shots, a próxima geração rederiva automaticamente; units inalterados não regeneram
- O conjunto de referência de cada unit herda dos shots membros: referência de produto injetada por completo e com prioridade absoluta (com sheet: sheet + original; sem sheet: original direto; instrução de alta fidelidade anexada), depois sheets de personagem/cena/prop; copy de locução **não** entra no prompt de imagem
- **Troca de caminho no meio**: após mudar `generation_mode`, a duração dos shots pode violar as novas restrições (storyboard exige membros de `supported_durations`; reference exige inteiro 1–15 s); listar proativamente shots fora da faixa e sugerir ajuste, corrigir com `patch_episode_script` e só então gerar

---

## Visão geral do fluxo de trabalho

O skill de orquestração `/manga-workflow` avança pelas etapas abaixo (confirmar com o usuário após cada etapa antes de seguir); use-o quando o usuário falar em fazer vídeo, continuar o projeto ou ver progresso. Em etapas ainda não implementadas, informe com honestidade — **não** substitua pelo fluxo de romance de narration/drama:

1. **Confirmar entrada criativa**: Read `project.json` e checar `brief`, `products`, `target_duration`, `generation_mode`, `brand_profile`. Em projeto de venda, se produto não estiver cadastrado ou faltar imagem original, orientar o usuário a enviar a imagem na página de inicialização do WebUI ou na página de ativos de produto (a original é o âncora de fidelidade do produto; o agent **não** pode enviar imagem no lugar do usuário; após upload o sistema pode gerar opcionalmente `*_isolated.png` de referência sem fundo, sem sobrescrever o original; curta genérico: ver abaixo, não pedir produto); se o usuário marcar «gerar referência padrão do produto», o product sheet entra na fila de tarefas. Se `brief` estiver vazio, completar o briefing na conversa (produto/tema, público-alvo, estilo desejado) e gravar com `mcp__arcreel__patch_project`
2. **Brand Analyzer**: com `brief`/produto prontos, chamar `mcp__arcreel__brand_analyzer_prompt` para obter instruções de redação, produzir `brand_profile` (visual_description, tone_of_voice, target_audience, brand_colors, style_keywords, style_prefix), confirmar com o usuário e gravar via `patch_project` settings — `style_prefix` é injetado em todos os prompts de storyboard/vídeo seguintes
3. **Confirmar selling points**: se produto cadastrado mas `selling_points` vazio, redigir lista de selling points a partir do brief, descrição do produto e original; confirmar com o usuário e gravar na tabela products via `patch_project` — a geração do script injeta selling points nas seções selling_point/demo do framework de venda
4. **Design de ativos (opcional)**: definir em `project.json` personagens/cenas/props que o script usará e dispatch do subagent `generate-assets` para as artes; curtas leves podem pular e depender só da referência de produto e do style do projeto
5. **Gerar script de uma vez**: `mcp__arcreel__generate_episode_script({"episode": 1})`, framework de oito seções de venda dimensionado por `target_duration`; após gerar, apresentar lista de shots e copy de locução; ajustar com `patch_episode_script` conforme necessário (reordenação de shots: orientar o usuário à página de script no WebUI)
6. **Revisão do product sheet (gate soft)**: se o produto tiver `product_sheet`, antes de iniciar storyboard (no caminho reference_video: antes da primeira geração de vídeo) pedir que o usuário confirme no ativo de produto que o sheet bate com o produto real (ver «Fidelidade do produto» abaixo); sem sheet (só original), seguir direto
7. **Geração de storyboard** (somente caminho storyboard; reference_video pula): shots de produto recebem automaticamente referência de produto + brand style_prefix; após gerar, orientar revisão de fidelidade da imagem do produto e regenerar o que falhar — interceptar **antes** de gastar com vídeo
8. **Geração de vídeo**: caminho storyboard faz imagem→vídeo shot a shot (`ad_video_takes` padrão 1; subir para 2–3 permite comparar takes; o version manager guarda cada take e o usuário pode restaurar a versão escolhida); entre shots, por padrão last-frame continuation (`ad_continuation`, último frame do shot anterior como start do próximo); caminho reference_video deriva grupos e gera por unit
9. **Crítica de consistência**: após o vídeo, chamar `mcp__arcreel__critique_ad_consistency`; regenerar shots com `recommend_regen=true` (pode trocar seed); só seguir para o filme final quando passar
10. **Export do filme final**:
    - **Rascunho CapCut/Jianying** (recomendado): export no Web (trilha de vídeo + trilha de legendas da copy de locução)
    - **compose-video in-app**: já suporta ad `shots[]`; pode gravar `ad_timeline` com `patch_project` (`text_overlays` + `music_track`, arquivo de música em `music/` do projeto) e depois rodar o skill compose-video

O fluxo tem **entrada flexível**: a partir de `project.json` e do estado do script, retoma a partir da etapa incompleta após interrupção.

### Fidelidade do produto (gate soft)

- **Revisão do product sheet antes do storyboard**: se o produto tiver referência padrão (`product_sheet`), antes de iniciar storyboard (no caminho reference_video: antes da primeira geração de vídeo — esse caminho injeta o sheet no conjunto de referência do vídeo, então confirme **antes** de gastar com vídeo) peça ao usuário confirmar na página de ativos que o sheet bate com o produto real (se não, regenerar); só continue após confirmação. Isso é convenção de fluxo, não máquina de estados do sistema — sem sheet (só original), pode iniciar direto
- Shots de produto (`products_in_shot` não vazio) recebem **automaticamente** referência de produto no storyboard e no vídeo (com sheet: sheet + original; sem sheet: original direto; inclui isolated sem fundo opcional) e instrução de restauração em alta fidelidade; **não** é preciso repetir detalhes de aparência do produto em image_prompt / video_prompt; shots de atmosfera sem produto: o estilo vem do style do projeto + `brand_profile.style_prefix`
- Após o storyboard, orientar revisão de fidelidade da imagem do produto e regenerar shots ruins — interceptar imagem errada do produto **antes** do custo de vídeo
- Após múltiplos takes de vídeo, use API de versões / time machine para escolher o melhor take; `critique_ad_consistency` marca shots a regenerar com base em similaridade estrutural + visual bruta

### Curta genérico (sem produto)

`products` vazio = curta genérico: a geração de script desvia automaticamente para o prompt genérico; não há submodo explícito. Venda vs genérico depende da **intenção do usuário** — se quer promover um produto ainda não cadastrado, orientar upload (completar produto **antes** do script); só se a intenção não envolve produto concreto seguir como curta genérico. Diferenças de orientação na conversa:

- Pular upload de produto, revisão de sheet e redação de selling points; **não** pedir informações de produto
- `brief` é a única entrada criativa; orientar o usuário a enriquecer tema, tom emocional, estilo visual e ritmo narrativo antes de gerar o script
- Ativos de personagem/cena/prop continuam disponíveis; rótulos `section` não precisam forçar as oito seções de venda — organize pelo ritmo do conteúdo

### Contorno de restrições a pessoas reais em cena

Alguns provedores de imagem/vídeo **suspenderam upload de imagens de referência com rosto humano nítido** (rejeição por moderação facial). Quais provedores estão restritos muda com a política; valer o erro real:

- Se produto/referência enviada pelo usuário tiver rosto humano nítido, avisar de antemão que a geração pode ser rejeitada por alguns provedores
- Ao planejar shots, priorizar expressões que não dependem de close de rosto real: mãos/partes interagindo com o produto, costas, silhueta, close do produto, plano vazio
- Se o usuário insistir em pessoa real em cena, gerar normalmente; em erro de moderação facial, **não** insistir no mesmo provedor — explicar e oferecer duas vias: trocar no settings para provedor sem a restrição e tentar de novo, ou redesenhar o shot sem close de rosto real
- Se o rosto estiver na **imagem original do produto ou no sheet**, mudar composição não ajuda — shots de produto injetam essas referências e o rosto vai junto ao provedor; orientar o usuário a trocar ou recortar a original (remover a parte do rosto) e reenviar

## Limites de responsabilidade

- **Proibido escrever código**: não criar nem modificar arquivos de código (`.py`/`.js`/`.sh` etc.); processamento de dados via ferramentas `mcp__arcreel__*` ou scripts existentes de `manage-project` / `compose-video`
- **Reportar bug de código**: se ficar claro que o erro do MCP tool ou do script do skill é bug de código (não de parâmetro ou ambiente), reportar ao usuário e sugerir feedback aos desenvolvedores

## Estrutura de diretórios do projeto

> A árvore abaixo é só ilustrativa; o cwd da sessão já está na raiz do projeto. **Bash chamando scripts de skill** usa caminhos relativos ao cwd (ex.: `scripts/`); **Read / Edit / Write / Glob / Grep** usam **caminho absoluto** conforme «Normas de caminho». Em nenhuma ferramenta use o prefixo `projects/{nome_do_projeto}/`.

```text
projects/{nome_do_projeto}/      # ← cwd da sessão já está aqui; abaixo são relativos ao cwd
├── project.json       # metadados (produtos, personagens, cenas, props, estilo, target_duration, brief)
├── scripts/           # script (JSON), sempre episode_1.json
├── products/          # product sheet; products/refs/ guarda originais enviados pelo usuário
├── characters/        # artes de personagem
├── scenes/            # artes de cena
├── props/             # artes de prop
├── storyboards/       # imagens de storyboard (modo storyboard)
├── videos/            # clipes de vídeo gerados (modo storyboard)
├── reference_videos/  # video_units gerados (modo reference_video)
├── thumbnails/        # thumbnails do primeiro frame
└── output/            # saída final
```

### Campos principais de project.json

- `schema_version`: versão do formato de dados do projeto
- `title`, `content_mode` (fixo `ad`), `generation_mode` (`storyboard`/`reference_video`), `style`, `style_description`
- `target_duration`: duração total alvo (segundos, inteiro positivo)
- `brief`: texto curto de briefing criativo (pode ser vazio)
- `brand_profile`: perfil de marca (visual_description / tone_of_voice / target_audience / brand_colors / style_keywords / style_prefix), redigido pelo Brand Analyzer
- `ad_timeline`: timeline do filme final (`text_overlays[]`, `music_track` caminho relativo no projeto)
- `ad_continuation`: last-frame continuation entre shots (padrão true)
- `ad_video_takes`: número de takes de vídeo por shot 1–3 (padrão 1; 2–3 para multi-take)
- `episodes`: sempre um único item do episódio 1 (episode, title, script_file)
- `products`: definição completa do ativo de produto (description, brand, reference_images lista de originais, selling_points, product_sheet)
- `characters` / `scenes` / `props`: definições completas dos ativos
- `music/`: pasta opcional de BGM (`ad_timeline.music_track` aponta para arquivo aqui no compose)

### Princípios de camadas de dados

- Definições completas de produto/personagem/cena/prop **só em project.json**; o script só referencia nomes
- Campos estatísticos (`scenes_count`, `status`, `progress` etc.) são **calculados na leitura** por StatusCalculator, não armazenados
- Metadados de episódio (episode/title/script_file) são **sincronizados na escrita** ao salvar o script
