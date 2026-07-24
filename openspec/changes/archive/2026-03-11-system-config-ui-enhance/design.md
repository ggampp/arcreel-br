## Context

O `SystemConfigPage.tsx` atual (~1389 linhas) usa duas Tabs na barra superior: "config" (todas as configurações misturadas) e "api-keys". Todos os campos de configuração ficam na Tab config única, com o botão salvar fixo no fim da página. Principais problemas:

- Campos sem classificação clara; o usuário tem dificuldade para achar o que precisa
- Só alguns campos (como API key) têm botão limpar; `base_url` e outros não podem ser limpos rapidamente
- O botão salvar fica no fim da página; ao editar campos em cima, o usuário não sabe que precisa salvar
- Componente grande demais, difícil de manter

## Goals / Non-Goals

**Goals:**
- Expandir as Tabs da barra superior de `[config, api-keys]` para `[Configuração do agente ArcReel, Configuração de geração de imagem/vídeo IA, Configuração avançada, API Keys]`, cada Tab com os campos da categoria correspondente
- Cada Tab de configuração tem botão salvar independente; com alterações não salvas na Tab, o rodapé de salvamento fica sticky na parte inferior do viewport
- Botão limpar (×) unificado em todos os campos opcionais
- Usar a skill `/frontend-design` no design de UI e a skill `/vercel-react-best-practices` no desenvolvimento

**Non-Goals:**
- Não alterar API de backend nem definições de tipos
- Não mudar a semântica ou os valores padrão das configurações existentes
- Não introduzir novas dependências externas

## Decisions

### Decisão 1: Estrutura das Tabs

**Escolha**: quatro Tabs na barra superior; a Tab `api-keys` original permanece; a Tab `config` original se divide em três

| Tab | Conteúdo |
|-----|------|
| Configuração do agente ArcReel | Anthropic API Key, Base URL, seleção de modelos |
| Configuração de geração de imagem/vídeo IA | Gemini API Key, Base URL, seleção de backend, seleção de modelo, credenciais Vertex |
| Configuração avançada | Rate limit (RPM), intervalo de requisição, máximo de Workers concorrentes |
| API Keys | Componente ApiKeysTab existente, inalterado |

**Justificativa**: Tabs têm hierarquia visual mais alta que agrupamento em cards e deixam a classificação mais clara; cada Tab fica focada e mais enxuta; manter a estrutura da Tab API Keys reduz o escopo da mudança.

### Decisão 2: Percepção de alterações não salvas — rodapé sticky de salvamento

**Problema central**: o conteúdo da Tab pode ser longo; o usuário edita campos em cima e não sabe que precisa clicar em salvar.

**Escolha**: o rodapé de salvamento de cada Tab de configuração fica sticky na parte inferior do viewport quando há alterações não salvas.

**Detalhes de interação**:
- Sem alterações não salvas: o rodapé renderiza normalmente no fim do conteúdo da Tab (não sticky); o botão save fica desabilitado
- Com alterações não salvas: o rodapé fica `position: sticky; bottom: 0`, o botão salvar em destaque (cor primary), badge de ponto pequeno ao lado do rótulo da Tab
- Salvando: botão em estado de carregamento, entradas desabilitadas
- Após sucesso: sticky removido, rodapé volta à área de conteúdo

```typescript
// Dentro da Tab
const isDirty = !deepEqual(draft, savedValues)

<div className={cn(
  "border-t p-4 flex items-center justify-between bg-background",
  isDirty && "sticky bottom-0 z-10 shadow-[0_-2px_8px_rgba(0,0,0,0.08)]"
)}>
  {isDirty && <span className="text-sm text-muted-foreground">Há alterações não salvas</span>}
  <div className="flex gap-2 ml-auto">
    {isDirty && <Button variant="ghost" onClick={handleReset}>Desfazer</Button>}
    <Button disabled={!isDirty || saving} onClick={handleSave}>
      {saving ? <Spinner /> : "Salvar"}
    </Button>
  </div>
</div>
```

### Decisão 3: Modelo de estado

**Escolha**: cada componente de Tab de configuração mantém o próprio estado de rascunho (`useState`); Tabs totalmente isoladas entre si

```typescript
type TabStatus = "idle" | "saving" | "error"

// Em cada componente de Tab
const [draft, setDraft] = useState<AgentDraft>(buildDraft(config))
const [status, setStatus] = useState<TabStatus>("idle")
const savedRef = useRef(draft)
const isDirty = !deepEqual(draft, savedRef.current)
```

**Justificativa**: isolamento de estado entre Tabs; trocar de Tab não afeta alterações não salvas de outras; cada componente de Tab é autocontido e fácil de testar.

