---
status: accepted
---

# Episódios: ledger em project.json como única fonte de verdade; arquivos físicos de episódio viram derivados sob o mesmo lock

O fluxo antigo de split tinha o arquivo físico como verdade (`episode_N.txt` existe = já splitado; `_remaining.txt` sobrescrito em rolagem como ponteiro de progresso), sem nenhum registro explícito de «o episódio N corresponde a qual trecho do original» — o downstream que escolhesse o arquivo errado não tinha como reconciliar; episódios seguintes inferiam o número via Glob e erravam fácil; `_remaining.txt` corrompido era irrecuperável. Decidimos unificar a fonte de verdade de episódios em `episodes[]` de project.json: a entrada ganha o alcance do material original (source_range — em narration ponto de corte exato, em drama alcance soft de material), hook, outline de episódio drama e campos de estado de consumo; no topo, planning_cursor marca o início do próximo lote de planejamento. O físico `episode_N.txt` vira derivado, reescrito junto com o ledger sob o mesmo lock de projeto pelas ferramentas de plan/replan, limpando resíduos fora do ledger — janela de inconsistência zero; `_remaining.txt` abolido. Projetos legados backfill mecânico na migração de startup do ADR 0022 — conteúdo do arquivo derivado casa substring exata de volta no original para inferir source_range; miss marca unanchored e trava (o arquivo físico é o registro final daquele episódio e não participa de replan).

## Considered Options

- Manter arquivo físico como fonte de verdade, só embrulhando ferramenta única mais confiável: base de reconciliação continua ausente; acidentes do tipo «episódios diferentes geraram o mesmo conteúdo» não se detectam.
- Ledger independente em arquivo ou tabela DB: o conceito de episódio se parte em dois lugares a reconciliar; DB conflita com a camada «dados de nível de projeto sempre no filesystem»; export/migração/backup todos complicam.
- Não derivar arquivo físico; downstream lê o original por range: os três subagents de preprocess e a exibição Web teriam de mudar todos — raio de explosão grande demais.
- Derivar sob demanda no consumo: nunca stale, mas «o agent lembra de chamar a ferramenta de derivar primeiro» devolve a confiabilidade ao cumprimento de fluxo.

## Consequences

- Continuação de session nova = ler o ledger; acaba inferência de número de episódio por Glob e ponteiro de progresso `_remaining.txt`.
- Replanear episódios já consumidos (já geraram step1/roteiro/mídia) exige confirmação explícita; produtos downstream invalidam junto com o ledger. Invalidação é marca (stale), não delete: a detecção de estado puxa o episódio de volta a «aguardando preprocess»; o refazer substitui pelos mecanismos existentes de overwrite/versão; versões antigas podem reverter — produtos de mídia caros não se perdem no replan.
- Editar ou renomear `episode_N.txt` à mão deixa de ser suportado — mudança passa por rederivar a partir do ledger.
- A comparação de backfill permite preprocess sem perda (normalizar newlines, Unicode NFC), mas sem match fuzzy: diferença semântica entre arquivo derivado e original só pode vir de edição humana; âncora aproximada distorceria o ledger. unanchored é degradação honesta, não falha — o arquivo físico ainda é o registro final daquele episódio, o consumo downstream não é afetado; só não participa de replan.
