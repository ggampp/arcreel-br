---
status: accepted
---

# Planejamento de episódios: modelo de texto no servidor, em lotes rolantes dentro da ferramenta; o ledger drama é o outline de episódios

O fluxo antigo tinha o agent principal executando em vários passos scripts mecânicos (peek na unidade de leitura → converter para unidade de caracteres → escolher âncora → dry-run → split): o ponto de corte sem semântica de enredo não retinha hooks; o contrato multi-passo dependia do agent seguir o fluxo; e o rolamento episódio a episódio fazia o plano não ver o conteúdo do próximo. Decidimos entregar o julgamento do ponto de split ao LLM e o fluxo à ferramenta determinística: novas ferramentas MCP server-side plan/replan, por dentro leem janela do original (dezenas de milhares de caracteres), chamam o modelo de texto configurado no projeto e planejam de uma vez todos os episódios com arco de enredo completo na janela (título/hook/range); o cursor só avança até o último ponto de corte de alta confiança, a cauda fica para o próximo lote; schema Pydantic força a forma; existência da âncora e continuidade do range são validadas mecanicamente; falha re-tenta automaticamente na camada da ferramenta, e o retry carrega o motivo da falha de validação da rodada anterior (erro de schema / âncora inexistente / range descontínuo) para correção dirigida, não reenvio idêntico. O agent principal só chama a ferramenta uma vez e recebe o resumo — não carrega o processo de split. Em modo drama a entrada do ledger engrossa em outline de episódio (nós de história, hooks, teaser do próximo + range soft de material); a entrada da geração de roteiro inclui o outline deste e do próximo episódio; o ledger narration permanece fino (ponto de corte exato + hook). Revisão é no nível do lote: após o plano, o resumo do ledger é exibido para o usuário confirmar; qualquer conjunto de opiniões do usuário passa por `replan(from_episode, instructions)` e replan local de uma vez; from_episode é o episódio mais cedo afetado nas opiniões; o alcance do replan (from_episode até o fim já planejado), quando cruza vários arquivos-fonte, se parte em trechos independentes por arquivo — um episódio não cruza arquivo; a fronteira de arquivo é a fronteira de episódio; a numeração de episódios é contínua entre trechos; o alcance como um todo fecha e o cursor não se move.

## Considered Options

- SubAgent de planejamento (Claude lê a janela e produz o ledger): capacidade multi-rodada de iteração não se usa aqui (qualidade do hook depende do prompt e da visão global); seguir o fluxo depende do prompt, difícil de unit-testar; tokens vão na credencial do agent.
- Planejar o livro inteiro de uma vez: custo de milhões de caracteres adiantado; o usuário muitas vezes só faz os primeiros episódios de teste e, se muda o estilo no meio, o ledger se invalida em massa.
- Split episódio a episódio (status quo melhorado): falta visão de ritmo cross-episódio; o teto de qualidade do hook é baixo; a continuação ainda depende de estado rolante.
- Drama: um passo direto para o roteiro: conflita com planejamento em lote (dezenas de episódios em um lote não se escrevem de uma vez); qualquer ajuste de ponto de corte reescreve o roteiro inteiro do episódio.

## Consequences

- `peek_split_point.py` / `split_episode.py` / `_text_utils.py` removidos; o capítulo de split de manage-project SKILL.md e as instruções de fase 2 de CLAUDE.*.md reescritos como uma única chamada de ferramenta.
- Garantia de qualidade v1 = visão de janela global + campo hook explícito + revisão no nível do lote; sem anel de verificação LLM judge.
- A qualidade do plano depende da capacidade do modelo de texto configurado no projeto; schema e validação mecânica só cobrem correção de forma.
- Contagem de caracteres da janela e teto de episódios por lote são defaults internos da ferramenta, sobrescrevíveis em project settings.
- Hook e teaser do próximo episódio do ledger entram na entrada da geração de roteiro e caem no JSON do roteiro como campos de metadados no nível do episódio (o desenho do hook aterrissa na última cena do produto); upgrades mais pesados de estrutura de roteiro (cenas/enquadramentos/voz off etc.) são item independente, fora desta decisão.
