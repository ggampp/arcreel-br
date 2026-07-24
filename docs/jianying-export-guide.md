# Guia de exportação de rascunho CapCut/Jianying

Exporte os clipes de vídeo já gerados no ArcReel, por episódio, como rascunho CapCut/Jianying, abra no CapCut/Jianying desktop e faça edição secundária — ajustar ritmo, legendas, transições, narração etc.

## Pré-requisitos

- Pelo menos um episódio com clipes de vídeo gerados no ArcReel
- **CapCut/Jianying desktop** instalado localmente (5.x ou 6+)

## Passos

### 1. Localizar o diretório de rascunhos CapCut/Jianying

Antes de exportar, você precisa do caminho local dos rascunhos CapCut/Jianying.

**macOS:**
```
/Users/<usuário>/Movies/JianyingPro/User Data/Projects/com.lveditor.draft
```

**Windows:**
```
C:\Users\<usuário>\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
```

> **Dica**: nas configurações do CapCut/Jianying você pode ver a posição do «caminho de rascunhos». Se alterou o padrão, use o diretório real.

### 2. Iniciar a exportação no ArcReel

1. Abra o projeto alvo
2. Clique no botão **Exportar** no canto superior direito
3. Escolha **Exportar como rascunho CapCut/Jianying**

### 3. Preencher os parâmetros de exportação

| Parâmetro | Descrição |
|------|------|
| **Episódio** | Escolha o episódio a exportar (em projetos multi-episódio aparece um seletor) |
| **Versão CapCut/Jianying** | Escolha **6.0+** (recomendado) ou **5.x**, de acordo com a versão instalada localmente |
| **Diretório de rascunhos** | Preencha o caminho de rascunhos encontrado acima (na primeira vez é memorizado) |

Clique em **Exportar rascunho**; o browser baixa um arquivo ZIP.

### 4. Descompactar no diretório de rascunhos

Descompacte o ZIP baixado no diretório de rascunhos CapCut/Jianying preenchido acima. A estrutura fica assim:

```
com.lveditor.draft/
├── ... (outros rascunhos já existentes)
└── {nome-do-projeto}_ep{N}/          ← pasta descompactada
    ├── draft_info.json        (CapCut/Jianying 6+) ou draft_content.json (5.x)
    ├── draft_meta_info.json
    └── assets/
        ├── segment_S1.mp4
        ├── segment_S2.mp4
        └── ...
```

### 5. Abrir no CapCut/Jianying

1. Abra (ou reinicie) o CapCut/Jianying desktop
2. Na lista de «Rascunhos», encontre o rascunho **{nome-do-projeto}\_ep{N}** recém-aparecido
3. Clique duas vezes para abrir e ver todos os clipes na timeline

## Conteúdo exportado

### Modo narração (Narration)

- **Trilha de vídeo**: todos os clipes gerados em ordem
- **Trilha de legendas**: o texto original do romance de cada segmento é anexado automaticamente como legenda (texto branco, contorno preto); estilo e posição são ajustáveis no CapCut/Jianying

### Modo drama (Drama)

- **Trilha de vídeo**: todos os clipes gerados em ordem de cena
- Sem legendas anexadas (a estrutura de legendas em cenas multi-personagem é mais complexa; recomenda-se adicionar manualmente no CapCut/Jianying)

### Tamanho do canvas

Determinado automaticamente pelas settings do projeto:
- Vertical (9:16) → 1080×1920
- Horizontal (16:9) → 1920×1080

Se o projeto não tiver aspect ratio definido, é detectado automaticamente a partir do primeiro arquivo de vídeo.

## Perguntas frequentes

### O rascunho exportado não aparece no CapCut/Jianying?

- Confirme que o ZIP foi descompactado no diretório correto de rascunhos
- Confirme que a pasta descompactada está **diretamente** sob o diretório de rascunhos (sem pasta intermediária extra)
- Tente reiniciar o CapCut/Jianying

### E se a versão não bater?

A versão CapCut/Jianying escolhida na exportação precisa corresponder à instalada localmente:
- CapCut/Jianying 6.0 ou superior → escolha **6.0+**
- CapCut/Jianying 5.x → escolha **5.x**

Se escolheu a versão errada, reexporte com a versão correta.

### Faltam alguns clipes de vídeo?

A exportação só inclui clipes gerados com sucesso. Se alguns ainda não foram gerados ou falharam, não aparecem no rascunho. Volte ao ArcReel, complete a geração e reexporte.
