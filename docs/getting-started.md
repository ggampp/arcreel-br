# Tutorial completo de introdução

Este tutorial guia você do zero, usando o ArcReel para converter um romance em short video.

## O que você vai aprender

1. **Preparação do ambiente** — obter chaves de API
2. **Deploy do serviço** — subir com Docker
3. **Fluxo completo** — cada passo do romance ao vídeo
4. **Técnicas avançadas** — regenerar, controlar custos, desenvolvimento local

## Tempo estimado

- Preparação do ambiente: 10–20 minutos (só na primeira vez)
- Gerar um vídeo de 1 minuto: cerca de 30 minutos

## Estimativa de custo

O ArcReel suporta vários fornecedores (Gemini, Volcengine Ark, Grok, OpenAI, Vidu, Alibaba DashScope, MiniMax, Kling e customizados). Exemplo com Gemini:

| Tipo | Modelo | Preço unitário | Nota |
|------|------|------|------|
| Geração de imagem | Nano Banana Pro | $0.134/img (1K/2K) | Alta qualidade, ideal para design de personagens |
| Geração de imagem | Nano Banana 2 | $0.067/img (1K) | Mais rápido e barato, ideal para storyboards |
| Geração de vídeo | Veo 3.1 | $0.40/s (1080p com áudio) | Alta qualidade |
| Geração de vídeo | Veo 3.1 Fast | $0.15/s (1080p com áudio) | Mais rápido e barato |
| Geração de vídeo | Veo 3.1 Lite | mais baixo | Modelo leve, só AI Studio |

> 💡 **Exemplo** (Gemini): um short com 10 cenas (8 s cada)
> - Imagens: 3 designs de personagem (Pro) + 10 storyboards (Flash) = $0.40 + $0.67 = $1.07
> - Vídeo: 80 s × $0.15 (modo Fast) = $12
> - **Total ~$13**

> Para outros fornecedores, veja as páginas oficiais de preço; o ArcReel oferece rastreio de custo em tempo real na página de settings.

---

## Capítulo 1: preparação do ambiente

### 1.1 Obter API keys de fornecedores de imagem/vídeo

O ArcReel suporta vários fornecedores; **configure pelo menos um** para começar:

