# Limites criativos impostos pelo produto

O ArcReel **não** impõe, na camada de produto, limites rígidos sobre as **dimensões criativas** do roteiro — por exemplo, forçar um teto no número de pessoas permitidas em um único storyboard/grid.

## Por que isso está fora de escopo

Exemplo de pedido (#947): após praticar com 800+ imagens, o usuário observou que, quando um storyboard referencia >3 imagens de referência (personagem1 + personagem2 + cena), a taxa de «sorte» (inconsistência) de grid/storyboard sobe de forma notável, e por isso pediu que o produto, na fase de normalização do roteiro, **forçasse** o número de pessoas por storyboard em ≤2.

Não aplicamos restrições forçadas de produto às dimensões criativas do roteiro, pelos motivos:

- **A escolha criativa pertence ao usuário**: quantas pessoas cabem em um storyboard e como o enquadramento é montado são decisões narrativas e criativas. Um corte rígido de produto sacrifica cenas multi-personagem legítimas (grupo, confronto, reunião) e transforma um problema de engenharia de estabilidade de geração em restrição à criação.
- **Problemas de estabilidade se resolvem no lado da geração, não restringindo a entrada**: taxa alta de inconsistência é problema de engenharia da geração de imagem/grid (quando há demasiadas refs, a consistência cai). A resposta correta é melhorar estratégias de geração e retry, ou dar meios de fallback ao usuário (ex.: histórico de versões/upload de grid, ver #975) — não proibir no upstream a expressão da intenção criativa.
- **Preferências personalizadas passam por controle semântico, não por força global**: o usuário pode de fato querer «menos pessoas por storyboard», mas isso é *preferência personalizada* — deve dizer isso em linguagem natural ao agente, que segue de forma soft (sobrescrevível quando o conteúdo exige), e não um corte único para todos os projetos. `default_duration` (preferência do usuário persistida + soft follow dos subagents de pré-processamento, sobrescrevível pela necessidade do conteúdo) já é o precedente desse padrão.

Portanto, «o produto forçar o número de pessoas por storyboard» fica fora de escopo. A alternativa viável é **preferência semântica personalizada na geração de episódios pelo agente** (injeção em linguagem natural + soft follow), acompanhada em #976.

## Pedidos anteriores

- #947 — «sugerir manter ≤2 pessoas por storyboard para reduzir a taxa de inconsistência de grid/storyboard»
