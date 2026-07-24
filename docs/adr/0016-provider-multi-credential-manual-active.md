---
status: accepted
---

# Multi-credencial de provider: tabela dedicada de credenciais + troca manual da ativa; sem rotação automática

Credencial é entidade estruturada (nome / secret / URL / flag ativa), com responsabilidade diferente da config KV compartilhada. Decidimos que cada provider suporte várias credenciais, na tabela dedicada `provider_credential` (separada da config compartilhada), no máximo uma `is_active` por provider (partial unique index no DB como rede de segurança), troca manual na UI pelo usuário, efeito global; ao apagar a credencial ativa, escolhe automaticamente a de `created_at` mais antiga restante; **explicitamente sem** rotação automática / balanceamento de carga / armazenamento cifrado / estatística de uso — modelar com prefixo KV é frágil em nomes, um único campo JSON com read-modify-write concorrente é complexo; tabela dedicada tem responsabilidade clara e comportamento previsível.

## Consequences

- A exclusão mútua da flag ativa precisa ser garantida na aplicação dentro da transação; troca/remoção deve invalidar o cache do backend.
- Credenciais Anthropic do Agent reutilizam o mesmo modelo «multi-credencial + um active», mas em tabela própria (ver `docs/adr/0017`); a remoção é mais estrita — a credencial ativa não pode ser apagada direto, é preciso trocar para outra antes; não há «auto-escolher a mais antiga».
