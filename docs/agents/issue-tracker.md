# Issue tracker: GitHub

Issues e specs deste repo vivem como GitHub issues. Use a CLI `gh` para todas as operações.

## Convenções

- **Criar issue**: `gh issue create --title "..." --body "..."`. Use heredoc para bodies multi-linha.
- **Ler issue**: `gh issue view <number> --comments`, filtrando comments com `jq` e também buscando labels.
- **Listar issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` com filtros `--label` e `--state` apropriados.
- **Comentar em issue**: `gh issue comment <number> --body "..."`
- **Aplicar / remover labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Fechar**: `gh issue close <number> --comment "..."`

Infira o repo a partir de `git remote -v` — o `gh` faz isso automaticamente quando roda dentro de um clone.

## Spec e issues de implementação

Spec (antigo PRD) e issues de implementação derivados de uma Spec precisam ser distinguíveis e rastreáveis **na visão de lista**, não só no corpo:

### Issue de Spec

- O título começa unificadamente com `Spec: `, ex.: `Spec: integrar TTS text-to-speech —— …`
- Aplique a label `Spec`. Ao publicar com `to-spec`, adicione ao mesmo tempo as labels `Spec` e `ready-for-agent`

### Issue de implementação (subdivisão)

- No **final** do título, acrescente o sufixo de pertencimento `[Spec #<número-pai>]`, ex.: `livro-razão de episódios: extensão do schema de project.json e backfill de projetos existentes na subida [Spec #751]` — qualquer visão de lista (`gh issue list`, Web, notificações) enxerga o pertencimento de imediato
- No corpo, mantenha a seção `## Parent` referenciando a Spec pai (o template existente não muda; o sufixo é complemento, não substituto)
- Ao mesmo tempo, anexe como **sub-issue nativa do GitHub** da Spec pai, para a Spec pai mostrar a barra de progresso de conclusão:

```bash
# 1. Pegar o database id da issue de implementação (não o número da issue)
sub_id=$(gh api repos/{owner}/{repo}/issues/<número-da-subdivisão> --jq .id)
# 2. Anexar sob a Spec pai (-F passa inteiro)
gh api repos/{owner}/{repo}/issues/<número-pai>/sub_issues -F sub_issue_id=$sub_id
```

Quando `to-tickets` subdividir uma Spec, cada issue criada deve completar esses dois passos (o sufixo do título já entra no create).

## Quando uma skill disser "publish to the issue tracker"

Crie uma GitHub issue.

## Quando uma skill disser "fetch the relevant ticket"

Execute `gh issue view <number> --comments`.

## Operações de wayfinding

Usadas por `/wayfinder`. O **mapa** é uma única issue com issues **filhas** como tickets.

- **Mapa**: uma única issue com label `wayfinder:map`, contendo o body Notes / Decisions-so-far / Fog. `gh issue create --label wayfinder:map`.
- **Ticket filho**: issue ligada ao mapa como sub-issue do GitHub (`gh api` no endpoint de sub-issues). Onde sub-issues não estiverem habilitadas, adicione o filho a uma task list no body do mapa e coloque `Part of #<map>` no topo do body do filho. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Uma vez reivindicado, o ticket é atribuído ao dev condutor.
- **Bloqueio**: **dependências nativas de issue do GitHub** — a representação canônica e visível na UI. Adicione uma aresta com `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, onde `<blocker-db-id>` é o **database id** numérico do blocker (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _não_ o `#number` nem o `node_id`). O GitHub reporta `issue_dependencies_summary.blocked_by` (só blockers abertos — o gate ao vivo). Onde dependências não estiverem disponíveis, caia para uma linha `Blocked by: #<n>, #<n>` no topo do body do filho. Um ticket fica desbloqueado quando todo blocker está fechado.
- **Consulta de fronteira**: liste os filhos abertos do mapa (`gh issue list --state open`, com escopo nas sub-issues / task list do mapa), descarte os que tiverem blocker aberto (`issue_dependencies_summary.blocked_by > 0`, ou issue aberta na linha `Blocked by`) ou assignee; o primeiro na ordem do mapa vence.
- **Reivindicar**: `gh issue edit <n> --add-assignee @me` — a primeira escrita da sessão.
- **Resolver**: `gh issue comment <n> --body "<resposta>"`, depois `gh issue close <n>`, depois anexe um ponteiro de contexto (gist + link) em Decisions-so-far do mapa.
