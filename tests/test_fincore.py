# Copyright (C) Inco - All Rights Reserved.
#
# Written by Rafael Viotti <viotti@inco.vc>, November 2022.
#
# Unauthorized copying of this file, via any medium, is strictly prohibited.
# Proprietary and confidential.
#
# See https://docs.google.com/document/d/11kBx3eg6ki-xw-AfcVxNdpQerxfFCUAahEd_lJk_TBs.
#
# See also http://medium.com/worldsensing-techblog/tips-and-tricks-for-unit-tests-b35af5ba79b1.
#

'''Fincore test module.'''

# Core.
import math
import types
import typing as t
import decimal
import logging
import datetime
import functools
import itertools
import collections
import unittest.mock

# Libs.
import pytest
import dateutil.relativedelta
import typeguard

# Inco.
import fincore

# Data e hora em que essa instrução global foi executada.
_NOW = datetime.datetime.now(datetime.timezone.utc)

# A month.
_MONTH = dateutil.relativedelta.relativedelta(months=1)

# Zero as decimal.
_0 = decimal.Decimal()

# One as decimal.
_1 = decimal.Decimal('1')

# Centi factor.
_CENTI = decimal.Decimal('0.01')

# Centesimal rounding.
_ROUND_CENTI = functools.partial(decimal.Decimal.quantize, exp=_CENTI, rounding=decimal.ROUND_HALF_UP)

# From https://docs.python.org/3/library/itertools.html.
def _tail(n, iterable):
    '''Return an iterator over the last n items'''

    return iter(collections.deque(iterable, maxlen=n))

class _RicherIpcaBackend(fincore.InMemoryBackend):
    '''A richer ICPA backend.'''

    # FIXME: enrich "fincore.InMemoryBackend" with this data. Might break some test cases.
    _registry_ipca = [
        (datetime.date(2018, 1, 1),  decimal.Decimal('0.29')),  (datetime.date(2018, 2, 1),  decimal.Decimal('0.32')),   # NOQA
        (datetime.date(2018, 3, 1),  decimal.Decimal('0.09')),  (datetime.date(2018, 4, 1),  decimal.Decimal('0.22')),   # NOQA
        (datetime.date(2018, 5, 1),  decimal.Decimal('0.40')),  (datetime.date(2018, 6, 1),  decimal.Decimal('1.26')),   # NOQA
        (datetime.date(2018, 7, 1),  decimal.Decimal('0.33')),  (datetime.date(2018, 8, 1),  decimal.Decimal('-0.09')),  # NOQA
        (datetime.date(2018, 9, 1),  decimal.Decimal('0.48')),  (datetime.date(2018, 10, 1), decimal.Decimal('0.45')),   # NOQA
        (datetime.date(2018, 11, 1), decimal.Decimal('-0.21')), (datetime.date(2018, 12, 1), decimal.Decimal('0.15')),   # NOQA
        (datetime.date(2019, 1, 1),  decimal.Decimal('0.32')),  (datetime.date(2019, 2, 1),  decimal.Decimal('0.43')),   # NOQA
        (datetime.date(2019, 3, 1),  decimal.Decimal('0.75')),  (datetime.date(2019, 4, 1),  decimal.Decimal('0.57')),   # NOQA
        (datetime.date(2019, 5, 1),  decimal.Decimal('0.13')),  (datetime.date(2019, 6, 1),  decimal.Decimal('0.01')),   # NOQA
        (datetime.date(2019, 7, 1),  decimal.Decimal('0.19')),  (datetime.date(2019, 8, 1),  decimal.Decimal('0.11')),   # NOQA
        (datetime.date(2019, 9, 1),  decimal.Decimal('-0.04')), (datetime.date(2019, 10, 1), decimal.Decimal('0.10')),   # NOQA
        (datetime.date(2019, 11, 1), decimal.Decimal('0.51')),  (datetime.date(2019, 12, 1), decimal.Decimal('1.15')),   # NOQA
        (datetime.date(2020, 1, 1),  decimal.Decimal('0.21')),  (datetime.date(2020, 2, 1),  decimal.Decimal('0.25')),   # NOQA
        (datetime.date(2020, 3, 1),  decimal.Decimal('0.07')),  (datetime.date(2020, 4, 1),  decimal.Decimal('-0.31')),  # NOQA
        (datetime.date(2020, 5, 1),  decimal.Decimal('-0.38')), (datetime.date(2020, 6, 1),  decimal.Decimal('0.26')),   # NOQA
        (datetime.date(2020, 7, 1),  decimal.Decimal('0.36')),  (datetime.date(2020, 8, 1),  decimal.Decimal('0.24')),   # NOQA
        (datetime.date(2020, 9, 1),  decimal.Decimal('0.64')),  (datetime.date(2020, 10, 1), decimal.Decimal('0.86')),   # NOQA
        (datetime.date(2020, 11, 1), decimal.Decimal('0.89')),  (datetime.date(2020, 12, 1), decimal.Decimal('1.35')),   # NOQA
        (datetime.date(2021, 1, 1),  decimal.Decimal('0.25')),  (datetime.date(2021, 2, 1),  decimal.Decimal('0.86')),   # NOQA
        (datetime.date(2021, 3, 1),  decimal.Decimal('0.93')),  (datetime.date(2021, 4, 1),  decimal.Decimal('0.31')),   # NOQA
        (datetime.date(2021, 5, 1),  decimal.Decimal('0.83')),  (datetime.date(2021, 6, 1),  decimal.Decimal('0.53')),   # NOQA
        (datetime.date(2021, 7, 1),  decimal.Decimal('0.96')),  (datetime.date(2021, 8, 1),  decimal.Decimal('0.87')),   # NOQA
        (datetime.date(2021, 9, 1),  decimal.Decimal('1.16')),  (datetime.date(2021, 10, 1), decimal.Decimal('1.25')),   # NOQA
        (datetime.date(2021, 11, 1), decimal.Decimal('0.95')),  (datetime.date(2021, 12, 1), decimal.Decimal('0.73')),   # NOQA
        (datetime.date(2022, 1, 1),  decimal.Decimal('0.54')),  (datetime.date(2022, 2, 1),  decimal.Decimal('1.01')),   # NOQA
        (datetime.date(2022, 3, 1),  decimal.Decimal('1.62')),  (datetime.date(2022, 4, 1),  decimal.Decimal('1.06')),   # NOQA
        (datetime.date(2022, 5, 1),  decimal.Decimal('0.47')),  (datetime.date(2022, 6, 1),  decimal.Decimal('0.67')),   # NOQA
        (datetime.date(2022, 7, 1),  decimal.Decimal('-0.68')), (datetime.date(2022, 8, 1),  decimal.Decimal('-0.36')),  # NOQA
        (datetime.date(2022, 9, 1),  decimal.Decimal('-0.29')), (datetime.date(2022, 10, 1), decimal.Decimal('0.59')),   # NOQA
        (datetime.date(2022, 11, 1), decimal.Decimal('0.41')),  (datetime.date(2022, 12, 1), decimal.Decimal('0.62')),   # NOQA
        (datetime.date(2023, 1, 1), decimal.Decimal('0.53')),   (datetime.date(2023, 2, 1), decimal.Decimal('0.84')),    # NOQA
        (datetime.date(2023, 3, 1), decimal.Decimal('0.71')),   (datetime.date(2023, 4, 1), decimal.Decimal('0.61')),    # NOQA
        (datetime.date(2023, 5, 1), decimal.Decimal('0.23')),   (datetime.date(2023, 6, 1), decimal.Decimal('-0.08')),   # NOQA
        (datetime.date(2023, 7, 1), decimal.Decimal('0.12')),   (datetime.date(2023, 8, 1), decimal.Decimal('0.23')),    # NOQA
        (datetime.date(2023, 9, 1), decimal.Decimal('0.26')),   (datetime.date(2023, 10, 1), decimal.Decimal('0.24')),   # NOQA
        (datetime.date(2023, 11, 1), decimal.Decimal('0.28')),  (datetime.date(2023, 12, 1), decimal.Decimal('0.56')),   # NOQA
        (datetime.date(2024, 1, 1), decimal.Decimal('0.42')),   (datetime.date(2024, 2, 1), decimal.Decimal('0.83')),    # NOQA
        (datetime.date(2024, 3, 1), decimal.Decimal('0.16')),   (datetime.date(2024, 4, 1), decimal.Decimal('0.38')),    # NOQA
        (datetime.date(2024, 5, 1), decimal.Decimal('0.46')),   (datetime.date(2024, 6, 1), decimal.Decimal('0.21')),    # NOQA
        (datetime.date(2024, 7, 1), decimal.Decimal('0.38')),   (datetime.date(2024, 8, 1), decimal.Decimal('-0.02')),   # NOQA
        (datetime.date(2024, 9, 1), decimal.Decimal('0.44')),   (datetime.date(2024, 10, 1), decimal.Decimal('0.56')),   # NOQA
        (datetime.date(2024, 11, 1), decimal.Decimal('0.39')), (datetime.date(2024, 12, 1), decimal.Decimal('0.52')),   # NOQA
        (datetime.date(2025, 1, 1), decimal.Decimal('0.16')),  (datetime.date(2025, 2, 1), decimal.Decimal('1.31')),    # NOQA
        (datetime.date(2025, 3, 1), decimal.Decimal('0.56')),  (datetime.date(2025, 4, 1), decimal.Decimal('0.43')),    # NOQA
        (datetime.date(2025, 5, 1), decimal.Decimal('0.26')),  (datetime.date(2025, 6, 1), decimal.Decimal('0.24')),    # NOQA
        (datetime.date(2025, 7, 1), decimal.Decimal('0.26')),  (datetime.date(2025, 8, 1), decimal.Decimal('-0.11')),   # NOQA
        (datetime.date(2025, 9, 1), decimal.Decimal('0.48')),  (datetime.date(2025, 10, 1), decimal.Decimal('0.09')),   # NOQA
        (datetime.date(2025, 11, 1), decimal.Decimal('0.18')), (datetime.date(2025, 12, 1), decimal.Decimal('0.33')),   # NOQA
        (datetime.date(2026, 1, 1), decimal.Decimal('0.33')),  (datetime.date(2026, 2, 1), decimal.Decimal('0.70')),    # NOQA
        (datetime.date(2026, 3, 1), decimal.Decimal('0.88')),  (datetime.date(2026, 4, 1), decimal.Decimal('0.67')),    # NOQA
        (datetime.date(2026, 5, 1), decimal.Decimal('0.58')),  (datetime.date(2026, 6, 1), decimal.Decimal('0.16'))     # NOQA
    ]

class _UnpaddedIpcaBackend(_RicherIpcaBackend):
    '''
    A mesma memória de índices do backend acima, mas SEM completar a série com zeros.

    O "fincore.InMemoryBackend" completa a série até o fim da janela pedida, com meses zerados. Os backends de
    produção não completam: devolvem só o que o BACEN publicou. Ver "util.finmore.MongoDbNamespaceCache" e
    "util.finmore.LocalDirectoryBackend", no "web-services". Este backend reproduz o comportamento de produção, para
    que a biblioteca não possa depender do preenchimento. Ver "[RATIO-ULTIMO-ITEM]" em "fincore._pl_cumulative".
    '''

    def get_ipca_indexes(self, begin, end):
        for month, value in self._registry_ipca:
            if begin <= month <= end:
                yield fincore.MonthlyIndex(date=month, value=value)

# 🚩 Parametrizações inválidas. {{{
def test_wont_create_sched_1():
    with pytest.raises(TypeError, match=r"build_bullet\(\) missing 4 required positional arguments: 'principal', 'apy', 'zero_date', and 'term'"):
        fincore.build_bullet()  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_bullet\(\) missing 3 required positional arguments: 'apy', 'zero_date', and 'term'"):
        fincore.build_bullet(_1)  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_bullet\(\) missing 2 required positional arguments: 'zero_date' and 'term'"):
        fincore.build_bullet('', 1)  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_bullet\(\) missing 1 required positional argument: 'term'"):
        fincore.build_bullet('', 1, ())  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "principal" \(str\) is not an instance of decimal.Decimal'):
        next(fincore.build_bullet('', 1, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "apy" \(int\) is not an instance of decimal.Decimal'):
        next(fincore.build_bullet(_0, 1, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "zero_date" \(tuple\) is not an instance of datetime.date'):
        next(fincore.build_bullet(_0, _0, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "term" \(float\) is not an instance of int'):
        next(fincore.build_bullet(_0, _0, datetime.date.min, 9.9))  # pyright: ignore

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        next(fincore.build_bullet(_0, _0, datetime.date.min, -1))  # pyright: ignore

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        next(fincore.build_bullet(_0, _0, datetime.date.min, 0))  # pyright: ignore

    with pytest.raises(ValueError, match='invalid value for insertion entry #0 – should be positive'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 6, 1), value=decimal.Decimal(-5000))]

        next(fincore.build_bullet(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, must succeed "zero_date", \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2021, 12, 1), value=decimal.Decimal(5000))]

        next(fincore.build_bullet(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the regular payment date, \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))]

        next(fincore.build_bullet(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds "anniversary_date", \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['anniversary_date'] = datetime.date(2023, 1, 5)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))]

        next(fincore.build_bullet(**kwa))

    with pytest.raises(ValueError, match='the "anniversary_date", 2022-01-01, must be greater than "zero_date", 2022-01-01'):
        kwa = {}

        kwa['principal'] = decimal.Decimal('120000')
        kwa['apy'] = decimal.Decimal('12')
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['anniversary_date'] = datetime.date(2022, 1, 1)
        kwa['term'] = 12

        next(fincore.build_bullet(**kwa))

def test_wont_create_sched_2():
    with pytest.raises(TypeError, match=r"build_jm\(\) missing 4 required positional arguments: 'principal', 'apy', 'zero_date', and 'term'"):
        fincore.build_jm()  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_jm\(\) missing 3 required positional arguments: 'apy', 'zero_date', and 'term'"):
        fincore.build_jm(_1)  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_jm\(\) missing 2 required positional arguments: 'zero_date' and 'term'"):
        fincore.build_jm('', 1)  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_jm\(\) missing 1 required positional argument: 'term'"):
        fincore.build_jm('', 1, ())  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "principal" \(str\) is not an instance of decimal.Decimal'):
        next(fincore.build_jm('', 1, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "apy" \(int\) is not an instance of decimal.Decimal'):
        next(fincore.build_jm(_0, 1, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "zero_date" \(tuple\) is not an instance of datetime.date'):
        next(fincore.build_jm(_0, _0, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "term" \(float\) is not an instance of int'):
        next(fincore.build_jm(_0, _0, datetime.date.min, 9.9))  # pyright: ignore

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        next(fincore.build_jm(_0, _0, datetime.date.min, -1))

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        next(fincore.build_jm(_0, _0, datetime.date.min, 0))

    with pytest.raises(NotImplementedError, match='"Poupança" is currently unsupported'):
        kwa = {}

        kwa['principal'] = decimal.Decimal('222000')
        kwa['apy'] = decimal.Decimal('13.5')
        kwa['zero_date'] = datetime.date(2021, 7, 23)
        kwa['term'] = 9
        kwa['vir'] = fincore.VariableIndex('Poupança')

        next(fincore.build_jm(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, must succeed "zero_date", \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2021, 12, 1), value=decimal.Decimal(5000))]

        next(fincore.build_jm(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))]

        next(fincore.build_jm(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['anniversary_date'] = datetime.date(2022, 2, 5)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))]

        next(fincore.build_jm(**kwa))

    with pytest.raises(ValueError, match='the "anniversary_date", 2021-07-01, must be greater than "zero_date", 2021-07-01'):
        kwa = {}

        kwa['principal'] = decimal.Decimal('222000')
        kwa['apy'] = decimal.Decimal('13.5')
        kwa['zero_date'] = datetime.date(2021, 7, 1)
        kwa['anniversary_date'] = datetime.date(2021, 7, 1)
        kwa['term'] = 9

        next(fincore.build_jm(**kwa))

def test_wont_create_sched_3():
    with pytest.raises(TypeError, match=r"build_price\(\) missing 4 required positional arguments: 'principal', 'apy', 'zero_date', and 'term'"):
        fincore.build_price()  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_price\(\) missing 3 required positional arguments: 'apy', 'zero_date', and 'term'"):
        fincore.build_price(_1)  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_price\(\) missing 2 required positional arguments: 'zero_date' and 'term'"):
        fincore.build_price('', 1)  # pyright: ignore

    with pytest.raises(TypeError, match=r"build_price\(\) missing 1 required positional argument: 'term'"):
        fincore.build_price('', 1, ())  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "principal" \(str\) is not an instance of decimal.Decimal'):
        next(fincore.build_price('', 1, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "apy" \(int\) is not an instance of decimal.Decimal'):
        next(fincore.build_price(_0, 1, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "zero_date" \(tuple\) is not an instance of datetime.date'):
        next(fincore.build_price(_0, _0, (), 9.9))  # pyright: ignore

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "term" \(float\) is not an instance of int'):
        next(fincore.build_price(_0, _0, datetime.date.min, 9.9))  # pyright: ignore

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        next(fincore.build_price(_0, _0, datetime.date.min, -1))  # pyright: ignore

    with pytest.raises(ValueError, match='"term" must be a greater than, or equal to, one'):
        next(fincore.build_price(_0, _0, datetime.date.min, 0))  # pyright: ignore

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, must succeed "zero_date", \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2021, 12, 1), value=decimal.Decimal(5000))]

        next(fincore.build_price(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))]

        next(fincore.build_price(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = _1
        kwa['apy'] = _1
        kwa['zero_date'] = datetime.date(2022, 1, 1)
        kwa['anniversary_date'] = datetime.date(2022, 2, 5)
        kwa['term'] = 12
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))]

        next(fincore.build_price(**kwa))

    with pytest.raises(ValueError, match='the "anniversary_date", 2021-07-01, must be greater than "zero_date", 2021-07-01'):
        kwa = {}

        kwa['principal'] = decimal.Decimal('222000')
        kwa['apy'] = decimal.Decimal('13.5')
        kwa['zero_date'] = datetime.date(2021, 7, 1)
        kwa['anniversary_date'] = datetime.date(2021, 7, 1)
        kwa['term'] = 9

        next(fincore.build_price(**kwa))

def test_wont_create_sched_4():
    with pytest.raises(ValueError, match='at least two amortizations are required: the start of the schedule, and its end'):
        kwa = {}

        kwa['principal'] = decimal.Decimal('222000')
        kwa['apy'] = decimal.Decimal('13.5')
        kwa['amortizations'] = tab = []

        next(fincore.build(**kwa))

    with pytest.raises(TypeError, match="amortization 1 has price level adjustment, but a variable index wasn't provided, or isn't IPCA nor IGPM"):
        kwa = {}

        kwa['principal'] = decimal.Decimal('222000')
        kwa['apy'] = decimal.Decimal('13.5')
        kwa['vir'] = fincore.VariableIndex('CDI')
        kwa['amortizations'] = tab = []

        # Monta a tabela de amortizações.
        tab.append(fincore.Amortization(date=datetime.date(2022, 2, 1), amortizes_interest=False))
        tab.append(fincore.Amortization(date=datetime.date(2022, 3, 1)))

        tab[-1].price_level_adjustment = fincore.PriceLevelAdjustment(code='IPCA', base_date=datetime.date(2018, 5, 1), period=1)

        next(fincore.build(**kwa))

    with pytest.raises(ValueError, match='invalid value for insertion entry #0 – should be positive'):
        kwa = {}

        kwa['principal'] = kwa['apy'] = _1
        kwa['amortizations'] = tab = []

        # Monta a tabela de amortizações.
        tab.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))

        for i in range(1, 13):
            tab.append(fincore.Amortization(date=tab[0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.08333333333333')))

        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 6, 1), value=decimal.Decimal(-5000))]

        next(fincore.build(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, must succeed "zero_date", \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['principal'] = kwa['apy'] = _1
        kwa['amortizations'] = tab = []

        # Monta a tabela de amortizações.
        tab.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))

        for i in range(1, 13):
            tab.append(fincore.Amortization(date=tab[0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.08333333333333')))

        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2021, 12, 1), value=decimal.Decimal(5000))]

        next(fincore.build(**kwa))

    with pytest.raises(ValueError, match=r'"insertions\[\d+\].date", \d{4}-\d{2}-\d{2}, succeeds the last regular payment date, \d{4}-\d{2}-\d{2}'):
        kwa = {}

        kwa['apy'] = kwa['principal'] = _1
        kwa['amortizations'] = tab = []

        # Monta a tabela de amortizações.
        tab.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))

        for i in range(1, 13):
            tab.append(fincore.Amortization(date=tab[0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.08333333333333')))

        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 1, 10), value=decimal.Decimal(5000))]

        next(fincore.build(**kwa))

    with pytest.raises(NotImplementedError, match='"Poupança" is currently unsupported'):
        kwa = {}

        kwa['principal'] = decimal.Decimal('750000')
        kwa['apy'] = decimal.Decimal('50')
        kwa['vir'] = fincore.VariableIndex('Poupança')
        kwa['amortizations'] = tab1 = []

        # Monta a tabela de amortizações.
        tab1.append(fincore.Amortization(date=datetime.date(2020, 2, 20), amortization_ratio=decimal.Decimal('0.25')))
        tab1.append(fincore.Amortization(date=datetime.date(2020, 3, 15), amortization_ratio=decimal.Decimal('0.25')))
        tab1.append(fincore.Amortization(date=datetime.date(2020, 4, 15), amortization_ratio=decimal.Decimal('0.25')))
        tab1.append(fincore.Amortization(date=datetime.date(2020, 5, 15), amortization_ratio=decimal.Decimal('0.25')))

        next(fincore.build(**kwa))

    with pytest.raises(ValueError, match='amortization dates must be unique'):
        kwa = {}

        kwa['principal'] = decimal.Decimal('222000')
        kwa['apy'] = decimal.Decimal('13.5')
        kwa['amortizations'] = tab1 = []

        # Monta a tabela de amortizações.
        tab1.append(fincore.Amortization(date=datetime.date(2020, 3, 15), amortization_ratio=decimal.Decimal('0.25')))
        tab1.append(fincore.Amortization(date=datetime.date(2020, 4, 15), amortization_ratio=decimal.Decimal('0.25')))
        tab1.append(fincore.Amortization(date=datetime.date(2020, 4, 15), amortization_ratio=decimal.Decimal('0.25')))
        tab1.append(fincore.Amortization(date=datetime.date(2020, 5, 15), amortization_ratio=decimal.Decimal('0.25')))

        next(fincore.build(**kwa))

    with pytest.raises(ValueError, match='the accumulated percentage of the amortizations does not reach 1.0'):
        kwa = {}

        kwa['principal'] = decimal.Decimal('222000')
        kwa['apy'] = decimal.Decimal('13.5')
        kwa['amortizations'] = tab = []

        # Monta a tabela de amortizações.
        tab.append(fincore.Amortization(date=datetime.date(2020, 2, 1), amortizes_interest=False))
        tab.append(fincore.Amortization(date=datetime.date(2020, 3, 1)))

        next(fincore.build(**kwa))

def test_wont_create_sched_5():
    '''Fincore deve falhar ao criar um empréstimo com principal maior que zero e menor que R$ 0,01.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    with pytest.raises(ValueError, match='principal value should be at least 0.01'):
        next(fincore.get_payments_table(_CENTI / 2, _0, [ent0, ent1]))

def test_wont_create_sched_6():
    '''Fincore deve falhar ao criar um empréstimo sem um cronograma de amortizações.'''

    with pytest.raises(ValueError, match='at least two amortizations are required: the start of the schedule, and its end'):
        next(fincore.get_payments_table(_1, _0, []))

def test_wont_create_sched_7():
    '''Fincore deve falhar ao criar um empréstimo sem indexador e com base 252.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    with pytest.raises(ValueError, match='fixed interest rates should not use the 252 working days capitalisation'):
        next(fincore.get_payments_table(_1, _0, [ent0, ent1], capitalisation='252'))

def test_wont_create_sched_8():
    '''Fincore deve falhar ao criar um empréstimo com indexador CDI e base diferente de 252.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    with pytest.raises(ValueError, match='CDI should use the 252 working days capitalisation'):
        next(fincore.get_payments_table(_1, _0, [ent0, ent1], vir=fincore.VariableIndex('CDI'), capitalisation='360'))

def test_wont_create_sched_9():
    '''Fincore deve falhar ao criar um empréstimo sem indexador IPCA/IGPM e com PLA na amortização.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    ent1.price_level_adjustment = fincore.PriceLevelAdjustment(code='IPCA', base_date=datetime.date(2018, 5, 1), period=1)

    with pytest.raises(TypeError, match="amortization 1 has price level adjustment, but either a variable index wasn't provided or it isn't IPCA nor IGPM"):
        next(fincore.get_payments_table(_1, _0, [ent0, ent1], vir=fincore.VariableIndex('CDI'), capitalisation='252'))

def test_wont_create_sched_10():
    '''Fincore deve falhar ao criar um empréstimo cujo percentual de amortização acumulado ultrapassa 1.0.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortization_ratio=_1 + _1, amortizes_interest=True)

    with pytest.raises(ValueError, match='the accumulated percentage of the amortizations overflows 1.0'):
        next(fincore.get_payments_table(_1, _0, [ent0, ent1]))

def test_wont_create_sched_11():
    '''Fincore deve falhar ao criar um empréstimo cujo percentual de amortização acumulado seja menor que 1.0.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    with pytest.raises(ValueError, match='the accumulated percentage of the amortizations does not reach 1.0'):
        next(fincore.get_payments_table(_1, _0, [ent0, ent1]))

def test_wont_create_sched_12():
    '''Fincore deve falhar ao criar um empréstimo com antecipação maior do que o saldo devedor.'''

    kwa = {}

    kwa['principal'] = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('5')

    kwa['amortizations'] = []
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2020, 1, 1), amortizes_interest=False))
    kwa['amortizations'].append(fincore.Amortization.Bare(date=datetime.date(2020, 6, 1), value=decimal.Decimal('150000')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2021, 1, 1), amortization_ratio=decimal.Decimal(1), amortizes_interest=True))

    with pytest.raises(Exception, match='the value of the amortization, 150000, is greater than the remaining balance of the loan, 102081.39'):
        next(fincore.get_payments_table(**kwa))
# }}}

# 🎈 Bullets. {{{
def test_will_create_bullet_pre360_1():
    '''
    Operação pré-fixada modalidade Bullet.

    Ref File: https://docs.google.com/spreadsheets/d/1ijJLZYP8BnuENPrTLFlfdqbiSx8Gs7wtO7T85cgkLgM
    Tab.....: Hipotética 01
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('120000')
    kwa['apy'] = decimal.Decimal('12')
    kwa['zero_date'] = datetime.date(2022, 1, 1)
    kwa['term'] = 12

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == datetime.date(2023, 1, 1)
        assert x.amort == decimal.Decimal('120000')
        assert x.gain == decimal.Decimal('14611.71')
        assert x.raw == decimal.Decimal('134611.71')
        assert x.tax == decimal.Decimal('2557.05')
        assert x.net == decimal.Decimal('132054.66')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_pre360_2():
    '''
    Operação pré-fixada modalidade Bullet com aniversário.

    Ref File: https://docs.google.com/spreadsheets/d/1ijJLZYP8BnuENPrTLFlfdqbiSx8Gs7wtO7T85cgkLgM
    Tab.....: Hipotética 02 - Aniversário
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['zero_date'] = datetime.date(2025, 1, 1)
    kwa['anniversary_date'] = datetime.date(2029, 1, 10)
    kwa['term'] = 48

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == kwa['anniversary_date']
        assert x.amort == decimal.Decimal('1000')
        assert x.gain == decimal.Decimal('1252.35')
        assert x.raw == decimal.Decimal('2252.35')
        assert x.tax == decimal.Decimal('187.85')
        assert x.net == decimal.Decimal('2064.5')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_pre360_3():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1ijJLZYP8BnuENPrTLFlfdqbiSx8Gs7wtO7T85cgkLgM
    Tab.....: Hipotética 03 - Aniversário e Antecipação Parcial
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('125000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['zero_date'] = datetime.date(2025, 1, 1)
    kwa['anniversary_date'] = datetime.date(2029, 1, 10)
    kwa['term'] = 48
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2027, 1, 25), value=decimal.Decimal('127077.1'))]

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == i

        if i == 1:
            assert x.date == kwa['insertions'][0].date
            assert x.amort == decimal.Decimal('62500')
            assert x.gain == decimal.Decimal('64577.1')
            assert x.raw == decimal.Decimal('127077.1')
            assert x.tax == decimal.Decimal('9686.57')
            assert x.net == decimal.Decimal('117390.53')
            assert x.bal == decimal.Decimal('62500')

        else:
            assert x.date == kwa['anniversary_date']
            assert x.amort == decimal.Decimal('62500')
            assert x.gain == decimal.Decimal('30319.69')
            assert x.raw == decimal.Decimal('92819.70')
            assert x.tax == decimal.Decimal('4547.95')
            assert x.net == decimal.Decimal('88271.75')
            assert x.bal == _0

    assert i == 2

def test_will_create_bullet_pre360_4():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1ijJLZYP8BnuENPrTLFlfdqbiSx8Gs7wtO7T85cgkLgM
    Tab.....: Hipotética 04 - Aniversário e Antecipação Total
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('125000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['zero_date'] = datetime.date(2025, 1, 1)
    kwa['anniversary_date'] = datetime.date(2029, 1, 5)
    kwa['term'] = 48
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2027, 1, 25), value=decimal.Decimal('189577.1'))]

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['insertions'][0].date
        assert x.raw == decimal.Decimal('189577.1')
        assert x.tax == decimal.Decimal('9686.57')
        assert x.net == decimal.Decimal('179890.53')
        assert x.gain == decimal.Decimal('64577.1')
        assert x.amort == decimal.Decimal('125000')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_pre365_1(caplog):
    '''
    Operação pré-fixada modalidade Bullet legada (com SPEC 365).

    Ref File: https://docs.google.com/spreadsheets/d/1ijJLZYP8BnuENPrTLFlfdqbiSx8Gs7wtO7T85cgkLgM
    Tab.....: Felicidade Residencial Clube
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('10000')
    kwa['apy'] = decimal.Decimal('13.5')
    kwa['zero_date'] = datetime.date(2021, 7, 23)
    kwa['term'] = 9
    kwa['capitalisation'] = '365'

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == datetime.date(2022, 4, 23)
        assert x.amort == decimal.Decimal('10000')
        assert x.gain == decimal.Decimal('997.26')
        assert x.raw == decimal.Decimal('10997.26')
        assert x.tax == decimal.Decimal('199.45')
        assert x.net == decimal.Decimal('10797.81')
        assert x.bal == _0

    assert i == 1

    assert caplog.record_tuples == [('fincore', logging.WARNING, 'capitalising 365 days per year exists solely for legacy Bullet support – prefer 360 days')]

    caplog.clear()

def test_will_create_bullet_pre365_2(caplog):
    '''
    Operação pré-fixada modalidade Bullet legada (com SPEC 365).

    Ref File: https://docs.google.com/spreadsheets/d/1ijJLZYP8BnuENPrTLFlfdqbiSx8Gs7wtO7T85cgkLgM
    Tab.....: Villa VIC Pisa
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('18.5')
    kwa['zero_date'] = datetime.date(2022, 3, 9)
    kwa['term'] = 12
    kwa['capitalisation'] = '365'

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == datetime.date(2023, 3, 9)
        assert x.amort == decimal.Decimal('100000')
        assert x.gain == decimal.Decimal('18500')
        assert x.raw == decimal.Decimal('118500')
        assert x.tax == decimal.Decimal('3237.5')
        assert x.net == decimal.Decimal('115262.5')
        assert x.bal == _0

    assert i == 1

    assert caplog.record_tuples == [('fincore', logging.WARNING, 'capitalising 365 days per year exists solely for legacy Bullet support – prefer 360 days')]

    caplog.clear()

def test_will_create_bullet_cdi_1():
    '''
    Operação pós-fixada CDI, modalidade Bullet.

    Carteira Pride - Tranche X - Bullet - 3 meses

    Ref File: https://docs.google.com/spreadsheets/d/1z0PhJcLK-noG-rH-t24NcdPQJZJ1-B0P0b0o4muv3rY
    Tab.....: 14
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('500000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['zero_date'] = datetime.date(2022, 8, 22)
    kwa['term'] = 3
    kwa['vir'] = fincore.VariableIndex(code='CDI')

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == datetime.date(2022, 11, 22)
        assert x.amort == decimal.Decimal('500000')
        assert x.gain == decimal.Decimal('23441.18')
        assert x.raw == decimal.Decimal('523441.18')
        assert x.tax == decimal.Decimal('5274.27')
        assert x.net == decimal.Decimal('518166.91')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_cdi_2():
    '''
    Operação pós-fixada CDI, modalidade Bullet.

    Carteira Pride - Tranche XIV - 27 meses - Pride

    Ref File: https://docs.google.com/spreadsheets/d/1z0PhJcLK-noG-rH-t24NcdPQJZJ1-B0P0b0o4muv3rY
    Tab.....: 31
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('200000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['zero_date'] = datetime.date(2022, 10, 31)
    kwa['term'] = 27
    kwa['vir'] = fincore.VariableIndex(code='CDI')

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == datetime.date(2025, 1, 31)
        assert x.amort == decimal.Decimal('200000')
        assert x.gain == decimal.Decimal('97090.16')
        assert x.raw == decimal.Decimal('297090.16')
        assert x.tax == decimal.Decimal('14563.52')
        assert x.net == decimal.Decimal('282526.64')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_cdi_3():
    '''
    Operação pós-fixada CDI, modalidade Bullet.

    Ágata - Bullet, ID "HpVcJYvhUSrRDLqQVWKaN". A operação teve um pagamento parcial no dia do seu vencimento,
    28/06/2023, no valor bruto de R$ 650.323,76. O valor remanescente do empréstimo foi pago um mês depois, em atraso,
    no dia 28/07/2023.

    Essa operação teve mais de um erro no segundo pagamento. O primeiro problema foi que apenas os juros foram pagos, a
    amortização do principal não. Isso foi corrigido pela migração 32, revisão “735ea22b58a”. O segundo problema foi
    que o sistema não cobrou a multa devida. Mais uma migração teve que ser elaborada. Na data de escrita desse caso
    de teste, ainda não estava pronta.

    Dada a complexidade da operação, que além de pós-fixada entrou em default e teve dois pagamentos parciais, o
    primeiro na data prevista, acabei elaborando duas planilhas para validá-la, e suportar os casos de teste.

    Ref File: https://docs.google.com/spreadsheets/d/1PpLL9ETtng9mfCWQbSWNnszoCfDd1MFAuKIrcHehwFE
    Tab.....: Ágata

    Ref File: https://docs.google.com/spreadsheets/d/1WEqqUWzJ5Pq_E1xNNjGDuUmwElDTN7MjsOGmjqLZZMU
    Tab.....: BULLET CDI - Ágata

    Sei que cada caso de teste deve ter um propósito específico, mas esse tem dois.

      1. Validar que o pagamento parcial no dia final do cronograma foi calculado corretamente, e validar os valores
      remanescentes do segundo pagamento.

      2. Validar que o pagamento em atraso, no dia 28/07/2023, tem todos os valores corretos. Ou seja, essa rotina é
      também um teste de atraso.
    '''

    kwa = {}

    # Test 1. Given.
    kwa['principal'] = decimal.Decimal('1000000')
    kwa['apy'] = decimal.Decimal('6.33')
    kwa['zero_date'] = datetime.date(2021, 12, 28)
    kwa['term'] = 18
    kwa['vir'] = fincore.VariableIndex(code='CDI')

    # Observe pela documentação desse caso de teste que o primeiro pagamento dessa operação foi parcial.
    # No Fincore, modela-se com uma inserção (“Amortization.Bare”). Inserções normalmente são usadas para antecipações
    # nos sistemas da INCO. Então, para os atentos, isso é contra-intuitivo. Um pagamento parcial no dia do vencimento
    # da operação indica que o restante do montante vai atrasar. Difícil enxergar essa situação como uma antecipação.
    #
    # Mas para o Fincore isso não faz diferença. A inserção é apenas uma entrada anormal em um cronograma de pagamento,
    # pode ocorrer no mesmo dia de um pagamento ordinário, e tem prioridade sobre ele. Ou seja, semanticamente serve
    # para representar uma antecipação total, parcial, ou mesmo um pagamento parcial, contanto que seja na data final
    # do cronograma previsto. Pagamentos parciais em atraso não podem ser modelados via inserções.
    #
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 6, 28), value=decimal.Decimal('650323.76'))]

    # Test 1. When & then.
    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        if x.no == 1:
            assert x.no == 1
            assert x.date == datetime.date(2023, 6, 28)
            assert x.gain == decimal.Decimal('311563.55')
            assert x.amort == decimal.Decimal('338760.21')
            assert x.raw == decimal.Decimal('650323.76')
            assert x.tax == decimal.Decimal('54523.62')
            assert x.net == decimal.Decimal('595800.14')
            assert x.bal == decimal.Decimal('661239.79')

        else:
            assert x.no == 2
            assert x.date == datetime.date(2023, 6, 28)
            assert x.gain == _0
            assert x.amort == decimal.Decimal('661239.79')
            assert x.raw == decimal.Decimal('661239.79')
            assert x.tax == _0
            assert x.net == decimal.Decimal('661239.79')
            assert x.bal == _0

    assert i == 2

    # Test 2. Late payment. Given.
    kwa = {}

    kwa['in_pmt'] = fincore.LatePayment()
    kwa['in_pmt'].no = x.no
    kwa['in_pmt'].date = x.date
    kwa['in_pmt'].amort = x.amort
    kwa['in_pmt'].gain = x.gain
    kwa['in_pmt'].raw = x.raw
    kwa['in_pmt'].bal = x.bal

    kwa['calc_date'] = datetime.date(2023, 7, 28)
    kwa['apy'] = decimal.Decimal('6.33')
    kwa['zero_date'] = datetime.date(2021, 12, 28)
    kwa['vir'] = fincore.VariableIndex('CDI')

    # Test 2. When.
    out = fincore.get_late_payment(**kwa)

    # Test 2. Then.
    assert out.no == x.no == 2
    assert out.date == kwa['calc_date']

    assert out.gain == _0
    assert out.extra_gain == decimal.Decimal('11020.36')
    assert out.penalty == decimal.Decimal('6722.6')
    assert out.fine == decimal.Decimal('13579.66')

    assert out.amort == x.amort

    assert out.raw == decimal.Decimal('692562.41')
    assert out.tax == decimal.Decimal('5481.46')
    assert out.net == decimal.Decimal('687080.95')
    assert out.bal == x.bal == _0

def test_will_create_bullet_cdi_4():
    '''
    Operação pós-fixada CDI, modalidade Bullet com aniversário.

    Ref File: https://docs.google.com/spreadsheets/d/1PpLL9ETtng9mfCWQbSWNnszoCfDd1MFAuKIrcHehwFE
    Tab.....: Hipotética CDI c/ Aniv.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('500000')
    kwa['apy'] = decimal.Decimal('6.33')
    kwa['zero_date'] = datetime.date(2021, 12, 28)
    kwa['anniversary_date'] = datetime.date(2023, 7, 14)
    kwa['term'] = 18
    kwa['vir'] = fincore.VariableIndex(code='CDI')

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == kwa['anniversary_date']
        assert x.amort == decimal.Decimal('500000.00')
        assert x.gain == decimal.Decimal('161720.87')
        assert x.raw == decimal.Decimal('661720.87')
        assert x.tax == decimal.Decimal('28301.15')
        assert x.net == decimal.Decimal('633419.72')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_cdi_5():
    '''
    Operação pós-fixada CDI, modalidade Bullet com antecipação total.

    Ref File: https://docs.google.com/spreadsheets/d/1PpLL9ETtng9mfCWQbSWNnszoCfDd1MFAuKIrcHehwFE
    Tab.....: Hipotética CDI c/ AT.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('500000')
    kwa['apy'] = decimal.Decimal('6.33')
    kwa['zero_date'] = datetime.date(2021, 12, 28)
    kwa['term'] = 18
    kwa['vir'] = fincore.VariableIndex(code='CDI')
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 12, 28), value=decimal.Decimal('597446.91'))]

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == kwa['insertions'][0].date
        assert x.amort == decimal.Decimal('500000.00')
        assert x.gain == decimal.Decimal('97446.91')
        assert x.raw == decimal.Decimal('597446.91')
        assert x.tax == decimal.Decimal('17053.21')
        assert x.net == decimal.Decimal('580393.70')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_ipca_1a():
    '''
    Operação pós-fixada IPCA, modalidade Bullet.

    Bossa Nova CCB 7

    Ref File: https://docs.google.com/spreadsheets/d/1PpLL9ETtng9mfCWQbSWNnszoCfDd1MFAuKIrcHehwFE
    Tab.....: Bossa Nova CCB 7
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('176000')
    kwa['apy'] = _0
    kwa['zero_date'] = datetime.date(2022, 10, 24)
    kwa['term'] = 120
    kwa['vir'] = fincore.VariableIndex('IPCA')

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        x = t.cast(fincore.PriceAdjustedPayment, x)

        assert x.no == 1
        assert x.date == datetime.date(2032, 10, 24)
        assert x.amort == decimal.Decimal('176000')
        assert x.gain == _0
        assert x.pla == decimal.Decimal('17510.84')
        assert x.raw == decimal.Decimal('193510.84')
        assert x.tax == decimal.Decimal('2626.63')
        assert x.net == decimal.Decimal('190884.21')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_ipca_1b():
    '''
    Operação pós-fixada IPCA, modalidade Bullet (com data de cálculo).

    Bossa Nova CCB 7

    Ref File: https://docs.google.com/spreadsheets/d/1PpLL9ETtng9mfCWQbSWNnszoCfDd1MFAuKIrcHehwFE
    Tab.....: Bossa Nova CCB 7
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('176000')
    kwa['apy'] = _0
    kwa['zero_date'] = datetime.date(2022, 10, 24)
    kwa['term'] = 120
    kwa['vir'] = fincore.VariableIndex('IPCA')
    kwa['calc_date'] = fincore.CalcDate(value=datetime.date(2022, 12, 1))

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        x = t.cast(fincore.PriceAdjustedPayment, x)

        assert x.no == 1
        assert x.date == datetime.date(2032, 10, 24)
        assert x.amort == decimal.Decimal('176000')
        assert x.gain == _0
        assert x.pla == decimal.Decimal('1038.40')
        assert x.raw == decimal.Decimal('177038.40')
        assert x.tax == decimal.Decimal('233.64')
        assert x.net == decimal.Decimal('176804.76')
        assert x.bal == _0

    assert i == 1

def test_will_create_bullet_ipca_1c():
    '''
    Operação pós-fixada IPCA, modalidade Bullet c/ antecipação parcial.

    Ref File: https://docs.google.com/spreadsheets/d/1PpLL9ETtng9mfCWQbSWNnszoCfDd1MFAuKIrcHehwFE
    Tab.....: Hipotética c/ AP
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('176000')
    kwa['apy'] = _0
    kwa['zero_date'] = datetime.date(2022, 10, 24)
    kwa['term'] = 120
    kwa['vir'] = fincore.VariableIndex('IPCA')
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 11, 24), value=decimal.Decimal(17600))]

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        x = t.cast(fincore.PriceAdjustedPayment, x)

        if x.no == 1:
            assert x.date == kwa['insertions'][0].date
            assert x.amort == decimal.Decimal('17600')
            assert x.gain == x.pla == _0
            assert x.raw == x.net == decimal.Decimal('17600')
            assert x.tax == _0
            assert x.bal == decimal.Decimal('158400')

        else:
            assert x.date == datetime.date(2032, 10, 24)
            assert x.amort == decimal.Decimal('158400')
            assert x.gain == _0
            assert x.pla == decimal.Decimal('15759.75')
            assert x.raw == decimal.Decimal('174159.75')
            assert x.tax == decimal.Decimal('2363.96')
            assert x.net == decimal.Decimal('171795.79')
            assert x.bal == _0

    assert i == 2
# }}}

# 🎭 Bullets vandalizadas. {{{
#
# Operações modalidade Bullet, bizarras.
#
@pytest.mark.parametrize('term', [1, 3, 6, 12, 60])
def test_will_create_bullet_zanzy_1(term):
    '''
    Cria cronogramas para operação Bullet com principal zero, taxa zero.

    Cinco prazos são parametrizados.
    '''

    assert len(list(fincore.build_bullet(_0, _0, datetime.date.min, term))) == 0

    for i, x in enumerate(fincore.build_bullet(_1, _0, datetime.date.min, term), 1):
        assert x.no == 1
        assert x.date == datetime.date(term // 12 + 1, term % 12 + 1, 1)
        assert x.amort == _1
        assert x.gain == _0
        assert x.raw == _1
        assert x.tax == _0
        assert x.net == _1
        assert x.bal == _0

    assert i == 1

    for i, x in enumerate(fincore.build_bullet(_0, _1, datetime.date.min, term), 1):
        assert x.no == 1
        assert x.date == datetime.date(term // 12 + 1, term % 12 + 1, 1)
        assert x.raw == x.tax == x.net == x.gain == x.amort == x.bal == _0

    assert i == 1

    for i, x in enumerate(fincore.build_bullet(_1, _1, datetime.date.min, term), 1):
        if term == 1 or term == 3:
            assert x.no == 1
            assert x.date == datetime.date(term // 12 + 1, term % 12 + 1, 1)
            assert x.amort == _1
            assert x.gain == _0
            assert x.raw == _1
            assert x.tax == _0
            assert x.net == _1
            assert x.bal == _0

        elif term == 6:
            assert x.no == 1
            assert x.date == datetime.date(term // 12 + 1, term % 12 + 1, 1)
            assert x.amort == _1
            assert x.gain == decimal.Decimal('0.01')
            assert x.raw == decimal.Decimal('1.01')
            assert x.tax == _0
            assert x.net == decimal.Decimal('1.01')
            assert x.bal == _0

        elif term == 12:
            assert x.no == 1
            assert x.date == datetime.date(term // 12 + 1, term % 12 + 1, 1)
            assert x.amort == _1
            assert x.gain == decimal.Decimal('0.01')
            assert x.raw == decimal.Decimal('1.01')
            assert x.tax == _0
            assert x.net == decimal.Decimal('1.01')
            assert x.bal == _0

        else:
            assert x.no == 1
            assert x.date == datetime.date(term // 12 + 1, term % 12 + 1, 1)
            assert x.amort == _1
            assert x.gain == decimal.Decimal('0.05')
            assert x.raw == decimal.Decimal('1.05')
            assert x.tax == decimal.Decimal('0.01')
            assert x.net == decimal.Decimal('1.04')
            assert x.bal == _0

    assert i == 1

def test_will_create_bullet_zanzy_2():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1ijJLZYP8BnuENPrTLFlfdqbiSx8Gs7wtO7T85cgkLgM
    Tab.....: Absurda 01 - Taxa Negativa
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('10000')
    kwa['apy'] = decimal.Decimal('-13.5')
    kwa['zero_date'] = datetime.date(2021, 7, 23)
    kwa['term'] = 9
    kwa['capitalisation'] = '365'

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == datetime.date(2022, 4, 23)
        assert x.amort == decimal.Decimal('10000')
        assert x.gain == decimal.Decimal('-1031.52')
        assert x.raw == decimal.Decimal('8968.48')
        assert x.tax == decimal.Decimal('-206.3')
        assert x.net == decimal.Decimal('9174.78')
        assert x.bal == _0

    assert i == 1

def test_will_warn_about_bullet_365(caplog):
    next(fincore.build_bullet(_1, _0, datetime.date(2018, 1, 1), 10, capitalisation='365'))

    assert caplog.record_tuples == [('fincore', logging.WARNING, 'capitalising 365 days per year exists solely for legacy Bullet support – prefer 360 days')]
# }}}

# US Juros Mensais. {{{
#
def test_will_create_jm_pre_1():
    '''
    Operação pré-fixada modalidade Juros Mensais.

    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Felicidade Residencial Clube
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('222000')
    kwa['apy'] = decimal.Decimal('13.5')
    kwa['zero_date'] = datetime.date(2021, 7, 23)
    kwa['term'] = 9

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['zero_date'] + _MONTH * i

        if x.no <= 5:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('2355.11')
            assert x.tax == decimal.Decimal('529.9')
            assert x.net == decimal.Decimal('1825.21')
            assert x.bal == decimal.Decimal('222000')

        elif x.no <= 8:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('2355.11')
            assert x.tax == decimal.Decimal('471.02')
            assert x.net == decimal.Decimal('1884.09')
            assert x.bal == decimal.Decimal('222000')

        else:
            assert x.amort == decimal.Decimal('222000')
            assert x.gain == decimal.Decimal('2355.11')
            assert x.raw == decimal.Decimal('224355.11')
            assert x.tax == decimal.Decimal('471.02')
            assert x.net == decimal.Decimal('223884.09')
            assert x.bal == _0

    assert i == kwa['term']

def test_will_create_jm_pre_2():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Villa VIC Pisa
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('890500')
    kwa['apy'] = decimal.Decimal('18.5')
    kwa['zero_date'] = datetime.date(2022, 3, 9)
    kwa['term'] = 12

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['zero_date'] + _MONTH * i

        if x.no <= 5:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('12685.84')
            assert x.tax == decimal.Decimal('2854.31')
            assert x.net == decimal.Decimal('9831.53')
            assert x.bal == decimal.Decimal('890500')

        elif x.no <= 11:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('12685.84')
            assert x.tax == decimal.Decimal('2537.17')
            assert x.net == decimal.Decimal('10148.67')
            assert x.bal == decimal.Decimal('890500')

        else:
            assert x.amort == decimal.Decimal('890500')
            assert x.gain == decimal.Decimal('12685.84')
            assert x.raw == decimal.Decimal('903185.84')
            assert x.tax == decimal.Decimal('2220.02')
            assert x.net == decimal.Decimal('900965.82')
            assert x.bal == _0

    assert i == kwa['term']

def test_will_create_jm_pre_3():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Hipotética 01 - Aniversário
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1000000')
    kwa['apy'] = decimal.Decimal('18.5')
    kwa['zero_date'] = datetime.date(2022, 3, 9)
    kwa['anniversary_date'] = datetime.date(2022, 3, 23)
    kwa['term'] = 36

    for i, x in enumerate(fincore.build_jm(**kwa)):
        assert x.no == i + 1
        assert x.date == kwa['anniversary_date'] + _MONTH * i

        if x.no == 1:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('7097.69')
            assert x.tax == decimal.Decimal('1596.98')
            assert x.net == decimal.Decimal('5500.71')
            assert x.bal == decimal.Decimal('1000000')

        elif x.no <= 6:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('14245.75')
            assert x.tax == decimal.Decimal('3205.29')
            assert x.net == decimal.Decimal('11040.46')
            assert x.bal == decimal.Decimal('1000000')

        elif x.no <= 12:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('14245.75')
            assert x.tax == decimal.Decimal('2849.15')
            assert x.net == decimal.Decimal('11396.6')
            assert x.bal == decimal.Decimal('1000000')

        elif x.no <= 24:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('14245.75')
            assert x.tax == decimal.Decimal('2493.01')
            assert x.net == decimal.Decimal('11752.74')
            assert x.bal == decimal.Decimal('1000000')

        elif x.no <= 35:
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('14245.75')
            assert x.tax == decimal.Decimal('2136.86')
            assert x.net == decimal.Decimal('12108.89')
            assert x.bal == decimal.Decimal('1000000')

        else:
            assert x.amort == decimal.Decimal('1000000')
            assert x.gain == decimal.Decimal('14245.75')
            assert x.raw == decimal.Decimal('1014245.75')
            assert x.tax == decimal.Decimal('2136.86')
            assert x.net == decimal.Decimal('1012108.89')
            assert x.bal == _0

    assert i + 1 == kwa['term']

def test_will_create_jm_pre_4():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Hipotética 02 - Antecipação Total
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1861200')
    kwa['apy'] = decimal.Decimal('21')
    kwa['zero_date'] = datetime.date(2015, 1, 9)
    kwa['term'] = 24
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2016, 1, 8), value=decimal.Decimal('1890032.55'))]

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if i <= 5:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('6705.29')
            assert x.net == decimal.Decimal('23096')
            assert x.bal == decimal.Decimal('1861200')

        elif i <= 11:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('5960.26')
            assert x.net == decimal.Decimal('23841.03')
            assert x.bal == decimal.Decimal('1861200')

        # Antecipação total.
        else:
            assert x.amort == decimal.Decimal('1861200')
            assert x.gain == decimal.Decimal('28832.55')
            assert x.date == kwa['insertions'][0].date
            assert x.raw == decimal.Decimal('1890032.55')
            assert x.tax == decimal.Decimal('5045.7')
            assert x.net == decimal.Decimal('1884986.85')
            assert x.bal == _0

    assert i == 12

def test_will_create_jm_pre_5():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Hipotética 03 - Antecipação Total
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1861200')
    kwa['apy'] = decimal.Decimal('21')
    kwa['zero_date'] = datetime.date(2015, 1, 9)
    kwa['term'] = 24
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2016, 1, 9), value=decimal.Decimal('1891001.29'))]

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if i <= 5:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('6705.29')
            assert x.net == decimal.Decimal('23096')
            assert x.bal == decimal.Decimal('1861200')

        elif i <= 11:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('5960.26')
            assert x.net == decimal.Decimal('23841.03')
            assert x.bal == decimal.Decimal('1861200')

        # Antecipação total.
        else:
            assert x.date == kwa['insertions'][0].date
            assert x.amort == decimal.Decimal('1861200')
            assert x.gain == decimal.Decimal('29801.29')
            assert x.raw == decimal.Decimal('1891001.29')
            assert x.tax == decimal.Decimal('5215.23')
            assert x.net == decimal.Decimal('1885786.06')
            assert x.bal == _0

    assert i == 12

def test_will_create_jm_pre_6():
    '''
    Nesse teste a data de antecipação coincide com a data de pagamento da prestação 13.

    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Hipotética 04 - Antecipação Total
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1861200')
    kwa['apy'] = decimal.Decimal('21')
    kwa['zero_date'] = datetime.date(2015, 1, 9)
    kwa['term'] = 24
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2016, 1, 10), value=decimal.Decimal('1862153.96'))]

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if i <= 5:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('6705.29')
            assert x.net == decimal.Decimal('23096')
            assert x.bal == decimal.Decimal('1861200')

        elif i <= 11:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('5960.26')
            assert x.net == decimal.Decimal('23841.03')
            assert x.bal == decimal.Decimal('1861200')

        elif i == 12:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('5215.23')
            assert x.net == decimal.Decimal('24586.06')
            assert x.bal == decimal.Decimal('1861200')

        # Antecipação total.
        else:
            assert x.date == kwa['insertions'][0].date
            assert x.amort == decimal.Decimal('1861200')
            assert x.gain == decimal.Decimal('953.96')
            assert x.raw == decimal.Decimal('1862153.96')
            assert x.tax == decimal.Decimal('166.94')
            assert x.net == decimal.Decimal('1861987.02')
            assert x.bal == _0

    assert i == 13

def test_will_create_jm_pre_7():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Hipotética 05 - Duas Antecipações Parciais
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1861200')
    kwa['apy'] = decimal.Decimal('21')
    kwa['zero_date'] = datetime.date(2015, 1, 9)
    kwa['term'] = 24
    kwa['insertions'] = []

    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2015, 7, 20), value=decimal.Decimal('475820.51')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2016, 3, 2), value=decimal.Decimal('482223.35')))

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if i <= 5:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('6705.29')
            assert x.net == decimal.Decimal('23096')
            assert x.bal == decimal.Decimal('1861200')

        elif i == 6:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('5960.26')
            assert x.net == decimal.Decimal('23841.03')
            assert x.bal == decimal.Decimal('1861200')

        # Antecipação parcial 1.
        elif i == 7:
            assert x.date == kwa['insertions'][0].date
            assert x.amort == decimal.Decimal('465300')
            assert x.gain == decimal.Decimal('10520.51')
            assert x.raw == decimal.Decimal('475820.51')
            assert x.tax == decimal.Decimal('2104.1')
            assert x.net == decimal.Decimal('473716.41')
            assert x.bal == decimal.Decimal('1395900')

        elif i == 8:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 1)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('14379.31')
            assert x.tax == decimal.Decimal('2875.86')
            assert x.net == decimal.Decimal('11503.45')
            assert x.bal == decimal.Decimal('1395900')

        elif i <= 12:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 1)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('22350.97')
            assert x.tax == decimal.Decimal('4470.19')
            assert x.net == decimal.Decimal('17880.78')
            assert x.bal == decimal.Decimal('1395900')

        elif i <= 14:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 1)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('22350.97')
            assert x.tax == decimal.Decimal('3911.42')
            assert x.net == decimal.Decimal('18439.55')
            assert x.bal == decimal.Decimal('1395900')

        # Antecipação parcial 2.
        elif i == 15:
            assert x.date == kwa['insertions'][1].date
            assert x.amort == decimal.Decimal('465300')
            assert x.gain == decimal.Decimal('16923.35')
            assert x.raw == decimal.Decimal('482223.35')
            assert x.tax == decimal.Decimal('2961.59')
            assert x.net == decimal.Decimal('479261.76')
            assert x.bal == decimal.Decimal('930600')

        elif i == 16:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 2)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('3575.07')
            assert x.tax == decimal.Decimal('625.64')
            assert x.net == decimal.Decimal('2949.43')
            assert x.bal == decimal.Decimal('930600')

        elif i <= 25:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 2)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('14900.64')
            assert x.tax == decimal.Decimal('2607.61')
            assert x.net == decimal.Decimal('12293.03')
            assert x.bal == decimal.Decimal('930600')

        else:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 2)
            assert x.amort == decimal.Decimal('930600')
            assert x.gain == decimal.Decimal('14900.64')
            assert x.raw == decimal.Decimal('945500.64')
            assert x.tax == decimal.Decimal('2235.1')
            assert x.net == decimal.Decimal('943265.54')
            assert x.bal == _0

    assert i == kwa['term'] + 2

def test_will_create_jm_pre_8():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Hipotética 06 - Antecipações Parciais e Total
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1861200')
    kwa['apy'] = decimal.Decimal('21')
    kwa['zero_date'] = datetime.date(2015, 1, 9)
    kwa['term'] = 24
    kwa['insertions'] = []

    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2015, 7, 20), value=decimal.Decimal('475820.51')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2016, 3, 2), value=decimal.Decimal('482223.35')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2016, 10, 25), value=decimal.Decimal('938261.1')))

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if i <= 5:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('6705.29')
            assert x.net == decimal.Decimal('23096')
            assert x.bal == decimal.Decimal('1861200')

        elif i == 6:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('29801.29')
            assert x.tax == decimal.Decimal('5960.26')
            assert x.net == decimal.Decimal('23841.03')
            assert x.bal == decimal.Decimal('1861200')

        # Antecipação parcial 1.
        elif i == 7:
            assert x.date == kwa['insertions'][0].date
            assert x.amort == decimal.Decimal('465300')
            assert x.gain == decimal.Decimal('10520.51')
            assert x.raw == decimal.Decimal('475820.51')
            assert x.tax == decimal.Decimal('2104.1')
            assert x.net == decimal.Decimal('473716.41')
            assert x.bal == decimal.Decimal('1395900')

        elif i == 8:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 1)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('14379.31')
            assert x.tax == decimal.Decimal('2875.86')
            assert x.net == decimal.Decimal('11503.45')
            assert x.bal == decimal.Decimal('1395900')

        elif i <= 12:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 1)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('22350.97')
            assert x.tax == decimal.Decimal('4470.19')
            assert x.net == decimal.Decimal('17880.78')
            assert x.bal == decimal.Decimal('1395900')

        elif i <= 14:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 1)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('22350.97')
            assert x.tax == decimal.Decimal('3911.42')
            assert x.net == decimal.Decimal('18439.55')
            assert x.bal == decimal.Decimal('1395900')

        # Antecipação parcial 2.
        elif i == 15:
            assert x.date == kwa['insertions'][1].date
            assert x.amort == decimal.Decimal('465300')
            assert x.gain == decimal.Decimal('16923.35')
            assert x.raw == decimal.Decimal('482223.35')
            assert x.tax == decimal.Decimal('2961.59')
            assert x.net == decimal.Decimal('479261.76')
            assert x.bal == decimal.Decimal('930600')

        elif i == 16:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 2)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('3575.07')
            assert x.tax == decimal.Decimal('625.64')
            assert x.net == decimal.Decimal('2949.43')
            assert x.bal == decimal.Decimal('930600')

        elif i <= 23:
            assert x.date == kwa['zero_date'] + _MONTH * (i - 2)
            assert x.amort == _0
            assert x.gain == x.raw == decimal.Decimal('14900.64')
            assert x.tax == decimal.Decimal('2607.61')
            assert x.net == decimal.Decimal('12293.03')
            assert x.bal == decimal.Decimal('930600')

        # Antecipação total.
        else:
            assert x.date == kwa['insertions'][2].date
            assert x.amort == decimal.Decimal('930600')
            assert x.gain == decimal.Decimal('7661.1')
            assert x.raw == decimal.Decimal('938261.1')
            assert x.tax == decimal.Decimal('1340.69')
            assert x.net == decimal.Decimal('936920.41')
            assert x.bal == _0

    assert i == kwa['term']

def test_will_create_jm_pre_9():
    '''Valida uma antecipação antes do primeiro pagamento regular.'''

    kwa = {}

    kwa['principal'] = decimal.Decimal('500000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['zero_date'] = datetime.date(2022, 8, 22)
    kwa['term'] = 3
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 8, 23), value=decimal.Decimal(5000))]

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if x.no == 1:
            assert x.date == datetime.date(2022, 8, 23)
            assert x.gain == decimal.Decimal('78.32')
            assert x.amort == decimal.Decimal('4921.68')
            assert x.raw == decimal.Decimal('5000.00')
            assert x.tax == decimal.Decimal('17.62')
            assert x.net == decimal.Decimal('4982.38')
            assert x.bal == decimal.Decimal('495078.32')

        elif x.no == 2:
            assert x.date == datetime.date(2022, 9, 22)
            assert x.gain == decimal.Decimal('2331.90')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('2331.90')
            assert x.tax == decimal.Decimal('524.68')
            assert x.net == decimal.Decimal('1807.22')
            assert x.bal == decimal.Decimal('495078.32')

        elif x.no == 3:
            assert x.date == datetime.date(2022, 10, 22)
            assert x.gain == decimal.Decimal('2409.82')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('2409.82')
            assert x.tax == decimal.Decimal('542.21')
            assert x.net == decimal.Decimal('1867.61')
            assert x.bal == decimal.Decimal('495078.32')

        else:
            assert x.date == datetime.date(2022, 11, 22)
            assert x.gain == decimal.Decimal('2409.82')
            assert x.amort == decimal.Decimal('495078.32')
            assert x.raw == decimal.Decimal('497488.14')
            assert x.tax == decimal.Decimal('542.21')
            assert x.net == decimal.Decimal('496945.93')
            assert x.bal == _0

    assert i == 4

def test_will_create_jm_pre_10():
    '''Valida uma antecipação antes do aniversário do empréstimo.'''

    kwa = {}

    kwa['principal'] = decimal.Decimal('500000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['zero_date'] = datetime.date(2022, 8, 22)
    kwa['anniversary_date'] = datetime.date(2022, 9, 27)
    kwa['term'] = 3
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 8, 27), value=decimal.Decimal(5000))]

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if x.no == 1:
            assert x.date == datetime.date(2022, 8, 27)
            assert x.gain == decimal.Decimal('391.75')
            assert x.amort == decimal.Decimal('4608.25')
            assert x.raw == decimal.Decimal('5000.00')
            assert x.tax == decimal.Decimal('88.14')
            assert x.net == decimal.Decimal('4911.86')
            assert x.bal == decimal.Decimal('495391.75')

        elif x.no == 2:
            assert x.date == datetime.date(2022, 9, 27)
            assert x.gain == decimal.Decimal('2411.34')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('2411.34')
            assert x.tax == decimal.Decimal('542.55')
            assert x.net == decimal.Decimal('1868.79')
            assert x.bal == decimal.Decimal('495391.75')

        elif x.no == 3:
            assert x.date == datetime.date(2022, 10, 27)
            assert x.gain == decimal.Decimal('2411.34')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('2411.34')
            assert x.tax == decimal.Decimal('542.55')
            assert x.net == decimal.Decimal('1868.79')
            assert x.bal == decimal.Decimal('495391.75')

        else:
            assert x.date == datetime.date(2022, 11, 27)
            assert x.gain == decimal.Decimal('2411.34')
            assert x.amort == decimal.Decimal('495391.75')
            assert x.raw == decimal.Decimal('497803.09')
            assert x.tax == decimal.Decimal('542.55')
            assert x.net == decimal.Decimal('497260.54')
            assert x.bal == _0

    assert i == 4

def test_will_create_jm_pre_11():
    '''Valida duas antecipações antes do aniversário do empréstimo.'''

    kwa = {}

    kwa['principal'] = decimal.Decimal('500000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['zero_date'] = datetime.date(2022, 8, 22)
    kwa['anniversary_date'] = datetime.date(2022, 9, 27)
    kwa['term'] = 3
    kwa['insertions'] = []

    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2022, 8, 27), value=decimal.Decimal(5000)))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2022, 9, 22), value=decimal.Decimal(5000)))

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if x.no == 1:
            assert x.date == datetime.date(2022, 8, 27)
            assert x.gain == decimal.Decimal('391.75')
            assert x.amort == decimal.Decimal('4608.25')
            assert x.raw == decimal.Decimal('5000.00')
            assert x.tax == decimal.Decimal('88.14')
            assert x.net == decimal.Decimal('4911.86')
            assert x.bal == decimal.Decimal('495391.75')

        elif x.no == 2:
            assert x.date == datetime.date(2022, 9, 22)
            assert x.gain == decimal.Decimal('2021.63')
            assert x.amort == decimal.Decimal('2978.37')
            assert x.raw == decimal.Decimal('5000.00')
            assert x.tax == decimal.Decimal('454.87')
            assert x.net == decimal.Decimal('4545.13')
            assert x.bal == decimal.Decimal('492413.37')

        elif x.no == 3:
            assert x.date == datetime.date(2022, 9, 27)
            assert x.gain == decimal.Decimal('385.80')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('385.80')
            assert x.tax == decimal.Decimal('86.81')
            assert x.net == decimal.Decimal('298.99')
            assert x.bal == decimal.Decimal('492413.37')

        elif x.no == 4:
            assert x.date == datetime.date(2022, 10, 27)
            assert x.gain == decimal.Decimal('2396.85')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('2396.85')
            assert x.tax == decimal.Decimal('539.29')
            assert x.net == decimal.Decimal('1857.56')
            assert x.bal == decimal.Decimal('492413.37')

        else:
            assert x.date == datetime.date(2022, 11, 27)
            assert x.gain == decimal.Decimal('2396.85')
            assert x.amort == decimal.Decimal('492413.37')
            assert x.raw == decimal.Decimal('494810.22')
            assert x.tax == decimal.Decimal('539.29')
            assert x.net == decimal.Decimal('494270.93')
            assert x.bal == _0

    assert i == 5

def test_will_create_jm_pre_12():
    '''
    Valida duas antecipações depois do aniversário e antes do segundo pagamento do empréstimo.

    Ref File: https://docs.google.com/spreadsheets/d/1qNIfAuvELTXepy6i8yyeNJVwUSLxiFRSDtWDzAk8T2k
    Tab.....: Hipotética 07 - Duas Antecipações Parciais
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('500000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['zero_date'] = datetime.date(2022, 8, 22)
    kwa['anniversary_date'] = datetime.date(2022, 9, 27)
    kwa['term'] = 3
    kwa['insertions'] = []

    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2022, 10, 2), value=decimal.Decimal('404.81')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2022, 10, 7), value=decimal.Decimal('404.81')))

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if x.no == 1:
            assert x.date == datetime.date(2022, 9, 27)
            assert x.gain == decimal.Decimal('2827.43')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('2827.43')
            assert x.tax == decimal.Decimal('636.17')
            assert x.net == decimal.Decimal('2191.26')
            assert x.bal == decimal.Decimal('500000.00')

        elif x.no == 2:
            assert x.date == datetime.date(2022, 10, 2)
            assert x.gain == decimal.Decimal('404.81')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('404.81')
            assert x.tax == decimal.Decimal('91.08')
            assert x.net == decimal.Decimal('313.73')
            assert x.bal == decimal.Decimal('500000.00')

        elif x.no == 3:
            assert x.date == datetime.date(2022, 10, 7)
            assert x.gain == decimal.Decimal('404.81')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('404.81')
            assert x.tax == decimal.Decimal('91.08')
            assert x.net == decimal.Decimal('313.73')
            assert x.bal == decimal.Decimal('500000.00')

        elif x.no == 4:
            assert x.date == datetime.date(2022, 10, 27)
            assert x.gain == decimal.Decimal('1621.20')
            assert x.amort == _0
            assert x.raw == decimal.Decimal('1621.20')
            assert x.tax == decimal.Decimal('364.77')
            assert x.net == decimal.Decimal('1256.43')
            assert x.bal == decimal.Decimal('500000.00')

        else:
            assert x.date == datetime.date(2022, 11, 27)
            assert x.gain == decimal.Decimal('2433.78')
            assert x.amort == decimal.Decimal('500000.00')
            assert x.raw == decimal.Decimal('502433.77')
            assert x.tax == decimal.Decimal('547.60')
            assert x.net == decimal.Decimal('501886.17')
            assert x.bal == _0

    assert i == 5

def test_will_create_jm_pos_1():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1XqaYsV1qg4jFf2ulQAuBh8JttYryPXHAGlwxgXqfwgc
    Tab.....: Villa VIC Pisa
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('555500')
    kwa['apy'] = decimal.Decimal(6)
    kwa['zero_date'] = datetime.date(2022, 3, 9)
    kwa['vir'] = fincore.VariableIndex('CDI')
    kwa['term'] = 12

    # Juros, I.R. e líquido.
    tab[1] = '8486.55', '1909.47', '6577.08'
    tab[2] = '6764.7', '1522.06', '5242.64'
    tab[3] = '9066.63', '2039.99', '7026.64'
    tab[4] = '8430.91', '1896.95', '6533.96'
    tab[5] = '8510.07', '1914.77', '6595.30'
    tab[6] = '9104.85', '1820.97', '7283.88'
    tab[7] = '8687.77', '1737.55', '6950.22'
    tab[8] = '8271', '1654.20', '6616.80'
    tab[9] = '8687.77', '1737.55', '6950.22'
    tab[10] = '8687.77', '1737.55', '6950.22'
    tab[11] = '9522.23', '1904.45', '7617.78'
    tab[12] = '7438.39', '1301.72', '561636.67'

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['zero_date'] + _MONTH * i

        if x.no < kwa['term']:
            assert x.amort == 0
            assert x.gain == x.raw == decimal.Decimal(tab[i][0])
            assert x.tax == decimal.Decimal(tab[i][1])
            assert x.net == decimal.Decimal(tab[i][2])
            assert x.bal == kwa['principal']

        else:
            assert x.amort == kwa['principal']
            assert x.gain == decimal.Decimal(tab[i][0])
            assert x.raw == decimal.Decimal(tab[i][0]) + kwa['principal']
            assert x.tax == decimal.Decimal(tab[i][1])
            assert x.net == decimal.Decimal(tab[i][2])
            assert x.bal == 0

    assert i == kwa['term']

def test_will_create_jm_pos_2():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1XqaYsV1qg4jFf2ulQAuBh8JttYryPXHAGlwxgXqfwgc
    Tab.....: Hipotética CDI c/ Aniv.
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('555500')
    kwa['apy'] = decimal.Decimal(6)
    kwa['zero_date'] = datetime.date(2022, 3, 9)
    kwa['anniversary_date'] = datetime.date(2022, 4, 18)
    kwa['vir'] = fincore.VariableIndex('CDI')
    kwa['term'] = 12

    # Juros, I.R. e líquido.
    tab[1] = '9996.71', '2249.26', '7747.45',
    tab[2] = '8033.05', '1807.44', '6225.61',
    tab[3] = '8679.28', '1952.84', '6726.44',
    tab[4] = '8073.70', '1816.58', '6257.12',
    tab[5] = '9393.69', '2113.58', '7280.11',
    tab[6] = '8687.77', '1737.55', '6950.22',
    tab[7] = '8271.00', '1654.20', '6616.80',
    tab[8] = '8687.77', '1737.55', '6950.22',
    tab[9] = '8687.77', '1737.55', '6950.22',
    tab[10] = '9104.85', '1820.97', '7283.88',
    tab[11] = '9522.23', '1904.45', '7617.78',
    tab[12] = '7438.39', '1301.72', '561636.67'

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['anniversary_date'] + _MONTH * (i - 1)

        if x.no < kwa['term']:
            assert x.amort == 0
            assert x.gain == x.raw == decimal.Decimal(tab[i][0])
            assert x.tax == decimal.Decimal(tab[i][1])
            assert x.net == decimal.Decimal(tab[i][2])
            assert x.bal == kwa['principal']

        else:
            assert x.amort == kwa['principal']
            assert x.gain == decimal.Decimal(tab[i][0])
            assert x.raw == decimal.Decimal(tab[i][0]) + kwa['principal']
            assert x.tax == decimal.Decimal(tab[i][1])
            assert x.net == decimal.Decimal(tab[i][2])
            assert x.bal == 0

    assert i == kwa['term']

def test_will_create_jm_pos_3():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1XqaYsV1qg4jFf2ulQAuBh8JttYryPXHAGlwxgXqfwgc
    Tab.....: Hipotética CDI c/ AP
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('555500')
    kwa['apy'] = decimal.Decimal(6)
    kwa['zero_date'] = datetime.date(2022, 3, 9)
    kwa['vir'] = fincore.VariableIndex('CDI')
    kwa['term'] = 12
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 9, 27), value=decimal.Decimal('100000.00'))]

    # Juros, bruto, I.R., líquido e saldo devedor.
    tab[1] = '8486.55', '8486.55', '1909.47', '6577.08', '555500.00',
    tab[2] = '6764.70', '6764.70', '1522.06', '5242.64', '555500.00',
    tab[3] = '9066.63', '9066.63', '2039.99', '7026.64', '555500.00',
    tab[4] = '8430.91', '8430.91', '1896.95', '6533.96', '555500.00',
    tab[5] = '8510.07', '8510.07', '1914.77', '6595.30', '555500.00',
    tab[6] = '9104.85', '9104.85', '1820.97', '7283.88', '555500.00',
    tab[7] = '4947.93', '100000.00', '989.59', '99010.41', '460447.93',  # Antecipação parcial.
    tab[8] = '3072.55', '3072.55', '614.51', '2458.04', '460447.93',
    tab[9] = '6855.75', '6855.75', '1371.15', '5484.60', '460447.93',
    tab[10] = '7201.20', '7201.20', '1440.24', '5760.96', '460447.93',
    tab[11] = '7201.20', '7201.20', '1440.24', '5760.96', '460447.93',
    tab[12] = '7892.87', '7892.87', '1578.57', '6314.30', '460447.93',
    tab[13] = '6165.60', '466613.53', '1078.98', '465534.55', '0.00'

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i

        if x.no == 7:
            assert x.date == kwa['insertions'][0].date

        else:
            assert x.date == kwa['zero_date'] + _MONTH * (i if i < 7 else i - 1)

        assert x.gain == decimal.Decimal(tab[i][0])
        assert x.raw == decimal.Decimal(tab[i][1])
        assert x.tax == decimal.Decimal(tab[i][2])
        assert x.net == decimal.Decimal(tab[i][3])
        assert x.bal == decimal.Decimal(tab[i][4])

    assert i - 1 == kwa['term']

def test_will_create_jm_pos_4():
    '''
    Ref File: https://docs.google.com/spreadsheets/d/1XqaYsV1qg4jFf2ulQAuBh8JttYryPXHAGlwxgXqfwgc
    Tab.....: Hipotética CDI c/ AT
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('555500')
    kwa['apy'] = decimal.Decimal(6)
    kwa['zero_date'] = datetime.date(2022, 3, 9)
    kwa['vir'] = fincore.VariableIndex('CDI')
    kwa['term'] = 12
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 9, 27), value=decimal.Decimal('560447.93'))]

    # Juros, bruto, I.R., líquido e saldo devedor.
    tab[1] = '8486.55', '8486.55', '1909.47', '6577.08', '555500.00',
    tab[2] = '6764.70', '6764.70', '1522.06', '5242.64', '555500.00',
    tab[3] = '9066.63', '9066.63', '2039.99', '7026.64', '555500.00',
    tab[4] = '8430.91', '8430.91', '1896.95', '6533.96', '555500.00',
    tab[5] = '8510.07', '8510.07', '1914.77', '6595.30', '555500.00',
    tab[6] = '9104.85', '9104.85', '1820.97', '7283.88', '555500.00',
    tab[7] = '4947.93', '560447.93', '989.59', '559458.34', '0.00',  # Antecipação total.

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['insertions'][0].date if x.no == 7 else kwa['zero_date'] + _MONTH * i
        assert x.gain == decimal.Decimal(tab[i][0])
        assert x.raw == decimal.Decimal(tab[i][1])
        assert x.tax == decimal.Decimal(tab[i][2])
        assert x.net == decimal.Decimal(tab[i][3])
        assert x.bal == decimal.Decimal(tab[i][4])

    assert i == 7

def test_will_create_jm_ipca_1():
    '''
    Operação "CRI - Max Tulum 2 (Isento de IR)", Juros mensais - 38 meses - IPCA, ID "SFITBR__Qo2dDrU5GfAGj".

    Primeiro cronograma de Juros Mensais com IPCA conferido contra planilha. Até aqui, o IPCA mensal só tinha
    referência externa na rotina de retornos diários, em "test_will_create_loan_daily_returns_jm_1".

    A referência é a curva PU diária da TRV, que constrói o fator de correção do mesmo modo que o motor: um único
    índice mensal por período, elevado a "DCP/DCT". É a coluna "N" da aba, "(K/L)^(H/I)", com o índice buscado pelo
    número do evento, "F-2". Não confundir com a planilha da operação Yees, que reescreveu essa coluna como um
    acúmulo diário indexado pelo mês-calendário, e por isso não fecha com o motor.

    A operação nasce em 12/12/2024 e o aniversário é 14/01/2025, então o primeiro período é irregular, com 33 dias
    corridos. O "first_dct_rule" de "31" reproduz o DCT da planilha, que é a distância entre os aniversários que
    cercam o pagamento – de 14/12 a 14/01.

    A série do "_RicherIpcaBackend" termina em junho de 2026. Com o deslocamento M-2, ela alcança o vigésimo
    pagamento, e os dezoito seguintes ficam sem índice, com fator um e correção zero.

    Atenção ao alcance da referência externa: a planilha projeta índice zero a partir de dezembro de 2024, então ela
    só corrobora o primeiro pagamento – e ali difere em R$ 1,85, porque guarda a variação com quatro casas, 0,5599%,
    contra os 0,56% do "backend". Para ancorar os demais é preciso regerar a curva da TRV com a série realizada.

    O décimo pagamento tem correção zero com índice existente: agosto de 2025 fechou em -0,11%, e o motor trava o
    fator de correção em um. É o único caso de deflação da tabela.

    Ref File: https://docs.google.com/spreadsheets/d/13Rr9b0BiQhvse-6-zbPAilfiUMfzHteu
    Tab.....: Cronograma
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('7000000')
    kwa['apy'] = decimal.Decimal('10.84')
    kwa['zero_date'] = datetime.date(2024, 12, 12)
    kwa['term'] = 38
    kwa['anniversary_date'] = datetime.date(2025, 1, 14)
    kwa['vir'] = fincore.VariableIndex(code='IPCA', backend=_RicherIpcaBackend())
    kwa['first_dct_rule'] = '31'

    # Juros, correção monetária, amortização e saldo devedor.
    tab[1] = '64467.67', '29064.94', '0.00', '7029064.94'  # Período irregular de abertura, 33 dias corridos.
    tab[2] = '60606.94', '36400.00', '0.00', '7036400.00'
    tab[3] = '60389.88', '11200.00', '0.00', '7011200.00'
    tab[4] = '61083.25', '91700.00', '0.00', '7091700.00'
    tab[5] = '60631.05', '39200.00', '0.00', '7039200.00'
    tab[6] = '60552.67', '30100.00', '0.00', '7030100.00'
    tab[7] = '60450.17', '18200.00', '0.00', '7018200.00'
    tab[8] = '60438.11', '16800.00', '0.00', '7016800.00'
    tab[9] = '60450.17', '18200.00', '0.00', '7018200.00'
    tab[10] = '60293.41', '0.00', '0.00', '7000000.00'  # Índice de agosto de 2025, -0,11%. Fator travado em um.
    tab[11] = '60582.82', '33600.00', '0.00', '7033600.00'
    tab[12] = '60347.67', '6300.00', '0.00', '7006300.00'
    tab[13] = '60401.94', '12600.00', '0.00', '7012600.00'
    tab[14] = '60492.38', '23100.00', '0.00', '7023100.00'
    tab[15] = '60492.38', '23100.00', '0.00', '7023100.00'
    tab[16] = '60715.46', '49000.00', '0.00', '7049000.00'
    tab[17] = '60823.99', '61600.00', '0.00', '7061600.00'
    tab[18] = '60697.38', '46900.00', '0.00', '7046900.00'
    tab[19] = '60643.11', '40600.00', '0.00', '7040600.00'
    tab[20] = '60389.88', '11200.00', '0.00', '7011200.00'  # Último pagamento alcançado pela série.
    tab[21] = '60293.41', '0.00', '0.00', '7000000.00'  # Vale também para os pagamentos 22 a 37.
    tab[38] = '60293.41', '0.00', '7000000.00', '0.00'

    for i, x in enumerate(fincore.build_jm(**kwa), 1):
        x = t.cast(fincore.PriceAdjustedPayment, x)

        assert x.no == i
        assert x.date == kwa['anniversary_date'] + _MONTH * (i - 1)
        assert [x.gain, x.pla, x.amort, x.bal] == [decimal.Decimal(y) for y in tab.get(i, tab[21])]
        assert x.raw == x.gain + x.pla + x.amort

    assert i == kwa['term']

# Antecipações em operações indexadas ao IPCA.
#
# A correção monetária é particionada pelo calendário regular: cada pagamento consome exatamente uma janela de índices,
# e a partição é disjunta e sem lacuna.
#
# Uma antecipação não tem calendário próprio, e por isso herda a janela do pagamento regular que a sucede. Os dois
# eventos repartem o índice do mês, e cada um corrige o saldo devedor vigente no seu período – a correção acompanha o
# saldo, e o principal que sai é nominal.
#
# Quando os juros consomem a antecipação a ponto de não sobrar para a correção inteira, o que falta fica diferido em
# "regs.correction", como fator mais crédito, e o próximo pagamento que liquide correção o recolhe.
#
# Especificado na thread "Ajustes Motor IPCA", de outubro de 2024:
#
#   https://inco1.slack.com/archives/C0103FS2CH4/p1728317663655909
#
def test_wont_leak_price_level_adjustment_on_prepayment():
    '''
    Conservação da correção monetária diante de uma antecipação que não amortiza principal.

    Uma antecipação integralmente consumida pelos juros acumulados não reduz o saldo devedor nominal. O perfil de saldo
    ao longo do tempo permanece idêntico ao do fluxo regular, logo a correção monetária total cobrada também deve
    permanecer idêntica.

    Baseado na operação "YUCA SPE V", Juros mensais - 30 meses - IPCA, ID "cmQFTXLsEB6Bg7Zlae1pV", acrescida de uma data
    de aniversário e de uma antecipação parcial fictícias.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1844500')
    kwa['apy'] = decimal.Decimal(7)
    kwa['zero_date'] = datetime.date(2022, 2, 18)
    kwa['term'] = 30
    kwa['anniversary_date'] = datetime.date(2022, 4, 5)
    kwa['vir'] = fincore.VariableIndex(code='IPCA')

    regular = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    # Os juros acumulados entre 05/04 e 20/04 superam cinco mil reais, então a antecipação não amortiza principal.
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 4, 20), value=decimal.Decimal('5000'))]

    prepaid = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    assert sum(x.amort for x in prepaid) == sum(x.amort for x in regular) == kwa['principal']
    assert sum(x.pla for x in prepaid) == sum(x.pla for x in regular)

def test_wont_leak_partially_deferred_price_level_adjustment_on_prepayment():
    '''
    Conservação da correção monetária quando a antecipação liquida apenas parte da correção do seu período.

    A ordem de imputação põe os juros à frente da correção. Uma antecipação que cubra os juros e só uma fração da
    correção deixa o restante diferido, e ainda assim não amortiza principal – logo a correção total do cronograma não
    pode mudar. Exercita a composição do fator diferido com o crédito do que já foi pago.

    Mesma operação de "test_wont_leak_price_level_adjustment_on_prepayment".
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1844500')
    kwa['apy'] = decimal.Decimal(7)
    kwa['zero_date'] = datetime.date(2022, 2, 18)
    kwa['term'] = 30
    kwa['anniversary_date'] = datetime.date(2022, 4, 5)
    kwa['vir'] = fincore.VariableIndex(code='IPCA')

    regular = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    # Os juros do período somam 5.261,68, e a correção devida 14.883,30. Dez mil cobrem os juros e parte da correção.
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 4, 20), value=decimal.Decimal('10000'))]

    prepaid = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]
    advance = next(x for x in prepaid if x.date == kwa['insertions'][0].date)

    assert advance.amort == _0
    assert _0 < advance.pla < decimal.Decimal('14883.30')

    assert sum(x.amort for x in prepaid) == sum(x.amort for x in regular) == kwa['principal']
    assert sum(x.pla for x in prepaid) == sum(x.pla for x in regular)

def test_wont_recharge_settled_price_level_indexes_on_prepayment():
    '''
    Janela de índices de IPCA de uma antecipação.

    A antecipação deve corrigir apenas o período em aberto, isto é, o intervalo entre o pagamento regular anterior e a
    sua própria data. Não deve recobrar índice já liquidado por um pagamento anterior, nem alcançar índice que antecede
    o primeiro mês do fluxo regular.

    Mesma operação de "test_wont_leak_price_level_adjustment_on_prepayment".
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1844500')
    kwa['apy'] = decimal.Decimal(7)
    kwa['zero_date'] = datetime.date(2022, 2, 18)
    kwa['term'] = 30
    kwa['anniversary_date'] = datetime.date(2022, 4, 5)
    kwa['vir'] = fincore.VariableIndex(code='IPCA')
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 4, 20), value=decimal.Decimal('5000'))]

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    # O primeiro pagamento regular liquida o índice de fevereiro de 2022, o primeiro do fluxo. A antecipação o sucede.
    assert sched[0].date == kwa['anniversary_date']
    assert [x.date for x in sched[0].cf_mem] == [datetime.date(2022, 2, 1)]

    assert sched[1].date == kwa['insertions'][0].date

    # O período em aberto, de 05/04 a 20/04, pertence ao índice de março de 2022, o mesmo que o pagamento de 05/05
    # consome. Os dois eventos devem reparti-lo, e nada além dele.
    assert [x.date for x in sched[1].cf_mem] == [datetime.date(2022, 3, 1)]

    assert sched[2].date == kwa['anniversary_date'] + _MONTH
    assert [x.date for x in sched[2].cf_mem] == [datetime.date(2022, 3, 1)]

# Antecipação que não amortiza juros.
#
# A ordem de imputação padrão põe juros e correção à frente do principal. Uma antecipação com "amortizes_interest"
# falso inverte isso: o valor vai inteiro para o principal, e o juro e a correção do período ficam devidos.
#
# O juro travado assim não se confunde com o de uma carência. O de carência capitaliza e sai à medida que o principal
# amortiza; este é cobrado por inteiro no pagamento regular seguinte, porque o tomador segue devendo o mês corrente.
# Daí o registrador "interest.locked", separado de "interest.deferred".
#
def test_will_amortize_only_principal_on_prepayment():
    '''
    Antecipação que não amortiza juros: o valor vai inteiro para o principal.

    Mesma operação de "test_wont_leak_price_level_adjustment_on_prepayment".
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1844500')
    kwa['apy'] = decimal.Decimal(7)
    kwa['zero_date'] = datetime.date(2022, 2, 18)
    kwa['term'] = 30
    kwa['anniversary_date'] = datetime.date(2022, 4, 5)
    kwa['vir'] = fincore.VariableIndex(code='IPCA')
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 4, 20), value=decimal.Decimal('50000'), amortizes_interest=False)]

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]
    advance = next(x for x in sched if x.date == kwa['insertions'][0].date)
    index = sched.index(advance)

    # Os juros do período, mais de cinco mil, seriam imputados antes do principal na ordem padrão. Aqui, não.
    assert advance.gain > _0
    assert advance.amort == kwa['insertions'][0].value
    assert advance.pla == _0
    assert advance.raw == kwa['insertions'][0].value

    # O pagamento regular seguinte liquida o juro travado por inteiro, somado ao do seu próprio período. Como o valor
    # bruto de um pagamento sem amortização é juros liquidados mais correção, a diferença isola os juros.
    #
    assert sched[index + 1].raw - sched[index + 1].pla == advance.gain + sched[index + 1].gain

    # E nada fica para trás: o pagamento seguinte a esse liquida apenas o juro do seu próprio período.
    assert sched[index + 2].raw - sched[index + 2].pla == sched[index + 2].gain

    assert sum(x.amort for x in sched) == kwa['principal']

def test_wont_settle_debt_with_prepayment_that_does_not_amortize_interest():
    '''
    Uma antecipação que não amortiza juros não pode quitar a dívida, nem exceder o principal em aberto.

    O valor máximo pede a quitação, e quitar exige liquidar juros e correção – não haveria pagamento posterior para
    recolhê-los. E, como o valor sai todo do principal nominal, o teto é o principal em aberto, e não o saldo
    corrigido, que é maior.

    Mesma operação de "test_wont_leak_price_level_adjustment_on_prepayment".
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1844500')
    kwa['apy'] = decimal.Decimal(7)
    kwa['zero_date'] = datetime.date(2022, 2, 18)
    kwa['term'] = 30
    kwa['anniversary_date'] = datetime.date(2022, 4, 5)
    kwa['vir'] = fincore.VariableIndex(code='IPCA')

    def build(value):
        kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 4, 20), value=value, amortizes_interest=False)]

        return list(fincore.build_jm(**kwa))

    with pytest.raises(ValueError, match='an advancement that does not amortize interest cannot settle the entire debt'):
        build(fincore.Amortization.Bare.MAX_VALUE)

    with pytest.raises(Exception, match='is greater than the outstanding principal of the loan'):
        build(kwa['principal'] + _1)

    # O saldo devedor corrigido na data já passa do principal, e ainda assim o teto é o principal.
    assert build(kwa['principal'])[1].amort == kwa['principal']

# Os dois casos de antecipação parcial da operação "CRI IPA Club Residencial", conferidos contra planilha.
#
# São o mesmo evento – 97.224,53 em 03/08/2026, dentro do período que vai de 07/07 a 07/08 – sob as duas ordens de
# imputação. O primeiro pagamento, de 07/07, é anterior à antecipação e é idêntico nos dois: serve de âncora, e bate
# com o admin da operação no centavo.
#
def _kwa_cri_ipa():
    kwa = {}

    kwa['principal'] = decimal.Decimal('6000000')
    kwa['apy'] = decimal.Decimal(12)
    kwa['zero_date'] = datetime.date(2026, 5, 29)
    kwa['term'] = 36
    kwa['anniversary_date'] = datetime.date(2026, 7, 7)
    kwa['first_dct_rule'] = '31'
    kwa['vir'] = fincore.VariableIndex(code='IPCA', backend=_RicherIpcaBackend())

    return kwa

def test_will_create_jm_ipca_2():
    '''
    Operação "CRI IPA Club Residencial", Juros mensais - 36 meses - IPCA, c/ antecipação parcial.

    Ordem de imputação padrão: juros, correção, principal. Dos 97.224,53 antecipados, 49.625,40 pagam os juros
    corridos de 07/07 a 03/08, 8.360,43 pagam a correção desse mesmo período, e só os 39.238,70 restantes abatem
    principal.

    A correção dos 27 dias incide sobre os 6.000.000,00 que estavam na operação durante eles, e a dos 4 dias que
    faltam para 07/08 incide sobre o saldo já reduzido. Os dois fatores compõem o índice do mês, de 0,16%.

    Ref File: https://docs.google.com/spreadsheets/d/1CH47cNnNc1QjcPb-WP7q6Gp1k1UNkDnQ
    Tab.....: Conferência
    '''

    kwa = _kwa_cri_ipa()
    tab = {}

    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2026, 8, 3), value=decimal.Decimal('97224.53'))]

    # Juros, correção monetária, amortização e valor bruto.
    tab[1] = '72236.23', '43813.36', '0.00', '116049.60'  # Anterior à antecipação. Bate com o admin da operação.
    tab[2] = '49625.40', '8360.43', '39238.70', '97224.53'  # A antecipação.
    tab[3] = '7269.64', '1229.75', '0.00', '8499.39'
    tab[4] = '56560.43', '0.00', '0.00', '56560.43'  # Vale até o penúltimo: a série de IPCA se esgota aqui.
    tab[37] = '56560.43', '0.00', '5960761.30', '6017321.73'

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    for i, x in enumerate(sched, 1):
        assert [x.gain, x.pla, x.amort, x.raw] == [decimal.Decimal(y) for y in tab.get(i, tab[4])]

    assert len(sched) == kwa['term'] + 1  # A antecipação acrescenta uma linha ao fluxo regular.
    assert sum(x.amort for x in sched) == kwa['principal']

def test_will_create_jm_ipca_3():
    '''
    Mesma operação e mesma antecipação de "test_will_create_jm_ipca_2", com "amortizes_interest" falso.

    Aqui os 97.224,53 vão inteiros para o principal. Os juros e a correção do período ficam devidos, e o pagamento de
    07/08 os recolhe: 56.895,02 de juros, que são os 7.269,62 do seu próprio período mais os 49.625,40 travados, e
    9.578,22 de correção, que são 8.360,43 dos 27 dias sobre 6.000.000,00 mais 1.217,79 dos 4 dias sobre o saldo já
    reduzido.

    O período de quatro dias rende sobre 6.007.221,37, e não sobre os 5.902.775,47 de principal nominal: a correção
    travada continua incorporada ao saldo devedor enquanto não é liquidada.

    A segunda parte do teste é a que pega o defeito: a correção do período tem que crescer com a data da antecipação,
    porque quanto mais tarde ela ocorre, mais tempo o principal antecipado passa rendendo correção. Travar o fator em
    vez do valor tornava esse número constante, e a data deixava de importar.

    Ref File: https://docs.google.com/spreadsheets/d/1CH47cNnNc1QjcPb-WP7q6Gp1k1UNkDnQ
    Tab.....: Conferência
    '''

    kwa = _kwa_cri_ipa()
    tab = {}

    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2026, 8, 3), value=decimal.Decimal('97224.53'), amortizes_interest=False)]

    # Juros, correção monetária, amortização e valor bruto.
    tab[1] = '72236.23', '43813.36', '0.00', '116049.60'  # Idêntico ao do caso anterior.
    tab[2] = '49625.40', '0.00', '97224.53', '97224.53'  # A antecipação, inteira em principal.
    tab[3] = '7269.62', '9578.22', '0.00', '66473.24'  # Recolhe o juro e a correção travados.
    tab[4] = '56010.21', '0.00', '0.00', '56010.21'
    tab[37] = '56010.21', '0.00', '5902775.47', '5958785.68'

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    for i, x in enumerate(sched, 1):
        assert [x.gain, x.pla, x.amort, x.raw] == [decimal.Decimal(y) for y in tab.get(i, tab[4])]

    assert sum(x.amort for x in sched) == kwa['principal']

    # A correção do período 07/07 a 07/08, variando a data da antecipação dentro dele.
    def correcao(dia):
        kwb = _kwa_cri_ipa()
        kwb['insertions'] = [fincore.Amortization.Bare(date=dia, value=decimal.Decimal('97224.53'), amortizes_interest=False)]
        sch = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwb)]

        return sum(x.pla for x in sch if datetime.date(2026, 7, 7) < x.date <= datetime.date(2026, 8, 7))

    curva = [correcao(datetime.date(2026, 7, 8) + datetime.timedelta(days=d)) for d in (0, 7, 14, 26, 29)]

    assert curva == sorted(curva) and len(set(curva)) == len(curva)  # Estritamente crescente.

    # O limite superior é a correção do mês sem antecipação nenhuma: 0,16% sobre os seis milhões.
    assert max(curva) < decimal.Decimal('9600')

# Os casos de antecipação da operação "Solve - CR Sênior - Fluxo Irregular - 30 meses".
#
# Bullet, IPCA, capitalização diária em ano de 360 dias, com NOVE antecipações. É a operação que revelou que o fator
# de correção de uma antecipação, neste caminho, era acumulado desde a emissão em vez de cobrir o trecho — e que o
# mecanismo de diferimento, ao compor dois acumulados, contava a história duas vezes, três vezes, nove vezes.
#
# A série de índices do "_RicherIpcaBackend" cobre exatamente a memória de índices da operação, de junho de 2025 a
# junho de 2026, inclusive o agosto de 2025 negativo, que entra no piso zero.
#
def _kwa_solve():
    kwa = {}

    kwa['principal'] = decimal.Decimal('3850000')
    kwa['apy'] = decimal.Decimal('15.05')
    kwa['zero_date'] = datetime.date(2025, 7, 7)
    kwa['term'] = 30
    kwa['anniversary_date'] = datetime.date(2028, 1, 7)
    kwa['capitalisation'] = '360'
    kwa['first_dct_rule'] = 'AUTO'
    kwa['gain_output'] = 'settled'  # O modo que a plataforma usa: juros do período que a linha efetivamente liquida.
    kwa['vir'] = fincore.VariableIndex(code='IPCA', backend=_RicherIpcaBackend())

    return kwa

def _ins_solve():
    lst = [
        (datetime.date(2025, 12, 10), '206280.83'), (datetime.date(2026, 2, 9), '215488.13'),
        (datetime.date(2026, 3, 12), '400661.15'), (datetime.date(2026, 5, 20), '1036253.75'),
        (datetime.date(2026, 6, 1), '214781.80'), (datetime.date(2026, 6, 19), '203341.17'),
        (datetime.date(2026, 7, 2), '168571.43'), (datetime.date(2026, 7, 6), '60000.00'),
        (datetime.date(2026, 8, 21), '12633.45')
    ]

    return [fincore.Amortization.Bare(date=x, value=decimal.Decimal(y)) for x, y in lst]

def test_will_create_bullet_ipca_with_nine_prepayments():
    '''
    Operação "Solve - CR Sênior", Bullet - 30 meses - IPCA, com nove antecipações em ordem de imputação padrão.

    Cada antecipação liquida primeiro os juros corridos, depois a correção do seu trecho, e só o resto abate
    principal. Em 10/12/2025 e em 21/08/2026 os juros consomem o bruto inteiro: a correção fica devida, o fator é
    diferido, e o pagamento seguinte o recolhe.

    O fator de correção de cada antecipação cobre o TRECHO desde a entrada anterior, e não a acumulação desde a
    emissão. É o que torna sólida a composição de fatores diferidos: compor dois acumulados conta a história duas
    vezes. Antes desta correção, esta operação produzia R$ 1.073.174,06 de correção total, contra as poucas centenas
    de milhares que a série de índices permite, e o cronograma fechava com saldo devedor NEGATIVO de R$ 55.737,79.

    Os valores abaixo foram conferidos por uma implementação independente, que não chama esta biblioteca, e aprovados
    pelo financeiro em 26/08/2026. Na mesma conferência confirmou-se que juros devidos e não pagos continuam
    rendendo, junto do saldo — o que já era o comportamento desta biblioteca.

    Ref File: https://docs.google.com/spreadsheets/d/1gGMRFCArAj0x7y10zjxiW3V1yXyxkgVp
    Tab.....: Conferência
    '''

    kwa = _kwa_solve()
    tab = {}

    kwa['insertions'] = _ins_solve()

    # Juros, correção monetária, amortização e valor bruto.
    tab[1] = '206280.83', '0.00', '0.00', '206280.83'  # Os juros consomem o bruto; a correção fica devida.
    tab[2] = '132445.81', '62135.10', '20907.22', '215488.13'  # Recolhe a correção diferida do trecho anterior.
    tab[3] = '46701.85', '16055.79', '337903.51', '400661.15'
    tab[4] = '96753.72', '61322.06', '878177.97', '1036253.75'
    tab[5] = '12271.44', '6763.11', '195747.26', '214781.80'
    tab[6] = '17065.57', '8731.78', '177543.83', '203341.17'
    tab[7] = '11396.21', '5619.94', '151555.28', '168571.43'
    tab[8] = '3257.86', '1610.80', '55131.33', '60000.00'
    tab[9] = '12633.45', '0.00', '0.00', '12633.45'  # De novo os juros consomem o bruto.
    tab[10] = '471102.17', '3645.44', '2033033.60', '2507781.21'  # O pagamento final, em 07/01/2028.

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_bullet(**kwa)]

    # Antes do laço, que indexa a tabela pela posição: se o cronograma crescer, a mensagem daqui é útil, e a de um
    # "KeyError" na linha seguinte não seria.
    #
    assert len(sched) == len(kwa['insertions']) + 1  # Nove antecipações e o pagamento final.

    for i, x in enumerate(sched, 1):
        assert [x.gain, x.pla, x.amort, x.raw] == [decimal.Decimal(y) for y in tab[i]]

def test_will_close_bullet_ipca_with_prepayments_on_a_zero_balance():
    '''
    Invariantes do cronograma da operação "Solve - CR Sênior". Ver "test_will_create_bullet_ipca_with_nine_prepayments".

    Não asseveram valor nenhum, e é isso que os torna úteis: pegam a CLASSE do defeito, e não este caso. Antes da
    correção do fator por trecho, o primeiro deles falhava — o cronograma fechava com saldo devedor negativo, porque a
    correção recomposta a cada evento saía do saldo sem nunca ter entrado nele.

    O terceiro é o teto de acumulação: a correção total não pode passar do que a série de índices permite sobre o
    principal. De junho de 2025 a junho de 2026, com os negativos no piso zero, o IPCA acumula 5,01%; sobre os
    3.850.000 do principal isso limita a correção a menos de 200 mil, e o saldo ainda cai ao longo da operação.
    '''

    kwa = _kwa_solve()

    kwa['insertions'] = _ins_solve()

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_bullet(**kwa)]

    assert sched[-1].bal == _0
    assert sum(x.amort for x in sched) == kwa['principal']
    assert sum(x.pla for x in sched) < kwa['principal'] * decimal.Decimal('0.0501')

def test_wont_move_bullet_ipca_without_prepayment():
    '''
    Operação "Solve - CR Sênior" sem antecipação nenhuma. Ver "test_will_create_bullet_ipca_with_nine_prepayments".

    O caminho do defeito só é alcançado por uma inserção no cronograma, e este teste é a trava que prova que a
    correção do fator por trecho não escapou para o fluxo regular: sem antecipação a entrada anterior ao pagamento é a
    própria data zero, o acumulado nela é um, e o quociente não altera nada.
    '''

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_bullet(**_kwa_solve())]

    assert len(sched) == 1
    assert [sched[0].gain, sched[0].pla, sched[0].amort, sched[0].raw] == [decimal.Decimal(x) for x in ('1728409.70', '192807.06', '3850000.00', '5771216.75')]

def test_will_prorate_the_current_month_on_a_bullet_prepayment():
    '''
    Uma antecipação só, na operação "Solve - CR Sênior". Ver "test_will_create_bullet_ipca_with_nine_prepayments".

    Com uma antecipação não há diferimento, logo não há composição de fatores a errar. O que muda aqui é outra coisa:
    o mês em curso passa a entrar rateado por dias corridos, e não inteiro. Em 12/03/2026 o trecho desde a emissão
    cobre oito meses cheios e cinco dias do nono, e é essa fração que separa este valor do anterior.

    O teste existe para fixar esse efeito. Ele é deliberado, e é a convenção que a conferência aprovou.
    '''

    kwa = _kwa_solve()

    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2026, 3, 12), value=decimal.Decimal('400661.15'))]

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_bullet(**kwa)]

    assert sched[0].pla == decimal.Decimal('2316.79')
    assert sched[0].amort == _0  # Juros e correção consomem o bruto inteiro.
    assert sched[-1].bal == _0

def test_wont_move_the_total_price_level_adjustment_with_a_token_prepayment():
    '''
    Costura entre os dois extremos de um trecho, na operação "Solve - CR Sênior". Ver
    "test_will_create_bullet_ipca_with_nine_prepayments".

    Uma antecipação de um centavo não move o saldo devedor, logo não pode mover a correção monetária total do
    cronograma. O que ela move é a fronteira: o pagamento seguinte passa a cobrar o trecho a partir dela. Se os dois
    lados dessa fronteira forem medidos de formas diferentes — meses cheios num, dias corridos no outro — sobra uma
    fatia de índice mensal cobrada duas vezes, ou nenhuma, com o sinal decidido pelo dia do mês em que a antecipação
    cai. Ver "[FRONTEIRA-COMUM]".

    Por isso as três posições: aniversário, meio do período, e véspera do aniversário seguinte. É teste de
    invariante, sem valor de referência, e é isso que o torna útil — pega a CLASSE do defeito, não este caso. Os
    demais casos desta operação não o pegam: o mês fracionário dela cai num índice no piso zero, e passam tanto com
    a fronteira comum quanto sem ela.
    '''

    kwa = _kwa_solve()
    ref = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_bullet(**kwa)]
    tot = sum(x.pla for x in ref)

    for dia in (datetime.date(2026, 3, 7), datetime.date(2026, 3, 22), datetime.date(2026, 4, 6)):
        kwa = _kwa_solve()

        kwa['insertions'] = [fincore.Amortization.Bare(date=dia, value=decimal.Decimal('0.01'))]

        sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_bullet(**kwa)]

        assert sum(x.pla for x in sched) == tot
        assert sched[-1].bal == _0

def test_wont_depend_on_a_backend_that_pads_the_index_series():
    '''
    O cálculo não pode mudar porque o backend completa a série de índices, ou não completa.

    "calculate_ipca_factor" aplica o "ratio" ao último item que a série DEVOLVEU, e não ao mês da posição "period". O
    "InMemoryBackend" completa a série até o fim da janela, com meses zerados, e ali o expoente é inócuo. Os backends
    de produção devolvem só o que o BACEN publicou, e ali o expoente cai sobre o último mês PUBLICADO, que é devido
    por inteiro. No aniversário a fração corrida é zero, então aquele mês entraria elevado a zero e desapareceria: o
    acumulado andaria PARA TRÁS, e quitar no dia do aniversário sairia mais barato que na véspera. Ver
    "[RATIO-ULTIMO-ITEM]".

    As três datas cercam a janela de exposição, que vai do aniversário até o BACEN publicar. A memória desta operação
    termina em junho de 2026 e o aniversário é dia 7, então 06/08 está fora e 07/08 e 20/08 estão dentro. Sem a
    separação entre meses fechados e mês em curso, o bruto do pagamento final divergia entre os dois backends em
    1.317,54, e em 788,46 no meio do mês.

    A asserção é a IGUALDADE entre os dois backends, e não um valor de referência: o que se fixa aqui é que a
    biblioteca não depende do preenchimento, e um número de referência não diria isso.
    '''

    for dia in (datetime.date(2026, 8, 6), datetime.date(2026, 8, 7), datetime.date(2026, 8, 20)):
        out = []

        for backend in (_RicherIpcaBackend(), _UnpaddedIpcaBackend()):
            kwa = _kwa_solve()

            kwa['vir'] = fincore.VariableIndex('IPCA', backend=backend)
            kwa['insertions'] = [fincore.Amortization.Bare(date=dia, value=decimal.Decimal('0.01'))]

            sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_bullet(**kwa)]

            out.append([sched[-1].raw, sum(x.pla for x in sched), sched[-1].bal])

        assert out[0] == out[1]

def test_will_accrue_interest_over_deferred_price_level_adjustment():
    '''
    Correção devida e não liquidada continua no saldo devedor, e rende juros.

    Mesma operação e mesma data de "test_will_create_jm_ipca_2", com uma antecipação de 52.000. Ela cobre os
    49.625,40 de juros do período e só 2.374,60 dos 8.360,43 de correção devida, deixando 5.985,83 diferidos. Nenhum
    principal é abatido, porque a ordem de imputação só chega nele depois da correção inteira.

    Os juros do período seguinte, de quatro dias, incidem sobre 6.007.221,37 – que são os 6.000.000,00 de principal
    mais os 5.985,83 diferidos, o conjunto corrigido pelo fator do próprio período. Não sobre os 6.000.000,00 secos.

    A especificação de outubro de 2024 chama a correção mensal de "fórmula de correção tradicional mais amortização
    extraordinária obrigatória do IPCA mensal". Quando a amortização extraordinária sai pela metade, a outra metade
    permanece incorporada – e é essa a razão de ela render.

    Ref File: https://docs.google.com/spreadsheets/d/1CH47cNnNc1QjcPb-WP7q6Gp1k1UNkDnQ
    Tab.....: Conferência
    '''

    kwa = _kwa_cri_ipa()
    tab = {}

    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2026, 8, 3), value=decimal.Decimal('52000'))]

    # Juros, correção monetária, amortização e valor bruto.
    tab[1] = '72236.23', '43813.36', '0.00', '116049.60'
    tab[2] = '49625.40', '2374.60', '0.00', '52000.00'  # Os juros consomem quase tudo, e a correção fica pela metade.
    tab[3] = '7324.79', '7225.40', '0.00', '14550.19'  # Juros sobre o saldo com a correção diferida dentro.
    tab[4] = '56932.76', '0.00', '0.00', '56932.76'

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    for i, x in enumerate(sched, 1):
        if i in tab:
            assert [x.gain, x.pla, x.amort, x.raw] == [decimal.Decimal(y) for y in tab[i]]

    # Sem a incorporação, os juros do período de quatro dias cairiam para 7.317,49 – a diferença é o que a correção
    # diferida rende. O teste falha por baixo se alguém tirar "regs.correction" da base dos juros.
    #
    assert sched[2].gain > decimal.Decimal('7320')

    # E a correção segue conservando: o que a antecipação não pagou, o pagamento seguinte recolhe, recorrigido.
    assert sum(x.pla for x in sched) == decimal.Decimal('53413.36')

def test_wont_charge_regular_payment_on_the_prepayment_date():
    '''
    Antecipação lançada na mesma data de um pagamento regular.

    Quando as datas empatam, o cronograma põe a antecipação à frente – ver o parágrafo sobre precedência na
    "_interleave". Ela então herda o período em aberto inteiro, e o pagamento regular do mesmo dia fica com zero dias:
    sem juros, sem correção, sem amortização, valor bruto zero.

    Reproduz a sequência que quebrou a operação "CRI IPA Club Residencial" em agosto de 2026: uma antecipação em
    03/08 e outra em 07/08, esta na data da segunda parcela. O cronograma que o motor produz é consistente – os juros
    do período de 03/08 a 07/08 são cobrados uma vez só, pela antecipação. A duplicidade em produção veio de a parcela
    ter sido faturada sob o cronograma anterior, e não estornada quando a antecipação entrou uma hora depois.

    Este caso existe para fixar o comportamento, e não para conferir valor: é contra ele que a guarda do controlador
    – recusar antecipação com data igual ou anterior à de uma cobrança encerrada – precisa ser especificada.

    Thread: https://inco1.slack.com/archives/C05UP765QBA/p1786545421791909
    '''

    kwa = _kwa_cri_ipa()

    kwa['insertions'] = [
        fincore.Amortization.Bare(date=datetime.date(2026, 8, 3), value=decimal.Decimal('97224.53')),
        fincore.Amortization.Bare(date=datetime.date(2026, 8, 7), value=decimal.Decimal('58134.57'))
    ]

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]
    linhas = [x for x in sched if x.date == datetime.date(2026, 8, 7)]

    assert len(linhas) == 2

    antecipacao, regular = linhas

    # A antecipação vem primeiro, e leva o período de 03/08 a 07/08 inteiro.
    assert antecipacao.raw == kwa['insertions'][1].value
    assert [antecipacao.gain, antecipacao.pla, antecipacao.amort] == [decimal.Decimal(y) for y in ('7269.64', '1229.75', '49635.18')]

    # O pagamento regular do mesmo dia sai vazio.
    assert [regular.gain, regular.pla, regular.amort, regular.raw] == [_0, _0, _0, _0]

    # Nada se cobra duas vezes: o total do dia é o valor da antecipação, e nada além dele.
    assert antecipacao.raw + regular.raw == kwa['insertions'][1].value

    # No cronograma anterior, sem a segunda antecipação, esses mesmos juros e correção pertenciam ao pagamento
    # regular. É essa migração – e não um cálculo errado – que produz a cobrança em dobro quando a parcela já foi
    # faturada antes de a antecipação ser inserida.
    #
    kwb = _kwa_cri_ipa()

    kwb['insertions'] = kwa['insertions'][:1]

    anterior = next(x for x in fincore.build_jm(**kwb) if x.date == datetime.date(2026, 8, 7))
    anterior = t.cast(fincore.PriceAdjustedPayment, anterior)

    assert [anterior.gain, anterior.pla] == [antecipacao.gain, antecipacao.pla]
    assert anterior.raw == decimal.Decimal('8499.39')

    assert sum(x.amort for x in sched) == kwa['principal']

def test_will_collect_locked_interest_and_adjustment_on_a_later_prepayment():
    '''
    Uma antecipação amortizante recolhe o juro e a correção travados por uma antecipação anterior.

    Mesma operação de "test_will_create_jm_ipca_2", com duas antecipações no mesmo período: uma de 50.000 em 20/07,
    que não amortiza juros e trava os 23.825,55 do seu período junto com a correção; e uma de 150.000 em 03/08, com a
    ordem de imputação padrão. A segunda liquida o juro travado somado ao do próprio período, a correção travada
    recorrigida somada à do próprio período, e abate o restante do principal.

    O pagamento regular de 07/08 fica só com os quatro dias que lhe pertencem. É o assert que pega a dupla cobrança:
    sem o abatimento de "regs.interest.locked" na antecipação que o recolheu, o pagamento regular seguinte, que
    libera o registrador por inteiro, cobraria os 23.825,55 de novo.

    Os valores fixados aqui saem do próprio motor, conferidos pelas conservações: a soma das amortizações fecha o
    principal, e nenhum pagamento cobra além do juro e da correção do seu período.
    '''

    kwa = _kwa_cri_ipa()

    kwa['insertions'] = [
        fincore.Amortization.Bare(date=datetime.date(2026, 7, 20), value=decimal.Decimal('50000'), amortizes_interest=False),
        fincore.Amortization.Bare(date=datetime.date(2026, 8, 3), value=decimal.Decimal('150000'))
    ]

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]
    travada, coletora, regular = sched[1], sched[2], sched[3]

    # A primeira antecipação vai inteira para o principal, e trava juro e correção.
    assert [travada.gain, travada.pla, travada.amort, travada.raw] == [decimal.Decimal(y) for y in ('23825.55', '0.00', '50000.00', '50000.00')]

    # A segunda liquida o juro travado mais o do próprio período – o que sobra do valor bruto, tirados a correção e
    # o principal, são exatamente os juros das duas antecipações.
    #
    assert coletora.raw - coletora.pla - coletora.amort == travada.gain + coletora.gain
    assert [coletora.gain, coletora.pla, coletora.raw] == [decimal.Decimal(y) for y in ('25568.69', '8321.41', '150000.00')]

    # E o pagamento regular seguinte cobra apenas o próprio período: sem dupla cobrança do juro travado.
    assert regular.raw - regular.pla == regular.gain
    assert [regular.gain, regular.pla, regular.amort] == [decimal.Decimal(y) for y in ('7143.97', '1208.49', '0.00')]

    # Dali em diante, um Juros Mensais comum: cada parcela cobra o juro do seu mês, e nada mais.
    assert sched[4].raw == sched[4].gain == decimal.Decimal('55582.65')

    assert sum(x.amort for x in sched) == kwa['principal']

def test_will_settle_debt_with_max_value_prepayment_after_deferral():
    '''
    Uma antecipação de valor máximo quita a dívida inteira, mesmo com correção diferida no saldo.

    Mesma operação e mesma antecipação de "test_will_accrue_interest_over_deferred_price_level_adjustment": os
    52.000 de 03/08 cobrem os juros do período e só parte da correção, deixando 5.985,83 diferidos no saldo. Dois
    dias depois, uma antecipação de valor máximo pede a quitação.

    O teto da quitação é o saldo em vigor – principal corrigido pelo fator composto com o diferido, mais o juro
    corrido, menos o crédito do que já se pagou de correção. Medir o teto sem o diferido deixaria os 5.985,83
    recorrigidos para trás, e a dívida nunca fecharia.
    '''

    kwa = _kwa_cri_ipa()

    kwa['insertions'] = [
        fincore.Amortization.Bare(date=datetime.date(2026, 8, 3), value=decimal.Decimal('52000')),
        fincore.Amortization.Bare(date=datetime.date(2026, 8, 5), value=fincore.Amortization.Bare.MAX_VALUE)
    ]

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    # A quitação zera o saldo e leva todo o principal que restava.
    assert sched[-1].date == kwa['insertions'][1].date
    assert sched[-1].bal == _0
    assert sched[-1].amort == kwa['principal']

    # E leva junto o juro dos dois dias e a correção diferida recorrigida, mais a do próprio período.
    assert [sched[-1].gain, sched[-1].pla] == [decimal.Decimal(y) for y in ('3660.90', '6605.58')]

    assert sum(x.amort for x in sched) == kwa['principal']

def _kwa_encaixada():
    '''
    Fluxo mensal de 24 meses com a janela de correção ENCAIXADA – base constante, período crescendo de um em um.

    É o que "preprocess_jm" monta com "amortizes_correction" falso: a correção não é liquidada mês a mês, acumula no
    saldo devedor e sai inteira no último pagamento. Ver "[JANELAS-ENCAIXADAS]".
    '''

    return {
        'principal': decimal.Decimal('1000000'),
        'apy': decimal.Decimal('12'),
        'zero_date': datetime.date(2023, 1, 10),
        'term': 24,
        'vir': fincore.VariableIndex(code='IPCA', backend=_RicherIpcaBackend()),
        'amortizes_correction': False
    }

def _ins_encaixada():
    lst = [(datetime.date(2023, 6, 20), '50000'), (datetime.date(2023, 11, 15), '50000'), (datetime.date(2024, 5, 5), '50000')]

    return [fincore.Amortization.Bare(date=x, value=decimal.Decimal(y)) for x, y in lst]

def test_will_reproduce_the_nested_window_by_composing_stretches():
    '''
    Sem antecipação, compor os trechos reproduz a janela encaixada ao centavo.

    A janela encaixada passou a ser lida UM MÊS POR VEZ, o último da janela, e o acumulado é reconstruído pelo
    produto dos trechos que os pagamentos anteriores foram compondo. Este caso é o que prova que a reconstrução é
    exata, e não uma aproximação: o total tem de ser o mesmo de antes da mudança, quando a janela inteira era relida
    a cada pagamento. Ver "[JANELAS-ENCAIXADAS]".

    O piso de zero por mês continua dentro de "calculate_ipca_factor", então nenhum mês negativo escapa por ser lido
    isolado – a memória deste backend tem agosto de 2025 em −0,11%.
    '''

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**_kwa_encaixada())]

    assert sum(x.pla for x in sched) == decimal.Decimal('98946.55')
    assert sum(x.amort for x in sched) == _kwa_encaixada()['principal']
    assert sched[-1].bal == _0

def test_wont_compose_nested_price_level_windows():
    '''
    Antecipação numa janela ENCAIXADA não pode multiplicar acumulados.

    Cada pagamento relia a série inteira desde a base, e o mecanismo de diferimento compunha a janela da antecipação
    com a do pagamento seguinte – duas leituras da MESMA história, multiplicadas. Com três antecipações a correção
    total chegava a 247.081,22 contra as 98.946,55 do mesmo cronograma sem nenhuma.

    A asserção é de invariante, sem valor de referência, e é o que a torna útil: a antecipação DERRUBA o saldo
    devedor, então menos correção acumula, e o total tem de ficar ABAIXO do cronograma sem antecipação. Um total
    acima daquele teto denuncia a classe do defeito, qualquer que seja a aritmética.
    '''

    kwa = _kwa_encaixada()
    teto = sum(t.cast(fincore.PriceAdjustedPayment, x).pla for x in fincore.build_jm(**kwa))

    kwa['insertions'] = _ins_encaixada()

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build_jm(**kwa)]

    assert sum(x.pla for x in sched) < teto
    assert sum(x.amort for x in sched) == kwa['principal']
    assert sched[-1].bal == _0

@pytest.mark.enigmatic
def test_will_report_negative_price_level_adjustment_on_a_stepped_window():
    '''
    ⚠️ A janela em ESCADA com antecipação ainda erra, e este caso registra o quanto.

    Base constante e período CONSTANTE ao longo de um bloco de pagamentos, saltando de doze em doze. É a geometria de
    "test_will_create_livre_4", a ASAD Energia, conferida contra planilha – mas a planilha não tem antecipação, e é
    por isso que os sete casos "livre" passam sem cobrir isto.

    Com uma antecipação, a janela de doze meses é cobrada INTEIRA na data dela – 4.490,63 contra os 718,16 que o
    pagamento do mês cobra –, e o pagamento seguinte recebe uma correção NEGATIVA de 3.019,29 para compensar. É o
    mesmo defeito de composição de acumulados que "test_wont_compose_nested_price_level_windows" cobre na geometria
    encaixada, e aqui ele segue aberto.

    Por que não foi corrigido junto: a escada não é declarada por ninguém – "preprocess_livre" aceita o "pla" que o
    chamador montou –, e "period > 1" não a separa da encaixada. Corrigi-la exige decidir o que uma taxa por período
    deve cobrar quando o período é repartido, e para isso não há curva de referência aprovada. Ver
    "[JANELAS-ENCAIXADAS]".

    Os valores abaixo são CARACTERIZAÇÃO do defeito, não o resultado desejado. Quando o fix vier, este caso muda de
    números e sai do "enigmatic".
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('145000')
    kwa['apy'] = decimal.Decimal(10)
    kwa['vir'] = fincore.VariableIndex('IPCA', backend=_RicherIpcaBackend())
    kwa['amortizations'] = [fincore.Amortization(date=datetime.date(2022, 4, 5), amortizes_interest=False)]

    for i in range(1, 25):
        due = datetime.date(2022, 5, 5) + _MONTH * (i - 1)
        pla = fincore.PriceLevelAdjustment('IPCA', base_date=datetime.date(2021, 7, 1), shift='AUTO', period=12 if i <= 12 else 24)

        kwa['amortizations'].append(fincore.Amortization(date=due, amortization_ratio=decimal.Decimal(1) / 24, price_level_adjustment=pla))

    ref = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build(**kwa)]

    # Sem antecipação a taxa do período sai igual em todo pagamento do bloco de doze, e o total é o da planilha.
    assert [ref[4].pla, ref[5].pla] == [decimal.Decimal('718.16')] * 2

    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 9, 20), value=decimal.Decimal('5000'))]

    sched = [t.cast(fincore.PriceAdjustedPayment, x) for x in fincore.build(**kwa)]

    # Com ela, a antecipação de 20/09 cobra a janela de doze meses INTEIRA, e o pagamento de 05/10 recebe o negativo
    # que a compensa. Nenhum dos dois é o valor devido; é a composição de dois acumulados aparecendo.
    #
    assert sched[5].date == kwa['insertions'][0].date
    assert sched[5].pla == decimal.Decimal('4490.63')
    assert sched[6].pla == decimal.Decimal('-3019.29')

    # O principal e o saldo, esses fecham – o defeito é de decomposição, e some no total.
    assert sum(x.amort for x in sched) == sum(x.amort for x in ref)
    assert sched[-1].bal == _0
# }}}

# 🎭 Juros Mensais vandalizadas. {{{
@pytest.mark.parametrize('term', [1, 3, 6, 12, 60])
def test_will_create_jm_zanzy_1(term):
    lst = list(fincore.build_jm(_0, _0, datetime.date.min, term))

    assert len(lst) == 0

    for i, x in enumerate(fincore.build_jm(_1, _0, datetime.date.min, term), 1):
        if i < term:
            assert x.no == i
            assert x.date == datetime.date(i // 12 + 1, i % 12 + 1, 1)
            assert x.amort == x.gain == x.raw == x.tax == x.net == _0
            assert x.bal == _1

        elif i == term:
            assert x.no == i
            assert x.date == datetime.date(i // 12 + 1, i % 12 + 1, 1)
            assert x.amort == _1
            assert x.gain == _0
            assert x.raw == _1
            assert x.tax == _0
            assert x.net == _1
            assert x.bal == _0

    assert i == term

    for i, x in enumerate(fincore.build_jm(_0, _1, datetime.date.min, term), 1):
        assert x.no == i
        assert x.date == datetime.date(i // 12 + 1, i % 12 + 1, 1)
        assert x.amort == x.gain == x.raw == x.tax == x.net == x.bal == _0

    assert i == term

    for i, x in enumerate(fincore.build_jm(_1, _1, datetime.date.min, term), 1):
        if i < term:
            assert x.no == i
            assert x.date == datetime.date(i // 12 + 1, i % 12 + 1, 1)
            assert x.amort == x.gain == x.raw == x.tax == x.net == _0
            assert x.bal == _1

        elif i == term:
            assert x.no == i
            assert x.date == datetime.date(i // 12 + 1, i % 12 + 1, 1)
            assert x.amort == _1
            assert x.gain == _0
            assert x.raw == _1
            assert x.tax == _0
            assert x.net == _1
            assert x.bal == _0

    assert i == term
# }}}

# FR Price. {{{
#
# Esse teste gera trezentos e sessenta pagamentos. Não vou testar todos aqui, vou testar apenas trinta: os dez
# iniciais, os dez centrais, e os dez finais. O teste não verifica I.R. e valor líquido, já que a planilha não tem esse
# dado.
#
def test_will_create_price_1():
    '''
    Operação pré-fixada modalidade Price.

    Ref File: https://docs.google.com/spreadsheets/d/1yG3rmODqbvyqDLCFU4VLFTrJwFAnacKE9NlnwtCrN-k
    Tab.....: Sheet1
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal(6)
    kwa['zero_date'] = datetime.date(2022, 11, 28)
    kwa['term'] = 30 * 12

    # Juros, amortização, saldo.
    tab[1] = '486.76', '102.62', '99897.38'
    tab[2] = '486.26', '103.11', '99794.27'
    tab[3] = '485.75', '103.62', '99690.65'
    tab[4] = '485.25', '104.12', '99586.53'
    tab[5] = '484.74', '104.63', '99481.9'
    tab[6] = '484.23', '105.14', '99376.77'
    tab[7] = '483.72', '105.65', '99271.12'
    tab[8] = '483.21', '106.16', '99164.95'
    tab[9] = '482.69', '106.68', '99058.27'
    tab[10] = '482.17', '107.2', '98951.08'

    tab[176] = '349.35', '240.02', '71530.27'
    tab[177] = '348.18', '241.19', '71289.08'
    tab[178] = '347', '242.37', '71046.71'
    tab[179] = '345.82', '243.55', '70803.16'
    tab[180] = '344.64', '244.73', '70558.43'
    tab[181] = '343.45', '245.92', '70312.51'
    tab[182] = '342.25', '247.12', '70065.39'
    tab[183] = '341.05', '248.32', '69817.06'
    tab[184] = '339.84', '249.53', '69567.53'
    tab[185] = '338.62', '250.75', '69316.78'

    tab[351] = '27.93', '561.44', '5177.51'
    tab[352] = '25.2', '564.17', '4613.34'
    tab[353] = '22.46', '566.91', '4046.43'
    tab[354] = '19.7', '569.67', '3476.75'
    tab[355] = '16.92', '572.45', '2904.3'
    tab[356] = '14.14', '575.23', '2329.07'
    tab[357] = '11.34', '578.03', '1751.04'
    tab[358] = '8.52', '580.85', '1170.19'
    tab[359] = '5.7', '583.67', '586.52'
    tab[360] = '2.85', '586.52', 0

    for i, x in enumerate(fincore.build_price(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['zero_date'] + _MONTH * i
        assert x.raw == decimal.Decimal('589.37')

        if x.no in tab:
            assert [x.gain, x.amort, x.bal] == [decimal.Decimal(y) for y in tab[i]]

    assert i == kwa['term']

def test_will_create_price_2():
    '''
    Operação pré-fixada modalidade Price.

    Ref File: https://docs.google.com/spreadsheets/d/1yG3rmODqbvyqDLCFU4VLFTrJwFAnacKE9NlnwtCrN-k
    Tab.....: Credlar Chopin
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('481000')
    kwa['apy'] = decimal.Decimal(19)
    kwa['zero_date'] = datetime.date(2022, 4, 4)
    kwa['term'] = 24

    # Juros, imposto, valor líquido, amortização, saldo.
    tab[1] = '7023.41', '1580.27', '22322.28', '16879.14', '464120.86'
    tab[2] = '6776.95', '1524.81', '22377.74', '17125.61', '446995.25'
    tab[3] = '6526.88', '1468.55', '22434', '17375.67', '429619.58'
    tab[4] = '6273.17', '1411.46', '22491.09', '17629.38', '411990.2'
    tab[5] = '6015.75', '1353.54', '22549.01', '17886.8', '394103.39'
    tab[6] = '5754.57', '1150.91', '22751.64', '18147.98', '375955.41'
    tab[7] = '5489.58', '1097.92', '22804.63', '18412.97', '357542.44'
    tab[8] = '5220.72', '1044.14', '22858.41', '18681.83', '338860.61'
    tab[9] = '4947.94', '989.59', '22912.96', '18954.62', '319905.99'
    tab[10] = '4671.17', '934.23', '22968.32', '19231.39', '300674.6'
    tab[11] = '4390.36', '878.07', '23024.48', '19512.2', '281162.41'
    tab[12] = '4105.45', '718.45', '23184.1', '19797.11', '261365.3'
    tab[13] = '3816.37', '667.87', '23234.68', '20086.18', '241279.12'
    tab[14] = '3523.08', '616.54', '23286.01', '20379.47', '220899.64'
    tab[15] = '3225.51', '564.46', '23338.09', '20677.05', '200222.6'
    tab[16] = '2923.59', '511.63', '23390.92', '20978.97', '179243.63'
    tab[17] = '2617.26', '458.02', '23444.53', '21285.3', '157958.33'
    tab[18] = '2306.46', '403.63', '23498.92', '21596.1', '136362.24'
    tab[19] = '1991.12', '348.45', '23554.1', '21911.44', '114450.8'
    tab[20] = '1671.17', '292.46', '23610.09', '22231.38', '92219.42'
    tab[21] = '1346.56', '235.65', '23666.9', '22556', '69663.43'
    tab[22] = '1017.2', '178.01', '23724.54', '22885.35', '46778.08'
    tab[23] = '683.04', '119.53', '23783.02', '23219.52', '23558.56'
    tab[24] = '343.99', '51.6', '23850.95', '23558.56', 0

    for i, x in enumerate(fincore.build_price(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['zero_date'] + _MONTH * i
        assert x.raw == decimal.Decimal('23902.55')  # PMT.
        assert [x.gain, x.tax, x.net, x.amort, x.bal] == [decimal.Decimal(y) for y in tab[i]]

    assert i == kwa['term']

def test_will_create_price_3():
    '''
    Operação pré-fixada modalidade Price.

    Ref File: https://docs.google.com/spreadsheets/d/1yG3rmODqbvyqDLCFU4VLFTrJwFAnacKE9NlnwtCrN-k
    Tab.....: Residencial Arnaldo Patrus 2
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('181000')
    kwa['apy'] = decimal.Decimal(18)
    kwa['zero_date'] = datetime.date(2022, 4, 3)
    kwa['term'] = 24

    # Juros, imposto, valor líquido, amortização, saldo.
    tab[1] = '2513.81', '565.61', '8354.43', '6406.23', '174593.77'
    tab[2] = '2424.83', '545.59', '8374.45', '6495.21', '168098.56'
    tab[3] = '2334.63', '525.29', '8394.75', '6585.41', '161513.15'
    tab[4] = '2243.16', '504.71', '8415.33', '6676.87', '154836.27'
    tab[5] = '2150.43', '483.85', '8436.19', '6769.61', '148066.67'
    tab[6] = '2056.41', '411.28', '8508.76', '6863.63', '141203.04'
    tab[7] = '1961.09', '392.22', '8527.82', '6958.95', '134244.09'
    tab[8] = '1864.44', '372.89', '8547.15', '7055.6', '127188.49'
    tab[9] = '1766.45', '353.29', '8566.75', '7153.59', '120034.9'
    tab[10] = '1667.1', '333.42', '8586.62', '7252.94', '112781.96'
    tab[11] = '1566.36', '313.27', '8606.77', '7353.67', '105428.28'
    tab[12] = '1464.23', '256.24', '8663.8', '7455.81', '97972.48'
    tab[13] = '1360.68', '238.12', '8681.92', '7559.36', '90413.12'
    tab[14] = '1255.7', '219.75', '8700.29', '7664.34', '82748.78'
    tab[15] = '1149.25', '201.12', '8718.92', '7770.79', '74977.99'
    tab[16] = '1041.33', '182.23', '8737.81', '7878.71', '67099.28'
    tab[17] = '931.9', '163.08', '8756.96', '7988.14', '59111.14'
    tab[18] = '820.96', '143.67', '8776.37', '8099.08', '51012.06'
    tab[19] = '708.48', '123.98', '8796.06', '8211.56', '42800.5'
    tab[20] = '594.43', '104.03', '8816.01', '8325.61', '34474.9'
    tab[21] = '478.8', '83.79', '8836.25', '8441.24', '26033.66'
    tab[22] = '361.57', '63.27', '8856.77', '8558.47', '17475.19'
    tab[23] = '242.7', '42.47', '8877.57', '8677.34', '8797.85'
    tab[24] = '122.19', '18.33', '8901.71', '8797.85', 0

    for i, x in enumerate(fincore.build_price(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['zero_date'] + _MONTH * i
        assert x.raw == decimal.Decimal('8920.04')  # PMT.
        assert [x.gain, x.tax, x.net, x.amort, x.bal] == [decimal.Decimal(y) for y in tab[i]]

    assert i == kwa['term']

def test_will_create_price_4():
    '''
    Operação pré-fixada modalidade Price, com antecipação total.

    Ref File: https://docs.google.com/spreadsheets/d/1yG3rmODqbvyqDLCFU4VLFTrJwFAnacKE9NlnwtCrN-k
    Tab.....: Residencial da Mata
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('115000')
    kwa['apy'] = decimal.Decimal(15)
    kwa['zero_date'] = datetime.date(2021, 6, 4)
    kwa['term'] = 18
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 10, 6), value=decimal.Decimal('14010.76'))]

    # Juros, imposto, valor líquido, amortização, saldo.
    tab[1] = '1347.22', '303.12', '6820.25', '5776.15', '109223.85'
    tab[2] = '1279.55', '287.9', '6835.47', '5843.82', '103380.03'
    tab[3] = '1211.09', '272.49', '6850.88', '5912.28', '97467.76'
    tab[4] = '1141.83', '256.91', '6866.46', '5981.54', '91486.22'
    tab[5] = '1071.75', '241.14', '6882.23', '6051.61', '85434.6'
    tab[6] = '1000.86', '200.17', '6923.20', '6122.51', '79312.1'
    tab[7] = '929.13', '185.83', '6937.54', '6194.23', '73117.87'
    tab[8] = '856.57', '171.31', '6952.06', '6266.8', '66851.07'
    tab[9] = '783.15', '156.63', '6966.74', '6340.21', '60510.86'
    tab[10] = '708.88', '141.78', '6981.59', '6414.49', '54096.37'
    tab[11] = '633.73', '126.75', '6996.62', '6489.63', '47606.74'
    tab[12] = '557.71', '97.6', '7025.77', '6565.66', '41041.09'
    tab[13] = '480.79', '84.14', '7039.23', '6642.57', '34398.51'
    tab[14] = '402.98', '70.52', '7052.85', '6720.39', '27678.12'
    tab[15] = '324.25', '56.74', '7066.63', '6799.12', '20879.01'
    tab[16] = '244.6', '42.8', '7080.57', '6878.77', '14000.24'

    for i, x in enumerate(fincore.build_price(**kwa), 1):
        assert x.no == i

        # Fluxo Price ordinário.
        if x.no <= 16:
            assert x.date == kwa['zero_date'] + _MONTH * i
            assert x.raw == decimal.Decimal('7123.37')  # PMT.
            assert [x.gain, x.tax, x.net, x.amort, x.bal] == [decimal.Decimal(y) for y in tab[i]]

        # Antecipação total.
        else:
            assert x.date == kwa['insertions'][0].date
            assert x.amort == decimal.Decimal('14000.24')
            assert x.gain == decimal.Decimal('10.52')
            assert x.raw == decimal.Decimal('14010.76')
            assert x.tax == decimal.Decimal('1.84')
            assert x.net == decimal.Decimal('14008.92')
            assert x.bal == _0

    assert i == 17

def test_will_create_price_5():
    '''
    Operação pré-fixada modalidade Price, com antecipação parcial.

    Ref File: https://docs.google.com/spreadsheets/d/1yG3rmODqbvyqDLCFU4VLFTrJwFAnacKE9NlnwtCrN-k
    Tab.....: Provi
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('1000000')
    kwa['apy'] = decimal.Decimal(19)
    kwa['zero_date'] = datetime.date(2022, 1, 20)
    kwa['term'] = 24
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 6, 21), value=decimal.Decimal('55668.16'))]

    # Valo bruto, juros, imposto, valor líquido, amortização, saldo.
    tab[1] = '49693.46', '14601.69', '3285.38', '46408.08', '35091.77', '964908.23',
    tab[2] = '49693.46', '14089.29', '3170.09', '46523.37', '35604.17', '929304.05',
    tab[3] = '49693.46', '13569.41', '3053.12', '46640.34', '36124.05', '893180.00',
    tab[4] = '49693.46', '13041.93', '2934.44', '46759.02', '36651.53', '856528.47',
    tab[5] = '49693.46', '12506.76', '2814.02', '46879.44', '37186.70', '819341.77',
    tab[6] = '55668.16', '396.00', '89.10', '55579.06', '55272.16', '764069.62',  # Antecipação parcial.
    tab[7] = '45966.68', '10782.20', '2156.44', '43810.24', '35184.47', '728885.14',
    tab[8] = '46341.18', '10642.95', '2128.59', '44212.59', '35698.23', '693186.92',
    tab[9] = '46341.18', '10121.70', '2024.34', '44316.84', '36219.48', '656967.44',
    tab[10] = '46341.18', '9592.83', '1918.57', '44422.61', '36748.35', '620219.09',
    tab[11] = '46341.18', '9056.25', '1811.25', '44529.93', '37284.93', '582934.16',
    tab[12] = '46341.18', '8511.82', '1702.36', '44638.82', '37829.36', '545104.80',
    tab[13] = '46341.18', '7959.45', '1392.90', '44948.28', '38381.73', '506723.07',
    tab[14] = '46341.18', '7399.01', '1294.83', '45046.35', '38942.17', '467780.91',
    tab[15] = '46341.18', '6830.39', '1195.32', '45145.86', '39510.79', '428270.12',
    tab[16] = '46341.18', '6253.47', '1094.36', '45246.82', '40087.71', '388182.41',
    tab[17] = '46341.18', '5668.12', '991.92', '45349.26', '40673.06', '347509.34',
    tab[18] = '46341.18', '5074.22', '887.99', '45453.19', '41266.96', '306242.39',
    tab[19] = '46341.18', '4471.66', '782.54', '45558.64', '41869.52', '264372.87',
    tab[20] = '46341.18', '3860.29', '675.55', '45665.63', '42480.89', '221891.98',
    tab[21] = '46341.18', '3240.00', '567.00', '45774.18', '43101.18', '178790.79',
    tab[22] = '46341.18', '2610.65', '456.86', '45884.32', '43730.53', '135060.26',
    tab[23] = '46341.18', '1972.11', '345.12', '45996.06', '44369.07', '90691.19',
    tab[24] = '46341.18', '1324.24', '231.74', '46109.44', '45016.93', '45674.26',
    tab[25] = '46341.18', '666.92', '100.04', '46241.14', '45674.26', 0

    for i, x in enumerate(fincore.build_price(**kwa), 1):
        assert x.no == i

        # Antecipação parcial.
        if x.no == 6:
            assert x.date == kwa['insertions'][0].date

        # Fluxo ordinário.
        else:
            assert x.date == kwa['zero_date'] + _MONTH * (i if i < 6 else i - 1)

        assert [x.raw, x.gain, x.tax, x.net, x.amort, x.bal] == [decimal.Decimal(y) for y in tab[i]]

    assert i == 25

def test_will_create_price_6():
    '''
    Operação pré-fixada modalidade Price.

    Ref File: https://docs.google.com/spreadsheets/d/1yG3rmODqbvyqDLCFU4VLFTrJwFAnacKE9NlnwtCrN-k
    Tab.....: Varanda da Vila 3
    '''

    kwa = {}
    tab = {}

    kwa['principal'] = decimal.Decimal('1592500')
    kwa['apy'] = decimal.Decimal(20)
    kwa['zero_date'] = datetime.date(2022, 10, 31)
    kwa['anniversary_date'] = datetime.date(2022, 12, 5)
    kwa['term'] = 30

    # Juros, imposto, valor líquido, amortização, saldo.
    tab[1] = '27553.25', '6199.48', '63575.11', '42221.34', '1550278.66'
    tab[2] = '23733.95', '5340.14', '61261.53', '42867.73', '1507410.93'
    tab[3] = '23077.66', '5192.47', '61409.2', '43524.01', '1463886.92'
    tab[4] = '22411.33', '5042.55', '61559.12', '44190.34', '1419696.58'
    tab[5] = '21734.8', '4890.33', '61711.34', '44866.87', '1374829.71'
    tab[6] = '21047.91', '4209.58', '62392.09', '45553.76', '1329275.96'
    tab[7] = '20350.51', '4070.1', '62531.57', '46251.16', '1283024.8'
    tab[8] = '19642.43', '3928.49', '62673.18', '46959.24', '1236065.55'
    tab[9] = '18923.51', '3784.7', '62816.97', '47678.16', '1188387.39'
    tab[10] = '18193.58', '3638.72', '62962.95', '48408.09', '1139979.3'
    tab[11] = '17452.48', '3490.5', '63111.17', '49149.19', '1090830.11'
    tab[12] = '16700.03', '2922.51', '63679.16', '49901.64', '1040928.46'
    tab[13] = '15936.06', '2788.81', '63812.86', '50665.61', '990262.86'
    tab[14] = '15160.4', '2653.07', '63948.6', '51441.27', '938821.58'
    tab[15] = '14372.86', '2515.25', '64086.42', '52228.81', '886592.77'
    tab[16] = '13573.27', '2375.32', '64226.35', '53028.41', '833564.37'
    tab[17] = '12761.43', '2233.25', '64368.42', '53840.24', '779724.12'
    tab[18] = '11937.16', '2089', '64512.67', '54664.51', '725059.61'
    tab[19] = '11100.28', '1942.55', '64659.12', '55501.39', '669558.22'
    tab[20] = '10250.58', '1793.85', '64807.82', '56351.09', '613207.13'
    tab[21] = '9387.88', '1642.88', '64958.79', '57213.8', '555993.33'
    tab[22] = '8511.96', '1489.59', '65112.08', '58089.71', '497903.62'
    tab[23] = '7622.64', '1333.96', '65267.71', '58979.03', '438924.59'
    tab[24] = '6719.7', '1007.96', '65593.71', '59881.97', '379042.62'
    tab[25] = '5802.94', '870.44', '65731.23', '60798.73', '318243.89'
    tab[26] = '4872.15', '730.82', '65870.85', '61729.53', '256514.36'
    tab[27] = '3927.1', '589.06', '66012.61', '62674.57', '193839.79'
    tab[28] = '2967.58', '445.14', '66156.53', '63634.09', '130205.7'
    tab[29] = '1993.38', '299.01', '66302.66', '64608.29', '65597.41'
    tab[30] = '1004.26', '150.64', '66451.03', '65597.41', 0

    for i, x in enumerate(fincore.build_price(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['anniversary_date'] + _MONTH * (i - 1)

        if i == 1:
            assert x.raw == decimal.Decimal('69774.59')  # PMT + extra interest.

        else:
            assert x.raw == decimal.Decimal('66601.67')  # PMT.

        assert [x.gain, x.tax, x.net, x.amort, x.bal] == [decimal.Decimal(y) for y in tab[i]]

    assert i == kwa['term']
# }}}

# 🗽 Livre. {{{
@pytest.mark.parametrize('sac_pct', [
    decimal.Decimal('0.0333333333'),  # Totals 0.999999999 when multiplied by thirty, which is exactly 1e-9 from one.
    decimal.Decimal('0.0333333333333'),  # Totals 0.999999999999 when multiplied by thirty, 1e-12 from one.
    decimal.Decimal('0.0333333333334'),  # Totals 1.000000000002 when multiplied by thirty, 2e-12 from one.
    decimal.Decimal('0.03333333334')  # Totals 1.000000002 when multiplied by thirty, 2e-10 from one.
])
def test_will_create_livre_1(sac_pct):
    '''
    Verifies that amortization percentages should add up to one, no more and no less, within 10⁻¹⁰ relative tolerance.

    See https://docs.python.org/3/library/math.html#math.isclose.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1100500')
    kwa['apy'] = decimal.Decimal('11')
    kwa['vir'] = fincore.VariableIndex(code='IPCA')
    kwa['amortizations'] = tab = []

    tab.append(fincore.Amortization(date=datetime.date(2022, 7, 8), amortizes_interest=False))

    for i in range(1, 31):
        ipca = fincore.PriceLevelAdjustment('IPCA')
        date = datetime.date(2022, 7, 8) + _MONTH * i

        ipca.base_date = datetime.date(2022, 7, 1)
        ipca.period = i + 1

        tab.append(fincore.Amortization(date, amortization_ratio=sac_pct, amortizes_interest=True, price_level_adjustment=ipca))

    for _ in fincore.build(**kwa):
        pass  # FIXME: check something here?

    assert i == 30

def test_will_create_livre_2():
    '''
    Operação pós-fixada CDI, modalidade Livre.

    Carteira Pride - Tranche I - Parcelas Amortizadas - 36 meses.

    Ref File: https://docs.google.com/spreadsheets/d/1z0PhJcLK-noG-rH-t24NcdPQJZJ1-B0P0b0o4muv3rY
    Tab.....: 01
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('5122000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['vir'] = fincore.VariableIndex(code='CDI')
    kwa['amortizations'] = tab1 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 5, 12), amortizes_interest=False))

    for i in range(1, 37):
        tab1.append(fincore.Amortization(date=tab1[0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.02777777777778')))

    # Juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = '79936.07', '222213.85', '17985.62', '204228.23', '4979722.22'
    tab2[2] = '72109.57', '214387.35', '16224.65', '198162.7', '4837444.44'
    tab2[3] = '81458.47', '223736.25', '18328.16', '205408.09', '4695166.67'
    tab2[4] = '69907.72', '212185.5', '15729.24', '196456.26', '4552888.89'
    tab2[5] = '74623.51', '216901.28', '16790.29', '200110.99', '4410611.11'
    tab2[6] = '68979.98', '211257.76', '13796', '197461.76', '4268333.33'
    tab2[7] = '60352.49', '202630.27', '12070.5', '190559.77', '4126055.56'
    tab2[8] = '70727.73', '213005.51', '14145.55', '198859.96', '3983777.78'
    tab2[9] = '65295.57', '207573.35', '13059.11', '194514.24', '3841500'
    tab2[10] = '51439.39', '193717.17', '10287.88', '183429.29', '3699222.22'
    tab2[11] = '57854.18', '200131.96', '11570.84', '188561.12', '3556944.44'
    tab2[12] = '52960.40', '195238.17', '9268.07', '185970.10', '3414666.67'
    tab2[13] = '50841.98', '193119.76', '8897.35', '184222.41', '3272388.89'
    tab2[14] = '53635.64', '195913.42', '9386.24', '186527.18', '3130111.11'
    tab2[15] = '53265.51', '195543.28', '9321.46', '186221.82', '2987833.33'
    tab2[16] = '45613.30', '187891.08', '7982.33', '179908.75', '2845555.56'
    tab2[17] = '44764.42', '187042.20', '7833.77', '179208.43', '2703277.78'
    tab2[18] = '41897.72', '184175.50', '7332.10', '176843.40', '2561000.00'
    tab2[19] = '37174.56', '179452.34', '6505.55', '172946.79', '2418722.22'
    tab2[20] = '37564.68', '179842.46', '6573.82', '173268.64', '2276444.44'
    tab2[21] = '31896.38', '174174.16', '5581.87', '168592.29', '2134166.67'
    tab2[22] = '29363.26', '171641.04', '5138.57', '166502.47', '1991888.89'
    tab2[23] = '29456.93', '171734.71', '5154.96', '166579.75', '1849611.11'
    tab2[24] = '24710.49', '166988.27', '3706.57', '163281.70', '1707333.33'
    tab2[25] = '23594.13', '165871.91', '3539.12', '162332.79', '1565055.56'
    tab2[26] = '21627.95', '163905.73', '3244.19', '160661.54', '1422777.78'
    tab2[27] = '18762.19', '161039.97', '2814.33', '158225.64', '1280500.00'
    tab2[28] = '18505.73', '160783.51', '2775.86', '158007.65', '1138222.22'
    tab2[29] = '15905.53', '158183.30', '2385.83', '155797.47', '995944.44'

    for i, x in enumerate(fincore.build(**kwa), 1):
        if i < 30:
            assert x.no == i
            assert x.date == tab1[0].date + _MONTH * i
            assert x.amort == decimal.Decimal('142277.78')
            assert [x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 1

def test_will_create_livre_3a():
    '''
    Operação pré-fixada modalidade Livre c/ carência de 6 meses.

    Crédito - Estudantes de Medicina

    Ref File: https://docs.google.com/spreadsheets/d/1S1FbR3HZLavkybf2uvXvHbL0ftUVPbmcsynNqiXZkZo
    Tab.....: Crédito - Estudantes de Medicina
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('520000')
    kwa['apy'] = decimal.Decimal('21.5')
    kwa['amortizations'] = tab1 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 8, 8), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 9, 8), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 10, 8), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 11, 8), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 12, 8), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 1, 8), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 2, 8), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 3, 8), amortization_ratio=decimal.Decimal('0.02608593235'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 4, 8), amortization_ratio=decimal.Decimal('0.0265127262'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 5, 8), amortization_ratio=decimal.Decimal('0.02694650285'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 6, 8), amortization_ratio=decimal.Decimal('0.02738737656'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 7, 8), amortization_ratio=decimal.Decimal('0.02783546343'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 8, 8), amortization_ratio=decimal.Decimal('0.02829088149'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 9, 8), amortization_ratio=decimal.Decimal('0.02875375067'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 10, 8), amortization_ratio=decimal.Decimal('0.02922419289'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 11, 8), amortization_ratio=decimal.Decimal('0.02970233205'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 12, 8), amortization_ratio=decimal.Decimal('0.03018829408'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 1, 8), amortization_ratio=decimal.Decimal('0.03068220697'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 2, 8), amortization_ratio=decimal.Decimal('0.03118420081'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 3, 8), amortization_ratio=decimal.Decimal('0.0316944078'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 4, 8), amortization_ratio=decimal.Decimal('0.03221296233'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 5, 8), amortization_ratio=decimal.Decimal('0.03274000096'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 6, 8), amortization_ratio=decimal.Decimal('0.03327566252'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 7, 8), amortization_ratio=decimal.Decimal('0.03382008807'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 8, 8), amortization_ratio=decimal.Decimal('0.03437342101'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 9, 8), amortization_ratio=decimal.Decimal('0.03493580706'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 10, 8), amortization_ratio=decimal.Decimal('0.03550739436'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 11, 8), amortization_ratio=decimal.Decimal('0.03608833344'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2024, 12, 8), amortization_ratio=decimal.Decimal('0.03667877731'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2025, 1, 8), amortization_ratio=decimal.Decimal('0.03727888147'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2025, 2, 8), amortization_ratio=decimal.Decimal('0.03788880398'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2025, 3, 8), amortization_ratio=decimal.Decimal('0.03850870548'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2025, 4, 8), amortization_ratio=decimal.Decimal('0.03913874923'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2025, 5, 8), amortization_ratio=decimal.Decimal('0.03977910117'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2025, 6, 8), amortization_ratio=decimal.Decimal('0.04042992996'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2025, 7, 8), amortization_ratio=decimal.Decimal('0.041091407'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2025, 8, 8), amortization_ratio=decimal.Decimal('0.0417637065'), amortizes_interest=True))

    # Pagamentos – amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '8507.76', 0, 0, 0, '528507.76'
    tab2[2] = 0, '8646.95', 0, 0, 0, '537154.71'
    tab2[3] = 0, '8788.43', 0, 0, 0, '545943.14'
    tab2[4] = 0, '8932.22', 0, 0, 0, '554875.36'
    tab2[5] = 0, '9078.36', 0, 0, 0, '563953.71'
    tab2[6] = 0, '9226.89', 0, 0, 0, '573180.6'
    tab2[7] = '13564.68', '9377.85', '24329.80', '2153.02', '22176.78', '558228.65'
    tab2[8] = '13786.62', '9133.22', '25644.10', '2371.50', '23272.60', '541717.77'
    tab2[9] = '14012.18', '8863.08', '26778.47', '2553.26', '24225.21', '523802.38'
    tab2[10] = '14241.44', '8569.97', '27641.11', '2679.93', '24961.18', '504731.25'
    tab2[11] = '14474.44', '8257.94', '28168.41', '2738.79', '25429.62', '484820.78'
    tab2[12] = '14711.26', '7932.19', '28334.22', '2384.02', '25950.20', '464418.74'
    tab2[13] = '14951.95', '7598.39', '28153.06', '2310.19', '25842.87', '443864.07'
    tab2[14] = '15196.58', '7262.09', '27676.61', '2184.01', '25492.60', '423449.55'
    tab2[15] = '15445.21', '6928.09', '26984.07', '2019.30', '24964.77', '403393.57'
    tab2[16] = '15697.91', '6599.95', '26168.46', '1832.35', '24336.11', '383825.06'
    tab2[17] = '15954.75', '6279.79', '25321.76', '1639.23', '23682.53', '364783.09'
    tab2[18] = '16215.78', '5968.24', '24521.92', '1453.57', '23068.35', '346229.41'
    tab2[19] = '16481.09', '5664.68', '23824.32', '1285.06', '22539.26', '328069.78'
    tab2[20] = '16750.74', '5367.57', '23258.57', '1138.87', '22119.70', '310178.78'
    tab2[21] = '17024.80', '5074.86', '22830.63', '1016.02', '21814.61', '292423'
    tab2[22] = '17303.34', '4784.35', '22528.48', '914.40', '21614.08', '274678.88'
    tab2[23] = '17586.45', '4494.04', '22329.53', '830.04', '21499.49', '256843.39'
    tab2[24] = '17874.18', '4202.23', '22207.65', '650.02', '21557.63', '238837.97'
    tab2[25] = '18166.62', '3907.65', '22138.40', '595.77', '21542.63', '220607.21'
    tab2[26] = '18463.85', '3609.37', '22102.10', '545.74', '21556.36', '202114.49'
    tab2[27] = '18765.93', '3306.81', '22084.63', '497.80', '21586.83', '183336.67'
    tab2[28] = '19072.96', '2999.58', '22076.98', '450.60', '21626.38', '164259.27'
    tab2[29] = '19385.02', '2687.46', '22073.95', '403.34', '21670.61', '144872.78'
    tab2[30] = '19702.18', '2370.27', '22072.88', '355.61', '21717.27', '125170.17'
    tab2[31] = '20024.53', '2047.92', '22072.55', '307.20', '21765.35', '105145.53'
    tab2[32] = '20352.15', '1720.29', '22072.47', '258.05', '21814.42', '84793.36'
    tab2[33] = '20685.13', '1387.31', '22072.45', '208.10', '21864.35', '64108.22'
    tab2[34] = '21023.56', '1048.88', '22072.44', '157.33', '21915.11', '43084.66'
    tab2[35] = '21367.53', '704.91', '22072.44', '105.74', '21966.70', '21717.13'
    tab2[36] = '21717.13', '355.32', '22072.44', '53.30', '22019.14', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == tab1[0].date + _MONTH * i

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 1 == len(tab2)

def test_will_create_livre_3b():
    '''
    Operação pós-fixada CDI, modalidade Livre c/ carência de 3 meses.

    Hipotética 1 - CDI + Carência de 3 meses

    Ref File: https://docs.google.com/spreadsheets/d/1UcgpmsZRCs3xyobSj6GIVWTSazRAz834fiuXqyOSVFM
    Tab.....: Hipotética 1 - CDI + Carência de 3 meses
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['vir'] = fincore.VariableIndex(code='CDI')
    kwa['amortizations'] = tab1 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 2, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 3, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 4, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 5, 1), amortization_ratio=decimal.Decimal('0.3333333333'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 6, 1), amortization_ratio=decimal.Decimal('0.3333333333'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 1), amortization_ratio=decimal.Decimal('0.3333333334'), amortizes_interest=True))

    # Pagamentos – amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '1222.59', 0, 0, 0, '101222.59'
    tab2[2] = 0, '1213.32', 0, 0, 0, '102435.91'
    tab2[3] = 0, '1476.89', 0, 0, 0, '103912.80'
    tab2[4] = '33333.33', '1328.31', '35965.91', '592.33', '35373.58', '69275.20'
    tab2[5] = '33333.33', '1073.67', '36146.03', '632.86', '35513.17', '34202.84'
    tab2[6] = '33333.33', '515.44', '34718.29', '276.99', '34441.30', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == tab1[0].date + _MONTH * i

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 1 == len(tab2)

def test_will_create_livre_4():
    '''
    Operação pré-fixada modalidade Livre c/ correção monetária por IPCA.

    ASAD Energia.

    Ref File: https://docs.google.com/spreadsheets/d/1mxhXoqP-f_SUQS-f_e4F79jqiBMuHJdZ0H3Gof67pGA
    Tab.....: ASAD Energia
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('145000')
    kwa['apy'] = decimal.Decimal(10)  # Decimals can be created with integers.
    kwa['vir'] = fincore.VariableIndex('IPCA')
    kwa['amortizations'] = []

    # Monta a tabela de amortizações.
    tab1 = []

    tab1.append((datetime.date(2022, 9, 5), decimal.Decimal('0.0134830659'), 12))
    tab1.append((datetime.date(2022, 10, 5), decimal.Decimal('0.0135905818'), 12))
    tab1.append((datetime.date(2022, 11, 5), decimal.Decimal('0.0136989550'), 12))
    tab1.append((datetime.date(2022, 12, 5), decimal.Decimal('0.0138081924'), 12))
    tab1.append((datetime.date(2023, 1, 5), decimal.Decimal('0.0139183008'), 12))
    tab1.append((datetime.date(2023, 2, 5), decimal.Decimal('0.0140292873'), 12))
    tab1.append((datetime.date(2023, 3, 5), decimal.Decimal('0.0141411588'), 12))
    tab1.append((datetime.date(2023, 4, 5), decimal.Decimal('0.0142539224'), 12))
    tab1.append((datetime.date(2023, 5, 5), decimal.Decimal('0.0143675852'), 12))
    tab1.append((datetime.date(2023, 6, 5), decimal.Decimal('0.0144821543'), 12))
    tab1.append((datetime.date(2023, 7, 5), decimal.Decimal('0.0145976371'), 12))
    tab1.append((datetime.date(2023, 8, 5), decimal.Decimal('0.0147140407'), 12))
    tab1.append((datetime.date(2023, 9, 5), decimal.Decimal('0.0148313725'), 24))
    tab1.append((datetime.date(2023, 10, 5), decimal.Decimal('0.0149496400'), 24))
    tab1.append((datetime.date(2023, 11, 5), decimal.Decimal('0.0150688505'), 24))
    tab1.append((datetime.date(2023, 12, 5), decimal.Decimal('0.0151890116'), 24))
    tab1.append((datetime.date(2024, 1, 5), decimal.Decimal('0.0153101309'), 24))
    tab1.append((datetime.date(2024, 2, 5), decimal.Decimal('0.0154322161'), 24))
    tab1.append((datetime.date(2024, 3, 5), decimal.Decimal('0.0155552747'), 24))
    tab1.append((datetime.date(2024, 4, 5), decimal.Decimal('0.0156793147'), 24))
    tab1.append((datetime.date(2024, 5, 5), decimal.Decimal('0.0158043437'), 24))
    tab1.append((datetime.date(2024, 6, 5), decimal.Decimal('0.0159303698'), 24))
    tab1.append((datetime.date(2024, 7, 5), decimal.Decimal('0.0160574008'), 24))
    tab1.append((datetime.date(2024, 8, 5), decimal.Decimal('0.0161854448'), 24))
    tab1.append((datetime.date(2024, 9, 5), decimal.Decimal('0.0163145098'), 36))
    tab1.append((datetime.date(2024, 10, 5), decimal.Decimal('0.0164446040'), 36))
    tab1.append((datetime.date(2024, 11, 5), decimal.Decimal('0.0165757355'), 36))
    tab1.append((datetime.date(2024, 12, 5), decimal.Decimal('0.0167079128'), 36))
    tab1.append((datetime.date(2025, 1, 5), decimal.Decimal('0.0168411440'), 36))
    tab1.append((datetime.date(2025, 2, 5), decimal.Decimal('0.0169754377'), 36))
    tab1.append((datetime.date(2025, 3, 5), decimal.Decimal('0.0171108022'), 36))
    tab1.append((datetime.date(2025, 4, 5), decimal.Decimal('0.0172472461'), 36))
    tab1.append((datetime.date(2025, 5, 5), decimal.Decimal('0.0173847781'), 36))
    tab1.append((datetime.date(2025, 6, 5), decimal.Decimal('0.0175234068'), 36))
    tab1.append((datetime.date(2025, 7, 5), decimal.Decimal('0.0176631409'), 36))
    tab1.append((datetime.date(2025, 8, 5), decimal.Decimal('0.0178039892'), 36))
    tab1.append((datetime.date(2025, 9, 5), decimal.Decimal('0.0179459608'), 48))
    tab1.append((datetime.date(2025, 10, 5), decimal.Decimal('0.0180890644'), 48))
    tab1.append((datetime.date(2025, 11, 5), decimal.Decimal('0.0182333091'), 48))
    tab1.append((datetime.date(2025, 12, 5), decimal.Decimal('0.0183787041'), 48))
    tab1.append((datetime.date(2026, 1, 5), decimal.Decimal('0.0185252584'), 48))
    tab1.append((datetime.date(2026, 2, 5), decimal.Decimal('0.0186729814'), 48))
    tab1.append((datetime.date(2026, 3, 5), decimal.Decimal('0.0188218824'), 48))
    tab1.append((datetime.date(2026, 4, 5), decimal.Decimal('0.0189719708'), 48))
    tab1.append((datetime.date(2026, 5, 5), decimal.Decimal('0.0191232559'), 48))
    tab1.append((datetime.date(2026, 6, 5), decimal.Decimal('0.0192757474'), 48))
    tab1.append((datetime.date(2026, 7, 5), decimal.Decimal('0.0194294550'), 48))
    tab1.append((datetime.date(2026, 8, 5), decimal.Decimal('0.0195843882'), 48))
    tab1.append((datetime.date(2026, 9, 5), decimal.Decimal('0.0197405568'), 60))
    tab1.append((datetime.date(2026, 10, 5), decimal.Decimal('0.0198979708'), 60))
    tab1.append((datetime.date(2026, 11, 5), decimal.Decimal('0.0200566400'), 60))
    tab1.append((datetime.date(2026, 12, 5), decimal.Decimal('0.0202165745'), 60))
    tab1.append((datetime.date(2027, 1, 5), decimal.Decimal('0.0203777843'), 60))
    tab1.append((datetime.date(2027, 2, 5), decimal.Decimal('0.0205402796'), 60))
    tab1.append((datetime.date(2027, 3, 5), decimal.Decimal('0.0207040707'), 60))
    tab1.append((datetime.date(2027, 4, 5), decimal.Decimal('0.0208691707'), 60))

    # Amortization schedule – day zero, the next four entries, and the rest.
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 4, 5), amortizes_interest=False))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 5, 5), amortization_ratio=decimal.Decimal('0.0130614411')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 6, 5), amortization_ratio=decimal.Decimal('0.0131655949')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 7, 5), amortization_ratio=decimal.Decimal('0.0132705792')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 8, 5), amortization_ratio=decimal.Decimal('0.0133764006')))

    for date, pct, period in tab1:
        pla = fincore.PriceLevelAdjustment('IPCA', base_date=datetime.date(2021, 7, 1), shift='AUTO', period=period)

        kwa['amortizations'].append(fincore.Amortization(date=date, amortization_ratio=pct, price_level_adjustment=pla))

    # Pagamentos – correção, amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '1893.91', '1156.25', '3050.16', '260.16', '2790.00', '143106.09'
    tab2[2] = 0, '1909.01', '1141.15', '3050.16', '256.76', '2793.40', '141197.08'
    tab2[3] = 0, '1924.23', '1125.93', '3050.16', '253.33', '2796.83', '139272.85'
    tab2[4] = 0, '1939.58', '1110.58', '3050.16', '249.88', '2800.28', '137333.27'
    tab2[5] = '232.39', '1955.04', '1225.29', '3412.72', '327.98', '3084.74', '151470.27'
    tab2[6] = '234.24', '1970.63', '1207.85', '3412.72', '288.42', '3124.30', '149265.39'
    tab2[7] = '236.11', '1986.35', '1190.26', '3412.72', '285.28', '3127.44', '147042.93'
    tab2[8] = '237.99', '2002.19', '1172.54', '3412.72', '282.11', '3130.61', '144802.75'
    tab2[9] = '239.89', '2018.15', '1154.68', '3412.72', '278.91', '3133.81', '142544.70'
    tab2[10] = '241.81', '2034.25', '1136.67', '3412.72', '275.70', '3137.02', '140268.65'
    tab2[11] = '243.73', '2050.47', '1118.52', '3412.72', '272.45', '3140.27', '137974.45'
    tab2[12] = '245.68', '2066.82', '1100.23', '3412.72', '235.53', '3177.19', '135661.95'
    tab2[13] = '247.64', '2083.30', '1081.79', '3412.72', '232.65', '3180.07', '133331.01'
    tab2[14] = '249.61', '2099.91', '1063.20', '3412.72', '229.74', '3182.98', '130981.49'
    tab2[15] = '251.60', '2116.66', '1044.46', '3412.72', '226.81', '3185.91', '128613.23'
    tab2[16] = '253.61', '2133.54', '1025.58', '3412.72', '223.86', '3188.86', '126226.09'
    tab2[17] = '367.04', '2150.55', '1053.15', '3570.73', '248.53', '3322.20', '129552.73'
    tab2[18] = '369.96', '2167.70', '1033.07', '3570.73', '245.53', '3325.20', '127015.07'
    tab2[19] = '372.91', '2184.98', '1012.84', '3570.73', '242.51', '3328.22', '124457.17'
    tab2[20] = '375.89', '2202.41', '992.44', '3570.73', '239.46', '3331.27', '121878.88'
    tab2[21] = '378.88', '2219.97', '971.88', '3570.73', '236.38', '3334.35', '119280.03'
    tab2[22] = '381.90', '2237.67', '951.16', '3570.73', '233.29', '3337.44', '116660.45'
    tab2[23] = '384.95', '2255.51', '930.27', '3570.73', '230.16', '3340.57', '114019.99'
    tab2[24] = '388.02', '2273.50', '909.21', '3570.73', '194.58', '3376.15', '111358.47'
    tab2[25] = '391.11', '2291.63', '887.99', '3570.73', '191.87', '3378.86', '108675.72'
    tab2[26] = '394.23', '2309.90', '866.60', '3570.73', '189.12', '3381.61', '105971.59'
    tab2[27] = '397.38', '2328.32', '845.03', '3570.73', '186.36', '3384.37', '103245.89'
    tab2[28] = '400.54', '2346.89', '823.30', '3570.73', '183.58', '3387.15', '100498.46'
    tab2[29] = '520.81', '2365.60', '835.27', '3721.69', '203.41', '3518.28', '101860.69'
    tab2[30] = '524.97', '2384.47', '812.25', '3721.69', '200.58', '3521.11', '98951.25'
    tab2[31] = '529.15', '2403.48', '789.05', '3721.69', '197.73', '3523.96', '96018.62'
    tab2[32] = '533.37', '2422.65', '765.67', '3721.69', '194.86', '3526.83', '93062.60'
    tab2[33] = '537.63', '2441.97', '742.09', '3721.69', '191.96', '3529.73', '90083.00'
    tab2[34] = '541.91', '2461.44', '718.33', '3721.69', '189.04', '3532.65', '87079.65'
    tab2[35] = '546.24', '2481.07', '694.39', '3721.69', '186.09', '3535.60', '84052.35'
    tab2[36] = '550.59', '2500.85', '670.25', '3721.69', '183.13', '3538.56', '81000.91'
    tab2[37] = '554.98', '2520.79', '645.91', '3721.69', '180.13', '3541.56', '77925.13'
    tab2[38] = '559.41', '2540.89', '621.39', '3721.69', '177.12', '3544.57', '74824.83'
    tab2[39] = '563.87', '2561.16', '596.66', '3721.69', '174.08', '3547.61', '71699.81'
    tab2[40] = '568.36', '2581.58', '571.74', '3721.69', '171.02', '3550.67', '68549.87'
    tab2[41] = '598.98', '2602.16', '551.12', '3752.27', '172.52', '3579.75', '65911.97'
    tab2[42] = '603.76', '2622.91', '525.59', '3752.27', '169.40', '3582.87', '62685.30'
    tab2[43] = '608.58', '2643.83', '499.86', '3752.27', '166.27', '3586.00', '59432.89'
    tab2[44] = '613.43', '2664.91', '473.93', '3752.27', '163.10', '3589.17', '56154.55'
    tab2[45] = '618.32', '2686.16', '447.78', '3752.27', '159.92', '3592.35', '52850.07'
    tab2[46] = '623.25', '2707.58', '421.43', '3752.27', '156.70', '3595.57', '49519.23'
    tab2[47] = '628.22', '2729.17', '394.87', '3752.27', '153.46', '3598.81', '46161.84'
    tab2[48] = '633.23', '2750.94', '368.10', '3752.27', '150.20', '3602.07', '42777.67'
    tab2[49] = '638.28', '2772.87', '341.12', '3752.27', '146.91', '3605.36', '39366.52'
    tab2[50] = '643.37', '2794.98', '313.91', '3752.27', '143.59', '3608.68', '35928.17'
    tab2[51] = '648.50', '2817.27', '286.50', '3752.27', '140.25', '3612.02', '32462.40'
    tab2[52] = '653.67', '2839.74', '258.86', '3752.27', '136.88', '3615.39', '28968.99'
    tab2[53] = '658.88', '2862.38', '231.00', '3752.27', '133.48', '3618.79', '25447.73'
    tab2[54] = '664.14', '2885.21', '202.92', '3752.27', '130.06', '3622.21', '21898.38'
    tab2[55] = '669.43', '2908.21', '174.62', '3752.27', '126.61', '3625.66', '18320.74'
    tab2[56] = '674.77', '2931.40', '146.09', '3752.27', '123.13', '3629.14', '14714.56'
    tab2[57] = '680.15', '2954.78', '117.34', '3752.27', '119.62', '3632.65', '11079.63'
    tab2[58] = '685.58', '2978.34', '88.35', '3752.27', '116.09', '3636.18', '7415.72'
    tab2[59] = '691.04', '3002.09', '59.13', '3752.27', '112.53', '3639.74', '3722.58'
    tab2[60] = '696.55', '3026.03', '29.68', '3752.27', '108.94', '3643.33', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == kwa['amortizations'][0].date + _MONTH * i

        if i <= 4:
            assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i][1:]]

        else:
            x = t.cast(fincore.PriceAdjustedPayment, x)

            assert [x.pla, x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(kwa['amortizations']) - 1 == len(tab2)

def test_will_create_livre_5a():
    '''
    Operação modalidade Livre com aniversário e carência trimestral.

    Ref File: https://docs.google.com/spreadsheets/d/1S1FbR3HZLavkybf2uvXvHbL0ftUVPbmcsynNqiXZkZo
    Tab.....: Hipotética 01 - Trimestral c/ Aniversário
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('750000')
    kwa['apy'] = decimal.Decimal('50')
    kwa['amortizations'] = tab1 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2020, 2, 20), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 3, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 4, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 5, 15), amortization_ratio=decimal.Decimal('0.25')))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 6, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 7, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 8, 15), amortization_ratio=decimal.Decimal('0.25')))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 9, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 10, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 11, 15), amortization_ratio=decimal.Decimal('0.25')))
    tab1.append(fincore.Amortization(date=datetime.date(2020, 12, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2021, 1, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2021, 2, 15), amortization_ratio=decimal.Decimal('0.25')))

    # Amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '19878.14', 0, 0, 0, '769878.14'
    tab2[2] = 0, '26457.70', 0, 0, 0, '796335.84'
    tab2[3] = '187500.00', '27366.94', '226450.90', '8763.95', '217686.95', '597251.88'
    tab2[4] = 0, '20525.21', 0, 0, 0, '617777.09'
    tab2[5] = 0, '21230.58', 0, 0, 0, '639007.67'
    tab2[6] = '187500.00', '21960.19', '247714.02', '13548.16', '234165.86', '413253.83'
    tab2[7] = 0, '14201.92', 0, 0, 0, '427455.75'
    tab2[8] = 0, '14689.98', 0, 0, 0, '442145.73'
    tab2[9] = '187500.00', '15194.82', '253054.11', '13110.82', '239943.29', '204286.43'
    tab2[10] = 0, '7020.52', 0, 0, 0, '211306.96'
    tab2[11] = 0, '7261.79', 0, 0, 0, '218568.75'
    tab2[12] = '187500.00', '7511.35', '226080.10', '6751.52', '219328.58', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == tab1[1].date + _MONTH * (i - 1)
        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 1 == len(tab2)

def test_will_create_livre_5b():
    '''
    Operação modalidade Livre CDI com aniversário e carência de 3 meses.

    Ref File: https://docs.google.com/spreadsheets/d/1UcgpmsZRCs3xyobSj6GIVWTSazRAz834fiuXqyOSVFM
    Tab.....: Hipotética 3 - CDI + Aniv. e carência
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['vir'] = fincore.VariableIndex(code='CDI')
    kwa['amortizations'] = tab1 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 2, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 3, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 4, 15), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 5, 15), amortization_ratio=decimal.Decimal('0.3333333333'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 6, 15), amortization_ratio=decimal.Decimal('0.3333333333'), amortizes_interest=True))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 15), amortization_ratio=decimal.Decimal('0.3333333334'), amortizes_interest=True))

    # Pagamentos – amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '1854.15', 0, 0, 0, '101854.15'
    tab2[2] = 0, '1166.84', 0, 0, 0, '103020.99'
    tab2[3] = 0, '1588.82', 0, 0, 0, '104609.81'
    tab2[4] = '33333.33', '1363.46', '36233.40', '652.51', '35580.89', '69739.87'
    tab2[5] = '33333.33', '1088.39', '36470.53', '705.87', '35764.66', '34357.73'
    tab2[6] = '33333.33', '523.90', '34881.64', '309.66', '34571.98', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == tab1[1].date + _MONTH * (i - 1)

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 1 == len(tab2)

def test_will_create_livre_6a():
    '''
    Operação pós-fixada IPCA, modalidade Livre.

    Unique Tower - Proteção Contra Inflação

    Ref File: https://docs.google.com/spreadsheets/d/1mxhXoqP-f_SUQS-f_e4F79jqiBMuHJdZ0H3Gof67pGA
    Tab.....: Unique Tower - PCI
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1100500')
    kwa['apy'] = decimal.Decimal('11')
    kwa['vir'] = fincore.VariableIndex(code='IPCA')
    kwa['amortizations'] = tab1 = []

    # Amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 8), amortizes_interest=False))

    for i in range(1, 31):
        pla = fincore.PriceLevelAdjustment(code='IPCA', base_date=datetime.date(2022, 7, 1), period=i, shift='M-1', amortizes_adjustment=True)

        tab1.append(fincore.Amortization(date=tab1[0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.033333333333333335'), price_level_adjustment=pla))

    # Pagamentos – correção, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = '245.78', '9676.82', '46605.94', '2232.59', '44373.35', '1070944.24'
    tab2[2] = '245.78', '9354.26', '46283.37', '2160.01', '44123.36', '1034015.13'
    tab2[3] = '245.78', '9031.70', '45960.81', '2087.43', '43873.38', '997086.01'
    tab2[4] = '245.78', '8709.14', '45638.25', '2014.86', '43623.39', '960156.90'
    tab2[5] = '463.66', '8436.06', '45583.05', '2002.44', '43580.61', '928674.84'
    tab2[6] = '615.96', '8144.86', '45444.15', '1752.16', '43691.99', '895183.11'
    tab2[7] = '847.22', '7867.54', '45398.09', '1742.95', '43655.14', '863202.69'
    tab2[8] = '1046.13', '7579.69', '45309.15', '1725.16', '43583.99', '830048.20'
    tab2[9] = '1363.06', '7311.04', '45357.43', '1734.82', '43622.61', '798974.21'
    tab2[10] = '1633.19', '7028.26', '45344.78', '1732.29', '43612.49', '766330.41'
    tab2[11] = '1866.92', '6734.42', '45284.67', '1720.27', '43564.40', '732454.77'
    tab2[12] = '1955.58', '6412.41', '45051.33', '1464.40', '43586.93', '695500.50'
    tab2[13] = '1955.58', '6074.91', '44713.83', '1405.34', '43308.49', '656861.59'
    tab2[14] = '2001.95', '5744.30', '44429.59', '1355.59', '43074.00', '618964.54'
    tab2[15] = '2090.93', '5418.84', '44193.10', '1314.21', '42878.89', '581613.90'
    tab2[16] = '2191.74', '5093.37', '43968.44', '1274.89', '42693.55', '544251.02'
    tab2[17] = '2285.04', '4765.22', '43733.59', '1233.80', '42499.79', '506588.85'
    tab2[18] = '2394.15', '4437.24', '43514.72', '1195.49', '42319.23', '468929.81'
    tab2[19] = '2612.99', '4118.85', '43415.17', '1178.07', '42237.10', '432259.50'
    tab2[20] = '2778.03', '3791.47', '43252.83', '1149.66', '42103.17', '394613.63'
    tab2[21] = '3105.56', '3475.40', '43264.29', '1151.67', '42112.62', '358100.03'
    tab2[22] = '3169.22', '3132.86', '42985.42', '1102.86', '41882.56', '318820.44'
    tab2[23] = '3320.66', '2795.35', '42799.34', '1070.30', '41729.04', '280027.96'
    tab2[24] = '3504.68', '2457.18', '42645.19', '894.28', '41750.91', '241128.07'
    tab2[25] = '3589.07', '2110.58', '42382.99', '854.95', '41528.04', '201362.04'
    tab2[26] = '3742.11', '1765.50', '42190.94', '826.14', '41364.80', '161701.77'
    tab2[27] = '3742.11', '1412.40', '41837.84', '773.18', '41064.66', '121276.33'
    tab2[28] = '3919.98', '1063.96', '41667.27', '747.59', '40919.68', '81206.63'
    tab2[29] = '3919.98', '709.31', '41312.62', '694.39', '40618.23', '40603.31'
    tab2[30] = '3919.98', '354.65', '40957.97', '641.20', '40316.77', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        x = t.cast(fincore.PriceAdjustedPayment, x)

        assert x.no == i
        assert x.date == tab1[0].date + _MONTH * i
        assert x.amort == decimal.Decimal('36683.33')
        assert [x.pla, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 1 == len(tab2)

# Esse teste é parametrizado para demonstrar que o argumento "calc_date" não
# afeta a tabela de pagamentos caso a data informada seja igual ou maior que
# data de quitação do empréstimo. Observe que o parâmetro "runaway" também não
# tem efeito algum nesses casos. A biblioteca nunca gera pagamentos após a data
# de quitação, mesmo que o cronograma regular ultrapasse essa data, o que
# acontece em uma antecipação total.
#
# No caso abaixo, o empréstimo sofre antecipação total no dia 6 de janeiro de
# 2022.
#
@pytest.mark.parametrize('calc_date', [
    None,
    fincore.CalcDate(value=datetime.date(2023, 1, 6), runaway=False),
    fincore.CalcDate(value=datetime.date(2023, 1, 6), runaway=True),
    fincore.CalcDate(value=datetime.date(2024, 1, 6), runaway=False),
    fincore.CalcDate(value=datetime.date(2025, 1, 6), runaway=True)
])
def test_will_create_livre_6b(calc_date):
    '''
    Operação pós-fixada IPCA, modalidade Livre c/ antecipação total.

    Unique Tower - Proteção Contra Inflação

    Ref File: https://docs.google.com/spreadsheets/d/1mxhXoqP-f_SUQS-f_e4F79jqiBMuHJdZ0H3Gof67pGA
    Tab.....: Unique Tower - PCI c/ AT
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1100500')
    kwa['apy'] = decimal.Decimal('11')
    kwa['vir'] = fincore.VariableIndex(code='IPCA')
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2023, 1, 6), value=decimal.Decimal('939851.51'))]
    kwa['calc_date'] = calc_date

    # Amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 8), amortizes_interest=False))

    for i in range(1, 31):
        pla = fincore.PriceLevelAdjustment(code='IPCA', base_date=datetime.date(2022, 7, 1), period=i, shift='M-1', amortizes_adjustment=True)

        tab1.append(fincore.Amortization(date=tab1[0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.033333333333333335'), price_level_adjustment=pla))

    # Pagamentos – correção, amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = '245.78', '36683.33', '9676.82', '46605.94', '2232.59', '44373.35', '1070944.24'
    tab2[2] = '245.78', '36683.33', '9354.26', '46283.37', '2160.01', '44123.36', '1034015.13'
    tab2[3] = '245.78', '36683.33', '9031.70', '45960.81', '2087.43', '43873.38', '997086.01'
    tab2[4] = '245.78', '36683.33', '8709.14', '45638.25', '2014.86', '43623.39', '960156.90'
    tab2[5] = '463.66', '36683.33', '8436.06', '45583.05', '2002.44', '43580.61', '928674.84'
    tab2[6] = '15152.95', '917083.33', '7615.23', '939851.51', '4553.64', '935297.87', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        x = t.cast(fincore.PriceAdjustedPayment, x)

        assert x.no == i

        if i < 6:
            assert x.date == tab1[0].date + _MONTH * i

        else:
            assert x.date == kwa['insertions'][0].date

        assert [x.pla, x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab2)

def test_will_create_livre_7():
    '''
    Operação Resolvvi, primeiro e segundo pagamentos.

    Modalidade Livre com antecipação durante o período de carência.

    Ref File: https://docs.google.com/spreadsheets/d/1S1FbR3HZLavkybf2uvXvHbL0ftUVPbmcsynNqiXZkZo
    Tab.....: Resolvvi - Pré-Fixada - Parcelas Amortizadas
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('660000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = []

    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2023, 7, 28), value=decimal.Decimal('34454.09')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2023, 8, 21), value=decimal.Decimal('90252.22')))

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2023, 6, 19), amortizes_interest=False))

    for i in range(29):
        tab1.append(fincore.Amortization(date=datetime.date(2023, 7, 21) + _MONTH * i, amortizes_interest=False))

    tab1.append(fincore.Amortization(date=datetime.date(2025, 12, 21), amortization_ratio=_1))

    # Amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '11386.71', 0, 0, 0, '671386.71'
    tab2[2] = '20550.47', '2516.91', '34454.09', '3128.31', '31325.78', '639449.53'
    tab2[3] = '81995.82', '8256.40', '90252.22', '1857.69', '88394.53', '557453.71'
    tab2[4] = 0, 0, 0, 0, 0, '557453.71'
    tab2[5] = 0, '9314.47', 0, 0, 0, '566768.18'
    tab2[6] = 0, '9470.11', 0, 0, 0, '576238.29'
    tab2[7] = 0, '9628.34', 0, 0, 0, '585866.64'
    tab2[8] = 0, '9789.22', 0, 0, 0, '595655.86'
    tab2[9] = 0, '9952.79', 0, 0, 0, '605608.66'
    tab2[10] = 0, '10119.09', 0, 0, 0, '615727.75'
    tab2[11] = 0, '10288.17', 0, 0, 0, '626015.92'
    tab2[12] = 0, '10460.08', 0, 0, 0, '636476.00'
    tab2[13] = 0, '10634.85', 0, 0, 0, '647110.85'
    tab2[14] = 0, '10812.55', 0, 0, 0, '657923.41'
    tab2[15] = 0, '10993.22', 0, 0, 0, '668916.62'
    tab2[16] = 0, '11176.90', 0, 0, 0, '680093.53'
    tab2[17] = 0, '11363.66', 0, 0, 0, '691457.19'
    tab2[18] = 0, '11553.53', 0, 0, 0, '703010.72'
    tab2[19] = 0, '11746.58', 0, 0, 0, '714757.30'
    tab2[20] = 0, '11942.85', 0, 0, 0, '726700.15'
    tab2[21] = 0, '12142.41', 0, 0, 0, '738842.56'
    tab2[22] = 0, '12345.29', 0, 0, 0, '751187.85'
    tab2[23] = 0, '12551.57', 0, 0, 0, '763739.42'
    tab2[24] = 0, '12761.29', 0, 0, 0, '776500.72'
    tab2[25] = 0, '12974.52', 0, 0, 0, '789475.24'
    tab2[26] = 0, '13191.31', 0, 0, 0, '802666.55'
    tab2[27] = 0, '13411.73', 0, 0, 0, '816078.28'
    tab2[28] = 0, '13635.82', 0, 0, 0, '829714.10'
    tab2[29] = 0, '13863.66', 0, 0, 0, '843577.77'
    tab2[30] = 0, '14095.31', 0, 0, 0, '857673.08'
    tab2[31] = 0, '14330.83', 0, 0, 0, '872003.91'
    tab2[32] = '557453.71', '14570.28', '886574.19', '49368.07', '837206.12', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i

        if i == 1:
            assert x.date == tab1[1].date + _MONTH * (i - 1)  # Cronograma regular.

        elif i == 2:
            assert x.date == kwa['insertions'][0].date  # Antecipação.

        elif i == 3:
            assert x.date == kwa['insertions'][1].date  # Antecipação.

        else:
            assert x.date == tab1[1].date + _MONTH * (i - 3)  # Cronograma regular.

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) + 1 == len(tab2)

def test_will_create_livre_8a():
    '''
    Operação hipotética, modalidade Livre, com antecipação durante o período de carência.

    Ref File: https://docs.google.com/spreadsheets/d/1S1FbR3HZLavkybf2uvXvHbL0ftUVPbmcsynNqiXZkZo
    Tab.....: Hipotética 02 - Antecipação
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('750000')
    kwa['apy'] = decimal.Decimal('50')
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 2, 10), value=decimal.Decimal('45000'))]

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 2, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 3, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 4, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 5, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 6, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 8, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 9, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 10, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 11, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 12, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 1, 1), amortization_ratio=_1))

    # Amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '25774.56', 0, 0, 0, '775774.56'
    tab2[2] = '10754.09', '8471.35', '45000', '7705.33', '37294.67', '739245.91'
    tab2[3] = 0, '17145.30', 0, 0, 0, '756391.21'
    tab2[4] = 0, '25994.20', 0, 0, 0, '782385.42'
    tab2[5] = 0, '26887.52', 0, 0, 0, '809272.94'
    tab2[6] = 0, '27811.54', 0, 0, 0, '837084.48'
    tab2[7] = 0, '28767.31', 0, 0, 0, '865851.79'
    tab2[8] = 0, '29755.93', 0, 0, 0, '895607.73'
    tab2[9] = 0, '30778.53', 0, 0, 0, '926386.26'
    tab2[10] = 0, '31836.27', 0, 0, 0, '958222.53'
    tab2[11] = 0, '32930.35', 0, 0, 0, '991152.88'
    tab2[12] = 0, '34062.04', 0, 0, 0, '1025214.92'
    tab2[13] = '739245.91', '35232.62', '1060447.54', '56210.29', '1004237.25', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i

        if i == 1:
            assert x.date == datetime.date(2022, 2, 1)

        elif i == 2:
            assert x.date == datetime.date(2022, 2, 10)

        else:
            assert x.date == tab1[1].date + _MONTH * (i - 2)

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) == len(tab2)

def test_will_create_livre_8b():
    '''
    Operação pós-fixada CDI hipotética, modalidade Livre, com antecipação dutrante o período de carência.

    Hipotética 2 - CDI + Antecipação em carência

    Ref File: https://docs.google.com/spreadsheets/d/1UcgpmsZRCs3xyobSj6GIVWTSazRAz834fiuXqyOSVFM
    Tab.....: Hipotética 2 - CDI + Antecipação em carência
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['vir'] = fincore.VariableIndex(code='CDI')
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 2, 15), value=decimal.Decimal('10000'))]

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 2, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 3, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 4, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 5, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 6, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 1), amortization_ratio=_1, amortizes_interest=True))

    # Pagamentos – amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '1222.59', 0, 0, 0, '101222.59'
    tab2[2] = '8145.85', '631.56', '10000.00', '417.18', '9582.82', '91854.15'
    tab2[3] = 0, '524.64', 0, 0, 0, '92378.79'
    tab2[4] = 0, '1331.89', 0, 0, 0, '93710.68'
    tab2[5] = 0, '1197.89', 0, 0, 0, '94908.58'
    tab2[6] = 0, '1470.95', 0, 0, 0, '96379.53'
    tab2[7] = '91854.15', '1452.45', '97831.98', '1195.57', '96636.41', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i

        if i == 2:
            assert x.date == kwa['insertions'][0].date  # Antecipação.

        else:
            assert x.date == tab1[0].date + _MONTH * (1 if i == 1 else i - 1)

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) == len(tab2)

def test_will_create_livre_9a():
    '''
    Operação hipotética, modalidade Livre, com antecipação durante o período de carência.

    Ref File: https://docs.google.com/spreadsheets/d/1S1FbR3HZLavkybf2uvXvHbL0ftUVPbmcsynNqiXZkZo
    Tab.....: Hipotética 03 - Antecipação Total
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('750000')
    kwa['apy'] = decimal.Decimal('50')
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 2, 10), value=decimal.Decimal('784245.91'))]

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 2, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 3, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 4, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 5, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 6, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 8, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 9, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 10, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 11, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 12, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 1, 1), amortization_ratio=_1))

    # Amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '25774.56', 0, 0, 0, '775774.56'
    tab2[2] = '750000.00', '8471.35', '784245.91', '7705.33', '776540.58', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == datetime.date(2022, 2, 1) if i == 1 else x.date == datetime.date(2022, 2, 10)

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 11 == len(tab2)

def test_will_create_livre_9b():
    '''
    Operação pós-fixada CDI hipotética, modalidade Livre, com antecipação dutrante o período de carência.

    Hipotética 4 - CDI + Antecipação total em carência

    Ref File: https://docs.google.com/spreadsheets/d/1UcgpmsZRCs3xyobSj6GIVWTSazRAz834fiuXqyOSVFM
    Tab.....: Hipotética 4 - CDI + Antecipação total em carência
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('6')
    kwa['vir'] = fincore.VariableIndex(code='CDI')
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 2, 15), value=decimal.Decimal('101854.15'))]

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 2, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 3, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 4, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 5, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 6, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 1), amortization_ratio=_1, amortizes_interest=True))

    # Pagamentos – amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = 0, '1222.59', 0, 0, 0, '101222.59'
    tab2[2] = '100000', '631.56', '101854.15', '417.18', '101436.97', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == datetime.date(2022, 2, 1) if i == 1 else x.date == kwa['insertions'][0].date

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 5 == len(tab2)

def test_will_create_livre_10():
    '''
    Operação hipotética, modalidade Livre, incorporação de juros e amortização de principal.

    Ref File: https://docs.google.com/spreadsheets/d/1S1FbR3HZLavkybf2uvXvHbL0ftUVPbmcsynNqiXZkZo
    Tab.....: Hipotética 04 - Incorp. & Amort.
    '''

    pct = _1 / decimal.Decimal('12')
    kwa = {}

    kwa['principal'] = decimal.Decimal('750000')
    kwa['apy'] = decimal.Decimal('50')
    kwa['amortizations'] = tab1 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 2, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 3, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 4, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 5, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 6, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 7, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 8, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 9, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 10, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 11, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2022, 12, 1), amortizes_interest=False, amortization_ratio=pct))
    tab1.append(fincore.Amortization(date=datetime.date(2023, 1, 1), amortization_ratio=pct))

    # Amortização, juros, valor bruto, imposto, valor líquido, saldo devedor.
    tab2 = {}

    tab2[1] = '62500.00', '25774.56', '62500.00', '0.00', '62500.00', '713274.56',
    tab2[2] = '62500.00', '24512.45', '62500.00', '0.00', '62500.00', '675287.02',
    tab2[3] = '62500.00', '23206.97', '62500.00', '0.00', '62500.00', '635993.98',
    tab2[4] = '62500.00', '21856.62', '62500.00', '0.00', '62500.00', '595350.61',
    tab2[5] = '62500.00', '20459.87', '62500.00', '0.00', '62500.00', '553310.48',
    tab2[6] = '62500.00', '19015.11', '62500.00', '0.00', '62500.00', '509825.59',
    tab2[7] = '62500.00', '17520.71', '62500.00', '0.00', '62500.00', '464846.30',
    tab2[8] = '62500.00', '15974.95', '62500.00', '0.00', '62500.00', '418321.24',
    tab2[9] = '62500.00', '14376.06', '62500.00', '0.00', '62500.00', '370197.31',
    tab2[10] = '62500.00', '12722.23', '62500.00', '0.00', '62500.00', '320419.54',
    tab2[11] = '62500.00', '11011.56', '62500.00', '0.00', '62500.00', '268931.10',
    tab2[12] = '62500.00', '9242.11', '278173.21', '37742.81', '240430.40', 0

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == tab1[i].date

        assert [x.amort, x.gain, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab2[i]]

    assert i == len(tab1) - 1 == len(tab2)
# }}}

# Modos de visualização de juros. {{{
def test_will_return_net_output_correctly_1():
    '''
    Testa a saída do motor quando não há pagamento de imposto de renda.

    Baseado na operação hipotética abaixo, pré-fixada e modalidade Bullet.

    Ref File: https://docs.google.com/spreadsheets/d/1ijJLZYP8BnuENPrTLFlfdqbiSx8Gs7wtO7T85cgkLgM
    Tab.....: Hipotética 01
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('120000')
    kwa['apy'] = decimal.Decimal('12')
    kwa['zero_date'] = datetime.date(2022, 1, 1)
    kwa['term'] = 12
    kwa['tax_exempt'] = True

    for i, x in enumerate(fincore.build_bullet(**kwa), 1):
        assert x.no == 1
        assert x.date == datetime.date(2023, 1, 1)
        assert x.amort == decimal.Decimal('120000')
        assert x.gain == decimal.Decimal('14611.71')
        assert x.raw == decimal.Decimal('134611.71')
        assert x.tax == decimal.Decimal('0.00')
        assert x.net == decimal.Decimal('134611.71')
        assert x.bal == _0

    assert i == 1
# }}}

# Modos de visualização de juros. {{{
def test_will_return_gain_output_correctly_1():
    '''
    Testa a saída de juros do motor no modo "current".

    Teste baseado no cronograma de pagamentos da Resolvvi - Pré-Fixada - Parcelas Amortizadas - 30 meses.

    ╒══════╤════════════╤═══════════╤════════════╤══════════╤════════════╤══════════╤════════════╤════════════╕
    │   Nº │    Data    │     Juros │       Amt. │   Amt. % │      Bruto │     I.R. │    Líquido │      Saldo │
    ╞══════╪════════════╪═══════════╪════════════╪══════════╪════════════╪══════════╪════════════╪════════════╡
    │    1 │ 21/07/2023 │ 11.386,71 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 671.386,71 │
    │    2 │ 28/07/2023 │  2.516,91 │  20.550,47 │  3.11371 │  34.454,09 │ 3.128,31 │  31.325,78 │ 639.449,53 │
    │    3 │ 21/08/2023 │  8.256,40 │  81.995,82 │ 12.42360 │  90.252,22 │ 1.857,69 │  88.394,53 │ 557.453,71 │
    │    4 │ 21/08/2023 │      0,00 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 557.453,71 │
    │    5 │ 21/09/2023 │  9.314,47 │ 233.209,43 │ 35.33480 │ 242.523,90 │ 2.095,76 │ 240.428,14 │ 324.244,28 │
    │    6 │ 21/09/2023 │      0,00 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 324.244,28 │
    │    7 │ 21/10/2023 │  5.417,79 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 329.662,07 │
    │    8 │ 23/10/2023 │    352,63 │ 324.244,28 │ 49.12790 │ 330.014,70 │ 1.298,34 │ 328.716,36 │       0,00 │
    ╘══════╧════════════╧═══════════╧════════════╧══════════╧════════════╧══════════╧════════════╧════════════╛
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('660000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = tab2 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2023, 6, 19), amortizes_interest=False))

    for i in range(1, 31):
        dda = datetime.date(2023, 7, 21)

        if i < 30:
            tab1.append(fincore.Amortization(date=dda + _MONTH * (i - 1), amortizes_interest=False))

        else:
            tab1.append(fincore.Amortization(date=dda + _MONTH * (i - 1), amortization_ratio=_1))

    # Monta tabela de inserções.
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 7, 28), value=decimal.Decimal('34454.09')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 8, 21), value=decimal.Decimal('90252.22')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 9, 21), value=decimal.Decimal('242523.90')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 10, 23), value=decimal.Decimal('330014.70')))

    # Data, juros, valor amortizado, valor bruto, imposto, valor líquido, saldo devedor.
    tab3 = {}

    tab3[1] = '2023-07-21', '11386.71', '0.00', '0.00', '0.00', '0.00', '671386.71'
    tab3[2] = '2023-07-28', '2516.91', '20550.47', '34454.09', '3128.31', '31325.78', '639449.53'
    tab3[3] = '2023-08-21', '8256.40', '81995.82', '90252.22', '1857.69', '88394.53', '557453.71'
    tab3[4] = '2023-08-21', '0.00', '0.00', '0.00', '0.00', '0.00', '557453.71'
    tab3[5] = '2023-09-21', '9314.47', '233209.43', '242523.90', '2095.76', '240428.14', '324244.28'
    tab3[6] = '2023-09-21', '0.00', '0.00', '0.00', '0.00', '0.00', '324244.28'
    tab3[7] = '2023-10-21', '5417.79', '0.00', '0.00', '0.00', '0.00', '329662.07'
    tab3[8] = '2023-10-23', '352.63', '324244.28', '330014.70', '1298.34', '328716.36', '0.00'

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == datetime.date.fromisoformat(tab3[i][0])
        assert [x.gain, x.amort, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab3[i][1:]]

def test_will_return_gain_output_correctly_2():
    '''
    Testa a saída de juros do motor no modo "deferred".

    Teste baseado no cronograma de pagamentos da Resolvvi - Pré-Fixada - Parcelas Amortizadas - 30 meses.

    ╒══════╤════════════╤═══════════╤════════════╤══════════╤════════════╤══════════╤════════════╤════════════╕
    │   Nº │    Data    │     Juros │       Amt. │   Amt. % │      Bruto │     I.R. │    Líquido │      Saldo │
    ╞══════╪════════════╪═══════════╪════════════╪══════════╪════════════╪══════════╪════════════╪════════════╡
    │    1 │ 21/07/2023 │ 11.386,71 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 671.386,71 │
    │    2 │ 28/07/2023 │ 13.903,62 │  20.550,47 │  3.11371 │  34.454,09 │ 3.128,31 │  31.325,78 │ 639.449,53 │
    │    3 │ 21/08/2023 │  8.256,40 │  81.995,82 │ 12.42360 │  90.252,22 │ 1.857,69 │  88.394,53 │ 557.453,71 │
    │    4 │ 21/08/2023 │      0,00 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 557.453,71 │
    │    5 │ 21/09/2023 │  9.314,47 │ 233.209,43 │ 35.33480 │ 242.523,90 │ 2.095,76 │ 240.428,14 │ 324.244,28 │
    │    6 │ 21/09/2023 │      0,00 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 324.244,28 │
    │    7 │ 21/10/2023 │  5.417,79 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 329.662,07 │
    │    8 │ 23/10/2023 │  5.770,41 │ 324.244,28 │ 49.12790 │ 330.014,70 │ 1.298,34 │ 328.716,36 │       0,00 │
    ╘══════╧════════════╧═══════════╧════════════╧══════════╧════════════╧══════════╧════════════╧════════════╛
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('660000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['gain_output'] = 'deferred'
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = tab2 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2023, 6, 19), amortizes_interest=False))

    for i in range(1, 31):
        dda = datetime.date(2023, 7, 21)

        if i < 30:
            tab1.append(fincore.Amortization(date=dda + _MONTH * (i - 1), amortizes_interest=False))

        else:
            tab1.append(fincore.Amortization(date=dda + _MONTH * (i - 1), amortization_ratio=_1))

    # Monta tabela de inserções.
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 7, 28), value=decimal.Decimal('34454.09')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 8, 21), value=decimal.Decimal('90252.22')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 9, 21), value=decimal.Decimal('242523.90')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 10, 23), value=decimal.Decimal('330014.70')))

    # Data, juros, valor amortizado, valor bruto, imposto, valor líquido, saldo devedor.
    tab3 = {}

    tab3[1] = '2023-07-21', '11386.71', '0.00', '0.00', '0.00', '0.00', '671386.71'
    tab3[2] = '2023-07-28', '13903.62', '20550.47', '34454.09', '3128.31', '31325.78', '639449.53'
    tab3[3] = '2023-08-21', '8256.40', '81995.82', '90252.22', '1857.69', '88394.53', '557453.71'
    tab3[4] = '2023-08-21', '0.00', '0.00', '0.00', '0.00', '0.00', '557453.71'
    tab3[5] = '2023-09-21', '9314.47', '233209.43', '242523.90', '2095.76', '240428.14', '324244.28'
    tab3[6] = '2023-09-21', '0.00', '0.00', '0.00', '0.00', '0.00', '324244.28'
    tab3[7] = '2023-10-21', '5417.79', '0.00', '0.00', '0.00', '0.00', '329662.07'
    tab3[8] = '2023-10-23', '5770.41', '324244.28', '330014.70', '1298.34', '328716.36', '0.00'

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == datetime.date.fromisoformat(tab3[i][0])
        assert [x.gain, x.amort, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab3[i][1:]]

def test_will_return_gain_output_correctly_3():
    '''
    Testa a saída de juros do motor no modo "settled".

    Teste baseado no cronograma de pagamentos da Resolvvi - Pré-Fixada - Parcelas Amortizadas - 30 meses.

    ╒══════╤════════════╤═══════════╤════════════╤══════════╤════════════╤══════════╤════════════╤════════════╕
    │   Nº │    Data    │     Juros │       Amt. │   Amt. % │      Bruto │     I.R. │    Líquido │      Saldo │
    ╞══════╪════════════╪═══════════╪════════════╪══════════╪════════════╪══════════╪════════════╪════════════╡
    │    1 │ 21/07/2023 │      0,00 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 671.386,71 │
    │    2 │ 28/07/2023 │ 13.903,62 │  20.550,47 │  3.11371 │  34.454,09 │ 3.128,31 │  31.325,78 │ 639.449,53 │
    │    3 │ 21/08/2023 │  8.256,40 │  81.995,82 │ 12.42360 │  90.252,22 │ 1.857,69 │  88.394,53 │ 557.453,71 │
    │    4 │ 21/08/2023 │      0,00 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 557.453,71 │
    │    5 │ 21/09/2023 │  9.314,47 │ 233.209,43 │ 35.33480 │ 242.523,90 │ 2.095,76 │ 240.428,14 │ 324.244,28 │
    │    6 │ 21/09/2023 │      0,00 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 324.244,28 │
    │    7 │ 21/10/2023 │      0,00 │       0,00 │        0 │       0,00 │     0,00 │       0,00 │ 329.662,07 │
    │    8 │ 23/10/2023 │  5.770,41 │ 324.244,28 │ 49.12790 │ 330.014,70 │ 1.298,34 │ 328.716,36 │       0,00 │
    ╘══════╧════════════╧═══════════╧════════════╧══════════╧════════════╧══════════╧════════════╧════════════╛
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('660000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['gain_output'] = 'settled'
    kwa['amortizations'] = tab1 = []
    kwa['insertions'] = tab2 = []

    # Monta a tabela de amortizações.
    tab1.append(fincore.Amortization(date=datetime.date(2023, 6, 19), amortizes_interest=False))

    for i in range(1, 31):
        dda = datetime.date(2023, 7, 21)

        if i < 30:
            tab1.append(fincore.Amortization(date=dda + _MONTH * (i - 1), amortizes_interest=False))

        else:
            tab1.append(fincore.Amortization(date=dda + _MONTH * (i - 1), amortization_ratio=_1))

    # Monta tabela de inserções.
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 7, 28), value=decimal.Decimal('34454.09')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 8, 21), value=decimal.Decimal('90252.22')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 9, 21), value=decimal.Decimal('242523.90')))
    tab2.append(fincore.Amortization.Bare(datetime.date(2023, 10, 23), value=decimal.Decimal('330014.70')))

    # Data, juros, valor amortizado, valor bruto, imposto, valor líquido, saldo devedor.
    tab3 = {}

    tab3[1] = '2023-07-21', '0.00', '0.00', '0.00', '0.00', '0.00', '671386.71'
    tab3[2] = '2023-07-28', '13903.62', '20550.47', '34454.09', '3128.31', '31325.78', '639449.53'
    tab3[3] = '2023-08-21', '8256.40', '81995.82', '90252.22', '1857.69', '88394.53', '557453.71'
    tab3[4] = '2023-08-21', '0.00', '0.00', '0.00', '0.00', '0.00', '557453.71'
    tab3[5] = '2023-09-21', '9314.47', '233209.43', '242523.90', '2095.76', '240428.14', '324244.28'
    tab3[6] = '2023-09-21', '0.00', '0.00', '0.00', '0.00', '0.00', '324244.28'
    tab3[7] = '2023-10-21', '0.00', '0.00', '0.00', '0.00', '0.00', '329662.07'
    tab3[8] = '2023-10-23', '5770.41', '324244.28', '330014.70', '1298.34', '328716.36', '0.00'

    for i, x in enumerate(fincore.build(**kwa), 1):
        assert x.no == i
        assert x.date == datetime.date.fromisoformat(tab3[i][0])
        assert [x.gain, x.amort, x.raw, x.tax, x.net, x.bal] == [decimal.Decimal(y) for y in tab3[i][1:]]
# }}}

# Enigmas. {{{
#
# Para operações Juros mensais e Price, atribuir uma data de aniversário equivalente à data esperada do pagamento da
# primeira prestação revelava um comportamento pouco intuitivo do Fincore.
#
# Você poderia esperar que os dois trechos de código abaixo produziriam o mesmo resultado. Trecho um.
#
#   >>> kwa = {}
#
#   >>> kwa['principal'] = decimal.Decimal(100000)
#   >>> kwa['apy'] = decimal.Decimal(10)
#   >>> kwa['zero_date'] = datetime.date(2023, 3, 31)
#   >>> kwa['term'] = 3
#
#   >>> sched1 = fincore.build_jm(**kwa)
#
# Trecho dois.
#
#   >>> kwa = {}
#
#   >>> kwa['principal'] = decimal.Decimal(100000)
#   >>> kwa['apy'] = decimal.Decimal(10)
#   >>> kwa['zero_date'] = datetime.date(2023, 3, 31)
#   >>> kwa['term'] = 3
#   >>> kwa['anniversary_date'] = datetime.date(2023, 4, 30)  # Linha extra.
#
#   >>> sched2 = fincore.build_jm(**kwa)
#
# Observe que o aniversário do trecho dois é exatamente a data do primeiro pagamento do trecho um. Teoricamente, e
# intuitivamente, os dois cronogramas devem ser iguais. Na prática, isso não acontecia. O primeiro cronograma gerava as
# três datas abaixo.
#
#   >>> [x.date for x in sched1]
#   [datetime.date(2023, 4, 30),
#    datetime.date(2023, 5, 31),
#    datetime.date(2023, 6, 30)]
#
# O segundo gerava outras três datas.
#
#   >>> [x.date for x in sched2]
#   [datetime.date(2023, 4, 30),
#    datetime.date(2023, 5, 30),
#    datetime.date(2023, 6, 30)]
#
@pytest.mark.enigmatic
def test_will_redundantly_set_aniversary_date_without_collateral_effect_1():
    '''
    Testa atribuição de data de aniversário redundante.

    O Fincore trata o empréstimo como regular, sem data de aniversário. Caso contrário, todas os pagamentos cairiam no
    dia trinta, exceto os de fevereiro, afetando o os valores do cronograma de pagamentos.

    Juros mensais e Price.
    '''

    kwa1 = {}
    kwa2 = {}

    # Given.
    kwa1['principal'] = decimal.Decimal('2000')
    kwa1['apy'] = decimal.Decimal('10')
    kwa1['term'] = 24
    kwa1['zero_date'] = datetime.date(2023, 3, 31)

    kwa2['principal'] = decimal.Decimal('2000')
    kwa2['apy'] = decimal.Decimal('10')
    kwa2['term'] = 24
    kwa2['zero_date'] = datetime.date(2023, 3, 31)
    kwa2['anniversary_date'] = datetime.date(2023, 4, 30)

    for x, y in zip(fincore.build_jm(**kwa1), fincore.build_jm(**kwa2)):  # When.
        assert x == y  # Then.

    for x, y in zip(fincore.build_price(**kwa1), fincore.build_price(**kwa2)):  # When.
        assert x == y  # Then.

@pytest.mark.enigmatic
def test_will_redundantly_set_aniversary_date_without_collateral_effect_2():
    '''
    Testa atribuição de data de aniversário redundante. O Fincore trata o empréstimo como regular, sem data de
    aniversário.

    Juros mensais e Price.
    '''

    kwa1 = {}
    kwa2 = {}

    # Given.
    kwa1['principal'] = decimal.Decimal('3042000')
    kwa1['apy'] = decimal.Decimal('10')
    kwa1['term'] = 24
    kwa1['zero_date'] = datetime.date(2023, 4, 4)

    kwa2['principal'] = decimal.Decimal('3042000')
    kwa2['apy'] = decimal.Decimal('10')
    kwa2['term'] = 24
    kwa2['zero_date'] = datetime.date(2023, 4, 4)
    kwa2['anniversary_date'] = datetime.date(2023, 5, 4)

    for x, y in zip(fincore.build_jm(**kwa1), fincore.build_jm(**kwa2)):  # When.
        assert x == y  # Then.

    for x, y in zip(fincore.build_price(**kwa1), fincore.build_price(**kwa2)):  # When.
        assert x == y  # Then.

@pytest.mark.enigmatic
@pytest.mark.parametrize('modalidade', ['Bullet', 'Price', 'Livre', 'Juros mensais'])
def test_will_have_rounding_artifacts_1(modalidade):
    '''
    Primeiro teste de artefato de arredondamento.

    Testa que a soma dos valores brutos pagos para M pagamentos de N partes de um empréstimo E não corresponde ao valor
    bruto pago M para pagamentos de E.

    Nesse caso de teste o empréstimo foi divido em 211 partes e, para nenhuma das modalidades Bullet, Price, Livre, e
    Juros mensais, a soma dos valores brutos dos pagamentos dos cronogramas casa com o valor bruto da soma dos
    pagamentos de E.
    '''

    buf = types.SimpleNamespace(parts=[], raw_1=_0, raw_2=_0)

    # Given. Partes do empréstimo.
    buf.parts.extend([decimal.Decimal('500')] * 34)
    buf.parts.extend([decimal.Decimal('1000')] * 21)
    buf.parts.extend([decimal.Decimal('1500')] * 15)
    buf.parts.extend([decimal.Decimal('2000')] * 10)
    buf.parts.extend([decimal.Decimal('2500')] * 8)
    buf.parts.extend([decimal.Decimal('3000')] * 12)
    buf.parts.extend([decimal.Decimal('3500')] * 5)
    buf.parts.extend([decimal.Decimal('4000')] * 7)
    buf.parts.extend([decimal.Decimal('4500')] * 5)
    buf.parts.extend([decimal.Decimal('5000')] * 5)
    buf.parts.extend([decimal.Decimal('5500')] * 11)
    buf.parts.extend([decimal.Decimal('6000')] * 8)
    buf.parts.extend([decimal.Decimal('6500')] * 14)
    buf.parts.extend([decimal.Decimal('7000')] * 1)
    buf.parts.extend([decimal.Decimal('7500')] * 15)
    buf.parts.extend([decimal.Decimal('8000')] * 15)
    buf.parts.extend([decimal.Decimal('8500')] * 11)
    buf.parts.extend([decimal.Decimal('9000')] * 9)
    buf.parts.extend([decimal.Decimal('9500')] * 5)

    if modalidade == 'Bullet':
        kwa = {}

        kwa['principal'] = sum(buf.parts)
        kwa['apy'] = decimal.Decimal('18.5')
        kwa['term'] = 12
        kwa['zero_date'] = datetime.date(2022, 3, 9)

        # Soma do valor bruto dos M pagamentos de E.
        for x in fincore.build_bullet(**kwa):  # When.
            buf.raw_1 += x.raw

        # Soma os pagamentos das partes de E.
        for val in buf.parts:
            kwa['principal'] = val

            for x in fincore.build_bullet(**kwa):
                buf.raw_2 += x.raw

        # Then. As somas não casam.
        assert buf.raw_2 - buf.raw_1 == decimal.Decimal('0.09')

    elif modalidade == 'Juros mensais':
        kwa = {}

        kwa['principal'] = sum(buf.parts)
        kwa['apy'] = decimal.Decimal('18.5')
        kwa['term'] = 12
        kwa['zero_date'] = datetime.date(2022, 3, 9)

        # Soma do valor bruto dos M pagamentos de E.
        for x in fincore.build_jm(**kwa):  # When.
            buf.raw_1 += x.raw

        # Soma os pagamentos das partes de E.
        for val in buf.parts:
            kwa['principal'] = val

            for x in fincore.build_jm(**kwa):
                buf.raw_2 += x.raw

        # Then. As somas não casam.
        assert buf.raw_1 - buf.raw_2 == decimal.Decimal('0.36')

    elif modalidade == 'Price':
        kwa = {}

        kwa['principal'] = sum(buf.parts)
        kwa['apy'] = decimal.Decimal('18.5')
        kwa['term'] = 12
        kwa['zero_date'] = datetime.date(2022, 3, 9)

        # Soma do valor bruto dos M pagamentos de E.
        for x in fincore.build_price(**kwa):  # When.
            buf.raw_1 += x.raw

        # Soma os pagamentos das partes de E.
        for val in buf.parts:
            kwa['principal'] = val

            for x in fincore.build_price(**kwa):
                buf.raw_2 += x.raw

        # Then. As somas não casam.
        assert buf.raw_1 - buf.raw_2 == decimal.Decimal('5.16')

    else:
        kwa = {}

        kwa['principal'] = sum(buf.parts)
        kwa['apy'] = decimal.Decimal('18.5')
        kwa['amortizations'] = []

        kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 3, 9), amortizes_interest=False))

        for i in range(1, 13):
            kwa['amortizations'].append(fincore.Amortization(date=kwa['amortizations'][0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.0833333333')))

        # Soma do valor bruto dos M pagamentos de E.
        for x in fincore.build(**kwa):  # When.
            buf.raw_1 += x.raw

        # Soma os pagamentos das partes de E.
        for val in buf.parts:
            kwa['principal'] = val

            for x in fincore.build(**kwa):
                buf.raw_2 += x.raw

        # Then. As somas não casam.
        assert buf.raw_1 - buf.raw_2 == decimal.Decimal('0.09')

# FIXME: reproduzir esse caso de teste para Bullet, Juros mensais e Price.
@pytest.mark.enigmatic
def test_will_have_rounding_artifacts_2():
    '''
    Segundo teste de artefato de arredondamento.

    Constata presença de artefato de arredondamento em duas situações que intuitivamente deveriam produzir valores
    iguais.

      • Situação um: gera-se um cronograma C1 com data de cálculo antes da data prevista para o pagamento final, e
        cálculo da posição nessa data, somando saldo devedor com valor bruto.

        • Payment.no = 7
        • Payment.date = datetime.date(2022, 10, 9)
        • Payment.raw = decimal.Decimal('78851.03')
        • Payment.tax = decimal.Decimal('928.54')
        • Payment.net = decimal.Decimal('77922.49')
        • Payment.gain = decimal.Decimal('4642.69')
        • Payment.amort = decimal.Decimal('74208.33')
        • Payment.bal = decimal.Decimal('371041.67')

      • Situação dois: gera-se um cronograma C2, idêntico ao C1, mas insere-se um adiantamento total na própria data de
        cálculo.

        • Payment.no = 7
        • Payment.date = datetime.date(2022, 10, 1)
        • Payment.raw = decimal.Decimal('449892.69')
        • Payment.tax = decimal.Decimal('928.54')
        • Payment.net = decimal.Decimal('448964.15')
        • Payment.gain = decimal.Decimal('4642.69')
        • Payment.amort = decimal.Decimal('445250')
        • Payment.bal = decimal.Decimal()

    Observe que na situação um, apesar da data de cálculo ser 01/10/2022, a data do pagamento sai em 09/10/2022. Isso é
    uma deficiência do Fincore (FIXME).

    A soma do saldo devedor com valor bruto na situação um não casa com o valor bruto pago na situação dois. Haverá
    diferença de um centavo.

    Modalidade Livre.
    '''

    d00 = datetime.date(2022, 3, 9)
    d01 = datetime.date(2022, 10, 1)
    kwa = {}

    # Given. Loan schedule.
    kwa['principal'] = decimal.Decimal('890500')
    kwa['apy'] = decimal.Decimal('18.5')
    kwa['amortizations'] = [fincore.Amortization(date=d00, amortizes_interest=False)]

    for i in range(1, 13):
        kwa['amortizations'].append(fincore.Amortization(date=d00 + _MONTH * i, amortization_ratio=decimal.Decimal('0.0833333333')))

    # When. Run cases one and two.
    pm1 = next(_tail(1, fincore.build(calc_date=fincore.CalcDate(value=d01, runaway=False), **kwa)))
    pm2 = next(_tail(1, fincore.build(insertions=[fincore.Amortization.Bare(d01, value=decimal.Decimal('449892.69'))], **kwa)))

    # Then. Rounding artifact. One cent difference between case one, "pm1.bal + pm1.raw"; and case two, "pm2.raw".
    assert pm1.bal + pm1.raw - pm2.raw == _CENTI

@pytest.mark.enigmatic
def test_wont_internally_round_calculations():
    '''
    Testa que internamente o Fincore não faz arredondamentos.

    Esse comportamento é incidental. O Fincore mimetiza o comportamento de planilhas de cálculo elaboradas com
    programas como Google Sheets, Excel, Numbers, OpenOffice etc. Nas planilhas, não é usual usar funções de
    arredondamento em cálculos intermediários. Em vez disso, usa-se formatação visual nas células e colunas.

    Esse teste tem uma sub-rotina que faz os arredondamentos sempre que precisa armazenar um valor monetário em uma
    variável automática local. Essa rotina é "instalada" no Fincore para demonstrar que os resultados produzidos pela
    biblioteca irão divergir daqueles que ela normalmente gera.

    Esse teste lida com modalidade Price, indexador pré-fixado. Isso faz com que a sub-rotina abaixo fique extremamente
    simples, por não ter que lidar com a complexidade dos cálculos pós-fixados. Tais complicações são irrelevantes para
    o efeito de demonstrar variações de arredondamento.
    '''

    def get_payments_table(principal, apy, amortizations, **_):
        def tray_a_gen(val_b):
            ratio, delta = _1, _0

            while True:
                saldo = _ROUND_CENTI(ratio * (principal + val_b.value))
                ratio = ratio - delta
                delta = yield saldo, _ROUND_CENTI((principal + val_b.value) * delta)

        def scale():
            val_b = types.SimpleNamespace(value=_0)
            gen_a = tray_a_gen(val_b)

            gen_a.send(None)

            return gen_a

        tray_a = scale()

        for i, (_, amort1) in enumerate(itertools.pairwise(amortizations), 1):
            fac = (_1 + decimal.Decimal(apy) / decimal.Decimal(100)) ** (_1 / decimal.Decimal(12))  # Spread factor.
            tup = tray_a.send(amort1.amortization_ratio)  # Balance, amortization value.
            dif = amort1.date - amortizations[0].date
            spd = _ROUND_CENTI(tup[0] * (fac - _1))  # Spread.
            bal = _ROUND_CENTI(tup[0] - tup[1])
            raw = _ROUND_CENTI(tup[1] + spd)
            pmt = fincore.Payment()
            tax = _0

            for minimum, maximum, ratio in fincore._BRAZIL_TAX_BRACKETS:
                if minimum < dif.days <= maximum:
                    tax = _ROUND_CENTI(spd * ratio)

                    break

            pmt.no = i
            pmt.date = amort1.date
            pmt.raw = raw
            pmt.tax = tax
            pmt.net = raw - tax
            pmt.gain = spd
            pmt.amort = tup[1]
            pmt.bal = bal

            yield pmt

    kwa = {}

    # Given: parâmetros do cronograma Price.
    kwa['principal'] = decimal.Decimal('890500')
    kwa['apy'] = decimal.Decimal('18.5')
    kwa['term'] = 12
    kwa['zero_date'] = datetime.date(2022, 3, 9)

    # When: gera o cronograma via vanilla Fincore.
    lst1 = list(fincore.build_price(**kwa))

    # When: gera um cronograma usando o Fincore com a sub-rotina adulterada.
    with unittest.mock.patch.object(fincore, 'get_payments_table', get_payments_table):
        lst2 = list(fincore.build_price(**kwa))

    # Then.
    for pmt1, pmt2 in zip(lst1, lst2):
        assert pmt1.no == pmt2.no
        assert pmt1.date == pmt2.date

        # Valida diferenças nos cálculos dos pagamentos dois, oito e nove.
        if pmt1.no == 2:
            assert pmt1.tax == pmt2.tax
            assert pmt1.net == pmt2.net
            assert pmt1.gain == pmt2.gain
            assert pmt1.amort == pmt2.amort
            assert pmt1.bal == pmt2.bal - _CENTI
            assert pmt1.raw == pmt2.raw

        elif pmt1.no == 8:
            assert pmt1.tax == pmt2.tax
            assert pmt1.net == pmt2.net - _CENTI
            assert pmt1.gain == pmt2.gain
            assert pmt1.amort == pmt2.amort
            assert pmt1.bal == pmt2.bal + _CENTI
            assert pmt1.raw == pmt2.raw - _CENTI

        elif pmt1.no == 9:
            assert pmt1.tax == pmt2.tax
            assert pmt1.net == pmt2.net
            assert pmt1.gain == pmt2.gain
            assert pmt1.amort == pmt2.amort
            assert pmt1.bal == pmt2.bal - _CENTI
            assert pmt1.raw == pmt2.raw

        else:
            assert pmt1.tax == pmt2.tax
            assert pmt1.net == pmt2.net
            assert pmt1.gain == pmt2.gain
            assert pmt1.amort == pmt2.amort
            assert pmt1.bal == pmt2.bal
            assert pmt1.raw == pmt2.raw

@pytest.mark.parametrize('indexador', ['PRE', 'CDI', 'IPCA', pytest.param('Poupança', id='SAVS')])
def test_will_redundantly_set_calc_date_bullet(indexador):
    '''
    Testa o uso redundante da data de cálculo em operação Bullet.

    A data de cálculo casa com a do pagamento da parcela Bullet. Os valores têm que ser iguais.
    '''

    calc = fincore.CalcDate(value=datetime.date(2024, 7, 13), runaway=False)
    opts = {}

    opts['principal'] = decimal.Decimal('8634500')
    opts['apy'] = decimal.Decimal('10')
    opts['zero_date'] = datetime.date(2023, 3, 27)
    opts['anniversary_date'] = datetime.date(2024, 7, 13)
    opts['term'] = 15

    if indexador == 'CDI':
        opts['vir'] = fincore.VariableIndex(code='CDI', percentage=200)

    elif indexador == 'Poupança':
        opts['vir'] = fincore.VariableIndex(code='Poupança', percentage=500)

    elif indexador == 'IPCA':
        opts['vir'] = fincore.VariableIndex(code='IPCA')

    for i, (x, y) in enumerate(zip(fincore.build_bullet(**opts), fincore.build_bullet(**opts, calc_date=calc)), 1):
        assert x.no == y.no
        assert x.date == y.date
        assert x.raw == y.raw
        assert x.tax == y.tax
        assert x.net == y.net
        assert x.gain == y.gain
        assert x.amort == y.amort
        assert x.bal == y.bal

    assert i == 1

# Juros mensais com indexador Poupança não é oficialmente suportada.
@pytest.mark.parametrize('indexador', ['PRE', 'CDI', 'IPCA'])
def test_will_redundantly_set_calc_date_jm_1(indexador):
    '''
    Testa o uso redundante da data de cálculo em operação Juros Mensais.

    A data de cálculo casa com a do pagamento da última parcela. Todas as parcelas têm que ter valores iguais.
    '''

    calc = fincore.CalcDate(value=datetime.date(2021, 10, 20), runaway=False)
    opts = {}

    opts['principal'] = decimal.Decimal('571500')
    opts['apy'] = decimal.Decimal('15')
    opts['zero_date'] = datetime.date(2020, 4, 20)
    opts['term'] = 18

    if indexador == 'CDI':
        opts['vir'] = fincore.VariableIndex(code='CDI', percentage=50)

    elif indexador == 'Poupança':
        opts['vir'] = fincore.VariableIndex(code='Poupança', percentage=30)

    elif indexador == 'IPCA':
        opts['vir'] = fincore.VariableIndex(code='IPCA')

    for i, (x, y) in enumerate(zip(fincore.build_jm(**opts), fincore.build_jm(**opts, calc_date=calc)), 1):
        assert x.no == y.no
        assert x.date == y.date
        assert x.raw == y.raw
        assert x.tax == y.tax
        assert x.net == y.net
        assert x.gain == y.gain
        assert x.amort == y.amort
        assert x.bal == y.bal

    assert i == 18

# Juros mensais com indexador Poupança não é oficialmente suportada.
@pytest.mark.parametrize('indexador', ['PRE', 'CDI', 'IPCA'])
def test_will_redundantly_set_calc_date_jm_2(indexador):
    '''
    Testa o uso redundante da data de cálculo em operação Juros Mensais.

    A data de cálculo casa com a do pagamento da sexta parcela. Todas as parcelas de ambos os cronogramas até a seis
    têm que ter valores iguais.
    '''

    calc = fincore.CalcDate(value=datetime.date(2020, 10, 20), runaway=False)
    opts = {}

    opts['principal'] = decimal.Decimal('571500')
    opts['apy'] = decimal.Decimal('15')
    opts['zero_date'] = datetime.date(2020, 4, 20)
    opts['term'] = 18

    if indexador == 'CDI':
        opts['vir'] = fincore.VariableIndex(code='CDI', percentage=50)

    elif indexador == 'Poupança':
        opts['vir'] = fincore.VariableIndex(code='Poupança', percentage=30)

    elif indexador == 'IPCA':
        opts['vir'] = fincore.VariableIndex(code='IPCA')

    for i, (x, y) in enumerate(zip(fincore.build_jm(**opts), fincore.build_jm(**opts, calc_date=calc)), 1):
        assert x.no == y.no
        assert x.date == y.date
        assert x.raw == y.raw
        assert x.tax == y.tax
        assert x.net == y.net
        assert x.gain == y.gain
        assert x.amort == y.amort
        assert x.bal == y.bal

    assert i == 6

def test_will_redundantly_set_calc_date_price_1():
    '''
    Testa o uso redundante da data de cálculo em operação Price.

    A data de cálculo casa com a do pagamento da última parcela. Todas as parcelas têm que ter valores iguais.
    '''

    calc = fincore.CalcDate(value=datetime.date(2018, 12, 30), runaway=False)
    opts = {}

    opts['principal'] = decimal.Decimal('7729890')
    opts['apy'] = decimal.Decimal('5')
    opts['zero_date'] = datetime.date(2018, 6, 30)
    opts['term'] = 6

    for i, (x, y) in enumerate(zip(fincore.build_price(**opts), fincore.build_price(**opts, calc_date=calc)), 1):
        assert x.no == y.no
        assert x.date == y.date
        assert x.raw == y.raw
        assert x.tax == y.tax
        assert x.net == y.net
        assert x.gain == y.gain
        assert x.amort == y.amort
        assert x.bal == y.bal

    assert i == 6

def test_will_redundantly_set_calc_date_price_2():
    '''
    Testa o uso redundante da data de cálculo em operação Price.

    A data de cálculo casa com a do pagamento da quinta parcela. Todas as parcelas até a cinco têm que ter valores
    iguais.
    '''

    calc = fincore.CalcDate(value=datetime.date(2018, 11, 30), runaway=False)
    opts = {}

    opts['principal'] = decimal.Decimal('7729890')
    opts['apy'] = decimal.Decimal('5')
    opts['zero_date'] = datetime.date(2018, 6, 30)
    opts['term'] = 6

    for i, (x, y) in enumerate(zip(fincore.build_price(**opts), fincore.build_price(**opts, calc_date=calc)), 1):
        assert x.no == y.no
        assert x.date == y.date
        assert x.raw == y.raw
        assert x.tax == y.tax
        assert x.net == y.net
        assert x.gain == y.gain
        assert x.amort == y.amort
        assert x.bal == y.bal

    assert i == 5

# Livre com indexador Poupança não é oficialmente suportada.
@pytest.mark.parametrize('indexador', ['PRE', 'CDI', 'IPCA'])
def test_will_redundantly_set_calc_date_livre_1(indexador):
    '''
    Testa o uso redundante da data de cálculo em operação Livre.

    A data de cálculo casa com a da última parcela. Todas as parcelas têm que ter valores iguais.
    '''

    calc = fincore.CalcDate(value=datetime.date(2025, 2, 8), runaway=False)
    opts = {}

    opts['principal'] = decimal.Decimal('7729890')
    opts['apy'] = decimal.Decimal('5')

    if indexador == 'CDI':
        opts['vir'] = fincore.VariableIndex(code='CDI', percentage=250)

    elif indexador == 'Poupança':
        opts['vir'] = fincore.VariableIndex(code='Poupança', percentage=350)

    elif indexador == 'IPCA':
        opts['vir'] = fincore.VariableIndex(code='IPCA')

    # Monta a tabela de amortizações.
    opts['amortizations'] = tab = []

    tab.append(fincore.Amortization(date=datetime.date(2022, 7, 8), amortizes_interest=False))

    for i in range(1, 31):
        tab.append(fincore.Amortization(date=tab[0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.033333333333333335')))

    for j, (x, y) in enumerate(zip(fincore.build(**opts), fincore.build(**opts, calc_date=calc)), 1):
        assert x.no == y.no
        assert x.date == y.date
        assert x.raw == y.raw
        assert x.tax == y.tax
        assert x.net == y.net
        assert x.gain == y.gain
        assert x.amort == y.amort
        assert x.bal == y.bal

    assert j == 30

# Livre com indexador Poupança não é oficialmente suportada.
@pytest.mark.parametrize('indexador', ['PRE', 'CDI', 'IPCA'])
def test_will_redundantly_set_calc_date_livre_2(indexador):
    '''
    Testa o uso redundante da data de cálculo em operação Livre c/ amortização extraordinária.

    A data de cálculo casa com a da parcela extraordinária, que amortiza 100% do valor do empréstimo. Todas as parcelas
    até o cálculo têm que ter valores iguais.
    '''

    calc = fincore.CalcDate(value=datetime.date(2022, 12, 31), runaway=False)
    opts = {}

    opts['principal'] = decimal.Decimal('7729890')
    opts['apy'] = decimal.Decimal('5')

    if indexador == 'CDI':
        opts['vir'] = fincore.VariableIndex(code='CDI', percentage=250)

    elif indexador == 'Poupança':
        opts['vir'] = fincore.VariableIndex(code='Poupança', percentage=350)

    elif indexador == 'IPCA':
        opts['vir'] = fincore.VariableIndex(code='IPCA')

    # Monta a tabela de amortizações.
    opts['amortizations'] = tab = []

    tab.append(fincore.Amortization(date=datetime.date(2022, 7, 8), amortizes_interest=False))

    for i in range(1, 31):
        tab.append(fincore.Amortization(date=tab[0].date + _MONTH * i, amortization_ratio=decimal.Decimal('0.033333333333333335')))

    # Insere uma entrada extraordinária.
    opts['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 12, 31), value=decimal.Decimal(100_000))]

    for j, (x, y) in enumerate(zip(fincore.build(**opts), fincore.build(**opts, calc_date=calc)), 1):
        assert x.no == y.no
        assert x.date == y.date
        assert x.raw == y.raw
        assert x.tax == y.tax
        assert x.net == y.net
        assert x.gain == y.gain
        assert x.amort == y.amort
        assert x.bal == y.bal

    assert j == 6
# }}}

# Auxiliares (impostos, atraso etc). {{{
def test_wont_calculate_revenue_tax():
    v1, v2 = _NOW, _NOW - datetime.timedelta(seconds=1)

    with pytest.raises(Exception):
        fincore.calculate_revenue_tax(v1, v2)

@pytest.mark.parametrize('begin_date, end_date, tax', [
    (_NOW, _NOW + datetime.timedelta(days=1), decimal.Decimal('0.225')),
    (_NOW, _NOW + datetime.timedelta(days=90), decimal.Decimal('0.225')),
    (_NOW, _NOW + datetime.timedelta(days=179), decimal.Decimal('0.225')),
    (_NOW, _NOW + datetime.timedelta(days=180), decimal.Decimal('0.225')),
    (_NOW, _NOW + datetime.timedelta(days=270), decimal.Decimal('0.2')),
    (_NOW, _NOW + datetime.timedelta(days=359), decimal.Decimal('0.2')),
    (_NOW, _NOW + datetime.timedelta(days=360), decimal.Decimal('0.2')),
    (_NOW, _NOW + datetime.timedelta(days=540), decimal.Decimal('0.175')),
    (_NOW, _NOW + datetime.timedelta(days=719), decimal.Decimal('0.175')),
    (_NOW, _NOW + datetime.timedelta(days=720), decimal.Decimal('0.175')),
    (_NOW, _NOW + datetime.timedelta(days=1000), decimal.Decimal('0.15')),
    (_NOW, _NOW + datetime.timedelta(days=2000), decimal.Decimal('0.15'))
])
def test_will_calculate_revenue_tax(begin_date, end_date, tax):
    assert fincore.calculate_revenue_tax(begin_date, end_date) == tax

@pytest.mark.parametrize('term, iof', [(1, decimal.Decimal('0.50741')), (12, decimal.Decimal('1.88'))])
def test_will_calculate_iof(term, iof):
    assert fincore.calculate_iof(datetime.date(2022, 1, 1), term) == iof

def test_will_get_delinquency_charges_1():
    '''
    Teste o retorno da função para um investimento pré-fixado.

    Ref File: https://docs.google.com/spreadsheets/d/1VcUJZn9YHTkjE2fvP4rafWIfyTcADFteFlBg4ljtLco
    Tab.....: PRE
    '''

    kwa = {}

    kwa['outstanding_balance'] = decimal.Decimal('100000')
    kwa['penalty_arrear_days'] = 1
    kwa['loan_apy'] = decimal.Decimal('10')

    obj = fincore.get_delinquency_charges(**kwa)

    assert obj.extra_gain == decimal.Decimal('26.48')
    assert obj.penalty == decimal.Decimal('33.34')
    assert obj.fine == decimal.Decimal('2001.20')

def test_will_get_delinquency_charges_2():
    '''
    Teste o retorno da função para um investimento com indexador CDI.

    Ref File: https://docs.google.com/spreadsheets/d/1VcUJZn9YHTkjE2fvP4rafWIfyTcADFteFlBg4ljtLco
    Tab.....: CDI
    '''

    kwa = {}

    kwa['outstanding_balance'] = decimal.Decimal('100000')
    kwa['penalty_arrear_days'] = 1
    kwa['loan_apy'] = decimal.Decimal('10')
    kwa['loan_vir'] = fincore.VariableIndex(code='CDI')
    kwa['loan_vir_ref_date'] = datetime.date(2022, 1, 1)

    obj = fincore.get_delinquency_charges(**kwa)

    assert obj.extra_gain == _0
    assert obj.penalty == decimal.Decimal('33.33')
    assert obj.fine == decimal.Decimal('2000.67')

def test_wont_create_late_payment():
    with pytest.raises(TypeError, match=r"get_late_payment\(\) missing 1 required positional argument: 'in_pmt'"):
        kwa = {}

        kwa['apy'] = decimal.Decimal('6')
        kwa['zero_date'] = datetime.date.today()
        kwa['calc_date'] = datetime.date.today() + _MONTH

        fincore.get_late_payment(**kwa)

    with pytest.raises(TypeError, match=r"get_late_payment\(\) missing 1 required positional argument: 'zero_date'"):
        kwa = {}

        kwa['in_pmt'] = fincore.LatePayment()
        kwa['apy'] = decimal.Decimal('6')
        kwa['calc_date'] = datetime.date.today() + _MONTH

        fincore.get_late_payment(**kwa)

    with pytest.raises(TypeError, match=r"get_late_payment\(\) missing 1 required positional argument: 'calc_date'"):
        kwa = {}

        kwa['in_pmt'] = fincore.LatePayment()
        kwa['apy'] = decimal.Decimal('6')
        kwa['zero_date'] = datetime.date.today()

        fincore.get_late_payment(**kwa)

    with pytest.raises(TypeError, match=r"get_late_payment\(\) missing 1 required positional argument: 'apy'"):
        kwa = {}

        kwa['in_pmt'] = fincore.LatePayment()
        kwa['zero_date'] = datetime.date.today()
        kwa['calc_date'] = datetime.date.today() + _MONTH

        fincore.get_late_payment(**kwa)

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "in_pmt" \(dict\) did not match any element in the union:\n  fincore.LatePayment: is not an instance of fincore.LatePayment\n  fincore.LatePriceAdjustedPayment: is not an instance of fincore.LatePriceAdjustedPayment'):
        kwa = {}

        kwa['in_pmt'] = {}
        kwa['apy'] = decimal.Decimal('6')
        kwa['zero_date'] = datetime.date.today()
        kwa['calc_date'] = datetime.date.today() + _MONTH

        fincore.get_late_payment(**kwa)

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "zero_date" \(str\) is not an instance of datetime.date'):
        kwa = {}

        kwa['in_pmt'] = fincore.LatePayment()
        kwa['apy'] = decimal.Decimal('6')
        kwa['zero_date'] = '2022-01-01'
        kwa['calc_date'] = datetime.date.today() + _MONTH

        fincore.get_late_payment(**kwa)

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "calc_date" \(str\) is not an instance of datetime.date'):
        kwa = {}

        kwa['in_pmt'] = fincore.LatePayment()
        kwa['apy'] = decimal.Decimal('6')
        kwa['zero_date'] = datetime.date.today()
        kwa['calc_date'] = '2022-01-01'

        fincore.get_late_payment(**kwa)

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "apy" \(float\) is not an instance of decimal.Decimal'):
        kwa = {}

        kwa['in_pmt'] = fincore.LatePayment()
        kwa['apy'] = 6.0
        kwa['zero_date'] = datetime.date.today()
        kwa['calc_date'] = datetime.date.today() + _MONTH

        fincore.get_late_payment(**kwa)

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "fee_rate" \(float\) is not an instance of decimal.Decimal'):
        kwa = {}

        kwa['in_pmt'] = fincore.LatePayment()
        kwa['apy'] = decimal.Decimal('6')
        kwa['zero_date'] = datetime.date.today()
        kwa['calc_date'] = datetime.date.today() + _MONTH
        kwa['fee_rate'] = 1.0

        fincore.get_late_payment(**kwa)

    with pytest.raises(typeguard.TypeCheckError, match=r'argument "fine_rate" \(float\) is not an instance of decimal.Decimal'):
        kwa = {}

        kwa['in_pmt'] = fincore.LatePayment()
        kwa['apy'] = decimal.Decimal('6')
        kwa['zero_date'] = datetime.date.today()
        kwa['calc_date'] = datetime.date.today() + _MONTH
        kwa['fine_rate'] = 2.0

        fincore.get_late_payment(**kwa)

def test_will_create_late_payment_pre_360_1():
    '''
    Operação na base 360.

    Ref File: https://docs.google.com/spreadsheets/d/1vNSRo6KO6KIV8ncNKYg_QeYn-vBsHw7PG0qHrGsrL7k
    Tab.....: 360
    '''

    pmt = fincore.LatePayment()
    kwa = {}

    # Given.
    pmt.date = datetime.date(2021, 10, 1)
    pmt.bal = _0
    pmt.raw = decimal.Decimal('11118.06')
    pmt.amort = decimal.Decimal('10000')
    pmt.gain = decimal.Decimal('1118.06')

    kwa['in_pmt'] = pmt
    kwa['apy'] = decimal.Decimal('15')
    kwa['zero_date'] = datetime.date(2021, 1, 1)
    kwa['calc_date'] = datetime.date(2022, 1, 25)

    # When.
    out = fincore.get_late_payment(**kwa)

    # Then.
    assert out.no == pmt.no
    assert out.date == kwa['calc_date']

    assert out.extra_gain == decimal.Decimal('512.14')
    assert out.penalty == decimal.Decimal('449.70')
    assert out.fine == decimal.Decimal('241.60')

    assert out.amort == pmt.amort
    assert out.gain == decimal.Decimal('1118.06')
    assert out.raw == decimal.Decimal('12321.50')
    assert out.tax == decimal.Decimal('406.26')
    assert out.net == decimal.Decimal('11915.24')
    assert out.bal == pmt.bal

def test_will_create_late_payment_pre_30_360_1():
    '''
    Operação na base 30/360.

    Ref File: https://docs.google.com/spreadsheets/d/1vNSRo6KO6KIV8ncNKYg_QeYn-vBsHw7PG0qHrGsrL7k
    Tab.....: 30/360 - 1
    '''

    pmt = fincore.LatePayment()
    kwa = {}

    # Given.
    pmt.date = datetime.date(2021, 10, 1)
    pmt.bal = _0
    pmt.raw = decimal.Decimal('10117.15')
    pmt.amort = decimal.Decimal('10000')
    pmt.gain = decimal.Decimal('117.15')

    kwa['in_pmt'] = pmt
    kwa['apy'] = decimal.Decimal('15')
    kwa['zero_date'] = datetime.date(2021, 1, 1)
    kwa['calc_date'] = datetime.date(2022, 1, 25)

    # When.
    out = fincore.get_late_payment(**kwa)

    # Then.
    assert out.no == pmt.no
    assert out.date == kwa['calc_date']

    assert out.extra_gain == decimal.Decimal('466.03')
    assert out.penalty == decimal.Decimal('409.22')
    assert out.fine == decimal.Decimal('219.85')

    assert out.amort == pmt.amort
    assert out.gain == decimal.Decimal('117.15')
    assert out.raw == decimal.Decimal('11212.25')
    assert out.tax == decimal.Decimal('212.14')
    assert out.net == decimal.Decimal('11000.11')
    assert out.bal == pmt.bal

def test_will_create_late_payment_pre_30_360_2():
    '''
    Operação na base 30/360.

    Ref File: https://docs.google.com/spreadsheets/d/1vNSRo6KO6KIV8ncNKYg_QeYn-vBsHw7PG0qHrGsrL7k
    Tab.....: 30/360 - 2
    '''

    pmt = fincore.LatePayment()
    kwa = {}

    # Given.
    pmt.date = datetime.date(2022, 9, 23)
    pmt.bal = decimal.Decimal('4920.25')
    pmt.raw = decimal.Decimal('478.32')
    pmt.amort = decimal.Decimal('417.75')
    pmt.gain = decimal.Decimal('60.57')

    kwa['in_pmt'] = pmt
    kwa['apy'] = decimal.Decimal('14.5')
    kwa['zero_date'] = datetime.date(2021, 8, 23)
    kwa['calc_date'] = datetime.date(2022, 9, 25)

    # When.
    out = fincore.get_late_payment(**kwa)

    # Then.
    assert out.no == pmt.no
    assert out.date == kwa['calc_date']

    assert out.extra_gain == decimal.Decimal('0.36')
    assert out.penalty == decimal.Decimal('0.32')
    assert out.fine == decimal.Decimal('9.58')

    assert out.amort == pmt.amort
    assert out.gain == decimal.Decimal('60.57')
    assert out.raw == decimal.Decimal('488.58')
    assert out.tax == decimal.Decimal('12.40')
    assert out.net == decimal.Decimal('476.18')
    assert out.bal == pmt.bal

def test_will_create_late_payment_pre_30_360_3():
    '''
    Operação na base 30/360.

    Ref File: https://docs.google.com/spreadsheets/d/1vNSRo6KO6KIV8ncNKYg_QeYn-vBsHw7PG0qHrGsrL7k
    Tab.....: 30/360 - 3
    '''

    pmt = fincore.LatePayment()
    kwa = {}

    # Given.
    pmt.date = datetime.date(2021, 10, 1)
    pmt.bal = _0
    pmt.raw = decimal.Decimal('1123.72')
    pmt.amort = decimal.Decimal('1111.11')
    pmt.gain = decimal.Decimal('12.61')

    kwa['in_pmt'] = pmt
    kwa['apy'] = decimal.Decimal('14.5')
    kwa['zero_date'] = datetime.date(2021, 1, 1)
    kwa['calc_date'] = datetime.date(2022, 1, 25)

    # When.
    out = fincore.get_late_payment(**kwa)

    # Then.
    assert out.no == pmt.no
    assert out.date == kwa['calc_date']

    assert out.extra_gain == decimal.Decimal('50.11')
    assert out.penalty == decimal.Decimal('45.39')
    assert out.fine == decimal.Decimal('24.38')

    assert out.amort == pmt.amort
    assert out.gain == decimal.Decimal('12.61')
    assert out.raw == decimal.Decimal('1243.60')
    assert out.tax == decimal.Decimal('23.19')
    assert out.net == decimal.Decimal('1220.41')
    assert out.bal == pmt.bal

def test_will_create_late_payment_ipca():
    '''
    Operação na base 30/360.

    Testa se o valor mínimo da correção será zero, quando o fator é negativo.
    '''

    pmt = fincore.LatePriceAdjustedPayment()
    pla = fincore.PriceLevelAdjustment('IPCA')
    sns = types.SimpleNamespace(value=decimal.Decimal('-0.001'), mem=[])
    kwa = {}

    pla.base_date = datetime.date(2022, 1, 1)
    pla.period = 1
    pla.shift = 'M-1'
    pla.amortizes_adjustment = True

    # Given.
    pmt.date = datetime.date(2021, 10, 1)
    pmt.bal = _0
    pmt.raw = decimal.Decimal('1123.72')
    pmt.amort = decimal.Decimal('1111.11')
    pmt.gain = decimal.Decimal('12.61')
    pmt.pla = _0

    kwa['in_pmt'] = pmt
    kwa['apy'] = decimal.Decimal('14.5')
    kwa['zero_date'] = datetime.date(2021, 1, 1)
    kwa['calc_date'] = datetime.date(2022, 1, 25)
    kwa['vir'] = fincore.VariableIndex('IPCA')
    kwa['pla_operations'] = [(kwa['calc_date'], True, pla)]

    with unittest.mock.patch('fincore.IndexStorageBackend.calculate_ipca_factor', return_value=sns):
        # When.
        out = t.cast(fincore.LatePriceAdjustedPayment, fincore.get_late_payment(**kwa))

        # Then.
        assert out.no == pmt.no
        assert out.date == kwa['calc_date']

        assert out.extra_gain == decimal.Decimal('50.11')
        assert out.penalty == decimal.Decimal('45.39')
        assert out.fine == decimal.Decimal('24.38')

        assert out.amort == pmt.amort
        assert out.gain == decimal.Decimal('12.61')
        assert out.pla == _0
        assert out.raw == decimal.Decimal('1243.60')
        assert out.tax == decimal.Decimal('23.19')
        assert out.net == decimal.Decimal('1220.41')
        assert out.bal == pmt.bal
# }}}

# Retornos diários. {{{
def test_wont_create_sched_daily_returns_1():
    '''Fincore deve falhar ao criar um empréstimo com principal maior que zero e menor que R$ 0,01.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    with pytest.raises(ValueError, match='principal value should be at least 0.01'):
        next(fincore.get_daily_returns(_CENTI / 2, _0, [ent0, ent1]))

def test_wont_create_sched_daily_returns_2():
    '''Fincore deve falhar ao criar um empréstimo sem um cronograma de amortizações.'''

    with pytest.raises(ValueError, match='at least two amortizations are required: the start of the schedule, and its end'):
        next(fincore.get_daily_returns(_1, _0, []))

def test_wont_create_sched_daily_returns_3():
    '''Fincore deve falhar ao criar um empréstimo sem indexador e com base 252.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    with pytest.raises(ValueError, match='fixed interest rates should not use the 252 working days capitalisation'):
        next(fincore.get_daily_returns(_1, _0, [ent0, ent1], capitalisation='252'))

def test_wont_create_sched_daily_returns_4():
    '''Fincore deve falhar ao criar um empréstimo com indexador CDI e base diferente de 252.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    with pytest.raises(ValueError, match='CDI should use the 252 working days capitalisation'):
        next(fincore.get_daily_returns(_1, _0, [ent0, ent1], vir=fincore.VariableIndex('CDI'), capitalisation='360'))

def test_wont_create_sched_daily_returns_5():
    '''Fincore deve falhar ao criar um empréstimo sem indexador IPCA/IGPM e com PLA na amortização.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    ent1.price_level_adjustment = fincore.PriceLevelAdjustment(code='IPCA', base_date=datetime.date(2018, 5, 1), period=1)

    with pytest.raises(TypeError, match="amortization 1 has price level adjustment, but a variable index wasn't provided, or isn't IPCA nor IGPM"):
        next(fincore.get_daily_returns(_1, _0, [ent0, ent1], vir=fincore.VariableIndex('CDI'), capitalisation='252'))

def test_wont_create_sched_daily_returns_6():
    '''Fincore deve falhar ao criar um empréstimo cujo percentual de amortização acumulado ultrapassa 1.0.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortization_ratio=_1 + _1, amortizes_interest=True)

    with pytest.raises(ValueError, match='the accumulated percentage of the amortizations overflows 1.0'):
        next(fincore.get_daily_returns(_1, _0, [ent0, ent1]))

def test_wont_create_sched_daily_returns_7():
    '''Fincore deve falhar ao criar um empréstimo cujo percentual de amortização acumulado seja menor que 1.0.'''

    ent0 = fincore.Amortization(date=datetime.date(2018, 1, 1))
    ent1 = fincore.Amortization(date=datetime.date(2018, 5, 1), amortizes_interest=True)

    with pytest.raises(ValueError, match='the accumulated percentage of the amortizations does not reach 1.0'):
        next(fincore.get_daily_returns(_1, _0, [ent0, ent1]))

def test_wont_create_sched_daily_returns_8():
    '''Fincore deve falhar ao criar um empréstimo com antecipação maior do que o saldo devedor.'''

    kwa = {}

    kwa['principal'] = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('5')

    kwa['amortizations'] = []
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2020, 1, 1), amortizes_interest=False))
    kwa['amortizations'].append(fincore.Amortization.Bare(date=datetime.date(2020, 6, 1), value=decimal.Decimal('150000')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2021, 1, 1), amortization_ratio=decimal.Decimal(1), amortizes_interest=True))

    with pytest.raises(Exception, match='the value of the amortization, 150000, is greater than the remaining balance of the loan, 102081.39'):
        list(fincore.get_daily_returns(**kwa))

def test_will_create_loan_daily_returns_bullet_1():
    '''
    Operação pré-fixada modalidade Bullet.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Bullet - PRE
    '''

    kwa = {}

    kwa['principal'] = bal = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('15')
    kwa['zero_date'] = datetime.date(2022, 1, 1)
    kwa['term'] = 12

    # Calcula os retornos diários.
    for entry in fincore.get_bullet_daily_returns(**kwa):
        # Valida fator de juros.
        assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00038830')

        # Valida valor do rendimento.
        assert entry.value == _ROUND_CENTI((entry.sf - _1) * bal)

        bal += entry.value

def test_will_create_loan_daily_returns_bullet_2():
    '''
    Operação pré-fixada modalidade Bullet, com data de aniversário, verificando se o pagamento ocorre em um dia corrido
    ou não.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Bullet - PRE
    '''

    kwa = {}

    kwa['principal'] = bal = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('15')
    kwa['zero_date'] = datetime.date(2022, 1, 1)
    kwa['anniversary_date'] = datetime.date(2022, 2, 5)
    kwa['term'] = 1
    kwa['is_bizz_day_cb'] = lambda x: x.weekday() < 5

    # Calcula os retornos diários.
    for entry in fincore.get_bullet_daily_returns(**kwa):
        # Valida fator de juros.
        assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00038830')

        if entry.date < kwa['anniversary_date']:
            # Valida valor do rendimento.
            assert entry.value == _ROUND_CENTI((entry.sf - _1) * bal)

            bal += entry.value

        else:
            # Valida valor do rendimento.
            assert entry.value == _0

def test_will_create_loan_daily_returns_bullet_3():
    '''
    Operação Poupança, modalidade Bullet.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Bullet - Poupança
    '''

    kwa = {}

    kwa['principal'] = bal = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('15')
    kwa['zero_date'] = datetime.date(2022, 1, 1)
    kwa['term'] = 12
    kwa['vir'] = fincore.VariableIndex(code='Poupança')

    # Calcula os retornos diários.
    for entry in fincore.get_bullet_daily_returns(**kwa):
        if entry.date < datetime.date(2022, 2, 1):
            # Valida fatores de juros.
            assert decimal.Decimal.quantize(entry.vf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00018041')
            assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00038830')

        elif entry.date < datetime.date(2022, 3, 1):
            # Valida fatores de juros.
            assert decimal.Decimal.quantize(entry.vf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00017814')
            assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00038830')

        else:
            break  # FIXME: validar demais períodos.

        # Valida valor do rendimento.
        assert entry.value == _ROUND_CENTI((entry.sf * entry.vf - _1) * bal)

        bal += entry.value

def test_will_create_loan_daily_returns_bullet_4():
    '''
    Operação pré-fixada modalidade Bullet, na base 365 (legada).

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Bullet - PRE
    '''

    kwa = {}

    kwa['principal'] = bal = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('15')
    kwa['zero_date'] = datetime.date(2022, 1, 1)
    kwa['term'] = 12
    kwa['capitalisation'] = '365'

    # Calcula os retornos diários.
    for entry in fincore.get_bullet_daily_returns(**kwa):
        # Valida fator de juros.
        assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00038298')

        # Valida valor do rendimento.
        assert math.isclose(entry.value, (entry.sf - _1) * bal, abs_tol=_CENTI)

        bal += entry.value

def test_will_create_loan_daily_returns_price():
    '''
    Operação pré-fixada modalidade Price, com data de aniversário, duas antecipações parciais e uma antecipação total.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Price - AP & AT
    '''

    kwa = {}

    kwa['principal'] = bal = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('15')
    kwa['zero_date'] = datetime.date(2022, 1, 1)
    kwa['anniversary_date'] = datetime.date(2022, 2, 5)
    kwa['term'] = 12
    kwa['insertions'] = []

    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2022, 1, 10), value=decimal.Decimal('10338.71')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2022, 1, 20), value=decimal.Decimal('10338.77')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2022, 2, 20), value=decimal.Decimal('73755.96')))

    # Calcula os pagamentos.
    payments = list(fincore.build_price(calc_date=fincore.CalcDate(datetime.date(2022, 2, 20)), **kwa))

    kwa['is_bizz_day_cb'] = lambda x: x.weekday() < 5

    # Calcula os retornos diários.
    for entry in fincore.get_price_daily_returns(**kwa):
        if entry.period == 1:
            # Valida fator de juros.
            assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00037577')

            for pmt in payments:
                if entry.date == pmt.date:
                    bal -= pmt.raw

        elif entry.period == 2:
            # Valida fator de juros.
            assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00041604')

            for pmt in payments:
                if entry.date == pmt.date:
                    bal -= pmt.raw

        else:
            break  # FIXME: validar demais períodos.

        # Valida valor do rendimento.
        assert entry.value == _ROUND_CENTI((entry.sf - _1) * bal)

        bal += entry.value

def test_will_create_loan_daily_returns_livre_1():
    '''
    Operação pré-fixada modalidade Livre.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Livre - PRE
    '''

    kwa = {}

    kwa['principal'] = bal = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('15')
    kwa['vir'] = None
    kwa['amortizations'] = tab = []

    tab.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))

    for i in range(1, 13):
        date = datetime.date(2022, 1, 1) + _MONTH * i
        pct = decimal.Decimal(1) / decimal.Decimal(12)

        tab.append(fincore.Amortization(date, amortization_ratio=pct, amortizes_interest=True))

    # Calcula os pagamentos.
    pays = fincore.build(calc_date=fincore.CalcDate(datetime.date(2022, 2, 28)), **kwa)

    # Calcula os retornos diários.
    for entry in fincore.get_livre_daily_returns(**kwa):
        # Valida fator de juros.
        if entry.period == 1:
            assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00037577')

        elif entry.period == 2:
            assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00041604')

            if pay := next((x for x in pays if x.date == entry.date), None):
                bal -= pay.raw

        else:
            break  # FIXME: validar demais períodos.

        # Valida valor do rendimento.
        assert entry.value == _ROUND_CENTI((entry.sf - _1) * bal)

        bal += entry.value

def test_will_create_loan_daily_returns_livre_2():
    '''
    Operação CDI, modalidade Livre.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Livre - CDI
    '''

    kwa = {}

    kwa['principal'] = bal = decimal.Decimal('100000')
    kwa['apy'] = decimal.Decimal('5')
    kwa['vir'] = fincore.VariableIndex(code='CDI')
    kwa['amortizations'] = tab = []

    tab.append(fincore.Amortization(date=datetime.date(2022, 1, 1), amortizes_interest=False))

    for i in range(1, 13):
        date = datetime.date(2022, 1, 1) + _MONTH * i
        pct = decimal.Decimal(1) / decimal.Decimal(12)

        tab.append(fincore.Amortization(date, amortization_ratio=pct, amortizes_interest=True))

    for entry in fincore.get_livre_daily_returns(**kwa):
        # Valida fator de juros.
        if entry.date.weekday() >= 5:
            assert entry.vf == _1
            assert entry.sf == _1

        elif entry.period == 1:
            assert decimal.Decimal.quantize(entry.vf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00034749')
            assert decimal.Decimal.quantize(entry.sf, exp=decimal.Decimal('0.00000001')) == decimal.Decimal('1.00019363')

        else:
            break  # FIXME: validar demais períodos.

        # Valida valor do rendimento.
        assert entry.value == _ROUND_CENTI((entry.sf * entry.vf - _1) * bal)

        bal += entry.value

def test_will_create_loan_daily_returns_livre_3():
    '''
    Operação Resolvvi - Pré-Fixada - Parcelas Amortizadas - 30 meses, ID "XeGMPU4QNJK0Utfk1FeN0".

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: RESOLVVI 1 - PRE 30M
    '''

    kwa = {}
    tst = {}

    kwa['principal'] = bal = decimal.Decimal('660000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['amortizations'] = []
    kwa['insertions'] = []

    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 6, 19), amortizes_interest=False))

    for i in range(1, 30):
        date = datetime.date(2023, 6, 21) + _MONTH * i

        kwa['amortizations'].append(fincore.Amortization(date, amortization_ratio=_0, amortizes_interest=False))

    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 12, 21), amortization_ratio=decimal.Decimal(1), amortizes_interest=True))

    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2023, 7, 28), value=decimal.Decimal('34454.09')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2023, 8, 21), value=decimal.Decimal('90252.22')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2023, 9, 21), value=decimal.Decimal('242523.90')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2023, 10, 23), value=decimal.Decimal('330014.70')))

    # Data, período, número, fator, saldo inicial, rendimento
    tst[1] = datetime.date(2023, 6, 19), 1, 1, '1.00053469', '660000.00', '352.89'
    tst[2] = datetime.date(2023, 6, 20), 1, 2, '1.00053469', '660352.89', '353.08'
    tst[3] = datetime.date(2023, 6, 21), 1, 3, '1.00053469', '660705.98', '353.27'
    tst[4] = datetime.date(2023, 6, 22), 1, 4, '1.00053469', '661059.25', '353.46'
    tst[5] = datetime.date(2023, 6, 23), 1, 5, '1.00053469', '661412.71', '353.65'
    tst[6] = datetime.date(2023, 6, 24), 1, 6, '1.00053469', '661766.36', '353.84'
    tst[7] = datetime.date(2023, 6, 25), 1, 7, '1.00053469', '662120.20', '354.03'
    tst[8] = datetime.date(2023, 6, 26), 1, 8, '1.00053469', '662474.23', '354.22'
    tst[9] = datetime.date(2023, 6, 27), 1, 9, '1.00053469', '662828.44', '354.41'
    tst[10] = datetime.date(2023, 6, 28), 1, 10, '1.00053469', '663182.85', '354.60'
    tst[11] = datetime.date(2023, 6, 29), 1, 11, '1.00053469', '663537.45', '354.79'
    tst[12] = datetime.date(2023, 6, 30), 1, 12, '1.00053469', '663892.23', '354.98'
    tst[13] = datetime.date(2023, 7, 1), 1, 13, '1.00053469', '664247.21', '355.17'
    tst[14] = datetime.date(2023, 7, 2), 1, 14, '1.00053469', '664602.37', '355.36'
    tst[15] = datetime.date(2023, 7, 3), 1, 15, '1.00053469', '664957.73', '355.55'
    tst[16] = datetime.date(2023, 7, 4), 1, 16, '1.00053469', '665313.27', '355.74'
    tst[17] = datetime.date(2023, 7, 5), 1, 17, '1.00053469', '665669.01', '355.93'
    tst[18] = datetime.date(2023, 7, 6), 1, 18, '1.00053469', '666024.93', '356.12'
    tst[19] = datetime.date(2023, 7, 7), 1, 19, '1.00053469', '666381.05', '356.31'
    tst[20] = datetime.date(2023, 7, 8), 1, 20, '1.00053469', '666737.35', '356.50'
    tst[21] = datetime.date(2023, 7, 9), 1, 21, '1.00053469', '667093.85', '356.69'
    tst[22] = datetime.date(2023, 7, 10), 1, 22, '1.00053469', '667450.54', '356.88'
    tst[23] = datetime.date(2023, 7, 11), 1, 23, '1.00053469', '667807.42', '357.07'
    tst[24] = datetime.date(2023, 7, 12), 1, 24, '1.00053469', '668164.48', '357.26'
    tst[25] = datetime.date(2023, 7, 13), 1, 25, '1.00053469', '668521.74', '357.45'
    tst[26] = datetime.date(2023, 7, 14), 1, 26, '1.00053469', '668879.19', '357.64'
    tst[27] = datetime.date(2023, 7, 15), 1, 27, '1.00053469', '669236.84', '357.83'
    tst[28] = datetime.date(2023, 7, 16), 1, 28, '1.00053469', '669594.67', '358.02'
    tst[29] = datetime.date(2023, 7, 17), 1, 29, '1.00053469', '669952.69', '358.22'
    tst[30] = datetime.date(2023, 7, 18), 1, 30, '1.00053469', '670310.91', '358.41'
    tst[31] = datetime.date(2023, 7, 19), 1, 31, '1.00053469', '670669.32', '358.60'
    tst[32] = datetime.date(2023, 7, 20), 1, 32, '1.00053469', '671027.92', '358.79'
    tst[33] = datetime.date(2023, 7, 21), 2, 1, '1.00053469', '671386.71', '358.98'
    tst[34] = datetime.date(2023, 7, 22), 2, 2, '1.00053469', '671745.69', '359.17'
    tst[35] = datetime.date(2023, 7, 23), 2, 3, '1.00053469', '672104.86', '359.37'
    tst[36] = datetime.date(2023, 7, 24), 2, 4, '1.00053469', '672464.23', '359.56'
    tst[37] = datetime.date(2023, 7, 25), 2, 5, '1.00053469', '672823.79', '359.75'
    tst[38] = datetime.date(2023, 7, 26), 2, 6, '1.00053469', '673183.54', '359.94'
    tst[39] = datetime.date(2023, 7, 27), 2, 7, '1.00053469', '673543.48', '360.14'
    tst[40] = datetime.date(2023, 7, 28), 2, 8, '1.00053469', '673903.62', '341.91'
    tst[41] = datetime.date(2023, 7, 29), 2, 9, '1.00053469', '639791.44', '342.09'
    tst[42] = datetime.date(2023, 7, 30), 2, 10, '1.00053469', '640133.52', '342.27'
    tst[43] = datetime.date(2023, 7, 31), 2, 11, '1.00053469', '640475.80', '342.45'
    tst[44] = datetime.date(2023, 8, 1), 2, 12, '1.00053469', '640818.25', '342.64'
    tst[45] = datetime.date(2023, 8, 2), 2, 13, '1.00053469', '641160.89', '342.82'
    tst[46] = datetime.date(2023, 8, 3), 2, 14, '1.00053469', '641503.71', '343.00'
    tst[47] = datetime.date(2023, 8, 4), 2, 15, '1.00053469', '641846.71', '343.19'
    tst[48] = datetime.date(2023, 8, 5), 2, 16, '1.00053469', '642189.90', '343.37'
    tst[49] = datetime.date(2023, 8, 6), 2, 17, '1.00053469', '642533.27', '343.55'
    tst[50] = datetime.date(2023, 8, 7), 2, 18, '1.00053469', '642876.83', '343.74'
    tst[51] = datetime.date(2023, 8, 8), 2, 19, '1.00053469', '643220.57', '343.92'
    tst[52] = datetime.date(2023, 8, 9), 2, 20, '1.00053469', '643564.49', '344.11'
    tst[53] = datetime.date(2023, 8, 10), 2, 21, '1.00053469', '643908.60', '344.29'
    tst[54] = datetime.date(2023, 8, 11), 2, 22, '1.00053469', '644252.89', '344.47'
    tst[55] = datetime.date(2023, 8, 12), 2, 23, '1.00053469', '644597.36', '344.66'
    tst[56] = datetime.date(2023, 8, 13), 2, 24, '1.00053469', '644942.02', '344.84'
    tst[57] = datetime.date(2023, 8, 14), 2, 25, '1.00053469', '645286.86', '345.03'
    tst[58] = datetime.date(2023, 8, 15), 2, 26, '1.00053469', '645631.89', '345.21'
    tst[59] = datetime.date(2023, 8, 16), 2, 27, '1.00053469', '645977.10', '345.40'
    tst[60] = datetime.date(2023, 8, 17), 2, 28, '1.00053469', '646322.50', '345.58'
    tst[61] = datetime.date(2023, 8, 18), 2, 29, '1.00053469', '646668.08', '345.77'
    tst[62] = datetime.date(2023, 8, 19), 2, 30, '1.00053469', '647013.84', '345.95'
    tst[63] = datetime.date(2023, 8, 20), 2, 31, '1.00053469', '647359.80', '346.14'
    tst[64] = datetime.date(2023, 8, 21), 3, 1, '1.00053469', '647705.93', '298.06'
    tst[65] = datetime.date(2023, 8, 22), 3, 2, '1.00053469', '557751.78', '298.22'
    tst[66] = datetime.date(2023, 8, 23), 3, 3, '1.00053469', '558050.00', '298.38'
    tst[67] = datetime.date(2023, 8, 24), 3, 4, '1.00053469', '558348.38', '298.54'
    tst[68] = datetime.date(2023, 8, 25), 3, 5, '1.00053469', '558646.92', '298.70'
    tst[69] = datetime.date(2023, 8, 26), 3, 6, '1.00053469', '558945.63', '298.86'
    tst[70] = datetime.date(2023, 8, 27), 3, 7, '1.00053469', '559244.49', '299.02'
    tst[71] = datetime.date(2023, 8, 28), 3, 8, '1.00053469', '559543.51', '299.18'
    tst[72] = datetime.date(2023, 8, 29), 3, 9, '1.00053469', '559842.69', '299.34'
    tst[73] = datetime.date(2023, 8, 30), 3, 10, '1.00053469', '560142.03', '299.50'
    tst[74] = datetime.date(2023, 8, 31), 3, 11, '1.00053469', '560441.53', '299.66'
    tst[75] = datetime.date(2023, 9, 1), 3, 12, '1.00053469', '560741.19', '299.82'
    tst[76] = datetime.date(2023, 9, 2), 3, 13, '1.00053469', '561041.02', '299.98'
    tst[77] = datetime.date(2023, 9, 3), 3, 14, '1.00053469', '561341.00', '300.14'
    tst[78] = datetime.date(2023, 9, 4), 3, 15, '1.00053469', '561641.14', '300.30'
    tst[79] = datetime.date(2023, 9, 5), 3, 16, '1.00053469', '561941.44', '300.46'
    tst[80] = datetime.date(2023, 9, 6), 3, 17, '1.00053469', '562241.91', '300.62'
    tst[81] = datetime.date(2023, 9, 7), 3, 18, '1.00053469', '562542.53', '300.78'
    tst[82] = datetime.date(2023, 9, 8), 3, 19, '1.00053469', '562843.32', '300.95'
    tst[83] = datetime.date(2023, 9, 9), 3, 20, '1.00053469', '563144.26', '301.11'
    tst[84] = datetime.date(2023, 9, 10), 3, 21, '1.00053469', '563445.37', '301.27'
    tst[85] = datetime.date(2023, 9, 11), 3, 22, '1.00053469', '563746.64', '301.43'
    tst[86] = datetime.date(2023, 9, 12), 3, 23, '1.00053469', '564048.06', '301.59'
    tst[87] = datetime.date(2023, 9, 13), 3, 24, '1.00053469', '564349.65', '301.75'
    tst[88] = datetime.date(2023, 9, 14), 3, 25, '1.00053469', '564651.40', '301.91'
    tst[89] = datetime.date(2023, 9, 15), 3, 26, '1.00053469', '564953.32', '302.07'
    tst[90] = datetime.date(2023, 9, 16), 3, 27, '1.00053469', '565255.39', '302.24'
    tst[91] = datetime.date(2023, 9, 17), 3, 28, '1.00053469', '565557.63', '302.40'
    tst[92] = datetime.date(2023, 9, 18), 3, 29, '1.00053469', '565860.02', '302.56'
    tst[93] = datetime.date(2023, 9, 19), 3, 30, '1.00053469', '566162.58', '302.72'
    tst[94] = datetime.date(2023, 9, 20), 3, 31, '1.00053469', '566465.30', '302.88'
    tst[95] = datetime.date(2023, 9, 21), 4, 1, '1.00055252', '566768.18', '179.15'
    tst[96] = datetime.date(2023, 9, 22), 4, 2, '1.00055252', '324423.44', '179.25'
    tst[97] = datetime.date(2023, 9, 23), 4, 3, '1.00055252', '324602.68', '179.35'
    tst[98] = datetime.date(2023, 9, 24), 4, 4, '1.00055252', '324782.03', '179.45'
    tst[99] = datetime.date(2023, 9, 25), 4, 5, '1.00055252', '324961.48', '179.55'
    tst[100] = datetime.date(2023, 9, 26), 4, 6, '1.00055252', '325141.03', '179.65'
    tst[101] = datetime.date(2023, 9, 27), 4, 7, '1.00055252', '325320.67', '179.74'
    tst[102] = datetime.date(2023, 9, 28), 4, 8, '1.00055252', '325500.42', '179.84'
    tst[103] = datetime.date(2023, 9, 29), 4, 9, '1.00055252', '325680.26', '179.94'
    tst[104] = datetime.date(2023, 9, 30), 4, 10, '1.00055252', '325860.20', '180.04'
    tst[105] = datetime.date(2023, 10, 1), 4, 11, '1.00055252', '326040.25', '180.14'
    tst[106] = datetime.date(2023, 10, 2), 4, 12, '1.00055252', '326220.39', '180.24'
    tst[107] = datetime.date(2023, 10, 3), 4, 13, '1.00055252', '326400.63', '180.34'
    tst[108] = datetime.date(2023, 10, 4), 4, 14, '1.00055252', '326580.97', '180.44'
    tst[109] = datetime.date(2023, 10, 5), 4, 15, '1.00055252', '326761.41', '180.54'
    tst[110] = datetime.date(2023, 10, 6), 4, 16, '1.00055252', '326941.96', '180.64'
    tst[111] = datetime.date(2023, 10, 7), 4, 17, '1.00055252', '327122.60', '180.74'
    tst[112] = datetime.date(2023, 10, 8), 4, 18, '1.00055252', '327303.34', '180.84'
    tst[113] = datetime.date(2023, 10, 9), 4, 19, '1.00055252', '327484.18', '180.94'
    tst[114] = datetime.date(2023, 10, 10), 4, 20, '1.00055252', '327665.12', '181.04'
    tst[115] = datetime.date(2023, 10, 11), 4, 21, '1.00055252', '327846.16', '181.14'
    tst[116] = datetime.date(2023, 10, 12), 4, 22, '1.00055252', '328027.30', '181.24'
    tst[117] = datetime.date(2023, 10, 13), 4, 23, '1.00055252', '328208.54', '181.34'
    tst[118] = datetime.date(2023, 10, 14), 4, 24, '1.00055252', '328389.88', '181.44'
    tst[119] = datetime.date(2023, 10, 15), 4, 25, '1.00055252', '328571.32', '181.54'
    tst[120] = datetime.date(2023, 10, 16), 4, 26, '1.00055252', '328752.86', '181.64'
    tst[121] = datetime.date(2023, 10, 17), 4, 27, '1.00055252', '328934.50', '181.74'
    tst[122] = datetime.date(2023, 10, 18), 4, 28, '1.00055252', '329116.24', '181.84'
    tst[123] = datetime.date(2023, 10, 19), 4, 29, '1.00055252', '329298.09', '181.94'
    tst[124] = datetime.date(2023, 10, 20), 4, 30, '1.00055252', '329480.03', '182.04'
    tst[125] = datetime.date(2023, 10, 21), 5, 1, '1.00053469', '329662.07', '176.27'
    tst[126] = datetime.date(2023, 10, 22), 5, 2, '1.00053469', '329838.34', '176.36'

    for i, entry in enumerate(fincore.get_livre_daily_returns(**kwa), 1):
        assert entry.date == tst[i][0]
        assert entry.period == tst[i][1]
        assert entry.no == tst[i][2]

        # Fator fixo, saldo, valor do rendimento.
        assert math.isclose(entry.sf, decimal.Decimal(tst[i][3]), rel_tol=1e-8)
        assert bal == decimal.Decimal(tst[i][4])
        assert entry.value == decimal.Decimal(tst[i][5])

        # Memoriza o saldo para a próxima iteração.
        bal = entry.bal

def test_will_create_loan_daily_returns_livre_4():
    '''
    Operação Resolvvi 4 - Pré-Fixada - Parcelas Amortizadas - 30 meses, ID "yNdS80j75OzXrqBH62WrF".

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: RESOLVVI 4 - PRE 30M
    '''

    kwa = {}
    tst = {}

    kwa['principal'] = bal = decimal.Decimal('988000')
    kwa['apy'] = decimal.Decimal('22')
    kwa['amortizations'] = []
    kwa['insertions'] = []

    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 9, 29), amortizes_interest=False))

    for i in range(1, 31):
        date = datetime.date(2023, 9, 29) + _MONTH * i

        if i < 30:
            kwa['amortizations'].append(fincore.Amortization(date, amortization_ratio=_0, amortizes_interest=False))

        else:
            kwa['amortizations'].append(fincore.Amortization(date, amortization_ratio=decimal.Decimal(1), amortizes_interest=True))

    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2024, 4, 1), value=decimal.Decimal('215350.00')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2024, 4, 29), value=decimal.Decimal('345074.00')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2024, 5, 28), value=decimal.Decimal('388507.00')))
    kwa['insertions'].append(fincore.Amortization.Bare(date=datetime.date(2024, 6, 28), value=decimal.Decimal('168930.68')))

    # Data, período, número, fator, saldo inicial, rendimento
    tst[1] = datetime.date(2023, 9, 29), 1, 1, '1.00055252', '988000.00', '545.89'
    tst[2] = datetime.date(2023, 9, 30), 1, 2, '1.00055252', '988545.89', '546.19'
    tst[3] = datetime.date(2023, 10, 1), 1, 3, '1.00055252', '989092.07', '546.49'
    tst[4] = datetime.date(2023, 10, 2), 1, 4, '1.00055252', '989638.56', '546.79'
    tst[5] = datetime.date(2023, 10, 3), 1, 5, '1.00055252', '990185.35', '547.09'
    tst[6] = datetime.date(2023, 10, 4), 1, 6, '1.00055252', '990732.45', '547.40'
    tst[7] = datetime.date(2023, 10, 5), 1, 7, '1.00055252', '991279.84', '547.70'
    tst[8] = datetime.date(2023, 10, 6), 1, 8, '1.00055252', '991827.54', '548.00'
    tst[9] = datetime.date(2023, 10, 7), 1, 9, '1.00055252', '992375.54', '548.30'
    tst[10] = datetime.date(2023, 10, 8), 1, 10, '1.00055252', '992923.84', '548.61'
    tst[11] = datetime.date(2023, 10, 9), 1, 11, '1.00055252', '993472.45', '548.91'
    tst[12] = datetime.date(2023, 10, 10), 1, 12, '1.00055252', '994021.36', '549.21'
    tst[13] = datetime.date(2023, 10, 11), 1, 13, '1.00055252', '994570.57', '549.52'
    tst[14] = datetime.date(2023, 10, 12), 1, 14, '1.00055252', '995120.09', '549.82'
    tst[15] = datetime.date(2023, 10, 13), 1, 15, '1.00055252', '995669.91', '550.12'
    tst[16] = datetime.date(2023, 10, 14), 1, 16, '1.00055252', '996220.03', '550.43'
    tst[17] = datetime.date(2023, 10, 15), 1, 17, '1.00055252', '996770.46', '550.73'
    tst[18] = datetime.date(2023, 10, 16), 1, 18, '1.00055252', '997321.19', '551.04'
    tst[19] = datetime.date(2023, 10, 17), 1, 19, '1.00055252', '997872.23', '551.34'
    tst[20] = datetime.date(2023, 10, 18), 1, 20, '1.00055252', '998423.57', '551.65'
    tst[21] = datetime.date(2023, 10, 19), 1, 21, '1.00055252', '998975.21', '551.95'
    tst[22] = datetime.date(2023, 10, 20), 1, 22, '1.00055252', '999527.16', '552.25'
    tst[23] = datetime.date(2023, 10, 21), 1, 23, '1.00055252', '1000079.42', '552.56'
    tst[24] = datetime.date(2023, 10, 22), 1, 24, '1.00055252', '1000631.98', '552.87'
    tst[25] = datetime.date(2023, 10, 23), 1, 25, '1.00055252', '1001184.84', '553.17'
    tst[26] = datetime.date(2023, 10, 24), 1, 26, '1.00055252', '1001738.01', '553.48'
    tst[27] = datetime.date(2023, 10, 25), 1, 27, '1.00055252', '1002291.49', '553.78'
    tst[28] = datetime.date(2023, 10, 26), 1, 28, '1.00055252', '1002845.27', '554.09'
    tst[29] = datetime.date(2023, 10, 27), 1, 29, '1.00055252', '1003399.36', '554.39'
    tst[30] = datetime.date(2023, 10, 28), 1, 30, '1.00055252', '1003953.76', '554.70'
    tst[31] = datetime.date(2023, 10, 29), 2, 1, '1.00053469', '1004508.46', '537.10'
    tst[32] = datetime.date(2023, 10, 30), 2, 2, '1.00053469', '1005045.56', '537.39'
    tst[33] = datetime.date(2023, 10, 31), 2, 3, '1.00053469', '1005582.94', '537.67'
    tst[34] = datetime.date(2023, 11, 1), 2, 4, '1.00053469', '1006120.61', '537.96'
    tst[35] = datetime.date(2023, 11, 2), 2, 5, '1.00053469', '1006658.58', '538.25'
    tst[36] = datetime.date(2023, 11, 3), 2, 6, '1.00053469', '1007196.82', '538.54'
    tst[37] = datetime.date(2023, 11, 4), 2, 7, '1.00053469', '1007735.36', '538.82'
    tst[38] = datetime.date(2023, 11, 5), 2, 8, '1.00053469', '1008274.18', '539.11'
    tst[39] = datetime.date(2023, 11, 6), 2, 9, '1.00053469', '1008813.30', '539.40'
    tst[40] = datetime.date(2023, 11, 7), 2, 10, '1.00053469', '1009352.70', '539.69'
    tst[41] = datetime.date(2023, 11, 8), 2, 11, '1.00053469', '1009892.39', '539.98'
    tst[42] = datetime.date(2023, 11, 9), 2, 12, '1.00053469', '1010432.36', '540.27'
    tst[43] = datetime.date(2023, 11, 10), 2, 13, '1.00053469', '1010972.63', '540.56'
    tst[44] = datetime.date(2023, 11, 11), 2, 14, '1.00053469', '1011513.19', '540.84'
    tst[45] = datetime.date(2023, 11, 12), 2, 15, '1.00053469', '1012054.03', '541.13'
    tst[46] = datetime.date(2023, 11, 13), 2, 16, '1.00053469', '1012595.16', '541.42'
    tst[47] = datetime.date(2023, 11, 14), 2, 17, '1.00053469', '1013136.59', '541.71'
    tst[48] = datetime.date(2023, 11, 15), 2, 18, '1.00053469', '1013678.30', '542.00'
    tst[49] = datetime.date(2023, 11, 16), 2, 19, '1.00053469', '1014220.30', '542.29'
    tst[50] = datetime.date(2023, 11, 17), 2, 20, '1.00053469', '1014762.59', '542.58'
    tst[51] = datetime.date(2023, 11, 18), 2, 21, '1.00053469', '1015305.17', '542.87'
    tst[52] = datetime.date(2023, 11, 19), 2, 22, '1.00053469', '1015848.04', '543.16'
    tst[53] = datetime.date(2023, 11, 20), 2, 23, '1.00053469', '1016391.21', '543.45'
    tst[54] = datetime.date(2023, 11, 21), 2, 24, '1.00053469', '1016934.66', '543.74'
    tst[55] = datetime.date(2023, 11, 22), 2, 25, '1.00053469', '1017478.40', '544.03'
    tst[56] = datetime.date(2023, 11, 23), 2, 26, '1.00053469', '1018022.44', '544.32'
    tst[57] = datetime.date(2023, 11, 24), 2, 27, '1.00053469', '1018566.76', '544.62'
    tst[58] = datetime.date(2023, 11, 25), 2, 28, '1.00053469', '1019111.38', '544.91'
    tst[59] = datetime.date(2023, 11, 26), 2, 29, '1.00053469', '1019656.28', '545.20'
    tst[60] = datetime.date(2023, 11, 27), 2, 30, '1.00053469', '1020201.48', '545.49'
    tst[61] = datetime.date(2023, 11, 28), 2, 31, '1.00053469', '1020746.97', '545.78'
    tst[62] = datetime.date(2023, 11, 29), 3, 1, '1.00055252', '1021292.75', '564.28'
    tst[63] = datetime.date(2023, 11, 30), 3, 2, '1.00055252', '1021857.03', '564.59'
    tst[64] = datetime.date(2023, 12, 1), 3, 3, '1.00055252', '1022421.62', '564.90'
    tst[65] = datetime.date(2023, 12, 2), 3, 4, '1.00055252', '1022986.53', '565.22'
    tst[66] = datetime.date(2023, 12, 3), 3, 5, '1.00055252', '1023551.75', '565.53'
    tst[67] = datetime.date(2023, 12, 4), 3, 6, '1.00055252', '1024117.27', '565.84'
    tst[68] = datetime.date(2023, 12, 5), 3, 7, '1.00055252', '1024683.12', '566.15'
    tst[69] = datetime.date(2023, 12, 6), 3, 8, '1.00055252', '1025249.27', '566.47'
    tst[70] = datetime.date(2023, 12, 7), 3, 9, '1.00055252', '1025815.74', '566.78'
    tst[71] = datetime.date(2023, 12, 8), 3, 10, '1.00055252', '1026382.52', '567.09'
    tst[72] = datetime.date(2023, 12, 9), 3, 11, '1.00055252', '1026949.61', '567.41'
    tst[73] = datetime.date(2023, 12, 10), 3, 12, '1.00055252', '1027517.02', '567.72'
    tst[74] = datetime.date(2023, 12, 11), 3, 13, '1.00055252', '1028084.73', '568.03'
    tst[75] = datetime.date(2023, 12, 12), 3, 14, '1.00055252', '1028652.77', '568.35'
    tst[76] = datetime.date(2023, 12, 13), 3, 15, '1.00055252', '1029221.12', '568.66'
    tst[77] = datetime.date(2023, 12, 14), 3, 16, '1.00055252', '1029789.78', '568.98'
    tst[78] = datetime.date(2023, 12, 15), 3, 17, '1.00055252', '1030358.75', '569.29'
    tst[79] = datetime.date(2023, 12, 16), 3, 18, '1.00055252', '1030928.04', '569.60'
    tst[80] = datetime.date(2023, 12, 17), 3, 19, '1.00055252', '1031497.65', '569.92'
    tst[81] = datetime.date(2023, 12, 18), 3, 20, '1.00055252', '1032067.57', '570.23'
    tst[82] = datetime.date(2023, 12, 19), 3, 21, '1.00055252', '1032637.80', '570.55'
    tst[83] = datetime.date(2023, 12, 20), 3, 22, '1.00055252', '1033208.35', '570.86'
    tst[84] = datetime.date(2023, 12, 21), 3, 23, '1.00055252', '1033779.21', '571.18'
    tst[85] = datetime.date(2023, 12, 22), 3, 24, '1.00055252', '1034350.39', '571.50'
    tst[86] = datetime.date(2023, 12, 23), 3, 25, '1.00055252', '1034921.89', '571.81'
    tst[87] = datetime.date(2023, 12, 24), 3, 26, '1.00055252', '1035493.70', '572.13'
    tst[88] = datetime.date(2023, 12, 25), 3, 27, '1.00055252', '1036065.83', '572.44'
    tst[89] = datetime.date(2023, 12, 26), 3, 28, '1.00055252', '1036638.27', '572.76'
    tst[90] = datetime.date(2023, 12, 27), 3, 29, '1.00055252', '1037211.03', '573.08'
    tst[91] = datetime.date(2023, 12, 28), 3, 30, '1.00055252', '1037784.10', '573.39'
    tst[92] = datetime.date(2023, 12, 29), 4, 1, '1.00053469', '1038357.50', '555.20'
    tst[93] = datetime.date(2023, 12, 30), 4, 2, '1.00053469', '1038912.69', '555.49'
    tst[94] = datetime.date(2023, 12, 31), 4, 3, '1.00053469', '1039468.19', '555.79'
    tst[95] = datetime.date(2024, 1, 1), 4, 4, '1.00053469', '1040023.98', '556.09'
    tst[96] = datetime.date(2024, 1, 2), 4, 5, '1.00053469', '1040580.07', '556.39'
    tst[97] = datetime.date(2024, 1, 3), 4, 6, '1.00053469', '1041136.45', '556.68'
    tst[98] = datetime.date(2024, 1, 4), 4, 7, '1.00053469', '1041693.14', '556.98'
    tst[99] = datetime.date(2024, 1, 5), 4, 8, '1.00053469', '1042250.12', '557.28'
    tst[100] = datetime.date(2024, 1, 6), 4, 9, '1.00053469', '1042807.40', '557.58'
    tst[101] = datetime.date(2024, 1, 7), 4, 10, '1.00053469', '1043364.97', '557.87'
    tst[102] = datetime.date(2024, 1, 8), 4, 11, '1.00053469', '1043922.85', '558.17'
    tst[103] = datetime.date(2024, 1, 9), 4, 12, '1.00053469', '1044481.02', '558.47'
    tst[104] = datetime.date(2024, 1, 10), 4, 13, '1.00053469', '1045039.49', '558.77'
    tst[105] = datetime.date(2024, 1, 11), 4, 14, '1.00053469', '1045598.26', '559.07'
    tst[106] = datetime.date(2024, 1, 12), 4, 15, '1.00053469', '1046157.33', '559.37'
    tst[107] = datetime.date(2024, 1, 13), 4, 16, '1.00053469', '1046716.70', '559.67'
    tst[108] = datetime.date(2024, 1, 14), 4, 17, '1.00053469', '1047276.37', '559.97'
    tst[109] = datetime.date(2024, 1, 15), 4, 18, '1.00053469', '1047836.33', '560.27'
    tst[110] = datetime.date(2024, 1, 16), 4, 19, '1.00053469', '1048396.60', '560.57'
    tst[111] = datetime.date(2024, 1, 17), 4, 20, '1.00053469', '1048957.17', '560.87'
    tst[112] = datetime.date(2024, 1, 18), 4, 21, '1.00053469', '1049518.03', '561.16'
    tst[113] = datetime.date(2024, 1, 19), 4, 22, '1.00053469', '1050079.20', '561.46'
    tst[114] = datetime.date(2024, 1, 20), 4, 23, '1.00053469', '1050640.66', '561.77'
    tst[115] = datetime.date(2024, 1, 21), 4, 24, '1.00053469', '1051202.43', '562.07'
    tst[116] = datetime.date(2024, 1, 22), 4, 25, '1.00053469', '1051764.49', '562.37'
    tst[117] = datetime.date(2024, 1, 23), 4, 26, '1.00053469', '1052326.86', '562.67'
    tst[118] = datetime.date(2024, 1, 24), 4, 27, '1.00053469', '1052889.52', '562.97'
    tst[119] = datetime.date(2024, 1, 25), 4, 28, '1.00053469', '1053452.49', '563.27'
    tst[120] = datetime.date(2024, 1, 26), 4, 29, '1.00053469', '1054015.76', '563.57'
    tst[121] = datetime.date(2024, 1, 27), 4, 30, '1.00053469', '1054579.33', '563.87'
    tst[122] = datetime.date(2024, 1, 28), 4, 31, '1.00053469', '1055143.20', '564.17'
    tst[123] = datetime.date(2024, 1, 29), 5, 1, '1.00053469', '1055707.37', '564.47'
    tst[124] = datetime.date(2024, 1, 30), 5, 2, '1.00053469', '1056271.85', '564.78'
    tst[125] = datetime.date(2024, 1, 31), 5, 3, '1.00053469', '1056836.62', '565.08'
    tst[126] = datetime.date(2024, 2, 1), 5, 4, '1.00053469', '1057401.70', '565.38'
    tst[127] = datetime.date(2024, 2, 2), 5, 5, '1.00053469', '1057967.08', '565.68'
    tst[128] = datetime.date(2024, 2, 3), 5, 6, '1.00053469', '1058532.76', '565.98'
    tst[129] = datetime.date(2024, 2, 4), 5, 7, '1.00053469', '1059098.75', '566.29'
    tst[130] = datetime.date(2024, 2, 5), 5, 8, '1.00053469', '1059665.04', '566.59'
    tst[131] = datetime.date(2024, 2, 6), 5, 9, '1.00053469', '1060231.63', '566.89'
    tst[132] = datetime.date(2024, 2, 7), 5, 10, '1.00053469', '1060798.52', '567.20'
    tst[133] = datetime.date(2024, 2, 8), 5, 11, '1.00053469', '1061365.72', '567.50'
    tst[134] = datetime.date(2024, 2, 9), 5, 12, '1.00053469', '1061933.22', '567.80'
    tst[135] = datetime.date(2024, 2, 10), 5, 13, '1.00053469', '1062501.02', '568.11'
    tst[136] = datetime.date(2024, 2, 11), 5, 14, '1.00053469', '1063069.13', '568.41'
    tst[137] = datetime.date(2024, 2, 12), 5, 15, '1.00053469', '1063637.54', '568.71'
    tst[138] = datetime.date(2024, 2, 13), 5, 16, '1.00053469', '1064206.25', '569.02'
    tst[139] = datetime.date(2024, 2, 14), 5, 17, '1.00053469', '1064775.27', '569.32'
    tst[140] = datetime.date(2024, 2, 15), 5, 18, '1.00053469', '1065344.59', '569.63'
    tst[141] = datetime.date(2024, 2, 16), 5, 19, '1.00053469', '1065914.22', '569.93'
    tst[142] = datetime.date(2024, 2, 17), 5, 20, '1.00053469', '1066484.15', '570.24'
    tst[143] = datetime.date(2024, 2, 18), 5, 21, '1.00053469', '1067054.39', '570.54'
    tst[144] = datetime.date(2024, 2, 19), 5, 22, '1.00053469', '1067624.93', '570.85'
    tst[145] = datetime.date(2024, 2, 20), 5, 23, '1.00053469', '1068195.78', '571.15'
    tst[146] = datetime.date(2024, 2, 21), 5, 24, '1.00053469', '1068766.93', '571.46'
    tst[147] = datetime.date(2024, 2, 22), 5, 25, '1.00053469', '1069338.39', '571.76'
    tst[148] = datetime.date(2024, 2, 23), 5, 26, '1.00053469', '1069910.15', '572.07'
    tst[149] = datetime.date(2024, 2, 24), 5, 27, '1.00053469', '1070482.22', '572.37'
    tst[150] = datetime.date(2024, 2, 25), 5, 28, '1.00053469', '1071054.59', '572.68'
    tst[151] = datetime.date(2024, 2, 26), 5, 29, '1.00053469', '1071627.27', '572.99'
    tst[152] = datetime.date(2024, 2, 27), 5, 30, '1.00053469', '1072200.26', '573.29'
    tst[153] = datetime.date(2024, 2, 28), 5, 31, '1.00053469', '1072773.55', '573.60'
    tst[154] = datetime.date(2024, 2, 29), 6, 1, '1.00057157', '1073347.15', '613.50'
    tst[155] = datetime.date(2024, 3, 1), 6, 2, '1.00057157', '1073960.65', '613.85'
    tst[156] = datetime.date(2024, 3, 2), 6, 3, '1.00057157', '1074574.49', '614.20'
    tst[157] = datetime.date(2024, 3, 3), 6, 4, '1.00057157', '1075188.69', '614.55'
    tst[158] = datetime.date(2024, 3, 4), 6, 5, '1.00057157', '1075803.24', '614.90'
    tst[159] = datetime.date(2024, 3, 5), 6, 6, '1.00057157', '1076418.14', '615.25'
    tst[160] = datetime.date(2024, 3, 6), 6, 7, '1.00057157', '1077033.40', '615.60'
    tst[161] = datetime.date(2024, 3, 7), 6, 8, '1.00057157', '1077649.00', '615.96'
    tst[162] = datetime.date(2024, 3, 8), 6, 9, '1.00057157', '1078264.96', '616.31'
    tst[163] = datetime.date(2024, 3, 9), 6, 10, '1.00057157', '1078881.26', '616.66'
    tst[164] = datetime.date(2024, 3, 10), 6, 11, '1.00057157', '1079497.92', '617.01'
    tst[165] = datetime.date(2024, 3, 11), 6, 12, '1.00057157', '1080114.94', '617.37'
    tst[166] = datetime.date(2024, 3, 12), 6, 13, '1.00057157', '1080732.30', '617.72'
    tst[167] = datetime.date(2024, 3, 13), 6, 14, '1.00057157', '1081350.02', '618.07'
    tst[168] = datetime.date(2024, 3, 14), 6, 15, '1.00057157', '1081968.09', '618.42'
    tst[169] = datetime.date(2024, 3, 15), 6, 16, '1.00057157', '1082586.52', '618.78'
    tst[170] = datetime.date(2024, 3, 16), 6, 17, '1.00057157', '1083205.30', '619.13'
    tst[171] = datetime.date(2024, 3, 17), 6, 18, '1.00057157', '1083824.43', '619.49'
    tst[172] = datetime.date(2024, 3, 18), 6, 19, '1.00057157', '1084443.91', '619.84'
    tst[173] = datetime.date(2024, 3, 19), 6, 20, '1.00057157', '1085063.75', '620.19'
    tst[174] = datetime.date(2024, 3, 20), 6, 21, '1.00057157', '1085683.95', '620.55'
    tst[175] = datetime.date(2024, 3, 21), 6, 22, '1.00057157', '1086304.49', '620.90'
    tst[176] = datetime.date(2024, 3, 22), 6, 23, '1.00057157', '1086925.40', '621.26'
    tst[177] = datetime.date(2024, 3, 23), 6, 24, '1.00057157', '1087546.66', '621.61'
    tst[178] = datetime.date(2024, 3, 24), 6, 25, '1.00057157', '1088168.27', '621.97'
    tst[179] = datetime.date(2024, 3, 25), 6, 26, '1.00057157', '1088790.24', '622.32'
    tst[180] = datetime.date(2024, 3, 26), 6, 27, '1.00057157', '1089412.56', '622.68'
    tst[181] = datetime.date(2024, 3, 27), 6, 28, '1.00057157', '1090035.24', '623.04'
    tst[182] = datetime.date(2024, 3, 28), 6, 29, '1.00057157', '1090658.28', '623.39'
    tst[183] = datetime.date(2024, 3, 29), 7, 1, '1.00053469', '1091281.67', '583.50'
    tst[184] = datetime.date(2024, 3, 30), 7, 2, '1.00053469', '1091865.16', '583.81'
    tst[185] = datetime.date(2024, 3, 31), 7, 3, '1.00053469', '1092448.97', '584.12'
    tst[186] = datetime.date(2024, 4, 1), 7, 4, '1.00053469', '1093033.09', '469.29'
    tst[187] = datetime.date(2024, 4, 2), 7, 5, '1.00053469', '878152.38', '469.54'
    tst[188] = datetime.date(2024, 4, 3), 7, 6, '1.00053469', '878621.92', '469.79'
    tst[189] = datetime.date(2024, 4, 4), 7, 7, '1.00053469', '879091.70', '470.04'
    tst[190] = datetime.date(2024, 4, 5), 7, 8, '1.00053469', '879561.74', '470.29'
    tst[191] = datetime.date(2024, 4, 6), 7, 9, '1.00053469', '880032.04', '470.54'
    tst[192] = datetime.date(2024, 4, 7), 7, 10, '1.00053469', '880502.58', '470.79'
    tst[193] = datetime.date(2024, 4, 8), 7, 11, '1.00053469', '880973.37', '471.05'
    tst[194] = datetime.date(2024, 4, 9), 7, 12, '1.00053469', '881444.42', '471.30'
    tst[195] = datetime.date(2024, 4, 10), 7, 13, '1.00053469', '881915.72', '471.55'
    tst[196] = datetime.date(2024, 4, 11), 7, 14, '1.00053469', '882387.27', '471.80'
    tst[197] = datetime.date(2024, 4, 12), 7, 15, '1.00053469', '882859.07', '472.05'
    tst[198] = datetime.date(2024, 4, 13), 7, 16, '1.00053469', '883331.12', '472.31'
    tst[199] = datetime.date(2024, 4, 14), 7, 17, '1.00053469', '883803.43', '472.56'
    tst[200] = datetime.date(2024, 4, 15), 7, 18, '1.00053469', '884275.99', '472.81'
    tst[201] = datetime.date(2024, 4, 16), 7, 19, '1.00053469', '884748.80', '473.06'
    tst[202] = datetime.date(2024, 4, 17), 7, 20, '1.00053469', '885221.87', '473.32'
    tst[203] = datetime.date(2024, 4, 18), 7, 21, '1.00053469', '885695.18', '473.57'
    tst[204] = datetime.date(2024, 4, 19), 7, 22, '1.00053469', '886168.75', '473.82'
    tst[205] = datetime.date(2024, 4, 20), 7, 23, '1.00053469', '886642.58', '474.08'
    tst[206] = datetime.date(2024, 4, 21), 7, 24, '1.00053469', '887116.66', '474.33'
    tst[207] = datetime.date(2024, 4, 22), 7, 25, '1.00053469', '887590.99', '474.58'
    tst[208] = datetime.date(2024, 4, 23), 7, 26, '1.00053469', '888065.57', '474.84'
    tst[209] = datetime.date(2024, 4, 24), 7, 27, '1.00053469', '888540.41', '475.09'
    tst[210] = datetime.date(2024, 4, 25), 7, 28, '1.00053469', '889015.50', '475.35'
    tst[211] = datetime.date(2024, 4, 26), 7, 29, '1.00053469', '889490.85', '475.60'
    tst[212] = datetime.date(2024, 4, 27), 7, 30, '1.00053469', '889966.45', '475.85'
    tst[213] = datetime.date(2024, 4, 28), 7, 31, '1.00053469', '890442.30', '476.11'
    tst[214] = datetime.date(2024, 4, 29), 8, 1, '1.00055252', '890918.41', '301.59'
    tst[215] = datetime.date(2024, 4, 30), 8, 2, '1.00055252', '546146.00', '301.75'
    tst[216] = datetime.date(2024, 5, 1), 8, 3, '1.00055252', '546447.75', '301.92'
    tst[217] = datetime.date(2024, 5, 2), 8, 4, '1.00055252', '546749.67', '302.09'
    tst[218] = datetime.date(2024, 5, 3), 8, 5, '1.00055252', '547051.76', '302.25'
    tst[219] = datetime.date(2024, 5, 4), 8, 6, '1.00055252', '547354.02', '302.42'
    tst[220] = datetime.date(2024, 5, 5), 8, 7, '1.00055252', '547656.44', '302.59'
    tst[221] = datetime.date(2024, 5, 6), 8, 8, '1.00055252', '547959.03', '302.76'
    tst[222] = datetime.date(2024, 5, 7), 8, 9, '1.00055252', '548261.78', '302.92'
    tst[223] = datetime.date(2024, 5, 8), 8, 10, '1.00055252', '548564.71', '303.09'
    tst[224] = datetime.date(2024, 5, 9), 8, 11, '1.00055252', '548867.80', '303.26'
    tst[225] = datetime.date(2024, 5, 10), 8, 12, '1.00055252', '549171.06', '303.43'
    tst[226] = datetime.date(2024, 5, 11), 8, 13, '1.00055252', '549474.48', '303.59'
    tst[227] = datetime.date(2024, 5, 12), 8, 14, '1.00055252', '549778.08', '303.76'
    tst[228] = datetime.date(2024, 5, 13), 8, 15, '1.00055252', '550081.84', '303.93'
    tst[229] = datetime.date(2024, 5, 14), 8, 16, '1.00055252', '550385.77', '304.10'
    tst[230] = datetime.date(2024, 5, 15), 8, 17, '1.00055252', '550689.86', '304.27'
    tst[231] = datetime.date(2024, 5, 16), 8, 18, '1.00055252', '550994.13', '304.43'
    tst[232] = datetime.date(2024, 5, 17), 8, 19, '1.00055252', '551298.56', '304.60'
    tst[233] = datetime.date(2024, 5, 18), 8, 20, '1.00055252', '551603.16', '304.77'
    tst[234] = datetime.date(2024, 5, 19), 8, 21, '1.00055252', '551907.93', '304.94'
    tst[235] = datetime.date(2024, 5, 20), 8, 22, '1.00055252', '552212.87', '305.11'
    tst[236] = datetime.date(2024, 5, 21), 8, 23, '1.00055252', '552517.98', '305.28'
    tst[237] = datetime.date(2024, 5, 22), 8, 24, '1.00055252', '552823.25', '305.44'
    tst[238] = datetime.date(2024, 5, 23), 8, 25, '1.00055252', '553128.70', '305.61'
    tst[239] = datetime.date(2024, 5, 24), 8, 26, '1.00055252', '553434.31', '305.78'
    tst[240] = datetime.date(2024, 5, 25), 8, 27, '1.00055252', '553740.09', '305.95'
    tst[241] = datetime.date(2024, 5, 26), 8, 28, '1.00055252', '554046.04', '306.12'
    tst[242] = datetime.date(2024, 5, 27), 8, 29, '1.00055252', '554352.16', '306.29'
    tst[243] = datetime.date(2024, 5, 28), 8, 30, '1.00055252', '554658.45', '91.80'
    tst[244] = datetime.date(2024, 5, 29), 9, 1, '1.00053469', '166243.25', '88.89'
    tst[245] = datetime.date(2024, 5, 30), 9, 2, '1.00053469', '166332.14', '88.94'
    tst[246] = datetime.date(2024, 5, 31), 9, 3, '1.00053469', '166421.07', '88.98'
    tst[247] = datetime.date(2024, 6, 1), 9, 4, '1.00053469', '166510.06', '89.03'
    tst[248] = datetime.date(2024, 6, 2), 9, 5, '1.00053469', '166599.09', '89.08'
    tst[249] = datetime.date(2024, 6, 3), 9, 6, '1.00053469', '166688.17', '89.13'
    tst[250] = datetime.date(2024, 6, 4), 9, 7, '1.00053469', '166777.29', '89.17'
    tst[251] = datetime.date(2024, 6, 5), 9, 8, '1.00053469', '166866.47', '89.22'
    tst[252] = datetime.date(2024, 6, 6), 9, 9, '1.00053469', '166955.69', '89.27'
    tst[253] = datetime.date(2024, 6, 7), 9, 10, '1.00053469', '167044.96', '89.32'
    tst[254] = datetime.date(2024, 6, 8), 9, 11, '1.00053469', '167134.27', '89.36'
    tst[255] = datetime.date(2024, 6, 9), 9, 12, '1.00053469', '167223.64', '89.41'
    tst[256] = datetime.date(2024, 6, 10), 9, 13, '1.00053469', '167313.05', '89.46'
    tst[257] = datetime.date(2024, 6, 11), 9, 14, '1.00053469', '167402.51', '89.51'
    tst[258] = datetime.date(2024, 6, 12), 9, 15, '1.00053469', '167492.02', '89.56'
    tst[259] = datetime.date(2024, 6, 13), 9, 16, '1.00053469', '167581.58', '89.60'
    tst[260] = datetime.date(2024, 6, 14), 9, 17, '1.00053469', '167671.18', '89.65'
    tst[261] = datetime.date(2024, 6, 15), 9, 18, '1.00053469', '167760.83', '89.70'
    tst[262] = datetime.date(2024, 6, 16), 9, 19, '1.00053469', '167850.53', '89.75'
    tst[263] = datetime.date(2024, 6, 17), 9, 20, '1.00053469', '167940.28', '89.80'
    tst[264] = datetime.date(2024, 6, 18), 9, 21, '1.00053469', '168030.07', '89.84'
    tst[265] = datetime.date(2024, 6, 19), 9, 22, '1.00053469', '168119.92', '89.89'
    tst[266] = datetime.date(2024, 6, 20), 9, 23, '1.00053469', '168209.81', '89.94'
    tst[267] = datetime.date(2024, 6, 21), 9, 24, '1.00053469', '168299.75', '89.99'
    tst[268] = datetime.date(2024, 6, 22), 9, 25, '1.00053469', '168389.74', '90.04'
    tst[269] = datetime.date(2024, 6, 23), 9, 26, '1.00053469', '168479.77', '90.08'
    tst[270] = datetime.date(2024, 6, 24), 9, 27, '1.00053469', '168569.86', '90.13'
    tst[271] = datetime.date(2024, 6, 25), 9, 28, '1.00053469', '168659.99', '90.18'
    tst[272] = datetime.date(2024, 6, 26), 9, 29, '1.00053469', '168750.17', '90.23'
    tst[273] = datetime.date(2024, 6, 27), 9, 30, '1.00053469', '168840.40', '90.28'
    tst[274] = datetime.date(2024, 6, 28), 9, 31, '1.00053469', '168930.68', '0.00'

    for i, entry in enumerate(fincore.get_livre_daily_returns(**kwa), 1):
        assert entry.date == tst[i][0]
        assert entry.period == tst[i][1]
        assert entry.no == tst[i][2]

        # Fator fixo, saldo, valor do rendimento.
        assert math.isclose(entry.sf, decimal.Decimal(tst[i][3]), rel_tol=1e-8)
        assert bal == decimal.Decimal(tst[i][4])
        assert entry.value == decimal.Decimal(tst[i][5])

        # Memoriza o saldo para a próxima iteração.
        bal = entry.bal

@pytest.mark.skip(reason='Not implemented yet.')
def test_will_create_loan_daily_returns_livre_5():
    '''
    Operação LIVRE CDI 2.

    Múltiplos pagamentos em fins de semana.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: LIVRE - CDI 2
    '''

    pass  # FIXME: implementar. Já está em planilha de testes.

def test_will_create_loan_daily_returns_livre_6():
    '''
    Operação ASAD Energia.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: ASAD Energia
    '''

    pla = functools.partial(fincore.PriceLevelAdjustment, 'IPCA', base_date=datetime.date(2021, 7, 1), shift='AUTO')
    kwa = {}
    tst = {}

    kwa['principal'] = decimal.Decimal('145000')
    kwa['apy'] = decimal.Decimal('10')
    kwa['vir'] = fincore.VariableIndex(code='IPCA', backend=_RicherIpcaBackend())
    kwa['amortizations'] = []

    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 4, 5), amortizes_interest=False))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 5, 5), amortization_ratio=decimal.Decimal('0.0130614411')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 6, 5), amortization_ratio=decimal.Decimal('0.0131655949')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 7, 5), amortization_ratio=decimal.Decimal('0.0132705792')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 8, 5), amortization_ratio=decimal.Decimal('0.0133764006')))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 9, 5), amortization_ratio=decimal.Decimal('0.0134830659'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 10, 5), amortization_ratio=decimal.Decimal('0.0135905818'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 11, 5), amortization_ratio=decimal.Decimal('0.0136989550'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2022, 12, 5), amortization_ratio=decimal.Decimal('0.0138081924'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 1, 5), amortization_ratio=decimal.Decimal('0.0139183008'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 2, 5), amortization_ratio=decimal.Decimal('0.0140292873'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 3, 5), amortization_ratio=decimal.Decimal('0.0141411588'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 4, 5), amortization_ratio=decimal.Decimal('0.0142539224'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 5, 5), amortization_ratio=decimal.Decimal('0.0143675852'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 6, 5), amortization_ratio=decimal.Decimal('0.0144821543'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 7, 5), amortization_ratio=decimal.Decimal('0.0145976371'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 8, 5), amortization_ratio=decimal.Decimal('0.0147140407'), price_level_adjustment=pla(period=12)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 9, 5), amortization_ratio=decimal.Decimal('0.0148313725'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 10, 5), amortization_ratio=decimal.Decimal('0.0149496400'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 11, 5), amortization_ratio=decimal.Decimal('0.0150688505'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2023, 12, 5), amortization_ratio=decimal.Decimal('0.0151890116'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 1, 5), amortization_ratio=decimal.Decimal('0.0153101309'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 2, 5), amortization_ratio=decimal.Decimal('0.0154322161'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 3, 5), amortization_ratio=decimal.Decimal('0.0155552747'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 4, 5), amortization_ratio=decimal.Decimal('0.0156793147'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 5, 5), amortization_ratio=decimal.Decimal('0.0158043437'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 6, 5), amortization_ratio=decimal.Decimal('0.0159303698'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 7, 5), amortization_ratio=decimal.Decimal('0.0160574008'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 8, 5), amortization_ratio=decimal.Decimal('0.0161854448'), price_level_adjustment=pla(period=24)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 9, 5), amortization_ratio=decimal.Decimal('0.0163145098'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 10, 5), amortization_ratio=decimal.Decimal('0.0164446040'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 11, 5), amortization_ratio=decimal.Decimal('0.0165757355'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2024, 12, 5), amortization_ratio=decimal.Decimal('0.0167079128'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 1, 5), amortization_ratio=decimal.Decimal('0.0168411440'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 2, 5), amortization_ratio=decimal.Decimal('0.0169754377'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 3, 5), amortization_ratio=decimal.Decimal('0.0171108022'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 4, 5), amortization_ratio=decimal.Decimal('0.0172472461'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 5, 5), amortization_ratio=decimal.Decimal('0.0173847781'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 6, 5), amortization_ratio=decimal.Decimal('0.0175234068'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 7, 5), amortization_ratio=decimal.Decimal('0.0176631409'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 8, 5), amortization_ratio=decimal.Decimal('0.0178039892'), price_level_adjustment=pla(period=36)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 9, 5), amortization_ratio=decimal.Decimal('0.0179459608'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 10, 5), amortization_ratio=decimal.Decimal('0.0180890644'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 11, 5), amortization_ratio=decimal.Decimal('0.0182333091'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2025, 12, 5), amortization_ratio=decimal.Decimal('0.0183787041'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 1, 5), amortization_ratio=decimal.Decimal('0.0185252584'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 2, 5), amortization_ratio=decimal.Decimal('0.0186729814'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 3, 5), amortization_ratio=decimal.Decimal('0.0188218824'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 4, 5), amortization_ratio=decimal.Decimal('0.0189719708'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 5, 5), amortization_ratio=decimal.Decimal('0.0191232559'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 6, 5), amortization_ratio=decimal.Decimal('0.0192757474'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 7, 5), amortization_ratio=decimal.Decimal('0.0194294550'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 8, 5), amortization_ratio=decimal.Decimal('0.0195843882'), price_level_adjustment=pla(period=48)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 9, 5), amortization_ratio=decimal.Decimal('0.0197405568'), price_level_adjustment=pla(period=60)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 10, 5), amortization_ratio=decimal.Decimal('0.0198979708'), price_level_adjustment=pla(period=60)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 11, 5), amortization_ratio=decimal.Decimal('0.0200566400'), price_level_adjustment=pla(period=60)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2026, 12, 5), amortization_ratio=decimal.Decimal('0.0202165745'), price_level_adjustment=pla(period=60)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2027, 1, 5), amortization_ratio=decimal.Decimal('0.0203777843'), price_level_adjustment=pla(period=60)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2027, 2, 5), amortization_ratio=decimal.Decimal('0.0205402796'), price_level_adjustment=pla(period=60)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2027, 3, 5), amortization_ratio=decimal.Decimal('0.0207040707'), price_level_adjustment=pla(period=60)))
    kwa['amortizations'].append(fincore.Amortization(date=datetime.date(2027, 4, 5), amortization_ratio=decimal.Decimal('0.0208691707'), price_level_adjustment=pla(period=60)))

    tst[1] = datetime.date(2022, 4, 5), 1, 1, '0.000264786', '0', '38.39', '145038.39'
    tst[2] = datetime.date(2022, 4, 6), 1, 2, '0.000264786', '0', '38.40', '145076.80'
    tst[3] = datetime.date(2022, 4, 7), 1, 3, '0.000264786', '0', '38.41', '145115.21'
    tst[4] = datetime.date(2022, 4, 8), 1, 4, '0.000264786', '0', '38.42', '145153.64'
    tst[5] = datetime.date(2022, 4, 9), 1, 5, '0.000264786', '0', '38.43', '145192.07'
    tst[6] = datetime.date(2022, 4, 10), 1, 6, '0.000264786', '0', '38.44', '145230.52'
    tst[7] = datetime.date(2022, 4, 11), 1, 7, '0.000264786', '0', '38.45', '145268.97'
    tst[8] = datetime.date(2022, 4, 12), 1, 8, '0.000264786', '0', '38.47', '145307.44'
    tst[9] = datetime.date(2022, 4, 13), 1, 9, '0.000264786', '0', '38.48', '145345.91'
    tst[10] = datetime.date(2022, 4, 14), 1, 10, '0.000264786', '0', '38.49', '145384.40'
    tst[11] = datetime.date(2022, 4, 15), 1, 11, '0.000264786', '0', '38.50', '145422.89'
    tst[12] = datetime.date(2022, 4, 16), 1, 12, '0.000264786', '0', '38.51', '145461.40'
    tst[13] = datetime.date(2022, 4, 17), 1, 13, '0.000264786', '0', '38.52', '145499.91'
    tst[14] = datetime.date(2022, 4, 18), 1, 14, '0.000264786', '0', '38.53', '145538.44'
    tst[15] = datetime.date(2022, 4, 19), 1, 15, '0.000264786', '0', '38.54', '145576.98'
    tst[16] = datetime.date(2022, 4, 20), 1, 16, '0.000264786', '0', '38.55', '145615.52'
    tst[17] = datetime.date(2022, 4, 21), 1, 17, '0.000264786', '0', '38.56', '145654.08'
    tst[18] = datetime.date(2022, 4, 22), 1, 18, '0.000264786', '0', '38.57', '145692.65'
    tst[19] = datetime.date(2022, 4, 23), 1, 19, '0.000264786', '0', '38.58', '145731.23'
    tst[20] = datetime.date(2022, 4, 24), 1, 20, '0.000264786', '0', '38.59', '145769.81'
    tst[21] = datetime.date(2022, 4, 25), 1, 21, '0.000264786', '0', '38.60', '145808.41'
    tst[22] = datetime.date(2022, 4, 26), 1, 22, '0.000264786', '0', '38.61', '145847.02'
    tst[23] = datetime.date(2022, 4, 27), 1, 23, '0.000264786', '0', '38.62', '145885.64'
    tst[24] = datetime.date(2022, 4, 28), 1, 24, '0.000264786', '0', '38.63', '145924.27'
    tst[25] = datetime.date(2022, 4, 29), 1, 25, '0.000264786', '0', '38.64', '145962.90'
    tst[26] = datetime.date(2022, 4, 30), 1, 26, '0.000264786', '0', '38.65', '146001.55'
    tst[27] = datetime.date(2022, 5, 1), 1, 27, '0.000264786', '0', '38.66', '146040.21'
    tst[28] = datetime.date(2022, 5, 2), 1, 28, '0.000264786', '0', '38.67', '146078.88'
    tst[29] = datetime.date(2022, 5, 3), 1, 29, '0.000264786', '0', '38.68', '146117.56'
    tst[30] = datetime.date(2022, 5, 4), 1, 30, '0.000264786', '0', '38.69', '146156.25'
    tst[31] = datetime.date(2022, 5, 5), 2, 1, '0.000256243', '0', '36.67', '143142.76'
    tst[32] = datetime.date(2022, 5, 6), 2, 2, '0.000256243', '0', '36.68', '143179.44'
    tst[33] = datetime.date(2022, 5, 7), 2, 3, '0.000256243', '0', '36.69', '143216.13'
    tst[34] = datetime.date(2022, 5, 8), 2, 4, '0.000256243', '0', '36.70', '143252.83'
    tst[35] = datetime.date(2022, 5, 9), 2, 5, '0.000256243', '0', '36.71', '143289.53'
    tst[36] = datetime.date(2022, 5, 10), 2, 6, '0.000256243', '0', '36.72', '143326.25'
    tst[37] = datetime.date(2022, 5, 11), 2, 7, '0.000256243', '0', '36.73', '143362.98'
    tst[38] = datetime.date(2022, 5, 12), 2, 8, '0.000256243', '0', '36.74', '143399.71'
    tst[39] = datetime.date(2022, 5, 13), 2, 9, '0.000256243', '0', '36.75', '143436.46'
    tst[40] = datetime.date(2022, 5, 14), 2, 10, '0.000256243', '0', '36.75', '143473.21'
    tst[41] = datetime.date(2022, 5, 15), 2, 11, '0.000256243', '0', '36.76', '143509.98'
    tst[42] = datetime.date(2022, 5, 16), 2, 12, '0.000256243', '0', '36.77', '143546.75'
    tst[43] = datetime.date(2022, 5, 17), 2, 13, '0.000256243', '0', '36.78', '143583.53'
    tst[44] = datetime.date(2022, 5, 18), 2, 14, '0.000256243', '0', '36.79', '143620.33'
    tst[45] = datetime.date(2022, 5, 19), 2, 15, '0.000256243', '0', '36.80', '143657.13'
    tst[46] = datetime.date(2022, 5, 20), 2, 16, '0.000256243', '0', '36.81', '143693.94'
    tst[47] = datetime.date(2022, 5, 21), 2, 17, '0.000256243', '0', '36.82', '143730.76'
    tst[48] = datetime.date(2022, 5, 22), 2, 18, '0.000256243', '0', '36.83', '143767.59'
    tst[49] = datetime.date(2022, 5, 23), 2, 19, '0.000256243', '0', '36.84', '143804.43'
    tst[50] = datetime.date(2022, 5, 24), 2, 20, '0.000256243', '0', '36.85', '143841.28'
    tst[51] = datetime.date(2022, 5, 25), 2, 21, '0.000256243', '0', '36.86', '143878.14'
    tst[52] = datetime.date(2022, 5, 26), 2, 22, '0.000256243', '0', '36.87', '143915.00'
    tst[53] = datetime.date(2022, 5, 27), 2, 23, '0.000256243', '0', '36.88', '143951.88'
    tst[54] = datetime.date(2022, 5, 28), 2, 24, '0.000256243', '0', '36.89', '143988.77'
    tst[55] = datetime.date(2022, 5, 29), 2, 25, '0.000256243', '0', '36.90', '144025.66'
    tst[56] = datetime.date(2022, 5, 30), 2, 26, '0.000256243', '0', '36.91', '144062.57'
    tst[57] = datetime.date(2022, 5, 31), 2, 27, '0.000256243', '0', '36.92', '144099.48'
    tst[58] = datetime.date(2022, 6, 1), 2, 28, '0.000256243', '0', '36.92', '144136.41'
    tst[59] = datetime.date(2022, 6, 2), 2, 29, '0.000256243', '0', '36.93', '144173.34'
    tst[60] = datetime.date(2022, 6, 3), 2, 30, '0.000256243', '0', '36.94', '144210.29'
    tst[61] = datetime.date(2022, 6, 4), 2, 31, '0.000256243', '0', '36.95', '144247.24'
    tst[62] = datetime.date(2022, 6, 5), 3, 1, '0.000264786', '0', '37.39', '141234.47'
    tst[63] = datetime.date(2022, 6, 6), 3, 2, '0.000264786', '0', '37.40', '141271.86'
    tst[64] = datetime.date(2022, 6, 7), 3, 3, '0.000264786', '0', '37.41', '141309.27'
    tst[65] = datetime.date(2022, 6, 8), 3, 4, '0.000264786', '0', '37.42', '141346.69'
    tst[66] = datetime.date(2022, 6, 9), 3, 5, '0.000264786', '0', '37.43', '141384.11'
    tst[67] = datetime.date(2022, 6, 10), 3, 6, '0.000264786', '0', '37.44', '141421.55'
    tst[68] = datetime.date(2022, 6, 11), 3, 7, '0.000264786', '0', '37.45', '141459.00'
    tst[69] = datetime.date(2022, 6, 12), 3, 8, '0.000264786', '0', '37.46', '141496.45'
    tst[70] = datetime.date(2022, 6, 13), 3, 9, '0.000264786', '0', '37.47', '141533.92'
    tst[71] = datetime.date(2022, 6, 14), 3, 10, '0.000264786', '0', '37.48', '141571.40'
    tst[72] = datetime.date(2022, 6, 15), 3, 11, '0.000264786', '0', '37.49', '141608.88'
    tst[73] = datetime.date(2022, 6, 16), 3, 12, '0.000264786', '0', '37.50', '141646.38'
    tst[74] = datetime.date(2022, 6, 17), 3, 13, '0.000264786', '0', '37.51', '141683.88'
    tst[75] = datetime.date(2022, 6, 18), 3, 14, '0.000264786', '0', '37.52', '141721.40'
    tst[76] = datetime.date(2022, 6, 19), 3, 15, '0.000264786', '0', '37.53', '141758.92'
    tst[77] = datetime.date(2022, 6, 20), 3, 16, '0.000264786', '0', '37.54', '141796.46'
    tst[78] = datetime.date(2022, 6, 21), 3, 17, '0.000264786', '0', '37.55', '141834.01'
    tst[79] = datetime.date(2022, 6, 22), 3, 18, '0.000264786', '0', '37.56', '141871.56'
    tst[80] = datetime.date(2022, 6, 23), 3, 19, '0.000264786', '0', '37.57', '141909.13'
    tst[81] = datetime.date(2022, 6, 24), 3, 20, '0.000264786', '0', '37.58', '141946.70'
    tst[82] = datetime.date(2022, 6, 25), 3, 21, '0.000264786', '0', '37.59', '141984.29'
    tst[83] = datetime.date(2022, 6, 26), 3, 22, '0.000264786', '0', '37.60', '142021.88'
    tst[84] = datetime.date(2022, 6, 27), 3, 23, '0.000264786', '0', '37.61', '142059.49'
    tst[85] = datetime.date(2022, 6, 28), 3, 24, '0.000264786', '0', '37.62', '142097.10'
    tst[86] = datetime.date(2022, 6, 29), 3, 25, '0.000264786', '0', '37.63', '142134.73'
    tst[87] = datetime.date(2022, 6, 30), 3, 26, '0.000264786', '0', '37.64', '142172.36'
    tst[88] = datetime.date(2022, 7, 1), 3, 27, '0.000264786', '0', '37.65', '142210.01'
    tst[89] = datetime.date(2022, 7, 2), 3, 28, '0.000264786', '0', '37.66', '142247.66'
    tst[90] = datetime.date(2022, 7, 3), 3, 29, '0.000264786', '0', '37.67', '142285.33'
    tst[91] = datetime.date(2022, 7, 4), 3, 30, '0.000264786', '0', '37.68', '142323.01'
    tst[92] = datetime.date(2022, 7, 5), 4, 1, '0.000256243', '0', '35.69', '139308.53'
    tst[93] = datetime.date(2022, 7, 6), 4, 2, '0.000256243', '0', '35.70', '139344.23'
    tst[94] = datetime.date(2022, 7, 7), 4, 3, '0.000256243', '0', '35.71', '139379.94'
    tst[95] = datetime.date(2022, 7, 8), 4, 4, '0.000256243', '0', '35.72', '139415.65'
    tst[96] = datetime.date(2022, 7, 9), 4, 5, '0.000256243', '0', '35.72', '139451.38'
    tst[97] = datetime.date(2022, 7, 10), 4, 6, '0.000256243', '0', '35.73', '139487.11'
    tst[98] = datetime.date(2022, 7, 11), 4, 7, '0.000256243', '0', '35.74', '139522.85'
    tst[99] = datetime.date(2022, 7, 12), 4, 8, '0.000256243', '0', '35.75', '139558.60'
    tst[100] = datetime.date(2022, 7, 13), 4, 9, '0.000256243', '0', '35.76', '139594.36'
    tst[101] = datetime.date(2022, 7, 14), 4, 10, '0.000256243', '0', '35.77', '139630.13'
    tst[102] = datetime.date(2022, 7, 15), 4, 11, '0.000256243', '0', '35.78', '139665.91'
    tst[103] = datetime.date(2022, 7, 16), 4, 12, '0.000256243', '0', '35.79', '139701.70'
    tst[104] = datetime.date(2022, 7, 17), 4, 13, '0.000256243', '0', '35.80', '139737.50'
    tst[105] = datetime.date(2022, 7, 18), 4, 14, '0.000256243', '0', '35.81', '139773.31'
    tst[106] = datetime.date(2022, 7, 19), 4, 15, '0.000256243', '0', '35.82', '139809.12'
    tst[107] = datetime.date(2022, 7, 20), 4, 16, '0.000256243', '0', '35.83', '139844.95'
    tst[108] = datetime.date(2022, 7, 21), 4, 17, '0.000256243', '0', '35.83', '139880.78'
    tst[109] = datetime.date(2022, 7, 22), 4, 18, '0.000256243', '0', '35.84', '139916.63'
    tst[110] = datetime.date(2022, 7, 23), 4, 19, '0.000256243', '0', '35.85', '139952.48'
    tst[111] = datetime.date(2022, 7, 24), 4, 20, '0.000256243', '0', '35.86', '139988.34'
    tst[112] = datetime.date(2022, 7, 25), 4, 21, '0.000256243', '0', '35.87', '140024.21'
    tst[113] = datetime.date(2022, 7, 26), 4, 22, '0.000256243', '0', '35.88', '140060.09'
    tst[114] = datetime.date(2022, 7, 27), 4, 23, '0.000256243', '0', '35.89', '140095.98'
    tst[115] = datetime.date(2022, 7, 28), 4, 24, '0.000256243', '0', '35.90', '140131.88'
    tst[116] = datetime.date(2022, 7, 29), 4, 25, '0.000256243', '0', '35.91', '140167.79'
    tst[117] = datetime.date(2022, 7, 30), 4, 26, '0.000256243', '0', '35.92', '140203.70'
    tst[118] = datetime.date(2022, 7, 31), 4, 27, '0.000256243', '0', '35.93', '140239.63'
    tst[119] = datetime.date(2022, 8, 1), 4, 28, '0.000256243', '0', '35.94', '140275.57'
    tst[120] = datetime.date(2022, 8, 2), 4, 29, '0.000256243', '0', '35.94', '140311.51'
    tst[121] = datetime.date(2022, 8, 3), 4, 30, '0.000256243', '0', '35.95', '140347.46'
    tst[122] = datetime.date(2022, 8, 4), 4, 31, '0.000256243', '0', '35.96', '140383.43'
    tst[123] = datetime.date(2022, 8, 5), 5, 1, '0.000256243', '0.003629695', '35.32', '137867.06'
    tst[124] = datetime.date(2022, 8, 6), 5, 2, '0.000256243', '0.003629695', '35.58', '138402.94'
    tst[125] = datetime.date(2022, 8, 7), 5, 3, '0.000256243', '0.003629695', '35.85', '138940.89'
    tst[126] = datetime.date(2022, 8, 8), 5, 4, '0.000256243', '0.003629695', '36.12', '139480.93'
    tst[127] = datetime.date(2022, 8, 9), 5, 5, '0.000256243', '0.003629695', '36.39', '140023.08'
    tst[128] = datetime.date(2022, 8, 10), 5, 6, '0.000256243', '0.003629695', '36.66', '140567.33'
    tst[129] = datetime.date(2022, 8, 11), 5, 7, '0.000256243', '0.003629695', '36.93', '141113.70'
    tst[130] = datetime.date(2022, 8, 12), 5, 8, '0.000256243', '0.003629695', '37.21', '141662.19'
    tst[131] = datetime.date(2022, 8, 13), 5, 9, '0.000256243', '0.003629695', '37.48', '142212.81'
    tst[132] = datetime.date(2022, 8, 14), 5, 10, '0.000256243', '0.003629695', '37.76', '142765.57'
    tst[133] = datetime.date(2022, 8, 15), 5, 11, '0.000256243', '0.003629695', '38.04', '143320.48'
    tst[134] = datetime.date(2022, 8, 16), 5, 12, '0.000256243', '0.003629695', '38.32', '143877.55'
    tst[135] = datetime.date(2022, 8, 17), 5, 13, '0.000256243', '0.003629695', '38.60', '144436.78'
    tst[136] = datetime.date(2022, 8, 18), 5, 14, '0.000256243', '0.003629695', '38.89', '144998.19'
    tst[137] = datetime.date(2022, 8, 19), 5, 15, '0.000256243', '0.003629695', '39.17', '145561.78'
    tst[138] = datetime.date(2022, 8, 20), 5, 16, '0.000256243', '0.003629695', '39.46', '146127.56'
    tst[139] = datetime.date(2022, 8, 21), 5, 17, '0.000256243', '0.003629695', '39.75', '146695.54'
    tst[140] = datetime.date(2022, 8, 22), 5, 18, '0.000256243', '0.003629695', '40.04', '147265.72'
    tst[141] = datetime.date(2022, 8, 23), 5, 19, '0.000256243', '0.003629695', '40.33', '147838.12'
    tst[142] = datetime.date(2022, 8, 24), 5, 20, '0.000256243', '0.003629695', '40.63', '148412.75'
    tst[143] = datetime.date(2022, 8, 25), 5, 21, '0.000256243', '0.003629695', '40.92', '148989.61'
    tst[144] = datetime.date(2022, 8, 26), 5, 22, '0.000256243', '0.003629695', '41.22', '149568.72'
    tst[145] = datetime.date(2022, 8, 27), 5, 23, '0.000256243', '0.003629695', '41.52', '150150.07'
    tst[146] = datetime.date(2022, 8, 28), 5, 24, '0.000256243', '0.003629695', '41.82', '150733.68'
    tst[147] = datetime.date(2022, 8, 29), 5, 25, '0.000256243', '0.003629695', '42.12', '151319.57'
    tst[148] = datetime.date(2022, 8, 30), 5, 26, '0.000256243', '0.003629695', '42.42', '151907.72'
    tst[149] = datetime.date(2022, 8, 31), 5, 27, '0.000256243', '0.003629695', '42.73', '152498.17'
    tst[150] = datetime.date(2022, 9, 1), 5, 28, '0.000256243', '0.003629695', '43.03', '153090.91'
    tst[151] = datetime.date(2022, 9, 2), 5, 29, '0.000256243', '0.003629695', '43.34', '153685.95'
    tst[152] = datetime.date(2022, 9, 3), 5, 30, '0.000256243', '0.003629695', '43.65', '154283.31'
    tst[153] = datetime.date(2022, 9, 4), 5, 31, '0.000256243', '0.003629695', '43.97', '154882.99'
    tst[154] = datetime.date(2022, 9, 5), 6, 1, '0.000264786', '0.003750911', '35.98', '135922.00'
    tst[155] = datetime.date(2022, 9, 6), 6, 2, '0.000264786', '0.003750911', '36.26', '136467.95'
    tst[156] = datetime.date(2022, 9, 7), 6, 3, '0.000264786', '0.003750911', '36.54', '137016.10'
    tst[157] = datetime.date(2022, 9, 8), 6, 4, '0.000264786', '0.003750911', '36.82', '137566.45'
    tst[158] = datetime.date(2022, 9, 9), 6, 5, '0.000264786', '0.003750911', '37.11', '138119.01'
    tst[159] = datetime.date(2022, 9, 10), 6, 6, '0.000264786', '0.003750911', '37.39', '138673.80'
    tst[160] = datetime.date(2022, 9, 11), 6, 7, '0.000264786', '0.003750911', '37.68', '139230.81'
    tst[161] = datetime.date(2022, 9, 12), 6, 8, '0.000264786', '0.003750911', '37.97', '139790.05'
    tst[162] = datetime.date(2022, 9, 13), 6, 9, '0.000264786', '0.003750911', '38.26', '140351.55'
    tst[163] = datetime.date(2022, 9, 14), 6, 10, '0.000264786', '0.003750911', '38.56', '140915.29'
    tst[164] = datetime.date(2022, 9, 15), 6, 11, '0.000264786', '0.003750911', '38.85', '141481.31'
    tst[165] = datetime.date(2022, 9, 16), 6, 12, '0.000264786', '0.003750911', '39.15', '142049.59'
    tst[166] = datetime.date(2022, 9, 17), 6, 13, '0.000264786', '0.003750911', '39.44', '142620.16'
    tst[167] = datetime.date(2022, 9, 18), 6, 14, '0.000264786', '0.003750911', '39.74', '143193.02'
    tst[168] = datetime.date(2022, 9, 19), 6, 15, '0.000264786', '0.003750911', '40.04', '143768.19'
    tst[169] = datetime.date(2022, 9, 20), 6, 16, '0.000264786', '0.003750911', '40.35', '144345.66'
    tst[170] = datetime.date(2022, 9, 21), 6, 17, '0.000264786', '0.003750911', '40.65', '144925.45'
    tst[171] = datetime.date(2022, 9, 22), 6, 18, '0.000264786', '0.003750911', '40.96', '145507.57'
    tst[172] = datetime.date(2022, 9, 23), 6, 19, '0.000264786', '0.003750911', '41.27', '146092.03'
    tst[173] = datetime.date(2022, 9, 24), 6, 20, '0.000264786', '0.003750911', '41.58', '146678.84'
    tst[174] = datetime.date(2022, 9, 25), 6, 21, '0.000264786', '0.003750911', '41.89', '147268.00'
    tst[175] = datetime.date(2022, 9, 26), 6, 22, '0.000264786', '0.003750911', '42.20', '147859.53'
    tst[176] = datetime.date(2022, 9, 27), 6, 23, '0.000264786', '0.003750911', '42.52', '148453.44'
    tst[177] = datetime.date(2022, 9, 28), 6, 24, '0.000264786', '0.003750911', '42.84', '149049.73'
    tst[178] = datetime.date(2022, 9, 29), 6, 25, '0.000264786', '0.003750911', '43.16', '149648.41'
    tst[179] = datetime.date(2022, 9, 30), 6, 26, '0.000264786', '0.003750911', '43.48', '150249.51'
    tst[180] = datetime.date(2022, 10, 1), 6, 27, '0.000264786', '0.003750911', '43.80', '150853.01'
    tst[181] = datetime.date(2022, 10, 2), 6, 28, '0.000264786', '0.003750911', '44.12', '151458.94'
    tst[182] = datetime.date(2022, 10, 3), 6, 29, '0.000264786', '0.003750911', '44.45', '152067.30'
    tst[183] = datetime.date(2022, 10, 4), 6, 30, '0.000264786', '0.003750911', '44.78', '152678.11'
    tst[184] = datetime.date(2022, 10, 5), 7, 1, '0.000256243', '0.003629695', '34.31', '133926.13'
    tst[185] = datetime.date(2022, 10, 6), 7, 2, '0.000256243', '0.003629695', '34.57', '134446.68'
    tst[186] = datetime.date(2022, 10, 7), 7, 3, '0.000256243', '0.003629695', '34.83', '134969.26'
    tst[187] = datetime.date(2022, 10, 8), 7, 4, '0.000256243', '0.003629695', '35.09', '135493.86'
    tst[188] = datetime.date(2022, 10, 9), 7, 5, '0.000256243', '0.003629695', '35.35', '136020.51'
    tst[189] = datetime.date(2022, 10, 10), 7, 6, '0.000256243', '0.003629695', '35.61', '136549.20'
    tst[190] = datetime.date(2022, 10, 11), 7, 7, '0.000256243', '0.003629695', '35.88', '137079.95'
    tst[191] = datetime.date(2022, 10, 12), 7, 8, '0.000256243', '0.003629695', '36.14', '137612.76'
    tst[192] = datetime.date(2022, 10, 13), 7, 9, '0.000256243', '0.003629695', '36.41', '138147.65'
    tst[193] = datetime.date(2022, 10, 14), 7, 10, '0.000256243', '0.003629695', '36.68', '138684.61'
    tst[194] = datetime.date(2022, 10, 15), 7, 11, '0.000256243', '0.003629695', '36.95', '139223.66'
    tst[195] = datetime.date(2022, 10, 16), 7, 12, '0.000256243', '0.003629695', '37.23', '139764.80'
    tst[196] = datetime.date(2022, 10, 17), 7, 13, '0.000256243', '0.003629695', '37.50', '140308.05'
    tst[197] = datetime.date(2022, 10, 18), 7, 14, '0.000256243', '0.003629695', '37.78', '140853.41'
    tst[198] = datetime.date(2022, 10, 19), 7, 15, '0.000256243', '0.003629695', '38.05', '141400.89'
    tst[199] = datetime.date(2022, 10, 20), 7, 16, '0.000256243', '0.003629695', '38.33', '141950.49'
    tst[200] = datetime.date(2022, 10, 21), 7, 17, '0.000256243', '0.003629695', '38.61', '142502.24'
    tst[201] = datetime.date(2022, 10, 22), 7, 18, '0.000256243', '0.003629695', '38.90', '143056.12'
    tst[202] = datetime.date(2022, 10, 23), 7, 19, '0.000256243', '0.003629695', '39.18', '143612.16'
    tst[203] = datetime.date(2022, 10, 24), 7, 20, '0.000256243', '0.003629695', '39.46', '144170.37'
    tst[204] = datetime.date(2022, 10, 25), 7, 21, '0.000256243', '0.003629695', '39.75', '144730.74'
    tst[205] = datetime.date(2022, 10, 26), 7, 22, '0.000256243', '0.003629695', '40.04', '145293.29'
    tst[206] = datetime.date(2022, 10, 27), 7, 23, '0.000256243', '0.003629695', '40.33', '145858.02'
    tst[207] = datetime.date(2022, 10, 28), 7, 24, '0.000256243', '0.003629695', '40.62', '146424.95'
    tst[208] = datetime.date(2022, 10, 29), 7, 25, '0.000256243', '0.003629695', '40.91', '146994.09'
    tst[209] = datetime.date(2022, 10, 30), 7, 26, '0.000256243', '0.003629695', '41.21', '147565.43'
    tst[210] = datetime.date(2022, 10, 31), 7, 27, '0.000256243', '0.003629695', '41.51', '148139.00'
    tst[211] = datetime.date(2022, 11, 1), 7, 28, '0.000256243', '0.003629695', '41.80', '148714.80'
    tst[212] = datetime.date(2022, 11, 2), 7, 29, '0.000256243', '0.003629695', '42.10', '149292.83'
    tst[213] = datetime.date(2022, 11, 3), 7, 30, '0.000256243', '0.003629695', '42.41', '149873.11'
    tst[214] = datetime.date(2022, 11, 4), 7, 31, '0.000256243', '0.003629695', '42.71', '150455.65'

    for i, entry in enumerate(fincore.get_livre_daily_returns(**kwa), 1):
        entry = t.cast(fincore.PriceAdjustedDailyReturn, entry)

        if i < 215:
            assert entry.date == tst[i][0]
            assert entry.period == tst[i][1]
            assert entry.no == tst[i][2]
            assert math.isclose(entry.sf, decimal.Decimal(tst[i][3]) + _1, rel_tol=1e-8)
            assert math.isclose(entry.cf, decimal.Decimal(tst[i][4]) + _1, rel_tol=1e-8)
            assert entry.value == decimal.Decimal(tst[i][5])
            assert entry.bal == decimal.Decimal(tst[i][6])

def test_will_create_loan_daily_returns_jm_1():
    '''
    Operação CRI - Max Tulum (Isento de IR).

    Juros mensais IPCA.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Max Tulum
    '''

    kwa = {}
    tst = {}

    kwa['principal'] = decimal.Decimal('11_000_000')
    kwa['apy'] = decimal.Decimal('10.84')
    kwa['zero_date'] = datetime.date(2024, 10, 30)
    kwa['term'] = 39
    kwa['anniversary_date'] = datetime.date(2024, 12, 7)
    kwa['vir'] = fincore.VariableIndex('IPCA', backend=_RicherIpcaBackend())

    # Período 1 – data, fator de spread, fator de correção, correção, juros, saldo.
    tst[1] = 1, 1, datetime.date(2024, 10, 30), '1.00027670', '1.00018016', '1981.73', '3044.23', '11005025.96'
    tst[2] = 1, 2, datetime.date(2024, 10, 31), '1.00027670', '1.00018016', '1982.09', '3046.17', '11010054.22'
    tst[3] = 1, 3, datetime.date(2024, 11, 1), '1.00027670', '1.00018016', '1982.45', '3048.11', '11015084.78'
    tst[4] = 1, 4, datetime.date(2024, 11, 2), '1.00027670', '1.00018016', '1982.80', '3050.05', '11020117.63'
    tst[5] = 1, 5, datetime.date(2024, 11, 3), '1.00027670', '1.00018016', '1983.16', '3051.99', '11025152.78'
    tst[6] = 1, 6, datetime.date(2024, 11, 4), '1.00027670', '1.00018016', '1983.52', '3053.94', '11030190.24'
    tst[7] = 1, 7, datetime.date(2024, 11, 5), '1.00027670', '1.00018016', '1983.88', '3055.88', '11035229.99'
    tst[8] = 1, 8, datetime.date(2024, 11, 6), '1.00027670', '1.00018016', '1984.23', '3057.83', '11040272.05'
    tst[9] = 1, 9, datetime.date(2024, 11, 7), '1.00027670', '1.00018016', '1984.59', '3059.77', '11045316.41'
    tst[10] = 1, 10, datetime.date(2024, 11, 8), '1.00027670', '1.00018016', '1984.95', '3061.72', '11050363.08'
    tst[11] = 1, 11, datetime.date(2024, 11, 9), '1.00027670', '1.00018016', '1985.31', '3063.67', '11055412.06'
    tst[12] = 1, 12, datetime.date(2024, 11, 10), '1.00027670', '1.00018016', '1985.66', '3065.62', '11060463.33'
    tst[13] = 1, 13, datetime.date(2024, 11, 11), '1.00027670', '1.00018016', '1986.02', '3067.57', '11065516.92'
    tst[14] = 1, 14, datetime.date(2024, 11, 12), '1.00027670', '1.00018016', '1986.38', '3069.52', '11070572.82'
    tst[15] = 1, 15, datetime.date(2024, 11, 13), '1.00027670', '1.00018016', '1986.74', '3071.47', '11075631.03'
    tst[16] = 1, 16, datetime.date(2024, 11, 14), '1.00027670', '1.00018016', '1987.09', '3073.42', '11080691.54'
    tst[17] = 1, 17, datetime.date(2024, 11, 15), '1.00027670', '1.00018016', '1987.45', '3075.38', '11085754.38'
    tst[18] = 1, 18, datetime.date(2024, 11, 16), '1.00027670', '1.00018016', '1987.81', '3077.33', '11090819.52'
    tst[19] = 1, 19, datetime.date(2024, 11, 17), '1.00027670', '1.00018016', '1988.17', '3079.29', '11095886.98'
    tst[20] = 1, 20, datetime.date(2024, 11, 18), '1.00027670', '1.00018016', '1988.53', '3081.25', '11100956.75'
    tst[21] = 1, 21, datetime.date(2024, 11, 19), '1.00027670', '1.00018016', '1988.88', '3083.20', '11106028.84'
    tst[22] = 1, 22, datetime.date(2024, 11, 20), '1.00027670', '1.00018016', '1989.24', '3085.16', '11111103.25'
    tst[23] = 1, 23, datetime.date(2024, 11, 21), '1.00027670', '1.00018016', '1989.60', '3087.12', '11116179.97'
    tst[24] = 1, 24, datetime.date(2024, 11, 22), '1.00027670', '1.00018016', '1989.96', '3089.09', '11121259.02'
    tst[25] = 1, 25, datetime.date(2024, 11, 23), '1.00027670', '1.00018016', '1990.32', '3091.05', '11126340.38'
    tst[26] = 1, 26, datetime.date(2024, 11, 24), '1.00027670', '1.00018016', '1990.68', '3093.01', '11131424.07'
    tst[27] = 1, 27, datetime.date(2024, 11, 25), '1.00027670', '1.00018016', '1991.04', '3094.97', '11136510.08'
    tst[28] = 1, 28, datetime.date(2024, 11, 26), '1.00027670', '1.00018016', '1991.39', '3096.94', '11141598.41'
    tst[29] = 1, 29, datetime.date(2024, 11, 27), '1.00027670', '1.00018016', '1991.75', '3098.91', '11146689.07'
    tst[30] = 1, 30, datetime.date(2024, 11, 28), '1.00027670', '1.00018016', '1992.11', '3100.87', '11151782.06'
    tst[31] = 1, 31, datetime.date(2024, 11, 29), '1.00027670', '1.00018016', '1992.47', '3102.84', '11156877.37'
    tst[32] = 1, 32, datetime.date(2024, 11, 30), '1.00027670', '1.00018016', '1992.83', '3104.81', '11161975.01'
    tst[33] = 1, 33, datetime.date(2024, 12, 1), '1.00027670', '1.00018016', '1993.19', '3106.78', '11167074.98'
    tst[34] = 1, 34, datetime.date(2024, 12, 2), '1.00027670', '1.00018016', '1993.55', '3108.75', '11172177.28'
    tst[35] = 1, 35, datetime.date(2024, 12, 3), '1.00027670', '1.00018016', '1993.91', '3110.72', '11177281.91'
    tst[36] = 1, 36, datetime.date(2024, 12, 4), '1.00027670', '1.00018016', '1994.27', '3112.70', '11182388.87'
    tst[37] = 1, 37, datetime.date(2024, 12, 5), '1.00027670', '1.00018016', '1994.63', '3114.67', '11187498.17'
    tst[38] = 1, 38, datetime.date(2024, 12, 6), '1.00027670', '1.00018016', '1994.98', '3116.65', '11192609.80'

    # Período 2 – data, fator de spread, fator de correção, correção, juros, saldo.
    tst[39] = 2, 1, datetime.date(2024, 12, 7), '1.00027670', '1.000125570', '1381.27', '3044.06', '11004425.33'
    tst[40] = 2, 2, datetime.date(2024, 12, 8), '1.00027670', '1.000125570', '1381.44', '3045.67', '11008852.44'
    tst[41] = 2, 3, datetime.date(2024, 12, 9), '1.00027670', '1.000125570', '1381.61', '3047.28', '11013281.33'
    tst[42] = 2, 4, datetime.date(2024, 12, 10), '1.00027670', '1.000125570', '1381.79', '3048.89', '11017712.00'
    tst[43] = 2, 5, datetime.date(2024, 12, 11), '1.00027670', '1.000125570', '1381.96', '3050.50', '11022144.46'
    tst[44] = 2, 6, datetime.date(2024, 12, 12), '1.00027670', '1.000125570', '1382.13', '3052.10', '11026578.70'
    tst[45] = 2, 7, datetime.date(2024, 12, 13), '1.00027670', '1.000125570', '1382.31', '3053.72', '11031014.72'
    tst[46] = 2, 8, datetime.date(2024, 12, 14), '1.00027670', '1.000125570', '1382.48', '3055.33', '11035452.53'
    tst[47] = 2, 9, datetime.date(2024, 12, 15), '1.00027670', '1.000125570', '1382.65', '3056.94', '11039892.12'
    tst[48] = 2, 10, datetime.date(2024, 12, 16), '1.00027670', '1.000125570', '1382.83', '3058.55', '11044333.50'
    tst[49] = 2, 11, datetime.date(2024, 12, 17), '1.00027670', '1.000125570', '1383.00', '3060.16', '11048776.66'
    tst[50] = 2, 12, datetime.date(2024, 12, 18), '1.00027670', '1.000125570', '1383.18', '3061.78', '11053221.62'
    tst[51] = 2, 13, datetime.date(2024, 12, 19), '1.00027670', '1.000125570', '1383.35', '3063.39', '11057668.36'
    tst[52] = 2, 14, datetime.date(2024, 12, 20), '1.00027670', '1.000125570', '1383.52', '3065.01', '11062116.89'
    tst[53] = 2, 15, datetime.date(2024, 12, 21), '1.00027670', '1.000125570', '1383.70', '3066.62', '11066567.21'
    tst[54] = 2, 16, datetime.date(2024, 12, 22), '1.00027670', '1.000125570', '1383.87', '3068.24', '11071019.32'
    tst[55] = 2, 17, datetime.date(2024, 12, 23), '1.00027670', '1.000125570', '1384.04', '3069.86', '11075473.22'
    tst[56] = 2, 18, datetime.date(2024, 12, 24), '1.00027670', '1.000125570', '1384.22', '3071.48', '11079928.91'
    tst[57] = 2, 19, datetime.date(2024, 12, 25), '1.00027670', '1.000125570', '1384.39', '3073.09', '11084386.40'
    tst[58] = 2, 20, datetime.date(2024, 12, 26), '1.00027670', '1.000125570', '1384.57', '3074.71', '11088845.67'
    tst[59] = 2, 21, datetime.date(2024, 12, 27), '1.00027670', '1.000125570', '1384.74', '3076.33', '11093306.75'
    tst[60] = 2, 22, datetime.date(2024, 12, 28), '1.00027670', '1.000125570', '1384.91', '3077.95', '11097769.61'
    tst[61] = 2, 23, datetime.date(2024, 12, 29), '1.00027670', '1.000125570', '1385.09', '3079.58', '11102234.28'
    tst[62] = 2, 24, datetime.date(2024, 12, 30), '1.00027670', '1.000125570', '1385.26', '3081.20', '11106700.74'
    tst[63] = 2, 25, datetime.date(2024, 12, 31), '1.00027670', '1.000125570', '1385.43', '3082.82', '11111168.99'
    tst[64] = 2, 26, datetime.date(2025, 1, 1), '1.00027670', '1.000125570', '1385.61', '3084.44', '11115639.04'
    tst[65] = 2, 27, datetime.date(2025, 1, 2), '1.00027670', '1.000125570', '1385.78', '3086.07', '11120110.90'
    tst[66] = 2, 28, datetime.date(2025, 1, 3), '1.00027670', '1.000125570', '1385.96', '3087.69', '11124584.55'
    tst[67] = 2, 29, datetime.date(2025, 1, 4), '1.00027670', '1.000125570', '1386.13', '3089.32', '11129060.00'
    tst[68] = 2, 30, datetime.date(2025, 1, 5), '1.00027670', '1.000125570', '1386.30', '3090.95', '11133537.25'
    tst[69] = 2, 31, datetime.date(2025, 1, 6), '1.00027670', '1.000125570', '1386.48', '3092.57', '11138016.30'

    for i, entry in enumerate(itertools.islice(fincore.get_jm_daily_returns(**kwa), 0, 69), 1):
        assert entry.period == tst[i][0]
        assert entry.date == tst[i][2]
        assert entry.no == tst[i][1]

        # Fator fixo, valor do rendimento.
        assert math.isclose(entry.sf, decimal.Decimal(tst[i][3]), rel_tol=1e-8)
        assert entry.value == decimal.Decimal(tst[i][6])

        # Fator de correção, valor da correção
        assert math.isclose(t.cast(fincore.PriceAdjustedDailyReturn, entry).cf, decimal.Decimal(tst[i][4]), rel_tol=1e-8)
        assert t.cast(fincore.PriceAdjustedDailyReturn, entry).pla == decimal.Decimal(tst[i][5])

        # Saldo.
        assert entry.bal == decimal.Decimal(tst[i][7])

@pytest.mark.skip(reason='Not implemented yet.')
def test_will_create_loan_daily_returns_jm_2():
    '''
    Operação Palazzo Saldanha - Juros mensais - 9 meses.

    Três antecipações, duas parciais e uma total.

    Ref File: https://docs.google.com/spreadsheets/d/1vzW6Kz_NvLRHj8WZv2dSSGSvHauwhM7eCS5YfQ_ohng
    Tab.....: Palazzo Saldanha
    '''

    pass  # FIXME: implementar. Já está em planilha de testes.

def test_will_defer_price_level_adjustment_on_daily_returns():
    '''
    Correção devida e não liquidada permanece no saldo diário, e rende.

    Espelho diário de "test_will_accrue_interest_over_deferred_price_level_adjustment": a antecipação de 52.000 em
    03/08 cobre os juros do período e só parte da correção. A ordem de imputação – juros, correção, principal – não
    deixa a antecipação chegar ao principal, então "op" fica intacto nos 6.000.000,00; o motor antigo abatia
    principal aqui, deflacionando o valor pelo fator de correção.

    No fim do dia da antecipação, a correção embutida no saldo ("opla") guarda os diferidos, recorrigidos. O
    pagamento regular de 07/08 os recolhe: "opla" zera, e o saldo do fim do dia volta ao principal nominal mais o
    rendimento do próprio dia.

    Os valores fixados saem do próprio motor. A tabela de pagamentos não fecha com eles no centavo – os dois motores
    divergem por construção na acumulação intra-período do IPCA – mas as conservações são as mesmas.
    '''

    kwa = _kwa_cri_ipa()

    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2026, 8, 3), value=decimal.Decimal('52000'))]

    drs = {x.date: t.cast(fincore.PriceAdjustedDailyReturn, x) for x in fincore.get_jm_daily_returns(**kwa)}

    # Véspera: a correção do período, de 8.360,43, está embutida no saldo.
    assert drs[datetime.date(2026, 8, 2)].opla == decimal.Decimal('8360.43')

    # Dia da antecipação: nada de principal amortizado, juros zerados, e o diferido segue no saldo.
    assert drs[datetime.date(2026, 8, 3)].op == decimal.Decimal('6000000.00')
    assert drs[datetime.date(2026, 8, 3)].oi == _0
    assert drs[datetime.date(2026, 8, 3)].opla == decimal.Decimal('6605.58')
    assert drs[datetime.date(2026, 8, 3)].bal == decimal.Decimal('6008435.75')

    # Pagamento regular seguinte: recolhe o diferido, e o saldo volta ao nominal mais o rendimento do dia.
    assert drs[datetime.date(2026, 8, 7)].opla == _0
    assert drs[datetime.date(2026, 8, 7)].bal - drs[datetime.date(2026, 8, 7)].value == decimal.Decimal('6000000.00')

def test_will_lock_interest_and_adjustment_on_daily_returns():
    '''
    Antecipação que não amortiza juros trava juro e correção no saldo diário; uma antecipação posterior os recolhe.

    Espelho diário de "test_will_collect_locked_interest_and_adjustment_on_a_later_prepayment". A antecipação de
    50.000 em 20/07 vai inteira ao principal – "op" cai exatamente pelo seu valor – e deixa os 23.825,55 de juros do
    período devidos ("oi"), junto com a correção, no saldo. A de 03/08 recolhe tudo: "oi" zera, e o que sobra abate
    o principal nominal.

    O regular de 07/08 fica só com o rendimento do próprio período: o saldo do fim do dia é o nominal mais o
    rendimento do dia, sem dupla cobrança do que a antecipação já liquidou.
    '''

    kwa = _kwa_cri_ipa()

    kwa['insertions'] = [
        fincore.Amortization.Bare(date=datetime.date(2026, 7, 20), value=decimal.Decimal('50000'), amortizes_interest=False),
        fincore.Amortization.Bare(date=datetime.date(2026, 8, 3), value=decimal.Decimal('150000'))
    ]

    drs = {x.date: t.cast(fincore.PriceAdjustedDailyReturn, x) for x in fincore.get_jm_daily_returns(**kwa)}

    # A travada: o valor sai inteiro do principal, e o juro do período fica devido, no saldo.
    assert drs[datetime.date(2026, 7, 20)].op == decimal.Decimal('5950000.00')
    assert drs[datetime.date(2026, 7, 20)].oi == decimal.Decimal('23825.55')
    assert drs[datetime.date(2026, 7, 20)].bal == decimal.Decimal('5980287.59')

    # A coletora: liquida o juro travado e a correção, e abate o restante do principal nominal.
    assert drs[datetime.date(2026, 8, 3)].op == decimal.Decimal('5858333.70')
    assert drs[datetime.date(2026, 8, 3)].oi == _0
    assert drs[datetime.date(2026, 8, 3)].bal == decimal.Decimal('5860420.92')

    # O regular seguinte cobra apenas o próprio período.
    assert drs[datetime.date(2026, 8, 7)].opla == _0
    assert drs[datetime.date(2026, 8, 7)].bal - drs[datetime.date(2026, 8, 7)].value == decimal.Decimal('5858333.70')
# }}}

# Cronograma de pagamentos mensal x retornos diários. {{{
def test_will_match_payments_table_and_daily_returns_1():
    '''
    Operação "Mais Park Pampulha 2", Livre - 18 meses - CDI, ID "lWwhog1nlyrIpBSDx5dD_".

    Compara os valores finais do cronograma de pagamentos mensal e da rotina de retornos diários.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('600000')
    kwa['apy'] = decimal.Decimal('7')
    kwa['vir'] = fincore.VariableIndex(code='CDI')
    kwa['amortizations'] = tab = []

    tab.append(fincore.Amortization(date=datetime.date(2021, 12, 3), amortizes_interest=False))

    for idx in range(1, 19):
        due = datetime.date(2021, 12, 3) + _MONTH * idx
        pct = decimal.Decimal(1) / decimal.Decimal(18)

        tab.append(fincore.Amortization(due, amortization_ratio=pct, amortizes_interest=True))

    pmt = next(_tail(1, fincore.build(**kwa)))
    drt = next(_tail(1, fincore.get_livre_daily_returns(**kwa)))

    assert pmt.raw == drt.bal

def test_will_match_payments_table_and_daily_returns_2():
    '''
    Operação "YUCA SPE V", Juros mensais - 30 meses - IPCA, ID "cmQFTXLsEB6Bg7Zlae1pV".

    Compara os valores finais do cronograma de pagamentos mensal e da rotina de retornos diários.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1844500')
    kwa['apy'] = decimal.Decimal('7')
    kwa['zero_date'] = datetime.date(2022, 2, 18)
    kwa['term'] = 30
    kwa['vir'] = fincore.VariableIndex(code='IPCA')
    kwa['amortizes_correction'] = False

    pmt = next(_tail(1, fincore.build_jm(**kwa)))
    drt = next(_tail(1, fincore.get_jm_daily_returns(**kwa)))

    assert pmt.raw == drt.bal

def test_will_match_payments_table_and_daily_returns_3():
    '''
    Baseado na operação "YUCA SPE V", Juros mensais - 30 meses - IPCA, ID "cmQFTXLsEB6Bg7Zlae1pV", com inserção de uma
    antecipação total fictícia.

    Compara os valores finais do cronograma de pagamentos mensal e da rotina de retornos diários.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1844500')
    kwa['apy'] = decimal.Decimal('7')
    kwa['zero_date'] = datetime.date(2022, 2, 18)
    kwa['term'] = 30
    kwa['vir'] = fincore.VariableIndex(code='IPCA')
    kwa['amortizes_correction'] = False
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2022, 4, 18), value=fincore.Amortization.Bare.MAX_VALUE)]

    pmt = next(_tail(1, fincore.build_jm(**kwa)))
    drt = next(_tail(1, fincore.get_jm_daily_returns(**kwa)))

    assert pmt.raw == drt.bal

def test_will_match_payments_table_and_daily_returns_4():
    '''
    Operação "CRI - Max Tulum 2 (Isento de IR)", Juros mensais - 38 meses - IPCA, ID "SFITBR__Qo2dDrU5GfAGj".

    Compara os valores iniciais do cronograma de pagamentos mensal e da rotina de retornos diários.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('7000000')
    kwa['apy'] = decimal.Decimal('10.84')
    kwa['zero_date'] = datetime.date(2024, 12, 12)
    kwa['term'] = 38
    kwa['anniversary_date'] = datetime.date(2025, 1, 14)
    kwa['vir'] = fincore.VariableIndex(code='IPCA')
    kwa['first_dct_rule'] = '31'

    pmt = next(fincore.build_jm(**kwa))
    drt = next(_tail(1, (x for x in fincore.get_jm_daily_returns(**kwa) if x.date < pmt.date)))

    assert pmt.raw + pmt.bal == drt.bal

def test_will_match_payments_table_and_daily_returns_5():
    '''
    Juros mensais prefixado com uma antecipação que não amortiza juros, seguida do regular que recolhe o travado.

    Sem correção monetária os dois motores caminham juntos, então a comparação vale em toda data de pagamento, e não
    só na última: o saldo do fim do dia, descontado o rendimento do próprio dia, é o saldo do cronograma mensal, ao
    centavo. Sem a trava no motor diário, a antecipação de 20/07 liquidaria os juros do período, o principal em
    aberto divergiria dali em diante, e a comparação quebraria de 07/08 até a última parcela.

    Os meses são alinhados de propósito, para que este teste meça só a trava. O caso de "first_dct_rule" fixa com
    aniversário tem teste próprio, o "test_will_apply_first_dct_rule_to_the_first_period_only_on_daily_returns".
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1000000')
    kwa['apy'] = decimal.Decimal('12')
    kwa['zero_date'] = datetime.date(2026, 6, 7)
    kwa['term'] = 6
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2026, 7, 20), value=decimal.Decimal('50000'), amortizes_interest=False)]

    sched = list(fincore.build_jm(**kwa))
    drs = {x.date: x for x in fincore.get_jm_daily_returns(**kwa)}

    # O motor diário não emite o dia do pagamento final: o saldo da véspera é o que ele paga.
    for pmt in sched[:-1]:
        assert drs[pmt.date].bal - drs[pmt.date].value == pmt.bal

    assert sched[-1].raw == list(drs.values())[-1].bal

    # E o principal nominal diário acompanha: a antecipação saiu inteira do principal.
    assert drs[datetime.date(2026, 7, 20)].op == decimal.Decimal('950000.00')

def test_will_keep_daily_returns_running_while_interest_stays_locked():
    '''
    Antecipação prefixada que leva todo o principal em aberto, sem amortizar juros.

    A lib permite de propósito – o teto do modo é o principal em aberto, e tomá-lo por inteiro não quita a dívida:
    os juros do trecho ficam devidos, e o pagamento regular seguinte os recolhe.

    O motor diário encerra a série quando o principal em aberto zera. O travado de correção mora dentro do
    "get_principal_outstanding" e segura a série sozinho, mas só quando há indexador; num prefixado ele é zero, e
    quem sobra é o juro travado. Sem o termo de juro travado na condição de parada, a série morreria em 19/07, na
    véspera da antecipação, enquanto o cronograma segue até 07/08 cobrando 3.990,08. Em produção isso congela a
    posição diária do investidor, e depois entra no extrato um pagamento que a série nunca acumulou.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1000000')
    kwa['apy'] = decimal.Decimal('12')
    kwa['zero_date'] = datetime.date(2026, 6, 7)
    kwa['term'] = 6
    kwa['insertions'] = [fincore.Amortization.Bare(date=datetime.date(2026, 7, 20), value=decimal.Decimal('1000000'), amortizes_interest=False)]

    dbl = kwa['insertions'][0].date
    sched = list(fincore.build_jm(**kwa))
    drs = list(fincore.get_jm_daily_returns(**kwa))

    # A antecipação leva o principal a zero, e ainda assim deixa juros em aberto.
    assert next(x for x in drs if x.date == dbl).op == _0
    assert next(x for x in drs if x.date == dbl).oi > _0

    # O cronograma tem um pagamento depois dela, que não amortiza nada: é o que recolhe o juro travado.
    assert (nxt := next(x for x in sched if x.date > dbl)).amort == _0
    assert nxt.raw > _0

    # E a série diária vai até a véspera desse pagamento, em vez de parar na antecipação.
    assert drs[-1].date > dbl
    assert drs[-1].date == sched[-1].date - datetime.timedelta(days=1)

def test_will_apply_first_dct_rule_to_the_first_period_only_on_daily_returns():
    '''
    Uma "first_dct_rule" fixa alcança só o primeiro período, também no motor diário.

    O cronograma mensal sempre fez assim – ver a guarda "num > 1" da fase FZA. O motor diário aplicava a regra a
    todos os períodos: um mês de DCT 30 rendia na base de 31, e cada mês cheio acumulava só 360/372 do juro devido.
    A cobrança não errava, porque vem do cronograma mensal; o que desviava era a posição diária, por volta de 3,2%
    do juro do mês na véspera de cada pagamento. As vinte operações CRI IPCA com regra 31 em produção caem neste
    caso.

    Duas verificações. No prefixado com aniversário, o rendimento total da série diária tem que fechar com o
    pagamento final do cronograma. E no IPCA da operação "CRI IPA Club Residencial", cujo primeiro período tem DCT
    31 também pelo cálculo automático, a série com regra 31 tem que coincidir dia a dia com a série em AUTO – antes
    do conserto elas divergiam a partir do segundo período.
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('1000000')
    kwa['apy'] = decimal.Decimal('12')
    kwa['zero_date'] = datetime.date(2026, 5, 29)
    kwa['term'] = 6
    kwa['anniversary_date'] = datetime.date(2026, 7, 7)
    kwa['first_dct_rule'] = '31'

    sched = list(fincore.build_jm(**kwa))
    drs = list(fincore.get_jm_daily_returns(**kwa))

    assert sched[-1].raw == drs[-1].bal

    kwb = _kwa_cri_ipa()
    kwc = _kwa_cri_ipa()

    del kwc['first_dct_rule']  # Volta ao AUTO, que calcula DCT 31 para o primeiro período desta operação.

    for x, y in zip(fincore.get_jm_daily_returns(**kwb), fincore.get_jm_daily_returns(**kwc), strict=True):
        assert (x.date, x.value, x.bal) == (y.date, y.value, y.bal)

def test_will_match_payments_table_and_daily_returns_6():
    '''
    Operação "Bossa Nova CCB 7", Bullet - 120 meses - IPCA.

    Um Bullet tem só duas amortizações, e é o que aciona o ramo "len(lst) == 2" do "normalize_ipca_indexes": a
    correção de cada mês é diluída nos dias do próprio mês. No vencimento a diluição recompõe os fatores mensais
    inteiros, e o saldo final da série diária fecha ao centavo com o pagamento único do cronograma – com e sem
    spread. No meio do caminho os dois motores divergem de propósito: o cronograma projeta a correção do período
    inteiro pró-rata, a série diária só acumula os índices já decorridos.

    Paga os dois FIXMEs históricos do "normalize_ipca_indexes".
    '''

    kwa = {}

    kwa['principal'] = decimal.Decimal('176000')
    kwa['apy'] = _0
    kwa['zero_date'] = datetime.date(2022, 10, 24)
    kwa['term'] = 120
    kwa['vir'] = fincore.VariableIndex('IPCA')

    pmt = next(fincore.build_bullet(**kwa))
    drt = next(_tail(1, fincore.get_bullet_daily_returns(**kwa)))

    assert pmt.raw == drt.bal == decimal.Decimal('193510.84')  # Conferido em "test_will_create_bullet_ipca_1a".

    # Com spread, para exercitar juro e correção juntos.
    kwa['apy'] = decimal.Decimal('8')

    pmt = next(fincore.build_bullet(**kwa))
    drt = next(_tail(1, fincore.get_bullet_daily_returns(**kwa)))

    assert pmt.raw == drt.bal

def test_will_match_payments_table_and_daily_returns_7():
    '''
    Antecipação parcial que alcança o juro diferido por uma carência, sobre a estrutura da operação "Mirante da
    Mata - Parcelas Amortizadas - 36 meses": seis meses de carência total a partir de 26/02/2024, e trinta parcelas
    amortizantes dali em diante. Simulada a juro prefixado – a operação real é CDI + 6,5%, mas o ponto do FIXME
    histórico é o diferimento, não o indexador.

    Em 10/11/2024 os juros do período em curso são 12.723,63. A antecipação de 100.000 os liquida, avança sobre o
    juro diferido pela carência, e não toca o principal – a ordem de imputação põe os juros na frente. E os dois
    motores atravessam o evento juntos: em toda data de pagamento o saldo diário do fim do dia, menos o rendimento
    do próprio dia, é o saldo do cronograma, com a tolerância de um centavo que a docstring da rotina documenta.
    '''

    kwa = {}
    lst: t.List[fincore.Amortization | fincore.Amortization.Bare] = [fincore.Amortization(date=datetime.date(2024, 2, 26), amortizes_interest=False)]

    for i in range(1, 37):
        pct = _0 if i < 7 else decimal.Decimal('0.03333333333333') if i < 36 else decimal.Decimal('0.03333333333344')

        lst.append(fincore.Amortization(date=datetime.date(2024, 2, 28) + _MONTH * i, amortization_ratio=pct, amortizes_interest=i >= 7))

    lst.append(fincore.Amortization.Bare(date=datetime.date(2024, 11, 10), value=decimal.Decimal('100000')))

    kwa['principal'] = decimal.Decimal('6000000')
    kwa['apy'] = decimal.Decimal('6.5')
    kwa['amortizations'] = sorted(lst, key=lambda x: x.date)
    kwa['capitalisation'] = '30/360'

    sched = list(fincore.get_payments_table(**kwa))
    drs = {x.date: x for x in fincore.get_daily_returns(**kwa)}
    adv = next(x for x in sched if x.date == datetime.date(2024, 11, 10))

    # A antecipação liquida os juros do período e avança sobre o diferido, sem tocar o principal.
    assert adv.gain == decimal.Decimal('12723.63')
    assert adv.amort == _0
    assert adv.raw == decimal.Decimal('100000.00')

    # Os motores atravessam juntos o evento, a carência e as parcelas.
    for pmt in sched[:-1]:
        assert abs(drs[pmt.date].bal - drs[pmt.date].value - pmt.bal) <= _CENTI

    assert sched[-1].raw == next(_tail(1, iter(drs.values()))).bal
    assert sum(x.amort for x in sched) == kwa['principal']
# }}}

# vi:fdm=marker:
