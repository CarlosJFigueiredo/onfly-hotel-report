# Entrega — Consolidador de reservas de hotel

O CLI gerava números errados e, nos CSVs reais, nem chegava a gerar relatório. Encontrei **7 defeitos** que alteravam o resultado, corrigi todos e adicionei validação de entrada e testes.

**Resultado:** `pytest -q` → **44 passed** (os 5 testes fornecidos, sem nenhuma alteração, mais 39 novos). No código original, os 5 fornecidos falhavam.

## Defeitos corrigidos

| # | Defeito | Causa raiz | Arquivo |
|---|---------|-----------|---------|
| 1 | O CLI abortava com "colunas obrigatórias ausentes" nos CSVs reais. | O `DictReader` era usado sem `skipinitialspace` e sem limpar o cabeçalho, mas os CSVs alinham as colunas com espaços, então os nomes das colunas ficavam com espaços e as aspas de `"Hotel Madrid, Gran Vía"` não eram reconhecidas. | `repositories/_csv.py` |
| 2 | Só as primeiras 200 de 300 reservas eram lidas. | Um `if len(rows) == 200: break` no loop de leitura truncava o arquivo sem aviso. | `repositories/csv_reservation_repository.py` |
| 3 | `NO_SHOW` entrava em noites, valores, `by_month` e `top_hotels`. | `is_billable` era `status != "CANCELLED"`, e a regra é que só `CONFIRMED` é faturável. | `services/status_policy.py` |
| 4 | Noites erradas, inclusive negativas na virada de mês (`-28` em vez de `3`). | O cálculo era `(checkout.day - checkin.day) * rooms`, que compara só o dia do mês, não a data. | `services/stay_calculator.py` |
| 5 | Valores em BRL errados em toda moeda diferente de BRL. | A conversão dividia o valor pela taxa (`amount / rate`) em vez de multiplicar. | `services/currency_converter.py` |
| 6 | Valores convertidos sujeitos a erro de centavo (com `float`, 0.75 USD × 5.42 sai `"4.06"` em vez de `"4.07"`). | A conversão passava por `float`, que não representa decimais com exatidão, contrariando a regra de usar `Decimal` no dinheiro. | `services/currency_converter.py` |
| 7 | `top_hotels` listava os hotéis de **menor** valor. | A ordenação usava `(amount, hotel_id)` ascendente; o correto é `total_brl` decrescente com desempate por `hotel_id` ascendente. | `services/report_builder.py` |

Observação sobre a ordem: nos CSVs reais, o defeito 1 impedia qualquer relatório e escondia os demais. Os defeitos 3, 4, 5 e 7 apareciam mesmo assim nos testes fornecidos, que geram CSVs limpos. Os defeitos 2 e 6 não são cobertos por nenhum teste fornecido e foram encontrados lendo o código.

## Como investiguei

Fiz a investigação com apoio do Claude Code; a sessão e a declaração do que foi feito por mim e pela IA estão em [`uso-de-ia/`](uso-de-ia/).

1. **Li o enunciado e extraí as regras** (status, noites, câmbio, exatidão, ordenação, contrato do CLI) para usar como critério de correto.
2. **Rodei os testes fornecidos no código original**: 5 falhas, cada uma apontando para um defeito (câmbio, noites, regressão da amostra, status, ranking).
3. **Rodei o CLI original nos CSVs reais.** Ele terminava com código 2 e "colunas obrigatórias ausentes", o que revelou o defeito 1, que os testes fornecidos não cobrem porque geram CSVs limpos.
4. **Li o código de ponta a ponta** seguindo a ordem do enunciado (`ler → converter tipos → contar status → filtrar CONFIRMED → agregar`) e comparei cada etapa com a regra correspondente. Foi assim que apareceram o truncamento em 200 linhas e o uso de `float` na conversão.
5. **Corrigi em commits pequenos e separados** (leitura do CSV, status, noites, câmbio e ranking), de modo que cada correção fica isolada no histórico e pode ser revisada sozinha.
6. **Validei na amostra do enunciado** (`data/exemplo-validacao.csv`) e conferi todos os campos, a ordem do `by_month` e do `top_hotels`.
7. **Reforcei as bordas** que o enunciado cita ou implica, sem alterar o contrato (seção abaixo).
8. **Verifiquei se os testes novos pegam defeitos de verdade**: introduzi 20 defeitos de propósito numa cópia do projeto (arredondamento half-even, `float` na conversão, ranking sem desempate, `by_month` pelo checkout, códigos de saída trocados, entre outros). Os testes novos detectaram todos; a suite fornecida detectava 2.
9. **Refatorei com comparação de saída**: antes e depois de cada refatoração, comparei o JSON gerado em 7 cenários (amostra, dataset completo com `--top` 1, 5 e 50, empate, nenhuma reserva faturável, arredondamento). Ficou idêntico.

