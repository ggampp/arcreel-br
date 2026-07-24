---
name: generate-narration-audio
description: Gera narração (TTS) segmento a segmento para scripts no modo narration. Use quando o usuário disser "gerar narração", "dublagem", "gerar narração do episódio inteiro", quiser regenerar a dublagem de um trecho, ou precisar completar lote interrompido.
---

# Gerar áudio de narração

Para cada segmento do script no modo narration, sintetiza um áudio de narração a partir do `novel_text` original do segmento
e grava de volta em `generated_assets.narration_audio` (saída `audio/segment_{segment_id}.wav`).
Depende só do script, não de storyboard/vídeo — pode avançar assim que o script existir.

## Chamadas de ferramentas

**Importante: a geração de narração deve enfileirar via as ferramentas MCP abaixo. Este skill não fornece scripts Python/Shell; não use BASH para chamar `python .../scripts/*.py`.**

Enfileirar via ferramenta MCP:

| Operação | Ferramenta |
|------|------|
| Completar o episódio (padrão: todos os segmentos sem áudio) | `mcp__arcreel__generate_narration_audio({"script": "episode_1.json"})` |
| Faixa em lote especificada | `mcp__arcreel__generate_narration_audio({"script": "episode_1.json", "segment_ids": ["E1S01", "E1S02"]})` |
| Regenerar um segmento | `mcp__arcreel__generate_narration_audio({"script": "episode_1.json", "segment_ids": ["E1S05"]})` |

> **Regra de seleção**: sem `segment_ids`, só enfileira segmentos sem `narration_audio`; segmentos passados explicitamente são resintetizados mesmo com áudio já existente (útil após trocar timbre/velocidade).
>
> **Dependência**: o generation worker deve estar online (canal audio independente); provedor de audio, modelo e timbre/velocidade padrão globais o usuário configura na página de settings do Web.
>
> **Override de timbre/velocidade no nível do projeto**: se o usuário pedir "neste projeto a narração usa timbre X / velocidade 1.2", chame
> `mcp__arcreel__patch_project({"settings": {"narration_voice": "X", "narration_speed": 1.2}})`
> para gravar o override do projeto (prevalece sobre as settings globais e só afeta o projeto atual; passe `null` para limpar e voltar ao global). Só passa a valer nos segmentos resintetizados depois da mudança.

## Fluxo de trabalho

1. **Detecção de estado** — ler o script, checar `generated_assets.narration_audio` de cada segmento, contar faltantes e informar o usuário
2. **Enfileirar geração** — chamar a ferramenta MCP; as tarefas passam pela fila e o worker processa; a ferramenta espera tudo terminar e devolve resultado por segmento
3. **Relatar** — resumir sucessos/falhas para o usuário

## Retomada por checkpoint

Após interrupção (restart do serviço, falha de tarefa, desconexão da sessão), chame de novo a **completação do episódio inteiro sem `segment_ids`**:
segmentos com áudio são pulados automaticamente; só completa os faltantes, sem cobrir de novo.

## Tratamento de erros

- Falha de um segmento não afeta o lote; a ferramenta devolve resultado por segmento
- Segmentos falhos: retente com precisão via `segment_ids`
- Se a ferramenta indicar que o provedor de audio não está configurado, oriente o usuário a configurar na página de settings do Web e tentar de novo
