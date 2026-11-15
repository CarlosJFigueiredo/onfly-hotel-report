# Declaração de uso de IA

## Ferramenta e modelo

- **Ferramenta:** Claude Code, no aplicativo desktop do Claude (aba Code).
- **Modelo:** Claude Opus 5.5 (`claude-opus-5-5`).
- **Sessão:** uma única sessão, exportada pelo próprio aplicativo em [`sessao.jsonl`](sessao.jsonl) (formato nativo do Claude Code).
- **Anonimização:** no arquivo exportado, troquei meu e-mail por `[e-mail removido]` e meu usuário do Windows nos caminhos por `<usuario>`, por privacidade. Nada mais foi alterado.
- Não usei nenhuma outra ferramenta de IA no case.

## O que eu fiz

- Conduzi o trabalho: defini a ordem das etapas, o escopo de cada pedido à IA e o que entrava ou não em cada mudança.
- Implementei manualmente, sem IA, as correções de status (`783b950`), noites (`6070efd`), câmbio (`3328b9b`) e ranking (`e38955f`), a partir da análise do código feita na sessão.
- Pedi à IA a correção da leitura do CSV especificando o que corrigir: espaços do cabeçalho, campos com vírgula entre aspas e o limite de 200 linhas.
- Revisei e commitei todas as mudanças e publiquei o repositório.
- Escrevi o `README-ENTREGA.md` sem IA; a IA revisou o texto e fez os ajustes listados abaixo.

## O que a IA fez

- Analisou o README e o código e explicou a arquitetura e a responsabilidade de cada módulo.
- Apontou os defeitos, incluindo os que os testes fornecidos não cobrem (formato do CSV, limite de 200 linhas e uso de `float`).
- Implementou a correção da leitura do CSV, conforme especifiquei.
- Revisou as minhas quatro correções, sem alterar o código.
- Projetou e escreveu os 39 testes adicionais e verificou a eficácia deles introduzindo 20 defeitos de propósito numa cópia do projeto.
- Implementou, a meu pedido:
  - normalização da moeda e tratamento de moeda sem taxa;
  - refatoração do `ReportBuilder` (agregação separada da serialização, estrutura `Totals`);
  - unificação da leitura de CSV em `repositories/_csv.py`;
  - hierarquia de exceções (`DomainError`, `MissingRateError`) e mensagens de erro.
- Revisou a entrega e apontou pendências; ajustou o `README-ENTREGA.md` (precisão da seção de investigação, separação do defeito do `float`, mudanças que faltavam listar) e redigiu o rascunho desta declaração, que revisei.
