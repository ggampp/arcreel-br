---
status: accepted
---

# Sandbox de kernel indisponível: falha dura no startup do server; só Windows tem degradação documentada

O modelo de segurança das ferramentas do Agent tem o sandbox de kernel (macOS Seatbelt / Linux bwrap) como base; se após falha de detecção degradar em silêncio para rodar sem sandbox, a defesa contra path out-of-bounds e requests de saída some sem aviso. Decidimos colocar a checagem de disponibilidade do sandbox no startup do server (`check_sandbox_available`): sem `sandbox-exec` no macOS, sem `bwrap`/`socat` no Linux, ou bwrap presente mas o trial run falha → raise direto, o serviço inteiro recusa subir (fail-closed), em vez de degradar e rodar ou só errar na primeira sessão; a única exceção é Windows nativo sem sandbox — warning e desliga o sandbox; a ferramenta Bash do Agent passa a usar whitelist de prefixos em código.

## Consequences

- O ambiente de deploy precisa ter as dependências de sandbox instaladas antes (macOS já traz `sandbox-exec`; Linux precisa de `bwrap` + `socat`), senão o serviço não sobe. Desenho deliberado: melhor recusar serviço do que rodar agent sem sandbox.
- A whitelist de prefixos no Windows é mais grossa que o sandbox (prefixos de comando liberáveis são limitados); deploy de produção ainda recomenda WSL2/Docker para o sandbox completo.
