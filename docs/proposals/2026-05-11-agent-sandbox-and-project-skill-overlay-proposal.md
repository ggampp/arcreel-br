# Proposta: sandbox do Agent + overlay de Skill em nível de projeto

> Data: 2026-05-12
> Status: Proposal (Pending)
> Versão do SDK: claude-agent-sdk-python 0.1.80

---

## Objetivo

Aumentar a liberdade do agente ArcReel sem ampliar a superfície de vazamento de secrets. Duas frentes concretas:

1. **Integrar o sandbox nativo do Claude Agent SDK**, liberando a ferramenta Bash da «whitelist de caminhos exatos» para «liberação livre dentro do sandbox», eliminando a experiência atual em que o agent frequentemente chama Bash e é rejeitado
2. **Suportar override de skill / agent / CLAUDE.md em nível de projeto de vídeo**, permitindo que o usuário adicione configuração exclusiva a um único projeto de vídeo sem contaminar outros projetos

## Situação atual

O ArcReel já fez a maior parte do trabalho de base:

- ✅ Isolamento bidirecional de `agent_runtime_profile/` (config do agente fisicamente separada do `.claude/` de desenvolvimento; deploy Docker com zero vazamento)
- ✅ Controle explícito `setting_sources=["project"]`, bloqueando poluição global de `~/.claude/`
- ✅ Hook `PreToolUse` + cerca de caminhos `_is_path_allowed` + whitelist de extensões de escrita (`.json/.md/.txt`)
- ✅ Regras de permissão declarativas (deny / allow em settings.json + whitelist de caminhos Bash exatos + `canUseTool` deny por padrão)
- ✅ Gestão de session do SDK 0.1.80+ (`sdk_session_id` já é identificador de negócio)
- ✅ ConfigService migrou config de provider de JSON para DB

Dois blocos ainda não feitos:

- ❌ **Sandbox do SDK não habilitado**: hoje `DEFAULT_ALLOWED_TOOLS` não inclui Bash; toda chamada Bash exige whitelist de caminho exato em settings.json; scripts novos de skill exigem alterar settings.json; e Bash exploratório (`ls`, `cat`, `jq`, `python -c`) não é suportado
- ❌ **Projeto de vídeo não pode ter skill customizado**: todos os projetos compartilham `agent_runtime_profile/.claude/skills/`; `projects/<name>/.claude` é só symlink. A demanda original "projetos diferentes podem ter skills extras próprios" não foi cumprida

## Decisões-chave

### Decisão 1: habilitar sandbox do SDK + `autoAllowBashIfSandboxed`, remover whitelist Bash

Dentro do sandbox, Bash no escopo do cwd é liberado automaticamente; scripts novos de skill não exigem mais mudar config de permissões.

O `SandboxSettings` do SDK 0.1.80 só cuida do comportamento de execução de comando, não de arquivo e rede. Restrições de arquivo/rede vão por `permissions.deny`, estendendo para arquivos sensíveis hoje em falta (`projects/.arcreel.db`, `projects/.system_config.json.bak`, `agent_runtime_profile/.claude/settings.json` etc.).

macOS usa Seatbelt automaticamente; Linux usa bubblewrap; overhead de startup <50ms.

### Decisão 2: em deploy Docker habilitar `enableWeakerNestedSandbox`

Dentro do container, bwrap por padrão não sobe (user namespace sem privilégio desabilitado); com essa opção, bwrap entra em reduced capability mode.

Do ponto de vista do sandbox, perde-se mount independente de `/proc` e PID namespace; isolamento de filesystem, proxy de rede e processos se mantêm. A borda do container já isola o host, e secrets não estão no env (decisão 4), então o valor residual de exposição de `/proc` é baixo. Este é o modo de deploy em container explicitamente recomendado na documentação da Anthropic.

### Decisão 3: overlay em nível de projeto no modo pure delta

