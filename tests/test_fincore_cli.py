# Copyright (C) Inco - All Rights Reserved.
#
# Written by Rafael Viotti <viotti@inco.vc>, August 2026.
#
# Unauthorized copying of this file, via any medium, is strictly prohibited.
# Proprietary and confidential.
#

'''Fincore CLI test module.

Covers the CLI's private schedule stereotyping, which derives amortization schedules from a start date plus a term,
in the Bullet, American Amortization, and Price modalities.
'''

# Core.
import math
import decimal
import datetime

# Libs.
import pytest

# Inco.
import fincore
import fincore_cli

# Zero as decimal.
_0 = decimal.Decimal()

# One as decimal.
_1 = decimal.Decimal('1')

# 🚩 Invalid parametrizations. {{{
def test_wont_preprocess_bullet():
    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        fincore_cli._preprocess_bullet(datetime.date.min, -1)

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        fincore_cli._preprocess_bullet(datetime.date.min, 0)

    with pytest.raises(ValueError, match='invalid value for insertion entry #0 – should be positive'):
        ent = fincore.Amortization.Bare(date=datetime.date(2022, 6, 1), value=decimal.Decimal(-5000))

        fincore_cli._preprocess_bullet(datetime.date(2022, 1, 1), 12, [ent])

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, must succeed "zero_date", \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2021, 12, 1), value=decimal.Decimal(5000))

        fincore_cli._preprocess_bullet(datetime.date(2022, 1, 1), 12, [ent])

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the regular payment date, \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))

        fincore_cli._preprocess_bullet(datetime.date(2022, 1, 1), 12, [ent])

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds "anniversary_date", \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))

        fincore_cli._preprocess_bullet(datetime.date(2022, 1, 1), 12, [ent], anniversary_date=datetime.date(2023, 1, 5))

    with pytest.raises(ValueError, match='the "anniversary_date", 2022-01-01, must be greater than "zero_date", 2022-01-01'):
        fincore_cli._preprocess_bullet(datetime.date(2022, 1, 1), 12, anniversary_date=datetime.date(2022, 1, 1))

def test_wont_preprocess_american():
    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        fincore_cli._preprocess_american(datetime.date.min, -1)

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        fincore_cli._preprocess_american(datetime.date.min, 0)

    with pytest.raises(NotImplementedError, match='"Poupança" is currently unsupported'):
        fincore_cli._preprocess_american(datetime.date(2021, 7, 23), 9, vir=fincore.VariableIndex('Poupança'))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, must succeed "zero_date", \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2021, 12, 1), value=decimal.Decimal(5000))

        fincore_cli._preprocess_american(datetime.date(2022, 1, 1), 12, [ent])

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))

        fincore_cli._preprocess_american(datetime.date(2022, 1, 1), 12, [ent])

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))

        fincore_cli._preprocess_american(datetime.date(2022, 1, 1), 12, [ent], anniversary_date=datetime.date(2022, 2, 5))

    with pytest.raises(ValueError, match='the "anniversary_date", 2021-07-01, must be greater than "zero_date", 2021-07-01'):
        fincore_cli._preprocess_american(datetime.date(2021, 7, 1), 9, anniversary_date=datetime.date(2021, 7, 1))

def test_wont_preprocess_price():
    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        fincore_cli._preprocess_price(_1, _1, datetime.date.min, -1)

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        fincore_cli._preprocess_price(_1, _1, datetime.date.min, 0)

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, must succeed "zero_date", \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2021, 12, 1), value=decimal.Decimal(5000))

        fincore_cli._preprocess_price(_1, _1, datetime.date(2022, 1, 1), 12, [ent])

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))

        fincore_cli._preprocess_price(_1, _1, datetime.date(2022, 1, 1), 12, [ent])

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        ent = fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))

        fincore_cli._preprocess_price(_1, _1, datetime.date(2022, 1, 1), 12, [ent], anniversary_date=datetime.date(2022, 2, 5))

    with pytest.raises(ValueError, match='the "anniversary_date", 2021-07-01, must be greater than "zero_date", 2021-07-01'):
        fincore_cli._preprocess_price(_1, _1, datetime.date(2021, 7, 1), 9, anniversary_date=datetime.date(2021, 7, 1))
# }}}

# ✅ Stereotyped schedules. {{{
def test_will_preprocess_bullet():
    '''A Bullet schedule has exactly two entries: the zero date, and a single total amortization at maturity.'''

    tab = fincore_cli._preprocess_bullet(datetime.date(2022, 1, 1), 12)

    assert len(tab) == 2
    assert tab[0].date == datetime.date(2022, 1, 1)
    assert tab[0].amortization_ratio == _0
    assert not tab[0].amortizes_interest
    assert tab[1].date == datetime.date(2023, 1, 1)
    assert tab[1].amortization_ratio == _1
    assert tab[1].amortizes_interest

def test_will_preprocess_american():
    '''An American Amortization schedule pays interest monthly, and the principal at maturity.'''

    tab = fincore_cli._preprocess_american(datetime.date(2022, 1, 1), 12)

    assert len(tab) == 13
    assert tab[0].date == datetime.date(2022, 1, 1)
    assert not tab[0].amortizes_interest
    assert all(x.amortization_ratio == _0 for x in tab[1:-1])
    assert all(x.amortizes_interest for x in tab[1:])
    assert tab[-1].date == datetime.date(2023, 1, 1)
    assert tab[-1].amortization_ratio == _1

def test_will_preprocess_price():
    '''A Price schedule amortizes the principal entirely, in constant installments.'''

    tab = fincore_cli._preprocess_price(decimal.Decimal('100000'), decimal.Decimal('10'), datetime.date(2022, 1, 1), 12)

    assert len(tab) == 13
    assert tab[0].date == datetime.date(2022, 1, 1)
    assert not tab[0].amortizes_interest
    assert all(x.amortizes_interest for x in tab[1:])
    assert math.isclose(sum(x.amortization_ratio for x in tab), _1)
# }}}
