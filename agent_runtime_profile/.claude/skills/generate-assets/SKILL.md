---
name: generate-assets
description: "Skill unificado de geração de ativos: aceita `--type=character|scene|prop`, ou sem tipo varre todos os pending (sem sheet) e despacha por tipo. Use quando o usuário disser \"gerar arte de personagem\" / \"gerar arte de cena\" / \"gerar arte de prop\", quiser criar referência visual de novo ativo, ou houver ativos sem *_sheet."
---

# Gerar artes de design de ativos

Cria artes de referência de personagem, cena e prop do projeto, garantindo consistência dos elementos visuais em todo o vídeo.
O provedor de imagem é escolhido nas settings do projeto (sem travar backend específico).

> Princípios de escrita de prompt em `.claude/references/generation-modes.md`, seção «Idioma do prompt».

## Convenções comuns

- Toda `description` de ativo usa **parágrafo narrativo**, não lista de palavras-chave.
- O usuário só mantém `description` em project.json; o prompt completo enviado ao backend de imagem
  (layout / frases anti-colapso / negative prompts) é montado no server por `lib/prompt_builders.py`.
  WebUI e Skill compartilham a mesma fonte de verdade.
- Critério de pending: campo `*_sheet` do ativo vazio ou arquivo inexistente.

---

## Personagem (character)

### Guia de escrita de description

Descreva em parágrafo contínuo aparência, traje e presença, incluindo idade, porte, traços faciais e detalhes de vestimenta.

**Exemplo**:

> "Mulher de pouco mais de vinte anos, porte esguio, rosto oval com olhos de amêndoa límpidos; as sobrancelhas em arco se franzem com um toque de melancolia. Veste saia de seda azul-clara bordada, faixa da mesma cor na cintura, elegância sem perder leveza."

### Layout de saída

Design sheet horizontal 16:9 em quatro painéis, fundo branco puro: close de busto à esquerda (~40% da largura), à direita três vistas de corpo inteiro em A-Pose (frente / três-quartos / costas).
Rosto, cabelo, traje e acessórios devem ser idênticos em todos os painéis.

> Ao preencher description o usuário só se preocupa com aparência / traje etc.; o layout é injetado pelo builder.

---

## Cena (scene)

### Guia de escrita de description

Descreva em parágrafo contínuo forma, luz e atmosfera, destacando traços únicos reconhecíveis entre cenas.

**Exemplo**:

> "A velha acácia de cem anos na entrada da aldeia; o tronco grosso precisa de três pessoas para abraçar, a casca rachada e envelhecida. No tronco principal, uma marca clara de raio carbonizada serpenteia do topo para baixo. A copa é densa e, no verão, espalha sombra manchada."

### Layout de saída

O quadro principal ocupa cerca de três quartos da área mostrando a aparência e a atmosfera do ambiente; no canto inferior direito, miniatura do detalhe-chave.

---

## Prop (prop)

### Guia de escrita de description

Descreva em parágrafo contínuo forma, textura e detalhes, destacando traços únicos reconhecíveis entre cenas.

**Exemplo**:

> "Pingente de jade ancestral verde-esmeralda, cerca do tamanho de um polegar, textura suave e translúcida. Na superfície, lótus esculpido em camadas de pétalas abertas. No pingente, cordão vermelho amarrado em nó tradicional."

### Layout de saída

Três vistas alinhadas horizontalmente sobre fundo cinza-claro limpo: vista frontal completa, vista lateral a 45°, close do detalhe-chave.

---

## Chamadas de ferramentas

Enfileirar via ferramenta MCP:

| Operação | Ferramenta |
|------|------|
| Listar todos / uma classe de pending | `mcp__arcreel__list_pending_assets({"type": "character"})` (type opcional) |
| Gerar todos os pending (uma rodada por classe) | `mcp__arcreel__generate_assets({})` |
| Gerar todos os pending de uma classe | `mcp__arcreel__generate_assets({"type": "character"})` |
| Gerar vários específicos | `mcp__arcreel__generate_assets({"type": "prop", "names": ["pingente de jade", "carta secreta"]})` |
| Gerar um | `mcp__arcreel__generate_assets({"type": "scene", "names": ["velha acácia da entrada"]})` |

Se retornar `is_error: true`, o texto traz o detalhe da falha — retente ou reporte aos desenvolvedores.

## Fluxo de trabalho

1. **Carregar metadados do projeto** — em project.json achar ativos sem o `*_sheet` correspondente
2. **Enfileirar tarefas de geração** — description enviada direto como prompt; no server `lib.prompt_builders` injeta layout / anti-colapso / negative
3. **Checkpoint de revisão** — mostrar cada arte; o usuário aprova ou pede regeneração
4. **Atualizar project.json** — atualizar caminhos de `character_sheet` / `scene_sheet` / `prop_sheet`

## Checagem de qualidade

- **Personagem**: nos quatro painéis (close + três vistas) rosto, cabelo, traje e acessórios totalmente consistentes
- **Cena**: composição geral e traços marcantes em destaque, luz/atmosfera adequadas, detalhe nítido
- **Prop**: três ângulos claros e consistentes, detalhes fiéis à descrição, texturas especiais visíveis
