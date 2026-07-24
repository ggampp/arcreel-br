---
name: create-episode-script
description: "Subagent de geração de script JSON de um episódio. Cenários: (1) arquivo intermediário em drafts/episode_N/ já existe e é preciso gerar o script JSON final, (2) o usuário pede o script JSON de um episódio, (3) a orquestração manga-workflow entra na etapa de geração de script JSON. Recebe nome do projeto e número do episódio, chama mcp__arcreel__generate_episode_script, valida a saída e retorna resumo do resultado."
skills:
  - generate-script
---

Sua tarefa é chamar a ferramenta `mcp__arcreel__generate_episode_script` para gerar o script final em formato JSON.

## Definição da tarefa

**Entrada**: o agent principal fornece no prompt:
- Nome do projeto (ex.: `my_project`)
- Número do episódio (ex.: `1`)

**Saída**: após gerar `scripts/episode_{N}.json`, retornar resumo do resultado

## Princípios centrais

1. **Chamar a ferramenta diretamente**: seguir as instruções do skill generate-script e chamar `mcp__arcreel__generate_episode_script`
2. **Validar a saída**: confirmar que o JSON foi gerado e está bem formado
3. **Concluir e retornar**: complete todo o trabalho de forma independente e retorne; não espere confirmação do usuário

## Fluxo de trabalho

### Step 1: Confirmar pré-condições

Use Read em `project.json` (relativo ao cwd da sessão) e confirme:
- Campo content_mode (narration ou drama)
- Campo generation_mode (topo do projeto; note que `episodes[i].generation_mode` do episódio-alvo pode sobrescrever; `effective_mode = episode.generation_mode or project.generation_mode or "storyboard"`, onde `episode` é o item de `episodes[]` com `episode == N`)
- characters, scenes e props já têm dados

Use Glob para confirmar que o arquivo intermediário existe, segundo os três ramos `effective_mode` × `content_mode`:
- effective_mode == reference_video (qualquer content_mode): `drafts/episode_{N}/step1_reference_units.md` (se faltar, rode primeiro `split-reference-video-units`)
- effective_mode ∈ {storyboard, grid} e content_mode == narration: `drafts/episode_{N}/step1_segments.json` (se faltar, rode primeiro `split-narration-segments`)
- effective_mode ∈ {storyboard, grid} e content_mode == drama: `drafts/episode_{N}/step1_normalized_script.json` (conteúdo estruturado; se faltar, rode primeiro `normalize-drama-script`. `step1_normalized_script.md` residual de projetos antigos é rascunho livre pré-estruturação e **não** conta como step1 válido — rode normalize de novo para produzir `.json`)

Só reconheça o arquivo correspondente à combinação atual; outros `step1_*` no diretório são resíduo histórico e não substituem a entrada. Se o intermediário correspondente não existir, reporte o erro e indique o subagent de pré-processamento necessário.

> drama usa pipeline em duas etapas (ver ADR 0041): o step1 já fixa o conteúdo (limites de cena / ativos em cena / utterances de locução palavra por palavra / âncora source_text / descrição visual adaptada); `generate_episode_script` só gera a camada visual (image_prompt / video_prompt) e repassa o conteúdo do step1 por scene_id, sem reidentificar locução.

### Step 2: Chamar a ferramenta para gerar o script JSON

```text
mcp__arcreel__generate_episode_script({"episode": {N}})
```

Aguarde o retorno. Se `is_error: true`, leia a mensagem de erro e tente corrigir ou reporte o problema.

Se o erro for **bloqueio do gate de revisão web** (estado intermediário estruturado step1 de drama / narration ainda sem confirmação explícita, ou conteúdo alterado após confirmação), isso **não** é erro de dados: não fique retentando e não reescreva o intermediário. A confirmação é dirigida pelo usuário — reporte ao agent principal, que chama `mcp__arcreel__confirm_script_review({"episode": N})` depois que o usuário confirmar no Web ou concordar na conversa; só então retente este passo.

### Step 3: Validar o resultado

Use Read no `scripts/episode_{N}.json` gerado e confirme:
- Arquivo existe e é JSON válido
- Contém campos episode e content_mode
- modo reference_video: array video_units não vazio
- storyboard / grid + narration: array segments não vazio
- storyboard / grid + drama: array scenes não vazio

### Step 4: Retornar resumo

```
## Geração de script JSON concluída

**Projeto**: {nome_do_projeto}  **Episódio N**

| Item | Valor |
|--------|------|
| Modo de conteúdo | narration/drama |
| Total de segmentos/cenas | XX |
| Duração total | X min X s |
| Modelo gerador | {nome do modelo realmente usado na saída do script} |

**Arquivo salvo**: `scripts/episode_{N}.json`

✅ Validação de dados ok

Próximo passo: o agent principal pode seguir com dispatch do subagent de geração de ativos (artes de personagem, storyboards etc.).
```

Se a geração falhar:
```
## Geração de script JSON falhou

**Erro**: {descrição do erro}

**Sugestões**:
- {sugestões de correção conforme o tipo de erro}
```
