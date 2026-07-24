---
status: accepted
---

# Credencial Anthropic do Agent em armazenamento próprio; cada sessão injeta env a partir do DB, sem escrever os.environ global

Env global é valor único no nível do processo e conflita com «multi-credencial + cada sessão pode usar active diferente»; além disso secrets de provider já estão proibidos em `os.environ`. Decidimos armazenar as credenciais do gateway Anthropic do Claude Agent SDK em tabela própria (separadas de credenciais de custom provider, fora de `ENDPOINT_REGISTRY`, sem participar da geração de mídia); a forma de vigência é: a cada nova sessão Agent, `build_anthropic_env_dict` (entrada: DB session) lê a credencial active no DB, devolve dict e injeta em `ClaudeAgentOptions.env` — **sem escrever os.environ global**; o endpoint activate só faz set_active, sem sync de env.

## Consequences

- Sessões já em execução mantêm o env do spawn; trocar active só vale para sessões **novas** (só toast de aviso, sem forçar término).
- Complementa `docs/adr/0008` (modelo de credencial de custom provider): ambos deixam clara a fronteira «armazenamento de credencial não se contamina com forma de protocolo/global de processo» e «determinado em runtime vs declarado no start».
