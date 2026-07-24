## Context

### Situação atual

No fluxo de criação de roteiro do ArcReel, `normalize_drama_script.py` por padrão lê e concatena todos os arquivos em `source/` e envia ao Gemini. Para contos curtos isso funciona, mas quando o usuário envia um romance longo completo não dá para especificar "este episódio usa só do trecho X ao Y". Embora a orquestração de `manga-workflow` reserve o parâmetro "intervalo do romance deste episódio", não há mecanismo real de fatiamento.

### Dependências

Este change depende da arquitetura já concluída em `refactor-script-creation-workflow` — subagents focados + skill de orquestração manga-workflow. O novo fluxo de planejamento de divisão se encaixa na checagem prévia da etapa 2 de manga-workflow.

### Arquivos relacionados

| Arquivo | Papel |
|------|------|
| `agent_runtime_profile/.claude/skills/manga-workflow/SKILL.md` | Skill de orquestração; precisa da checagem prévia |
| `agent_runtime_profile/.claude/skills/manage-project/scripts/` | Diretório de scripts de gestão de projeto; novos scripts ficam aqui |
| `agent_runtime_profile/.claude/settings.json` | Configuração de permissões |
| `agent_runtime_profile/.claude/agents/normalize-drama-script.md` | Subagent de pré-processamento no modo drama |
| `agent_runtime_profile/.claude/agents/split-narration-segments.md` | Subagent de pré-processamento no modo narration |

## Goals / Non-Goals

**Goals:**

1. Fornecer o script `peek_split_point.py` para mostrar o contexto perto da meta de caracteres, apoiando a decisão do agent e do usuário
2. Fornecer o script `split_episode.py` para fatiar fisicamente o romance em arquivo per-episode + arquivo restante
3. Embutir o planejamento de divisão na checagem prévia da etapa 2 de manga-workflow
4. Manter inalterados os scripts existentes (`normalize_drama_script.py`, `generate_script.py`)

**Non-Goals:**

- Não implementar divisão automática total (IA decide sozinha os limites de cada episódio) — manter confirmação humana
- Não implementar UI no frontend (arrastar para marcar intervalos etc.) — feito via conversa com o agent
- Não alterar a estrutura de dados de project.json (não armazenar mapeamento episode_plan)
- Não adotar mapeamento lógico (recorte dinâmico por texto âncora) — adotar corte físico

## Decisions

### Decision 1: Localização do corte — correspondência por texto âncora

**Escolha**: `split_episode.py` localiza o ponto de corte por **texto âncora** (N caracteres antes do ponto), e não por offset numérico

**Fluxo**:
```
peek gera o contexto → agent sugere o ponto de quebra → usuário confirma
    ↓
split --anchor "Ele se virou e partiu." --dry-run    ← dry run primeiro
    ↓
Saída: "Posição encontrada; o corte será no caractere 1047.
      Fim da parte anterior: ...a luz da lua sobre as pedras. Ele se virou e partiu.
      Início da parte seguinte: Capítulo 2 O deserto..."
    ↓
Usuário confirma → split --anchor "Ele se virou e partiu."  ← execução real
```

**Design dos parâmetros**:
- `--anchor <text>`: trecho de texto antes do ponto de corte (sugerido 10–20 caracteres); o script busca esse texto no original e corta no **fim** dele
- `--dry-run`: só mostra a prévia (50 caracteres do fim da parte anterior + início da parte seguinte), sem gravar
- Se a âncora casar em vários pontos, erro pedindo âncora mais longa

**Alternativas**:
- Offset numérico `--split-at 1047` → peek e split precisam da mesma base de contagem; o usuário não valida a posição facilmente
- Número de linha → parágrafos de romance chinês/português variam muito; impreciso

**Justificativa**: texto âncora é legível e verificável. O dry run permite confirmar antes do corte real. Mesmo com pequenas mudanças no arquivo (ex.: correção de digitação), se a âncora ainda existir a posição permanece correta.

### Decision 2: Corte físico vs mapeamento lógico

**Escolha**: corte físico (gerar arquivos `source/episode_N.txt`)

**Alternativas**:
- Registrar mapeamento `{start_marker, end_marker}` em project.json e recortar dinamicamente na execução → exige mudar vários scripts downstream; âncoras falham com facilidade
- Usuário divide e envia os arquivos manualmente → má experiência

**Justificativa**: após o corte físico, o fluxo downstream (`normalize_drama_script.py --source source/episode_N.txt`) fica com **zero mudanças**. Arquivo = estado; simples, confiável e depurável.

### Decision 2 (cont.): Regra de contagem de caracteres

**Escolha**: inclui pontuação, exclui linhas em branco

- Escopo da contagem: caracteres de todas as linhas não vazias (incluindo CJK, pontuação, dígitos, letras latinas)
- Exclusões: linhas só em branco (`\n`, `\r\n`, linhas só com espaços)
- Justificativa: pontuação faz parte do conteúdo (afeta duração de narração); linhas em branco são só formatação

### Decision 3: Gestão do conteúdo restante

**Escolha**: `_remaining.txt` sobrescrito a cada split

- Após cada split, `_remaining.txt` é atualizado com o restante
- O original `novel.txt` (ou o arquivo enviado pelo usuário) é sempre preservado
- Para recomeçar a divisão, parte-se de novo do original

**Alternativas**:
- Só registrar offsets e recortar dinamicamente do original → complexidade de estado
- Não guardar restante e subtrair a cada vez do original → cálculo frágil

### Decision 4: Local dos scripts

**Escolha**: `agent_runtime_profile/.claude/skills/manage-project/scripts/`

**Justificativa**: divisão em episódios é gestão de projeto, no mesmo diretório de `add_characters_clues.py`. Não pertence à skill `generate-script` (essa gera o roteiro JSON).

### Decision 5: Posição do planejamento de divisão no fluxo

**Escolha**: checagem prévia da etapa 2, não uma etapa independente

**Justificativa**:
- Só dispara quando necessário (`source/episode_{N}.txt` inexistente)
- Se o usuário já preparou arquivos per-episode, o fluxo é totalmente pulado
- Não aumenta o número de etapas do fluxo

**Lógica de disparo**:
```
Início da etapa 2 (produzir episódio N) →
  source/episode_{N}.txt existe?
    ├─ Sim → usar no pré-processamento
    └─ Não → disparar corte do episódio:
         _remaining.txt existe?
           ├─ Sim → peek _remaining.txt (continuar do restante anterior)
           └─ Não → peek arquivo original do romance (primeiro corte)
         → agent sugere ponto de quebra → usuário confirma
         → split --dry-run valida → split executa
         → gera episode_{N}.txt + atualiza _remaining.txt
         → continua o pré-processamento
```

**Característica sob demanda**: corta só o episódio que se vai produzir agora; não exige planejar todos de uma vez. O usuário pode fazer um episódio e voltar dias depois.

## Risks / Trade-offs

### [Risco] Cenário de redivisão

O usuário corta 3 episódios e depois acha ruim o ponto do episódio 1.

→ **Mitigação**: o original sempre fica. Pode apagar `episode_*.txt` e `_remaining.txt` e recomeçar. Ou refazer só um episódio (editando o arquivo manualmente).

### [Trade-off] Mais arquivos físicos

Um arquivo por episódio + `_remaining.txt` aumenta o número de arquivos em source/.

→ **Aceitar**: quantidade proporcional ao número de episódios, controlável. Nomes claros (`episode_N.txt`), sem confusão.
