# Pesquisa de proporção de duração do framework de 8 seções para short video de vendas

> Uso: base numérica das proporções de duração por faixa no prompt de geração de roteiro do modo anúncio/curta (content_mode=ad). A tabela de quatro faixas já foi aprovada pelo mantenedor (2026-06-11); este documento preserva a cadeia de fontes da pesquisa e as marcações de inferência, para calibração e extensão de faixas futuras. Método: leitura completa do repositório coreyhaines31/marketingskills (50 skills) + cruzamento com material público do setor.

## 1. Inventário do repositório marketingskills

Conteúdo relevante no repositório (https://github.com/coreyhaines31/marketingskills). **O repositório não tem tabela de proporção de duração de anúncio por faixas 15/30/60/90 s** — é um conjunto de skills orientado a marketing SaaS; o mais próximo são dois templates de estrutura de short video com intervalos em segundos no skill social. Há vários princípios estruturais transferíveis:

| Skill (caminho) | Experiência aplicável |
|---|---|
| **social** (capítulo Short-Form Video de `skills/social/SKILL.md`) | Mais diretamente relacionado. ① "Regra dos 3 segundos": gancho visual + gancho falado + gancho textual juntos; acertar no 1º segundo; ② duração ótima por plataforma: TikTok 15-60s / Reels 15-30s / Shorts 30-60s; ③ **Estrutura Problem-Solution (15-30s): hook 0-3s → amplificar dor 3-10s → solução 10-25s → CTA 25-30s** (esqueleto direto da faixa de 30 s); ④ erros comuns: gancho com setup lento demais, encurtar quando possível, sem CTA |
| **social/references/short-form-video.md** | ① Biblioteca de ganchos em quatro tipos (curiosidade/valor/história/polêmica), pode alimentar o prompt do trecho hook; ② template de roteiro fixo "Hook 0-3s + Body + **CTA final 3-5s**"; ③ Story Arc (45-60s): hook 0-3 / setup 3-15 / processo 15-45 / resultado 45-55 / CTA 55-60; ④ **Ritmo de takes: B-roll corte rápido 1-3s/plano, slideshow 2-4s/página** (alinha com a restrição de plano único 2-6s) |
| **ads** (`skills/ads/SKILL.md` + `references/ad-copy-templates.md`) | ① PAS (problema→amplificar→solução→CTA), BAB, Social Proof Lead, **fórmula Direct Response (promessa ousada→prova→CTA com urgência)** — esta última fundamenta a ordem trust→price_promo→cta; ② CTA em três níveis soft/hard/urgência, conforme o objetivo; ③ **Prioridade de teste: hook tem o maior impacto no resultado**, depois headline, benefício, CTA |
| **ad-creative** (`skills/ad-creative/SKILL.md`) | ① Antes de criar, definir 3-5 "ângulos" (dor/resultado/prova social/urgência/identidade…), mapeando 1:1 à taxonomia de 8 seções; ② consciência de especificação de plataforma: copy de anúncio TikTok ≤80 caracteres |
| **marketing-psychology** (`skills/marketing-psychology/SKILL.md`) | ① AIDA (atenção→interesse→desejo→ação) reforça a ordem das 8 seções; ② "construir confiança→autoridade+prova social" (direção de material do trecho trust), "criar urgência→escassez+aversão à perda" (redação do trecho price_promo); ③ técnicas de apresentação de preço (Rule of 100, conta mental "R$ 1 por dia") podem entrar no prompt de price_promo |
| **video** (`skills/video/SKILL.md`) | Mais voltado a cadeia de produção; sem input para proporções; mas as três regras "**85% dos vídeos sociais são vistos sem som**, 9:16, modelo de IA não renderiza texto legível" têm valor de restrição para geração de prompts de plano |
| **copywriting** (`references/copy-frameworks.md`) | Fórmulas de título ("{resultado} without {dor}" etc.) reutilizáveis como templates de falas do hook; ordem de seções de landing page (problema→solução→prova social→FAQ→CTA) reforça de novo a ordem dos trechos |

**Princípios transferíveis extraídos** (evidência do repositório → uso na tabela de proporções):

1. **hook e CTA são trechos de "duração absoluta"**: em todos os templates, seja 15s ou 60s de total, hook é sempre 0-3s e CTA sempre os últimos 3-5s — alongar o vídeo não amplia cabeça e cauda proporcionalmente.
2. **Todo o tempo extra vai para o meio** (solução/demo/prova); essa é a única zona elástica entre faixas.
3. **A ordem dor→solução→prova→ação não muda com a duração**; faixas curtas "cortam seções", não reordenam.
4. **Corte rápido de 1-4s por plano e um novo ponto de informação a cada poucos segundos** é o ritmo base do short video.

## 2. Conclusões-chave do material do setor (com fontes)

**Oficial da plataforma / dados oficiais**

| # | Conclusão | Fonte |
|---|---|---|
| 1 | TikTok oficial: entre os vídeos com maior CTR, **63% mostram a informação central ou o produto nos primeiros 3 segundos** | PDF oficial TikTok *9 Creative Tips to drive performance* https://ads.tiktok.com/business/library/Auction_Ads_Creative_Tips.pdf (citado em: https://lebesgue.io/tiktok-ads/how-to-increase-tiktok-ctr-9-creative-tips ) |
| 2 | TikTok oficial: **os primeiros 6 segundos capturam 90% do efeito de memória do anúncio**; recomenda estrutura em três atos hook–body–close | Blog TikTok For Business https://ads.tiktok.com/business/en/blog/creative-best-practices-top-performing-ads (o domínio foi bloqueado por validação de certificado na captura direta; números cruzados com https://www.stackmatix.com/blog/tiktok-hook-first-3-seconds e https://www.2pointagency.com/glossary/tiktok-creative-best-practices-the-3-second-rule/ ) |
| 3 | Dados TikTok: **vídeos com troca multi-cenário/multi-ângulo convertem 38% a mais**, impressões +40%+, **99% dos vídeos e-commerce virais usaram multi-cenário multi-ângulo**; 93% dos virais têm áudio | https://tinuiti.com/blog/paid-social/tiktok-best-practices/ (cita dados oficiais TikTok; original https://ads.tiktok.com/business/en-US/blog/creative-that-drives-conversions ) |
| 4 | Dados TikTok: **1/4 dos vídeos de melhor desempenho tem duração entre 21-34 segundos** (impressões +1,6%) | https://creatify.ai/blog/tiktok-ads-complete-guide-to-creating-high-performing-creatives-in-2026 (cita dados TikTok) |
| 5 | Meta: limite de anúncios Reels 90s; sweet spot 15-60s, **acima de 30s a atenção no FB Reels cai de forma clara**; para a maioria das campanhas o ideal é 6-15s; **produto/dor/resultado devem entrar em quadro nos primeiros 0,3-2 segundos** | https://www.jonloomer.com/meta-video-ad-length-requirements/ , https://thedesignsfirm.com/en/blog/facebook-video-ad-length , https://www.brandwatch.com/blog/facebook-video-ads-best-practices/ , especificação oficial https://www.facebook.com/business/help/817989058548892 |

**Douyin / vendas em chinês**

| # | Conclusão | Fonte |
|---|---|---|
| 6 | Proporção de quatro blocos em roteiro de vendas viral: **abertura 0-3 s pergunta de dor → em seguida 20% da duração reforçando a necessidade → meio 50% listando benefícios + demonstração do produto → últimos 10% "razão para comprar agora + benefício/preço" para fechar** | Qinggua Media *Desmontagem da estrutura de roteiro de short video de vendas viral* https://www.opp2.com/317828.html (captura direta verificada) |
| 7 | 3 segundos de ouro: **mais de 50% dos usuários decidem deslizar ou não nos primeiros 3 segundos**; três paradigmas de gancho (suspense/dor/benefício direto) | Chanmama *Metodologia de otimização dos 3 segundos de ouro do e-commerce Douyin* https://www.chanmama.com/yunyingquan/article/1428.html (captura direta verificada) |
| 8 | Retenção 3s ≥58% como linha saudável, conclusão completa ≥32% (viral 45%+); **um ponto de interesse a cada 5 segundos**; **iniciantes começam nos 30 s; 90 s exige controle de ritmo alto** | https://www.cnblogs.com/huizhudev/p/19148789 (post de experiência setorial, não oficial) |
| 9 | Vídeos de e-commerce de vendas costumam ter **cerca de 15 s, no máximo 30 s**; em 8-15 s é preciso ver destaque do produto/preço/promoção; **preço é o fator mais importante para a compra**, vantagem de preço no final para fechar | https://www.changbiyuan.com/douyin/duanshipin/2022/duanshipin_1003/54743.html |

**UGC / estrutura Direct Response**

| # | Conclusão | Fonte |
|---|---|---|
| 10 | Fórmula UGC de resposta direta **Hook → Problem → Solution → Value Prop → Social Proof → CTA**; hook no máximo 2-3 s; "15s comprime o meio, 30s equilibra, 60s expande a demo" | https://motionapp.com/blog/how-to-write-ugc-ad-scripts (captura verificada) |
| 11 | **Proporção de 5 trechos em UGC de 60 s: hook 0-3 / dor 3-10 / solução 10-25 / prova social 25-45 / CTA 45-60**; trocar de quadro a cada 5-8 s; escrever ≥5 hooks por roteiro e testar separados | https://www.retiplex.com/blog/ugc-ad-script-guide (captura verificada) |
| 12 | **Estrutura demo e-commerce 90 s: gancho de benefício 0-5 / demo guiada 6-75 (benefício com prova ao vivo, prova social entrelaçada no meio) / CTA de urgência 76-90**; **90 s narrativo: personagem e conflito 0-15 / processo 16-75 / revelação+CTA 76-90**; anúncio social 30 s: hook 0-3 / valor 4-25 / CTA 26-30; **15 s estilo nativo TikTok: abertura chamativa 0-1 / valor de alta densidade 2-12 / gap de curiosidade+CTA 13-15** | https://shortgenius.com/blog/ad-script-example (captura verificada) |
| 13 | Proporção de roteiro de vídeo explicativo **Problem 30% / Solution 40% / Proof 20% / Action 10%**; conversão de ritmo **150 palavras em inglês/minuto**: 30s=60-75 palavras, 60s=140-160 palavras, 90s=210-230 palavras | https://vidico.com/news/explainer-video-script-examples/ (captura verificada) |
| 14 | Narração UGC **30 s ≈ 75-120 palavras**; os primeiros 3-5 s definem o destino | https://billo.app/blog/ugc-scripts/ (captura verificada) |
| 15 | Experiência VSL: **o hook carrega cerca de 80% do peso do sucesso/fracasso**; "a maior perda ocorre nos primeiros 10-30 s"; o trecho de prova (resultados reais de clientes com números concretos) sustenta a conversão; tendência 2026: "micro-VSL" de 30-90 s | https://www.blog.theperformers.io/p/video-sales-letters-ads , https://adlibrary.com/guides/vsl-ads-ecommerce-guide |
| 16 | UGC de resposta direta recomenda 15-30 s; "o erro mais comum é setup longo demais" | https://www.rathlymarketing.com/faq/best-ugc-ad-structure/ (captura verificada) |

## 3. Tabela de proporções das quatro faixas (já aprovada)

**Regras gerais** (aplicam-se a todas as faixas; entram no prompt de geração de roteiro junto com a tabela):

- hook e cta são **trechos de duração absoluta** (hook 2-4s, cta 3-6s), sem ampliação proporcional por faixa; segundos extras priorizam selling_point/demo, depois trust (bases #10, #11, #12, princípios 1-2 do repositório).
- price_promo fica sempre colado ao cta formando o "bloco de fechamento" (bases #6, #9, fórmula Direct Response do skill ads).
- Mesmo que o hook não seja o quadro do produto, **o produto deve entrar em quadro nos primeiros 3 segundos** (texto/detalhe/mão ok) (bases #1, #5).
- Seção única acima de 6 s deve virar vários planos; média do filme 3-5 s/plano, abertura permite corte rápido 2-3 s (bases #11 trocar quadro a cada 5-8 s, #8 um ponto de interesse a cada 5 s, B-roll 1-3s do repositório).
- Preferir mais planos a menos: multi-cenário multi-ângulo tem melhoria de conversão com respaldo oficial (base #3).

### Faixa 1: 15 segundos (impulso/mídia paga, 5-6 planos)

| section | segundos | acumulado | planos | descrição |
|---|---|---|---|---|
| hook | 3 | 0-3 | 1 | Abertura com pergunta de dor ou resultado à frente; **hook assume também pain_point** |
| product_reveal | 2 | 3-5 | 1 | Produto em quadro + nome |
| selling_point | 3 | 5-8 | 1 | Só 1 benefício central |
| demo | 4 | 8-12 | 1-2 | 1 cenário de uso / comparação de efeito |
| cta | 3 | 12-15 | 1 | Comando de ação; **pode levar uma frase promocional e assumir price_promo** |

**Cortados**: pain_point (dobrado no hook — o problem do PAS já está em 0-3s, ver #6, #7), trust (15 s não cabem trecho de prova independente, ver estilo 15s de #12), price_promo (dobrado em uma frase no cta, ver #12 "gap de curiosidade+CTA 13-15").
**Base**: esqueleto alinhado ao estilo 15 s nativo TikTok de #12 (0-1 abertura / 2-12 valor de alta densidade / 13-15 CTA): no total, reveal+selling+demo de 3-12 s somam 9 s = "bloco de valor de alta densidade"; hook 3s e cta 3s vêm do template social skill do repositório e de #1. Nº de planos = 15s ÷ 2,5-3s de corte rápido.

### Faixa 2: 30 segundos (posição padrão de vendas, faixa recomendada padrão, 8-10 planos)

| section | segundos | acumulado | planos | descrição |
|---|---|---|---|---|
| hook | 3 | 0-3 | 1 | Três ganchos juntos (imagem+narração+texto na tela) |
| pain_point | 4 | 3-7 | 1-2 | Amplificar dor, cenário de empatia |
| product_reveal | 3 | 7-10 | 1 | Produto entra como "a resposta" |
| selling_point | 6 | 10-16 | 2 | 1-2 benefícios |
| demo | 6 | 16-22 | 2 | Uso nas mãos/rosto/teste real |
| trust | 3 | 22-25 | 1 | Prova social em uma frase (vendas/nota/antes-depois), pode ser texto sobreposto |
| price_promo | 2 | 25-27 | 1 | Card de preço / flash de desconto |
| cta | 3 | 27-30 | 1 | Comando de ação + urgência |

**Cortar/encolher**: as 8 seções se mantêm, mas trust e price_promo viram "plano de uma frase"; se ticket muito baixo e sem credibilidade, **cortar trust primeiro** e devolver segundos à demo.
**Base**: esqueleto alinhado rigorosamente ao template Problem-Solution 15-30s do social skill do repositório (hook 0-3 / dor 3-10 / solução 10-25 / CTA 25-30) — nesta tabela 3-10 = pain+reveal, 10-25 = selling+demo+trust, 25-30 = price+cta, fronteiras dos três blocos coincidem; também alinha ao estilo 30s de #12. Motivo para manter trust como batida independente: #16 e #15 (prova sustenta conversão). 21-34s é a faixa de duração ótima dos dados TikTok (#4); esta é a faixa recomendada padrão.

### Faixa 3: 60 segundos (cadeia completa de persuasão, 13-16 planos)

| section | segundos | acumulado | planos | descrição |
|---|---|---|---|---|
| hook | 3 | 0-3 | 1 | Como acima |
| pain_point | 7 | 3-10 | 2 | Dor em cena (1-2 situações concretas) |
| product_reveal | 5 | 10-15 | 1-2 | Entrada + o que é + para quem |
| selling_point | 12 | 15-27 | 3 | 2-3 benefícios, cada um 4-6s por plano |
| demo | 15 | 27-42 | 3-4 | Demo multi-ângulo / antes-depois / visualização de dados |
| trust | 8 | 42-50 | 2 | Print de avaliação + vendas/credenciais, dois planos |
| price_promo | 5 | 50-55 | 1-2 | Âncora de preço original → preço final → benefício por tempo limitado |
| cta | 5 | 55-60 | 1 | Comando de ação + reforço do benefício central |

**Trade-off**: as 8 seções se mantêm, cada uma em bloco; o incremento de 60 s vai quase todo para selling_point+demo (27s no total, 45%).
**Base**: pain 3-10, hook 0-3 e bloco final de CTA vêm direto de #11 (template retiplex 60s); a diferença em relação a #11 é diluir o bloco de 20 s de prova social (trust 8s) e transferir segundos à demo — motivos: #10 "60s expande a demo", #6 os 50% do meio são "benefícios um a um + demonstração do produto" (nesta tabela selling+demo=27s=45%≈50% da Qinggua). Checagem de proporção: dor 12%/bloco solução 53%/prova 13%/fechamento 17%, contra 30/40/20/10 de #13 — dor mais leve, fechamento mais pesado, porque o cenário-alvo é venda de resposta direta, não vídeo explicativo; a cauda de fechamento se aproxima de "últimos 10%+vantagem de preço" de #6 e da fórmula DR.

### Faixa 4: 90 segundos (narrativo/ticket alto, 18-22 planos)

| section | segundos | acumulado | planos | descrição |
|---|---|---|---|---|
| hook | 4 | 0-4 | 1 | Pode usar gancho de suspense/história ("3 meses atrás eu ainda…") |
| pain_point | 10 | 4-14 | 2-3 | Mini-narrativa de personagem + conflito |
| product_reveal | 6 | 14-20 | 1-2 | Ponto de virada: encontrar o produto |
| selling_point | 20 | 20-40 | 3-4 | 3 benefícios, cada um expandido |
| demo | 24 | 40-64 | 4-6 | Processo de uso multi-cenário (bloco central) |
| trust | 12 | 64-76 | 2-3 | Depoimento de usuário / laudo / vendas |
| price_promo | 8 | 76-84 | 2 | Âncora de preço + desmontagem de oferta por tempo limitado |
| cta | 6 | 84-90 | 1 | Fechamento com urgência |

**Trade-off**: as 8 seções se mantêm; em relação a 60s, o incremento vai para demo (+9), selling_point (+8), trust (+4), pain_point (+3).
**Base**: esqueleto alinhado aos dois templates de 90s de #12 — narrativo "personagem e conflito 0-15" (nesta tabela hook+pain=0-14), demo "demo guiada 6-75" (nesta tabela reveal+selling+demo=14-64 como corpo da demo, trust 64-76 em seguida), e o comum aos dois "CTA de urgência 76-90" (nesta tabela price_promo+cta=76-90 coincide por completo). **Alerta de risco**: #5 (>30s no FB Reels é difícil manter atenção; 90s é o teto dos Reels) e #8 (90 s exige ritmo alto) apontam que esta faixa só serve a produtos de ticket alto/que precisam de educação; o prompt deve exigir que a faixa 90s se organize como "mini-história", não lista plana de benefícios, e manter um novo ponto de informação a cada ~5 s.

**Anexo: referência de contagem de palavras da narração** (restringe comprimento das falas): inglês 15s≈40 palavras, 30s≈60-120 palavras (#13, #14), 60s≈140-160 palavras, 90s≈210-230 palavras (#13). Em chinês, com ~4 caracteres/segundo: 15s≈60 caracteres / 30s≈120 / 60s≈240 / 90s≈360 — **esta conversão é valor inferido, sem fonte direta; recomenda-se calibrar com velocidade real de TTS**.

## 4. Fontes e marcações de inferência

**Números com fonte direta**:

- hook sempre 0-3s (múltiplas fontes: #1/#6/#7/#11/#12/social skill do repositório); cta sempre últimos 3-6s (#11/#12/short-form-video.md do repositório).
- Fronteiras dos três grandes blocos da faixa 30s (0-3 / 3-25 / 25-30): template Problem-Solution do repositório e #12, duas fontes diretas.
- Faixa 60s pain 3-10 e início do bloco CTA final: segundos originais de #11.
- Faixa 90s bloco de conflito 0-15 e bloco de fechamento 76-90: segundos originais de #12.
- Plano único 2-6s / corte rápido 2-3s: B-roll 1-3s e slideshow 2-4s do repositório, #11 troca a cada 5-8s, #8 ponto de interesse a cada 5s.
- "Produto nos primeiros 3 s" (63% de #1), "90% de memória nos primeiros 6 s" (#2), "multi-cenário +38% conversão" (#3), "faixa ótima 21-34s" (#4), esqueleto de proporção 3s/20%/50%/10% (#6) e 30/40/20/10 (#13), conversão de palavras (#13/#14).

**Inferências baseadas em princípios estruturais (sem fonte única direta)**:

1. **Todos os valores de corte precisos ao segundo no nível de section** (ex.: trust=3s e price_promo=2s na faixa 30; reveal=5s na 60; selling=20s na 90 etc.): as fontes do setor só dão intervalos de 3-5 blocos grossos; esta tabela interpola as fronteiras dos blocos grossos na taxonomia de 8 seções — princípio de interpolação: "fronteiras dos blocos grossos não se movem; dentro do bloco divide-se pela contagem de benefícios/comprimento de plano". A soma exata de cada faixa igual à duração da faixa é normalização para o prompt ser executável.
2. **Decisão de cortar três seções na faixa 15 s**: templates de 15s do setor têm só 3-4 seções, nunca 8; cortar pain_point/trust/price_promo e não outras seções se baseia em: no PAS o problem já ocupa 0-3s (hook pode assumir), promo pode virar uma frase dentro do CTA (o final do estilo 15s de #12 já é "gap de curiosidade+CTA" junto), e produto/benefício/demo são a unidade mínima de persuasão inegociável do vídeo de vendas (#9: em 8-15 s é preciso ver destaque do produto).
3. **Intervalos de número de planos**: calculados por "duração da faixa ÷ 2-6s por plano" e puxados para o meio-alto (multi-cenário tem respaldo oficial #3); nenhuma fonte dá o número direto.
4. **Faixas 60/90 comprimem o bloco de 20 s de prova social estilo retiplex para 8-12s**: meio-termo entre a escola #11 (prova social pesada) e #6/#10 (demo pesada), inclinando-se à última porque o cenário-alvo é peça de vendas image-to-video, em que a gerabilidade de quadro de demo é maior; julgamento orientado a produto, já aprovado pelo mantenedor junto com a tabela de proporções.
5. **Caracteres chineses por segundo**: inferido por analogia com 150 palavras em inglês/minuto; não se encontrou fonte autoritativa de ritmo de fala em chinês.

**Não encontrado / não verificado**: o repositório marketingskills não tem nenhum conteúdo de proporção de duração por faixa (inventário honesto); dois URLs do blog oficial TikTok não puderam ser capturados direto por problema de certificado; os números relacionados foram cruzados com ≥2 citações de terceiros; "retenção 3s ≥58%" vem de post de experiência setorial (#8), não de comunicação oficial Douyin — ao citar, rebaixar a valor de referência.
