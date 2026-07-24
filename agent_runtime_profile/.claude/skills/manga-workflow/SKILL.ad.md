---
name: manga-workflow
description: Entrada de fluxo de trabalho de projetos anúncio/curta. Use este skill sempre que o usuário falar em fazer vídeo, continuar o projeto ou ver progresso. Gatilhos incluem, sem se limitar a: "me ajuda a fazer um vídeo de venda", "continuar", "próximo passo", "ver o progresso do projeto" etc. Mesmo se o usuário só disser "continuar" ou "próximo passo", se o contexto atual for de projeto de vídeo, dispare. Não use para geração isolada de ativo (ex.: só redesenhar uma storyboard ou só regenerar a arte de um personagem — isso tem skill próprio).
---
<!-- mode: ad -->

# Fluxo de trabalho anúncio/curta

Este projeto é **modo anúncio/curta** (`ad`): vídeo único, sempre um episódio (o script é `scripts/episode_1.json`), shots planejados por `target_duration`. **Não há conceito de divisão em episódios** — não faça planejamento de episódios, divisão nem processamento de arquivo-fonte de romance.

## Passos do fluxo

1. **Confirmar estado do projeto**: Read `project.json`, confirme `title`, `content_mode` (fixo `ad`), `target_duration` (duração total alvo, segundos), `brief` (briefing criativo, pode ser vazio), `generation_mode` (`storyboard` / `reference_video`; `grid` não disponível), `products` (ativos de produto)
2. **Entrada criativa**: em projeto de venda, se o produto não estiver cadastrado ou faltar original (`reference_images` vazio), oriente o usuário a enviar a imagem do produto na página de inicialização do WebUI ou na página de ativos de produto — a original é o âncora de fidelidade do produto; o agent **não** pode enviar imagem no lugar do usuário; descrição/marca do produto podem ser escritas via `mcp__arcreel__patch_project`. Se `brief` estiver vazio, oriente o usuário a completar o briefing criativo (produto/tema, público-alvo, estilo desejado — selling points ficam para o próximo passo, não peça de novo aqui) e grave também via `patch_project`
3. **Redigir selling points**: se o produto estiver cadastrado mas `selling_points` vazio, redija a lista de selling points a partir de `brief`, descrição do produto e originais (`reference_images`); confirme com o usuário e grave na tabela products via `mcp__arcreel__patch_project` — a geração do script injeta selling points nas seções selling_point/demo do framework de venda
4. **Definição de ativos e artes**: após gravar definições de personagem/cena/prop em `project.json`, dispatch do subagent `generate-assets` para as artes; product sheet é gerado na página de ativos de produto
5. **Gerar script de uma vez**: chame `mcp__arcreel__generate_episode_script({"episode": 1})`. ad não precisa de intermediário step1; o prompt vem direto de brief + info de produto + tabela de proporção do framework de oito seções de venda aprovado (dimensionada por `target_duration`); com `products` vazio desvia automaticamente para script de curta genérico. Após gerar, desvio grande da duração total em relação a `target_duration` só gera log de aviso, não bloqueia
6. **Revisão do sheet (gate soft)**: se o produto tiver `product_sheet`, antes de iniciar storyboard (no caminho saída direta por referência: antes da primeira geração de vídeo — o sheet entra direto no conjunto de referência da unit) peça ao usuário confirmar na página de ativos de produto que o sheet bate com o produto real (se não, regenerar o sheet); só continue após confirmação; sem sheet (só original), inicie direto. Isso é convenção de fluxo, sem força de máquina de estados do sistema
7. **Orquestração e geração de shots**: copy de locução / duração / section de cada shot podem ser ajustadas via `patch_episode_script`; **ordem** dos shots só é reordenável na página de script do WebUI (não há ferramenta de reordenação no lado do agent — se o usuário pedir trocar ordem, oriente à página de script; não simule reordenação trocando conteúdo campo a campo). Dois caminhos de geração:
   - **Caminho storyboard**: use `generate-storyboard` / `generate-video` shot a shot para imagem e vídeo; após o storyboard, oriente revisão da imagem do produto e regenere o que falhar — interceptar **antes** de gastar com vídeo
   - **Caminho reference_video (saída direta por referência)**: chame direto `mcp__arcreel__generate_video_episode` para saída de uma vez — a ferramenta agrupa automaticamente shots consecutivos em video_units (cada unit ≤4 shots, duração total limitada pelo teto do provedor), injeta referência de produto e sheets de ativos em cada unit e enfileira a geração, pulando o passo de storyboard. Após editar shots, chamar de novo rederiva automaticamente; units inalterados não regeneram

   Shots de produto (`products_in_shot` não vazio) recebem automaticamente referência de produto e instrução de alta fidelidade no storyboard e no vídeo; o prompt não precisa repetir a aparência do produto

8. **Export de rascunho CapCut/Jianying**: com o vídeo completo, oriente o usuário a exportar o rascunho CapCut/Jianying no Web (trilha de vídeo + trilha de legendas da copy de locução, legendas na safe-zone vertical); abrir no CapCut/Jianying já dá a timeline completa — duble pela copy de locução e feche o filme. Compose in-app (compose-video) **não** se aplica a ad — saia direto pelo rascunho

## Curta genérico (sem produto)

`products` vazio = curta genérico; a geração de script desvia automaticamente para o prompt genérico. Venda vs genérico depende da **intenção do usuário**: se quer promover um produto ainda não cadastrado, siga a orientação de upload do passo 2 (completar o produto **antes** do script); só se a intenção não envolve produto concreto siga como curta genérico. Diferenças de orientação: pule os passos ligados a produto — upload do passo 2, redação de selling points do passo 3, revisão de sheet do passo 6; não peça informações de produto ao usuário; `brief` é a única entrada criativa — oriente o usuário a enriquecer (tema, tom emocional, estilo visual, ritmo narrativo) antes de gerar o script; ativos de personagem/cena/prop continuam disponíveis.

## Troca de caminho no meio

Se o usuário trocar `generation_mode` entre storyboard ↔ reference_video, primeiro verifique se a duração dos shots existentes respeita as restrições do novo caminho (storyboard exige membros de `supported_durations` do modelo de vídeo — consulte via `mcp__arcreel__get_video_capabilities`; reference exige inteiro 1–15 s). Se não respeitar, **liste proativamente** os shots fora da faixa, sugira valores de ajuste, corrija com `patch_episode_script` e só então gere — não enfileire direto e deixe a camada de execução falhar.

## Fronteiras

- Esqueleto do script é único: `shots[]` não muda com `generation_mode`; no caminho reference_video a duração por shot é inteiro livre 1–15 s; no caminho storyboard toma membros de `supported_durations` do modelo de vídeo
- O índice de agrupamento do caminho reference_video (campo `reference_units` do script) é mantido pelas ferramentas; não edite à mão; shots são a única fonte de verdade de conteúdo