Projetos de vídeo podem ter seu próprio CLAUDE.md (append ao profile), skill e subagent.

- **Só armazena delta, não cópia completa**. Upgrade do profile: projetos acompanham sem perceber.
- **Override por nome igual**: o que existir no overlay, aquele projeto usa a versão do overlay; outros projetos continuam no profile.
- **Ciclo de vida só com duas ações**: usuário adiciona/altera um arquivo de overlay; usuário apaga um arquivo de overlay. **Sem sync / reset / merge de três vias / número de versão**.
- **Não fazer** interpolação de variáveis de template nem diff visual; só quando houver demanda real.
- **Import/export**: overlay é parte dos assets do projeto; o zip de export leva; o import restaura. Dados internos de runtime do projeto (migration markers etc.) não entram no archive.

### Decisão 4: provider secrets saem por completo de `os.environ`

O SDK 0.1.80 não tem campo programático `api_key`; autenticação só por variável de ambiente. Mas o env do subprocesso do SDK é montado com merge `{**os.environ, **options.env, ...}` (código exposto no GitHub Issue #573); `options.env` pode sobrescrever env homônimo do processo pai.

Com base nisso:

- **O `os.environ` do processo pai só mantém config de startup** (`AUTH_*` / `DATABASE_URL` / `LOG_LEVEL`); todos os provider secrets (`ANTHROPIC_*` / `ARK_API_KEY` / `XAI_API_KEY` / `GEMINI_*` / `GOOGLE_APPLICATION_CREDENTIALS`) deixam de ser escritos no env. ConfigService DB é a única fonte.
- **A cada construção de SDK options**, buscar config Anthropic do DB e injetar em `options.env`; ao mesmo tempo, sobrescrever as outras chaves de provider com valor vazio, como defesa residual de qualquer caminho residual.
- Depois que o usuário trocar a config de provider, a próxima session nova ou reconexão aplica.

Como a autenticação Anthropic chega ao subprocesso do SDK e ao mesmo tempo fica invisível ao subprocesso Bash (ver linha vermelha de segurança) é decisão de design de implementação, fora do escopo desta proposta.

### Decisão 5: rede do sandbox liberada por padrão

Não manter whitelist de domínio WebFetch.

- Usuário adiciona/edita fornecedores a qualquer momento; manter whitelist é inviável e interrompe a experiência
- Agent consultar docs e baixar amostras é demanda razoável
- Decisão 4 + linha vermelha de segurança retiram secrets de env, filesystem e subprocesso Bash; a cadeia real "ler dado sensível e enviar para fora" é cortada; liberar a "saída" não adiciona superfície de ataque

## Linha vermelha de segurança (indicadores rígidos)

Os indicadores abaixo não podem ser contornados; se a implementação não puder satisfazer todas as linhas vermelhas ao mesmo tempo, a demanda não se sustenta.

- **Subprocesso Bash não pode ver nenhuma chave de provider nem chave de autenticação** (incluindo a própria Anthropic)
- **Agent não pode ler** `.env` / `projects/.arcreel.db` / `projects/.system_config.json.bak` / `vertex_keys/**` / `agent_runtime_profile/.claude/settings.json` e outros arquivos sensíveis
- **Agent não pode escrever fora do diretório do projeto**
- **`os.environ` do processo pai não contém chaves de provider**

## Escopo

### Módulos envolvidos nesta rodada

- Camada de construção de config do SDK (SessionManager)
- Gestão de projeto e estrutura de diretórios (ProjectManager)
- Archive de projeto (project_archive)
- Config service e todos os caminhos de fallback de env de provider (ConfigService, `_load_project_env`, `sync_anthropic_env`, camada de compatibilidade `SystemConfig` etc.)
- Página de configurações de projeto no frontend (gestão de overlay)
- Docs de deploy e Dockerfile

### Não-objetivos

- Checkpoint / rewind antes de escrita (`enable_file_checkpointing` do SDK 0.1.80 é mutuamente exclusivo com o DB session store usado desde ArcReel 0.13.0; exige avaliação técnica separada antes de abrir projeto)
- Interpolação de variáveis de template / merge de três vias / número de versão de template / sync API
- Marketplace externo de skill / mecanismo de assinatura
- Snapshot completo de diretório / shadow git
- Rollback de DB e mídia
- Rollback de escritas de Bash / scripts de skill
- Landlock LSM / isolamento em nível de OS user / Firecracker
- Blacklist WebFetch

## Aceite funcional

**Sandbox**
- Agent roda livremente `ls / cat / jq / python -c` dentro do diretório do projeto sem ser rejeitado
- Scripts novos de skill não exigem mudar config de permissões
- Com todas as linhas vermelhas de segurança aceitas, agent pode `curl` qualquer domínio livremente

**Overlay em nível de projeto**
- novel-a escrever "estilo: wuxia" só afeta novel-a; novel-b não muda
- novel-a adicionar skill exclusivo: dispara em novel-a, não em novel-b
- Skill de mesmo nome: em novel-a usa versão do overlay; em novel-b usa versão do profile
- Após upgrade do profile, todos os projetos acompanham sem perceber
- Export zip do projeto leva o overlay; após import, restaura

**Isolamento de variáveis de ambiente**
- Depois que o usuário troca a config Anthropic, a próxima session nova ou reconexão aplica

**Deploy**
- Docs de deploy Docker dão passos claros de habilitação do sandbox; deploy novo funciona out-of-the-box
- Ambientes de desenvolvimento local Linux + macOS conseguem subir o sandbox
- Projetos antigos passam a usar overlay normalmente via script de migração

## Itens de pesquisa prévia

Antes da implementação, validar as hipóteses técnicas abaixo com PoC mínima. O resultado afeta diretamente o desenho da solução:

1. **Comportamento de herança do subprocesso Bash do SDK em relação a `options.env`**. O caminho de implementação da decisão 4 + linha vermelha "Bash não vê secrets" depende disso.
2. **Comportamento cross-platform (macOS/Linux) do SDK 0.1.80 com symlink / local plugin**. O mecanismo de carga do overlay da decisão 3 depende disso.
3. **Se `autoAllowBashIfSandboxed=True` basta para a ferramenta Bash ficar de fato utilizável**, e se no status atual (sem Bash em `DEFAULT_ALLOWED_TOOLS`) ainda é preciso ajustar `allowed_tools` ou o fallback de `canUseTool`.

## Riscos

1. **Degradação de segurança do Docker `enableWeakerNestedSandbox`**: a documentação Anthropic avisa "considerably weakens security". Borda do container + permissions deny + isolamento de env formam três camadas de fallback; no conjunto, controlável.
2. **Secrets residuais em `os.environ`**: `sync_anthropic_env`, camada de compatibilidade `SystemConfig`, `_load_project_env` e outros pontos históricos de escrita; se faltar algum, a chave é herdada pelo subprocesso. A sobrescrita defensiva com valor vazio da decisão 4 é o fallback, mas a fase de implementação exige auditoria completa.
3. **Comandos Bash incompatíveis com o sandbox** (`docker`, `watchman` etc.): ArcReel não usa; impacto pequeno. Se no futuro forem introduzidos, usar `excludedCommands`.
4. **Seatbelt do macOS já está deprecated**: Anthropic oficial admite; sem substituto de curto prazo; seguir Anthropic.

## Trabalho posterior (explicitamente adiado)

- Checkpoint / rewind antes de escrita (aguardando avaliação do caminho de compatibilidade entre DB session store e `enable_file_checkpointing` do SDK)
- Interpolação de variáveis de template no overlay / merge visual de três vias
- Marketplace externo de skill
- Endurecimento Landlock LSM
- Blacklist WebFetch
- Rollback de escritas de Bash / scripts de skill