## Além dos defeitos

Mudanças que **não alteram** nome, tipo ou semântica de nenhum campo do relatório:

- **Moeda normalizada para maiúsculas** na reserva (`usd` → `USD`), como já acontecia na tabela de câmbio.
- **Moeda sem taxa** agora gera `MissingRateError` (código de saída 2, mensagem com as moedas cadastradas), em vez de `KeyError` com código 1.
- **Hierarquia de erros de domínio** (`DomainError` → `InputFileError`, `MissingRateError`): qualquer entrada inválida sai com código 2, sem traceback; só erro realmente inesperado sai com 1.
- **Mensagens de erro claras**: valor inválido indica linha, coluna e valor (`linha 3: valor inválido em amount: 'cem reais'`); falha ao gravar o relatório sai com código 1 e mensagem, sem traceback.
- **Leitura de CSV extraída** para `repositories/_csv.py`, compartilhada pelos repositórios de reservas e de câmbio. Com isso, a tabela de câmbio passou a aceitar o mesmo formato alinhado por espaços do CSV de reservas.
- **Agregação e serialização** do `ReportBuilder` separadas, com uma estrutura `Totals` no lugar das somas repetidas, `Decimal` em todo o fluxo e arredondamento half-up **somente na serialização**.
- **39 testes novos** (arquivos novos em `tests/`: aceitação, contrato do relatório, regras de agregação, precisão monetária, tratamento de moeda, repositórios CSV e erros do CLI). Os testes fornecidos continuam inalterados.

## Como validar

Requisitos: Python 3.11+.

```bash
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# testes
pytest -q

# relatório completo
PYTHONPATH=src python -m onfly_report \
  --input data/reservas_hoteis.csv \
  --rates data/taxas_cambio.csv \
  --output output/report.json

# amostra de validação
PYTHONPATH=src python -m onfly_report \
  --input data/exemplo-validacao.csv \
  --rates data/taxas_cambio.csv \
  --output output/exemplo.json
```

**Amostra de validação** (confere com a tabela do enunciado):

| Campo | Obtido |
|-------|--------|
| `total_reservations` | 12 |
| `confirmed_reservations` | 9 |
| `cancelled_reservations` | 2 |
| `no_show_reservations` | 1 |
| `total_room_nights` | 28 |
| `total_amount_brl` | 7566.00 |
| `average_nightly_rate_brl` | 270.21 |

`by_month`: `2025-01` (8 reservas, 25 noites, 6684.00) e `2025-02` (1 reserva, 3 noites, 882.00).
`top_hotels`: H01, H02, H12, H10, H09, nessa ordem.

**Dataset completo:** 300 reservas, 235 confirmadas, 1347 noites de quarto, `total_amount_brl` = `396170.00`, `average_nightly_rate_brl` = `294.11`.

**Códigos de saída:** `0` sucesso; `2` entrada ou argumento inválido (arquivo inexistente, coluna ausente, linha malformada, moeda sem taxa, `--top < 1`); `1` erro inesperado ou falha ao gravar o relatório.

## Resultado do `pytest`

```
$ pytest -q
............................................                             [100%]
44 passed
```

## O que não foi alterado

- Comando e argumentos do CLI.
- Schema e semântica do relatório.
- `data/reservas_hoteis.csv` e `data/taxas_cambio.csv`.
- Os testes fornecidos (`test_currency.py`, `test_nights.py`, `test_regression_report.py`, `test_status_rules.py`, `test_top_hotels.py`, `helpers.py`), idênticos ao commit original.

## Uso de IA

Usei o Claude Code (modelo Claude Opus 5.5) como apoio. A sessão exportada e a declaração do que foi feito por mim e pela IA estão em [`uso-de-ia/`](uso-de-ia/).