| Fornecedor | Onde obter | Nota |
|--------|---------|------|
| **Gemini** (Google) | [AI Studio](https://aistudio.google.com/apikey) | Camada paga; billing por token/tabela (USD) |
| **Volcengine Ark** | [Console Volcengine](https://console.volcengine.com/ark) | Billing por token/imagem (CNY) |
| **Grok** (xAI) | [xAI Console](https://console.x.ai/) | Billing por imagem/segundo (USD) |
| **OpenAI** | [OpenAI Platform](https://platform.openai.com/) | Imagem por token, vídeo por segundo (USD) |
| **Vidu** | [Plataforma Vidu](https://platform.vidu.com/) | Billing por créditos convertidos (CNY) |
| **Alibaba DashScope** | [Console Bailian](https://bailian.console.aliyun.com) | Multimodal: texto / imagem / vídeo / TTS (CNY) |
| **MiniMax** | [Plataforma aberta MiniMax](https://platform.minimaxi.com/console) | Site CN; exterior pode usar site internacional (CNY) |
| **Kling** (Kuaishou) | [Plataforma aberta Kling](https://klingai.com/dev) | API Key ou par de chaves (Access Key + Secret Key) (CNY) |

Após o deploy, você também pode adicionar **fornecedores customizados** na página de settings (qualquer API compatível com OpenAI / Google).

> ⚠️ API keys são sensíveis — guarde com cuidado; não compartilhe nem envie para repositórios públicos.

### 1.2 Obter API key Anthropic

O ArcReel inclui um assistente de IA baseado no Claude Agent SDK, responsável por criação de roteiro, diálogo inteligente e outras etapas críticas.

**Opção A: API oficial Anthropic**

1. Acesse o [Anthropic Console](https://console.anthropic.com/)
2. Crie uma conta e uma API key
3. Configure depois na página de settings da Web UI

**Opção B: API de terceiros compatível com Anthropic**

Se não puder acessar a API Anthropic diretamente, configure na página de settings:

- **Base URL** — endereço do serviço proxy ou API compatível
- **Model** — nome do modelo a usar (ex.: `claude-sonnet-4-6`)
- Também é possível configurar modelos default de Haiku / Sonnet / Opus e o modelo de Subagent

### 1.3 Preparar o servidor

**Requisitos do servidor:**

- SO: recomenda-se Linux / macOS / WSL2 / Docker; Windows nativo roda fluxos básicos, mas sandbox Bash e outros isolamentos POSIX-only rebaixam automaticamente; em produção, WSL2 ou Docker Desktop
- Memória: 2 GB+ recomendado
- Docker e Docker Compose instalados

**Instalar Docker (se ainda não tiver):**

```bash
# Ubuntu / Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Relogue e verifique
docker --version
docker compose version
```

---

## Capítulo 2: deploy do serviço

### 2.1 Baixar e subir

#### Opção A: deploy padrão (SQLite, recomendado para começar)

```bash
# 1. Clonar o projeto
git clone https://github.com/ArcReel/ArcReel.git
cd ArcReel/deploy

# 2. Criar o arquivo de variáveis de ambiente
cp .env.example .env

# 3. Subir o serviço
docker compose up -d
```

#### Opção B: deploy de produção (PostgreSQL, recomendado para uso formal)

```bash
cd ArcReel/deploy/production

# Criar o arquivo de variáveis de ambiente (defina POSTGRES_PASSWORD)
cp .env.example .env

docker compose up -d
```

Quando o container estiver pronto, abra no browser **http://IP-do-seu-servidor:1241**

### 2.2 Configuração inicial

1. Login com a conta padrão (usuário `admin`; a senha vem de `AUTH_PASSWORD` em `.env`; se não estiver definida, é gerada no primeiro start e gravada de volta em `.env`)
2. Entre na **página de settings** (`/app/settings`)
3. Configure as **credenciais do assistente de IA** (impulsionam o assistente), com suporte a Anthropic oficial e vários fornecedores compatíveis; Base URL e modelo customizáveis
4. Configure a **API Key / credenciais** de pelo menos um fornecedor de imagem/vídeo (Gemini / Volcengine Ark / Grok / OpenAI / Vidu / Alibaba DashScope / MiniMax / Kling), ou adicione um fornecedor customizado
5. Ajuste escolha de modelo, limites de taxa etc. conforme necessário

> 💡 Todos os itens de configuração podem ser alterados na página de settings, sem editar arquivos de config à mão.

---

## Capítulo 3: fluxo completo

Os passos abaixo são feitos na estação de trabalho da Web UI.

### 3.1 Criar projeto

1. Na lista de projetos, clique em «Novo projeto»
2. Informe o nome do projeto (ex.: «Meu romance»)
3. Faça upload do arquivo de texto do romance (.txt)

> 💡 Além do romance original, você também pode importar um **roteiro finalizado** (screenplay); o sistema preserva falas e voice-over literalmente e cria personagens pela tabela de elenco do autor. Para shorts de venda, escolha o tipo **anúncio/curta** ao criar o projeto e gere o script de takes de venda pela duração total alvo.

### 3.2 Gerar o roteiro de storyboard

Abra o painel do assistente de IA à direita da estação de trabalho do projeto e, por diálogo, peça a geração do roteiro:

- A IA analisa o romance e o divide em segmentos adequados a vídeo
- Cada segmento inclui descrição visual, personagens em cena e props/cenas importantes (pistas)

**Ponto de revisão**: confira se a estrutura do roteiro é razoável e se personagens e pistas foram identificados corretamente.

### 3.3 Gerar designs de personagens

A IA gera um design para cada personagem, usado para manter a aparência consistente em todas as cenas posteriores.

**Ponto de revisão**: confira se a imagem do personagem bate com a descrição do romance; se não gostar, regenere.

### 3.4 Gerar designs de pistas

A IA gera imagens de referência para props e elementos de cena importantes (ex.: objeto-símbolo, local específico).

**Ponto de revisão**: confira se o design da pista está como esperado.

### 3.5 Gerar imagens de storyboard

A IA gera a imagem estática de cada cena a partir do roteiro, referenciando automaticamente os designs de personagens e pistas para consistência.

**Ponto de revisão**: confira composição da cena, consistência de personagens e atmosfera.

### 3.6 Gerar clipes de vídeo

As imagens de storyboard servem de frame inicial; o fornecedor de vídeo escolhido (Veo 3.1 / Seedance / Grok / Sora 2 / Vidu Q3 / Alibaba DashScope / MiniMax / Kling etc.) gera o clipe dinâmico. A duração disponível depende do fornecedor; alguns só suportam faixas fixas (ex.: MiniMax 6 / 10 s).

As tarefas entram na fila assíncrona; você acompanha o progresso em tempo real no painel de monitoramento. Os canais Image / Video / Audio concorrem de forma independente; o rate limit RPM evita estourar a cota da API.

**Ponto de revisão**: pré-visualize cada clipe; se não gostar, regenere individualmente.

### 3.7 Gerar narração por voz (opcional)

Nos modos narração / anúncio, é possível gerar narração por segmento: configure o fornecedor TTS na página de settings (Alibaba DashScope Qwen3 TTS ou qualquer TTS compatível com OpenAI), timbre e velocidade; ouça por segmento, complete o episódio em um clique, ou peça ao assistente de IA em uma frase. A narração segue na exportação CapCut/Jianying como trilha de narração por segmento.

### 3.8 Compor o vídeo final

Todos os clipes são concatenados com FFmpeg, com transições e música de fundo, gerando o vídeo final.

A saída padrão é **9:16 vertical**, adequada a plataformas de short video.

---

## Capítulo 4: técnicas avançadas

### 4.1 Histórico de versões e rollback

A cada regeneração de mídia, o sistema salva uma versão histórica. Na visão de timeline da estação de trabalho, você navega as versões e faz rollback em um clique.

### 4.2 Controlar custos

**Ver estatísticas de custo:**

Na página de settings, confira contagem de chamadas de API e detalhamento de custo.

**Dicas para gastar menos:**

- Revise com cuidado a saída de cada estágio, reduzindo retrabalho
- Gere primeiro poucas cenas para testar o efeito; se estiver bom, gere em lote
- No vídeo, o modo Fast economiza cerca de 60% do custo
- Storyboards com modelo Flash; designs de personagem com modelo Pro

### 4.3 Importação/exportação de projeto

O projeto pode ser empacotado em arquivo, para backup e migração:

- **Exportar**: empacota o projeto inteiro (com toda a mídia) em um arquivo de archive
- **Importar**: restaura o projeto a partir do archive

---

## Capítulo 5: perguntas frequentes

### P: Docker não sobe?

1. Confirme que o serviço Docker está rodando: `systemctl status docker`
2. Verifique se a porta 1241 está ocupada: `ss -tlnp | grep 1241`
3. Veja os logs do container: `docker compose logs` (no diretório `deploy/` ou `deploy/production/` correspondente)

### P: Chamada de API falhou?

1. Confirme que a API Key do fornecedor correspondente está correta na página de settings
2. Confirme que o modelo escolhido tem a capacidade necessária na conta daquele fornecedor (geração de imagem/vídeo às vezes exige camada paga ou solicitação à parte)
3. Verifique se a rede do servidor alcança a API do fornecedor
4. No console do fornecedor, confira se o uso da API estourou o limite

### P: O personagem aparece diferente em cenas diferentes?

1. Garanta que o design do personagem foi gerado primeiro
2. Confira a qualidade do design; se não estiver boa, regenere antes
3. O sistema usa automaticamente o design do personagem como referência para manter as cenas posteriores consistentes

### P: A geração de vídeo está lenta?

A geração de vídeo costuma levar 1–3 minutos por clipe — é normal. Fatores:

- Duração do vídeo (4 s vs 8 s)
- Carga do servidor da API
- Condições de rede

A fila de tarefas suporta processamento concorrente; vários clipes podem gerar ao mesmo tempo.

### P: A geração foi interrompida — e agora?

A fila de tarefas suporta retomada. Ao re-disparar a geração, o sistema pula automaticamente os clipes já concluídos e processa só o restante.

---

## Próximos passos

Parabéns por concluir o tutorial de introdução! Em seguida você pode:

- 💰 Ver [custos Google GenAI](google-genai-docs/Google视频&图片生成费用参考.md) e [custos Volcengine Ark](ark-docs/火山方舟费用参考.md) para preços detalhados
- 🐛 Problemas? Abra um [Issue](https://github.com/ArcReel/ArcReel/issues)
- 💬 Escaneie o QR e entre no grupo Feishu para ajuda e novidades:

<img src="assets/feishu-qr.png" alt="QR do grupo Feishu" width="280">

Se o projeto for útil, deixe uma ⭐ Star!