### Decisão 4: Estrutura de componentes

```
SystemConfigPage
├── TopTabs (navegação de Tabs na barra superior)
│   ├── Tab: agent      → AgentConfigTab
│   ├── Tab: media      → MediaConfigTab
│   ├── Tab: advanced   → AdvancedConfigTab
│   └── Tab: api-keys   → ApiKeysTab (inalterado)
└── TabSaveFooter (reutilizável, no fim de cada Tab de configuração)
```

**Rótulos das Tabs**: com alterações não salvas, ponto pequeno `●` ao lado do nome da Tab, para lembrar o usuário.

### Decisão 5: Detecção e aviso de configuração obrigatória ausente

**Definição de itens obrigatórios**: as três condições a seguir devem ser atendidas para o sistema funcionar normalmente:

1. **API Key do agente ArcReel**: `anthropic_api_key.is_set === true`
2. **Credenciais do backend de geração de imagem**: conforme o valor de `image_backend`:
   - `"aistudio"` → `gemini_api_key.is_set === true`
   - `"vertex"` → `vertex_credentials.is_set === true`
3. **Credenciais do backend de geração de vídeo**: conforme o valor de `video_backend`:
   - `"aistudio"` → `gemini_api_key.is_set === true`
   - `"vertex"` → `vertex_credentials.is_set === true`

Nota: `image_backend` e `video_backend` são independentes e podem usar provedores diferentes; `gemini_api_key` e `vertex_credentials` são compartilhados pelos dois (o mesmo conjunto de credenciais).

**Função de detecção**:

```typescript
function checkBackendCredential(backend: SystemBackend, config: SystemConfigView): boolean {
  return backend === "aistudio"
    ? config.gemini_api_key.is_set
    : config.vertex_credentials.is_set
}

function getConfigIssues(config: SystemConfigView): ConfigIssue[] {
  const issues: ConfigIssue[] = []
  if (!config.anthropic_api_key.is_set)
    issues.push({ key: "anthropic", tab: "agent", label: "API Key do agente ArcReel (Anthropic) não configurada" })
  if (!checkBackendCredential(config.image_backend, config))
    issues.push({ key: "image", tab: "media",
      label: config.image_backend === "aistudio"
        ? "API Key de geração de imagem IA (Gemini AI Studio) não configurada"
        : "Credenciais Vertex AI de geração de imagem não enviadas" })
  if (!checkBackendCredential(config.video_backend, config))
    issues.push({ key: "video", tab: "media",
      label: config.video_backend === "aistudio"
        ? "API Key de geração de vídeo IA (Gemini AI Studio) não configurada"
        : "Credenciais Vertex AI de geração de vídeo não enviadas" })
  // Deduplicar: se image e video apontam para a mesma tab e o mesmo motivo, unificar
  return dedupIssues(issues)
}
```

`SecretFieldView.is_set` e `VertexCredentialView.is_set` vêm direto do backend; o frontend não precisa interpretar formato mascarado.

**Onde e como avisar**:

| Local | Forma do aviso |
|------|---------|
| Botão de configurações no canto superior direito de `ProjectsPage.tsx` | Badge de ponto vermelho sobre o ícone Settings |
| Botão de configurações no canto superior direito de `GlobalHeader.tsx` | Idem |
| Topo da página de configurações (acima da navegação de Tabs) | Banner amarelo de aviso listando cada motivo de ausência, com link para a Tab correspondente |

**Compartilhamento de dados**: o estado de completude da configuração é compartilhado globalmente via hook `useConfigStatus` (Zustand ou React Context); `ProjectsPage` e `GlobalHeader` leem o mesmo cache, evitando requisições duplicadas.

**Estratégia de cache**: uma requisição na inicialização do app (após AuthGuard); redetectar após salvamento bem-sucedido da Tab de configuração.

## Risks / Trade-offs

- **Perder alterações não salvas ao trocar de Tab** → badge de ponto no rótulo da Tab lembra o usuário; opcional: diálogo de confirmação na troca → começar com badge, evitando interrupção excessiva
- **Rodapé sticky cobrindo a última linha** → `padding-bottom` suficiente no fim da página; ao remover sticky, restaura automaticamente → risco baixo
- **Escopo grande de refatoração** → `SystemConfigPage.tsx` precisa de reescrita ampla → em fases: primeiro dividir a estrutura de Tabs, depois a percepção sticky
- **Momento da requisição de completude da configuração** → se não estiver logado na inicialização, não dá para pedir → a detecção de completude roda após AuthGuard; sem login, sem badge
