## Why

O sistema atual carece de um **mecanismo de mapeamento romance → episódios**. Depois que o usuário envia o romance completo, o sistema passa o texto inteiro ao Gemini para gerar o roteiro, mas não é possível especificar "este episódio usa só esta parte do romance". Manifestações concretas:

1. `normalize_drama_script.py` por padrão lê **todos os arquivos concatenados** em `source/`; o parâmetro `--source` só aceita o arquivo inteiro, não um intervalo dentro do arquivo
2. A description do subagent `split-narration-segments` menciona "intervalo de texto do romance deste episódio", mas não há mecanismo real para o usuário definir ou fatiar esse intervalo
3. No dispatch de `manga-workflow` está escrito `intervalo do romance deste episódio: {nome do capítulo/arquivo/descrição de início-fim}`, mas esse valor não tem de onde vir — o agente principal não sabe qual parte do romance corresponde a qual episódio

Consequências:
- Romance de 100 mil caracteres é despejado por completo no Gemini; a qualidade fica incontrolável (o modelo decide sozinho o que usar)
- O usuário não consegue produzir sob demanda só um episódio (ex.: só os primeiros 1000 caracteres)
- Na produção multi-episódio faltam limites de divisão consistentes

## What Changes

Novo mecanismo de **planejamento progressivo de divisão em episódios**: dois scripts implementam o fluxo colaborativo humano–máquina.

### Ideia central

```
Usuário define a meta de caracteres (ex.: 1000 caracteres/episódio)
    ↓
Script peek mostra o contexto perto do ponto de corte (200 caracteres antes/depois)
    ↓
Agent lê o contexto e sugere um ponto de quebra natural (ponto final, parágrafo, limite de capítulo)
    ↓
Usuário confirma ou ajusta
    ↓
split --anchor "texto antes do ponto de quebra" --dry-run  valida a posição de corte
    ↓
Confirmação → split executa de verdade: episode_N.txt + _remaining.txt
    ↓
Repete para o próximo episódio
```

### Scripts novos

**1. `peek_split_point.py`** — sondagem do ponto de corte

```bash
python peek_split_point.py --source source/novel.txt --target 1000 --context 200
```

- Entrada: caminho do arquivo-fonte, meta de caracteres, tamanho do contexto (padrão 200)
- Regra de contagem: inclui pontuação, exclui linhas em branco (apenas formatação)
- Saída: texto de contexto antes/depois do ponto de corte + metadados (total de caracteres, posição-alvo, offset real de caracteres)

**2. `split_episode.py`** — executar o corte

```bash
# Dry run primeiro para validar a posição
python split_episode.py --source source/novel.txt --episode 1 --anchor "Ele se virou e partiu." --dry-run

# Após confirmar, executar de verdade
python split_episode.py --source source/novel.txt --episode 1 --anchor "Ele se virou e partiu."
```

- Entrada: caminho do arquivo-fonte, número do episódio, texto âncora (10–20 caracteres antes do ponto de corte)
- `--dry-run`: só mostra a prévia do corte (50 caracteres do fim da parte anterior + início da parte seguinte), sem gravar arquivos
- Se a âncora casar em vários pontos, erro pedindo âncora mais longa
- Saída:
  - `source/episode_N.txt` — conteúdo deste episódio
  - `source/_remaining.txt` — conteúdo restante (atualização por sobrescrita)
- O arquivo original permanece intacto

### Integração no fluxo de trabalho

O planejamento de divisão entra como **checagem prévia da etapa 2 (pré-processamento de episódio)** em `manga-workflow`:

```
Ao disparar a etapa 2:
  Verificar se source/episode_{N}.txt existe
    ├─ Existe → entrar direto no pré-processamento
    └─ Não existe → disparar o fluxo de planejamento de divisão:
         1. Agente principal pergunta a meta de caracteres (ou usa a última definida)
         2. Despacha subagent para chamar peek_split_point.py
         3. Agent analisa o contexto e sugere o ponto de corte
         4. Usuário confirma
         5. Chama split_episode.py para executar o corte
         6. Continua o pré-processamento (usando episode_N.txt)
```

### Corte sob demanda por episódio

O planejamento de divisão **não fatia o romance inteiro de uma vez**; corta só o episódio que se pretende produzir agora:

```
Ao produzir o episódio 1:
  source/episode_1.txt não existe
  → peek novel.txt → confirmar → split → episode_1.txt + _remaining.txt
  → continua pré-processamento, geração de roteiro, geração de ativos...

(Alguns dias depois) ao produzir o episódio 2:
  source/episode_2.txt não existe
  → peek _remaining.txt → confirmar → split → episode_2.txt + _remaining.txt (atualizado)
  → continua produção do episódio 2...

O usuário pode parar a qualquer momento; não precisa planejar todos os episódios de uma vez.
```

### Adaptação dos scripts existentes

`normalize_drama_script.py` e o subagent `split-narration-segments` não precisam de grandes mudanças — basta, no dispatch, especificar `--source source/episode_N.txt` para lerem o arquivo de episódio já fatiado em vez do romance inteiro.

## Capabilities

### New Capabilities
- `episode-splitting`: planejamento progressivo de divisão em episódios — peek do ponto de corte + confirmação colaborativa humano–máquina + corte físico em arquivos per-episode

### Modified Capabilities
- `workflow-orchestration` (de refactor-script-creation-workflow): etapa 2 de manga-workflow ganha checagem prévia; se faltar arquivo de episódio, dispara o fluxo de divisão

## Impact

- **Arquivos novos**:
  - `agent_runtime_profile/.claude/skills/manage-project/scripts/peek_split_point.py`
  - `agent_runtime_profile/.claude/skills/manage-project/scripts/split_episode.py`
- **Arquivos modificados**:
  - `agent_runtime_profile/.claude/skills/manga-workflow/SKILL.md` — lógica de checagem prévia na etapa 2
  - `agent_runtime_profile/.claude/settings.json` — permissão Bash dos dois novos scripts
- **Não afetados**:
  - `normalize_drama_script.py` — já suporta `--source`, sem mudanças
  - subagent `split-narration-segments` — basta especificar o caminho no dispatch
  - serviços de backend, frontend e modelos de dados não são afetados
