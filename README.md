# Fincore

INCO financial core.

Financial calculation library for credit and investment operations.

Its main purpose is to generate payments for loans with a Bullet, Price, American Amortization, or Custom (constant amortization, grace period, etc.) systems. Supports fixed-rate operations, or indexed to CDI, Brazilian Savings, or IPCA. Accounts for interest in a 252 business day year for CDI; or 30/360 basis for fixed-rate and other indexes.

This library also generates daily returns tables for loans. It covers the same modalities and the same capitalization forms as the payments generation routine.

The library supports not only regular flows, but also irregular ones, with prepayments, and assists in the calculation of arrears.

## Payments Table

The `get_payments_table` function generates a table of payments from a minimum of three parameters: the amount of money invested (principal); the annual return rate, as a percentage (apy); and an amortization schedule.

The amortization schedule is nothing more than a list of monthly amortizations. Each amortization is a monlthy entry, and provides basic information on how on a given date.

1. The date of the amortization.
2. What percentage of the principal will be amortized on that date. This percentage can be zero.
3. A boolean flag indicating wether interest should be also amortized on that date.

The amortization schedule should abide to some provisors, otherwise expect the function to raise exceptions. Here are the fundamental ones:

1. The first amortization represents the date the loan starts generating interest. It does not represent a settlement, hence, its amortization ratio must be zero, and the interest amortization flag must be false.
2. The amortization ratio must sum to one with a precision of at least 10 decimal places. This means that on the last amortization, the principal will have been entirely settled.

### Example Usage

```python
import decimal
import datetime
import fincore

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
import decimal
import datetime
import fincore

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

## Coverage

[![Coverage badge](https://raw.githubusercontent.com/inco-org/fincore/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/inco-org/fincore/blob/python-coverage-comment-action-data/htmlcov/index.html)

## Testing

    pytest -Werror --doctest-modules tests fincore.py

## Type-checking Fincore

    mypy --ignore-missing-imports --strict --follow-imports silent fincore.py
