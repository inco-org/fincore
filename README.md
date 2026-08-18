# Fincore

INCO financial core.

Financial calculation library for credit and investment operations.

Its main purpose is to generate payments for loans with a Bullet, Price, American Amortization, or Custom (constant amortization, grace period, etc.) systems. Supports fixed-rate operations, or indexed to CDI, Brazilian Savings, or IPCA. Accounts for interest in a 252 business day year for CDI; or 30/360 basis for fixed-rate and other indexes.

This library also generates daily returns tables for loans. It covers the same modalities and the same capitalization forms as the payments generation routine.

The library supports not only regular flows, but also irregular ones, with prepayments, and assists in the calculation of arrears.

## Payments Table

The `get_payments_table` function generates a table of payments from a minimum of three parameters: the amount of money invested (principal); the annual return rate, as a percentage (apy); and an amortization schedule.

The amortization schedule is nothing more than a list of monthly amortizations. Each amortization is a monlthy entry, and provides basic information on how the algorithm behaves on a given date.

1. The date of the amortization.
2. What percentage of the principal will be amortized on that date. This percentage can be zero.
3. A boolean flag indicating wether interest should be also amortized on that date.

The amortization schedule should abide to some provisors, otherwise expect the function to raise exceptions. Here are the fundamental ones:

1. The first amortization represents the date the loan starts generating interest. It does not represent a settlement, hence, its amortization ratio must be zero, and the interest amortization flag must be false.
2. The amortization ratio must sum to one with a precision of at least 10 decimal places. This means that on the last amortization, the principal will have been entirely settled.
3. All amortizations must occur strictly on a monthly basis, with no gaps allowed. If no settlement is scheduled for a given month, you must still include an entry with ratio equal to zero, and no interest amortization, just as in the first entry of the schedule.

### Example Usage

```python
import decimal, datetime, fincore

amortizations = [
    fincore.Amortization(date=datetime.date(2022, 3, 9), amortizes_interest=False),
    fincore.Amortization(date=datetime.date(2022, 4, 9), amortization_ratio=decimal.Decimal('0.8'), amortizes_interest=True),
    fincore.Amortization(date=datetime.date(2022, 5, 9), amortization_ratio=decimal.Decimal('0.2'), amortizes_interest=True)
]

for payment in fincore.get_payments_table(
    principal=decimal.Decimal('100000'),
    apy=decimal.Decimal('5.0'),
    amortizations=amortizations
):
    print(payment)
```

## get_daily_returns

The `get_daily_returns` function generates a table of daily returns from a list of amortizations.

### Example Usage

```python
import decimal, datetime, fincore

amortizations = [
    fincore.Amortization(date=datetime.date(2022, 3, 9), amortizes_interest=False),
    fincore.Amortization(date=datetime.date(2022, 4, 9), amortization_ratio=decimal.Decimal('0.5'), amortizes_interest=True),
    fincore.Amortization(date=datetime.date(2022, 5, 9), amortization_ratio=decimal.Decimal('0.5'), amortizes_interest=True)
]

for daily_return in fincore.get_daily_returns(
    principal=decimal.Decimal('100000'),
    apy=decimal.Decimal('5.0'),
    amortizations=amortizations
):
    print(daily_return)
```

## Command Line Interface

The `fincore_cli.py` script is a self-contained [uv script](https://docs.astral.sh/uv/guides/scripts/): invoking it directly installs its dependencies automatically. Use `gera_pagamentos` to generate a payment schedule. Its positional arguments are the modality, the principal, the fixed annual rate, and the start date plus term in the `DATE+MONTHS` format.

Bullet — principal and interest settled in a single payment at maturity:

    ./fincore_cli.py gera_pagamentos Bullet 100000 10 2024-01-15+6

Monthly interest (Juros mensais) — interest paid monthly, principal at maturity:

    ./fincore_cli.py gera_pagamentos Juros\ mensais 100000 10 2024-01-15+6

Price — fixed installments amortizing principal and interest:

    ./fincore_cli.py gera_pagamentos Price 100000 10 2024-01-15+12

Use `gera_rendimentos_diarios` to generate a daily returns table. It takes the same positional arguments as `gera_pagamentos`:

    ./fincore_cli.py gera_rendimentos_diarios Bullet 100000 10 2024-01-15+6

    ./fincore_cli.py gera_rendimentos_diarios Juros\ mensais 100000 10 2024-01-15+6

    ./fincore_cli.py gera_rendimentos_diarios Price 100000 10 2024-01-15+12

Each row shows the payment period (T), the day number, the opening balance, the daily return, and the daily factors. Use `formato=csv` or `formato=json` for machine-readable output.

Both routines support post-fixed operations through the `indice_variavel` option. With CDI, the fixed rate acts as a spread over the index, and interest accrues only on business days. Indexes are fetched from the BACEN API and cached locally, so the first run of the day requires network access:

    ./fincore_cli.py gera_pagamentos Bullet 100000 6 2024-01-15+6 indice_variavel=CDI

    ./fincore_cli.py gera_rendimentos_diarios Bullet 100000 6 2024-01-15+6 indice_variavel=CDI

Use `indice_variavel_percentual` to apply a percentage of the index, e.g. `indice_variavel_percentual=120` for 120% of CDI.

Run `./fincore_cli.py ajuda gera_pagamentos` or `./fincore_cli.py ajuda gera_rendimentos_diarios` for the full list of options, including other variable indexes (IPCA, Savings), prepayments, and output formats.

## Coverage

[![Coverage badge](https://raw.githubusercontent.com/inco-org/fincore/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/inco-org/fincore/blob/python-coverage-comment-action-data/htmlcov/index.html)

## Testing

    pytest -Werror --doctest-modules tests fincore.py

## Type-checking Fincore

    mypy --ignore-missing-imports --strict --follow-imports silent fincore.py
