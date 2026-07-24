---
status: accepted
---

# style do projeto guarda snapshot expandido do prompt do template; mútuo exclusivo com imagem de referência de estilo

Só guardar `style_template_id` e expandir na tabela na geração faria upgrades do template propagarem sozinhos, mas projetos já filmados mudariam de estilo após alteração no registry e quebrariam a consistência do material existente. Decidimos, ao escolher o template de estilo, expandir o prompt inteiro de visual e gravar no campo `style` de project.json (mantendo `style_template_id` como marca de origem — PATCH com id de template novo reexpande e grava; migração na leitura só resolve de uma vez labels curtos legacy sem id, sem reexpandir por id já gravado); alterações posteriores no registry não reescrevem projetos antigos de forma proativa; e o estilo do projeto fica como estado final mútuo exclusivo triplo «template / imagem custom de referência de estilo / nenhum», garantido no caminho de escrita para que os dois não valham ao mesmo tempo, e o lado de composição de prompt consuma só a única origem já expandida.

## Consequences

- Otimizações de template não se propagam de forma proativa a projetos já criados; a semântica de `style` muda de label curto para texto longo (transparente para o LLM, mas breaking).
- A restrição mútua percorre vários caminhos de escrita (create / PATCH / migração): ao gravar template, limpa `style_image`; ao gravar imagem de referência de estilo, limpa `style_template_id`; ao limpar template explicitamente (id = null), limpa também o `style` já expandido, sem deixar texto órfão; em race de dados históricos, style_image tem prioridade e o template_id é limpo de forma proativa.
