# Copyright (C) Inco - All Rights Reserved.
#
# Written by Rafael Viotti <viotti@inco.vc>,
#            Gustavo Zille <gustavo.zille@inco.vc>, April 2022.
#
# Unauthorized copying of this file, via any medium, is strictly prohibited. Proprietary and confidential.
#
# [FINCORE V3]
#
# This module is in its third generation. There was also a generation zero, which preceded the creation of this
# module, when the financial calculation routines were auxiliary to the "util" module. At that time we only handled
# fixed-rate operations with normal flows.
#
# The first generation of Fincore was born on March 22, 2022, in the support repository, as a Jupyter
# notebook, "lab-000.ipynb". See revision "6f12bab6dc". In April it was integrated into INCO's backend as
# "util.cli.fin_lib".
#
# The second generation came from a refactoring in November 2022, revision "ca58a71c19". At that time, the library suffered
# from anemia. The data types had no names or attributes. All input and output happened through tuples or
# "collections.namedtuple". The public API was extremely confusing, with poorly designed factories.
#
# In July 2023, I did a new refactoring, now focusing on making Fincore's algorithms universal, which enters its
# third generation. Revision "42bdf101c5" and subsequent. We still had arbitrary operating limitations and
# errors. What was mere inconvenience became an impediment to new INCO operations. Here is a summary of what
# changed:
#
#   • The core became better structured and documented. It operates in three well-defined phases:
#
#     1. Calculates "spread" and correction factors.
#     2. Records values of the current iteration of the schedule: principal and amortization percentage, interest, correction etc.
#     3. Creates the output instance of the iteration, Payment / PriceAdjustedPayment, and rounding.
#
#   • It became more generic:
#
#     • Covers 100% of cases in Free mode.
#       • Example: quarterly payments.
#
#     • Covers more alternative flows.
#       • Example: payment in grace period.
#
#   • Errors were fixed:
#
#     • Does not incorporate interest into principal.
#       • This fixes operations with grace periods.
#
#     • Does not project monetary correction after calculation date.
#       • This fixes the 3040 maturity schedule.
#
#   • Public API improved. Prepayment became more semantic:
#
#     • Takes the prepaid value, not a percentage value.
#       • Death of the "fincore.get_remaining_amortization" routine.
#
#   • The module decreased by almost 15% in size. From ~1600 to ~1400 lines of code.
#
# [ANNOTATED_TYPES]
#
# Use annotated types instead of explicit checking in code – http://stackoverflow.com/a/72563242.
#
# [WEAKNESSES]
#
#   • Fincore works with dates, not datetime. For this reason, if it's necessary to amortize twice in the same day,
#     their order is implicit in the amortization table. Ideally, this module would be agnostic to elapsed time measurements.
#     The "date" field of the Amortization class should accept both a date and a datetime. The output
#     of "get_payments_table" should adjust according to the data type used in the input. Internally, Fincore
#     could simply discard the time information and deal only with dates.
#
#   • Rounding is not documented. Explicitly state that Fincore rounds on output, i.e., instances of
#     Payment or PriceAdjustedPayment are always rounded. But there are no internal roundings. Provide examples.
#
#   • The library's behavior in case of a negative index could be customizable.
#
#   • How does this library behave in case of future calculations? Currently, it projects automatically. This could
#     be parameterizable. The routine that calculates the payment table could fail if an index is not found
#     (future date).
#
#   • What about a correction factor less than zero? Currently, when there's an advance payment, there's no deduction of correction if it's already
#     negative. In other words, the advanced value will be deducted from interest and then from principal. This could also
#     be parameterizable.
#
#   • Because it only rounds values on output, output values from a payment schedule should not be reused as
#     input. For example, one should not run the core routine, "get_payments_table", with a calculation date and add the
#     gross value to the output debt balance to obtain the value of a supposed total prepayment
#
#       _tail = lambda iterable: iter(collections.deque(iterable, maxlen=1))
#       kargs = { … }  # Options for a Free amortization schedule, including a calculation date.
#
#       # Execute Fincore (1st time) to get the position on the calculation date.
#       row = next(_tail(fincore.build(**kargs)))
#
#       # Here, "row.raw + row.bal" would be the value of a total prepayment on the calculation date, but it won't always be.
#       kargs['insertions'].append(fincore.Amortization.Bare(date=datetime.date(…), value=row.raw + row.bal))
#
#       # Execute Fincore (2nd time). Theoretically, the payment schedule would end at the prepayment.
#       row = next(_tail(fincore.build(**kargs)))
#
#     In the previous example, both "row.raw" and "row.bal" may have been rounded up, and the value of the
#     prepayment would be higher than the remaining balance of the loan by one cent. It's better to be explicit and use
#     "fincore.Amortization.Bare.MAX_VALUE" to signal that the entire outstanding value of the loan should be
#     prepaid.
#
#       fincore.Amortization.Bare(date=datetime.date(…), value=fincore.Amortization.Bare.MAX_VALUE)
#
#     Similarly, if rounding down occurs, the prepayment value won't settle the entire operation. An
#     inadequate value for a total prepayment could go unnoticed.
#
#     FIXME: if Fincore did internal rounding, the problem described above wouldn't happen. It would be
#     possible to feed an amortization schedule with values from a payment schedule generated
#     by a previous invocation of the core routine.
#
# [TODO]
#
#   • Implement validations to prevent non-quantized "Amortization.Bare" inputs in auxiliary routines,
#     the "factories", and in "get_payments_table".
#
#   • Implement a memory for paid IPCA and for the accumulated, in case of prepayment, similar to paid interest.
#     Remember that interest compounds, but IPCA doesn't.
#

'''
INCO financial core, Fincore.

Financial calculation library for credit and investment operations.

Its main purpose is to generate monthly amortization schedules for loans in the Bullet, Price,
Monthly Interest, and Free (SAC, grace period, etc.) modalities. Supports fixed-rate operations, or indexed to CDI, Savings, or IPCA.
Accounts for interest in a 252 business day year for indexes published on business days, such as CDI; or 30/360 basis
for fixed-rate and other indexes.

This library also generates daily yield tables for loans. It covers the same modalities and
the same capitalization forms as the payment schedule generation routine.

The library supports not only regular flows, but also irregular ones with prepayments, and assists in the calculation of
arrears.

You can find the code for this module in the IPython notebook "lab-000.ipynb" located in the support repository.
But be aware that the notebook may be out of date.
'''

# Python.
import sys
import math
import types
import typing as t
import decimal
import logging
import calendar
import datetime
import functools
import itertools
import contextlib
import dataclasses

# Libs.
import typeguard
import dateutil.relativedelta

# Logger object.
_LOG = logging.getLogger('fincore')

# Zero as decimal.
_0 = decimal.Decimal()

# One as decimal.
_1 = decimal.Decimal(1)

# Centi factor.
_CENTI = decimal.Decimal('0.01')

# Centesimal quantization.
_Q = functools.partial(decimal.Decimal.quantize, exp=_CENTI, rounding=decimal.ROUND_HALF_UP)

# Generic type.
_T = t.TypeVar('_T')

# A month.
_MONTH = dateutil.relativedelta.relativedelta(months=1)

# Tabela de IR para aplicações de renda fixa.
#
# Sei que "sys.maxsize" não é o valor máximo de um numero inteiro no Python 3,
# mas sim o tamanho máximo da palavra na arquitetura em que o interpretador
# estiver executando.
#
#   https://stackoverflow.com/a/7604981
#
# Não me importo. O que quero na última entrada da tabela é apenas um número
# suficientemente grande.
#
_REVENUE_TAX_BRACKETS = [
    (0, 180, decimal.Decimal('0.225')),
    (180, 360, decimal.Decimal('0.2')),
    (360, 720, decimal.Decimal('0.175')),
    (720, sys.maxsize, decimal.Decimal('0.15'))
]

# Supported operation modes.
_OP_MODES = t.Literal['Bullet', 'Juros mensais', 'Price', 'Livre']

# Variable rate indexes.
_VR_INDEX = t.Literal['CDI', 'Poupança']

# Price level indexes.
_PL_INDEX = t.Literal['IPCA', 'IGPM']

# Price level indexes, range shifters: AUTO, M-1, M-2.
_PL_SHIFT = t.Literal['AUTO', 'M-1', 'M-2']

# Capitalisation methods, daily and monthly. Defines how DP/DT calculations are performed.
_CAPITALISATION = t.Literal['252', '360', '365', '30/360']

# Daily capitalisation methods.
_DAILY_CAPITALISATION = t.Literal['252', '360', '365']

# Gain output mode.
_GAIN_OUTPUT_MODE = t.Literal['current', 'deferred', 'settled']

# Helpers. {{{
@typeguard.typechecked
def _delta_months(d1: datetime.date, d2: datetime.date) -> int:
    '''
    Returns the number of months between two given dates, D1 and D2.

    This function will subtract D2 from D1, i.e., it will roughly perform
    "(D1 - D2).months". The day of the month is completely ignored in the
    calculation.

    >>> from datetime import date
    >>>
    >>> _delta_months(date(2018, 5, 5), date(2018, 5, 15))
    0
    >>> _delta_months(date(2019, 11, 1), date(2019, 10, 10))
    1
    >>> _delta_months(date(2023, 5, 3), date(2022, 5, 4))
    12
    >>> _delta_months(date(2000, 6, 1), date(1996, 6, 19))
    48

    Deltas will be negative if D2 > D1.

    >>> _delta_months(date(2018, 5, 5), date(2018, 11, 5))
    -6
    '''

    return (d1.year - d2.year) * 12 + d1.month - d2.month

@typeguard.typechecked
def _date_range(start_date: datetime.date, end_date: datetime.date) -> t.Iterable[datetime.date]:
    iterator = start_date

    while iterator < end_date:
        yield iterator

        iterator += datetime.timedelta(days=1)

@typeguard.typechecked
def _diff_surrounding_dates(base: datetime.date, day_of_month: int) -> int:
    '''
    Returns the amount of days between two dates derived from a base date.

    Given a base date, this function will find two dates that surround it on
    the specified day of the month. For example, if the base date is
    2022-06-12, and the day of the month is 15, then de surrounding dates are
    2022-05-15 and 2022-06-15. It will then return the difference between these
    dates, in days.

    >>> from datetime import date
    >>>
    >>> _diff_surrounding_dates(date(2022, 6, 12), 24)
    31

    So, this function has four possible outputs: 28, 29, 30, and 31 days.

    >>> _diff_surrounding_dates(date(1999, 2, 25), 10)
    28
    >>> _diff_surrounding_dates(date(2000, 3, 20), 25)
    29
    >>> _diff_surrounding_dates(date(1900, 11, 20), 19)
    30
    >>> _diff_surrounding_dates(date(2050, 7, 2), 1)
    31
    >>> _diff_surrounding_dates(date(2050, 7, 2), 2)
    31
    >>> _diff_surrounding_dates(date(2050, 7, 2), 3)
    30

    It should be possible to find a date before the base date, otherwise an
    error is thrown.

    >>> _diff_surrounding_dates(date.min, 3)
    Traceback (most recent call last):
        ...
    ValueError: can't find a date prior to the base of 0001-01-01 on day 3
    '''

    if base.day >= day_of_month or base >= datetime.date(1, 2, 1):
        d01 = base.replace(day=day_of_month)
        d02 = d01 + _MONTH if base.day >= day_of_month else d01 - _MONTH
        dff = d02 - d01 if base.day >= day_of_month else d01 - d02

        return dff.days

    else:
        raise ValueError(f"can't find a date prior to the base of {base} on day {day_of_month}")

@typeguard.typechecked
def _interleave(a: t.Iterable[_T], b: t.Iterable[_T], *, key: t.Callable[..., t.Any] = lambda x: x) -> t.Iterable[types.SimpleNamespace]:
    '''
    Interleave two ordered iterables into another, also ordered, iterable.

    Both source iterables, A and B, should produce items in order.

    >>> list(_interleave([], []))
    []

    >>> [(x.index_a, x.from_a, x.index_b, x.from_b, x.item) for x in _interleave([1, 3, 5], [2, 4, 6])]  # doctest: +NORMALIZE_WHITESPACE
    [(0, True,  0, False, 1),
     (1, False, 0, True,  2),
     (1, True,  1, False, 3),
     (2, False, 1, True,  4),
     (2, True,  2, False, 5),
     (2, False, 2, True,  6)]

    >>> list(_interleave([1, 5, 3], [2, 4, 6]))
    Traceback (most recent call last):
        ...
    ValueError: iterable A is not ordered

    When two items arising from A and B compare equally, the one from B have precedence over the one from A. This is
    because iterable A represents ordinary amortizations, whilst iterable B produces advance payments. In finance,
    advancements are usually processed first.

    >>> a = [1, 4, 6, 22, 55, 1232]
    >>> b = [4, 9, 11, 344, 999]
    >>> [(x.index_a, x.from_a, x.index_b, x.from_b, x.item) for x in _interleave(a, b)]  # doctest: +NORMALIZE_WHITESPACE
    [(0, True,  0, False, 1),
     (1, False, 0, True,  4),
     (1, True, 1, False,  4),
     (2, True,  1, False, 6),
     (3, False, 1, True,  9),
     (3, False, 2, True,  11),
     (3, True,  3, False, 22),
     (4, True,  3, False, 55),
     (5, False, 3, True,  344),
     (5, False, 4, True,  999),
     (5, True,  4, False, 1232)]

    But when a single source iterable produces items that compare equally, an exception is thrown. This generator was
    designed to interleave scheduled payments, A, with unscheduled payments, B. It is unusual to have more than one
    unscheduled payment on a given day.

    >>> a = [1, 5, 5, 6, 22, 90, 1000]
    >>> b = [5, 5, 9, 11, 82, 829]
    >>> list(_interleave(a, b))
    Traceback (most recent call last):
        ...
    ValueError: iterable B, item “5” found multiple times

      ADENDO: Aqui reside o nosso bloqueio contra duas antecipações no mesmo dia, dentre outros. Isso é bom, pois no
      ADENDO: momento as controladoras estão pouco testadas, e já houve tentativa de submeter uma única antecipação
      ADENDO: mais de uma vez. Aconteceu com a Mariana Castro no dia 01 de Agosto de 2023. Ela teve um fluxo de geração
      ADENDO: de antecipações totais interrompidos por um erro de requisição. Ao tentar resumir o processo, em uma
      ADENDO: requisição subsequente, a controladora passou novamente por investimentos que já possuíam a antecipação
      ADENDO: gerada, e tentou inseri-la novamente. Se não fosse essa proteção, teríamos um erro de esquema de dados.
      ADENDO:
      ADENDO: Assim que tivermos melhor cobertura nas controladoras de geração de antecipação, pagamento parcial,
      ADENDO: pagamento de prestações em lote etc, podemos remover essa limitação. Afinal de contas, ela é arbitrária.
      ADENDO: Do ponto de vista do Fincore, a ordem de duas antecipações em uma mesma data é dada pela posição na lista.
      ADENDO: Também é necessário ter casos de testes para antecipações consecutivas com os diversos indexadores
      ADENDO: suportados pelo Fincore, antes da remoção dessa trava.
      ADENDO:
      ADENDO: Vale lembrar que se há multiplas antecipações no mesmo dia, a solução simples seria somar os seus valores
      ADENDO: brutos.

    A key function can be used to establish comparison between elements.

    >>> a = [{'x': 500, 'date': '2022-02-05'}, {'x': 100, 'date': '2022-04-05'}, {'x': -50, 'date': '2022-06-05'}]
    >>> b = [{'y': 'a', 'date': '2021-02-05'}, {'y': 'b', 'date': '2021-04-05'}, {'y': 'c', 'date': '2021-06-05'}]
    >>> [(x.index_a, x.from_a, x.index_b, x.from_b, x.item) for x in _interleave(a, b, key=lambda x: x['date'])]  # doctest: +NORMALIZE_WHITESPACE
    [(0, False, 0, True,  {'y': 'a', 'date': '2021-02-05'}),
     (0, False, 1, True,  {'y': 'b', 'date': '2021-04-05'}),
     (0, False, 2, True,  {'y': 'c', 'date': '2021-06-05'}),
     (0, True,  2, False, {'x': 500, 'date': '2022-02-05'}),
     (1, True,  2, False, {'x': 100, 'date': '2022-04-05'}),
     (2, True,  2, False, {'x': -50, 'date': '2022-06-05'})]
    '''

    val_a = val_b = sav_a = sav_b = None
    idx_a = idx_b = -1

    iter_a = iter(a)
    iter_b = iter(b)

    with contextlib.suppress(StopIteration):
        val_a = next(iter_a)

        idx_a += 1

    with contextlib.suppress(StopIteration):
        val_b = next(iter_b)

        idx_b += 1

    while val_a or val_b:
        if sav_a and val_a and key(sav_a) > key(val_a):
            raise ValueError('iterable A is not ordered')

        elif sav_a and val_a and key(sav_a) == key(val_a):
            raise ValueError(f'iterable A, item “{sav_a}” found multiple times')

        elif sav_b and val_b and key(sav_b) > key(val_b):
            raise ValueError('iterable B is not ordered')

        elif sav_b and val_b and key(sav_b) == key(val_b):  # Ver o adendo na "docstring" da rotina. FIXME.
            raise ValueError(f'iterable B, item “{sav_b}” found multiple times')

        if val_a and val_b and key(val_a) == key(val_b):
            sav_b = val_b

            yield types.SimpleNamespace(index_a=idx_a, from_a=False, index_b=idx_b, from_b=True, item=val_b)

            with contextlib.suppress(StopIteration):
                val_b = None
                val_b = next(iter_b)

                idx_b += 1

        elif val_a and val_b and key(val_a) < key(val_b):
            sav_a = val_a

            yield types.SimpleNamespace(index_a=idx_a, from_a=True, index_b=idx_b, from_b=False, item=val_a)

            with contextlib.suppress(StopIteration):
                val_a = None
                val_a = next(iter_a)

                idx_a += 1

        elif val_a and val_b:
            sav_b = val_b

            yield types.SimpleNamespace(index_a=idx_a, from_a=False, index_b=idx_b, from_b=True, item=val_b)

            with contextlib.suppress(StopIteration):
                val_b = None
                val_b = next(iter_b)

                idx_b += 1

        elif val_a:
            sav_a = val_a

            yield types.SimpleNamespace(index_a=idx_a, from_a=True, index_b=idx_b, from_b=False, item=val_a)

            with contextlib.suppress(StopIteration):
                val_a = None
                val_a = next(iter_a)

                idx_a += 1

        else:
            sav_b = val_b

            yield types.SimpleNamespace(index_a=idx_a, from_a=False, index_b=idx_b, from_b=True, item=val_b)

            with contextlib.suppress(StopIteration):
                val_b = None
                val_b = next(iter_b)

                idx_b += 1
# }}}

# Public API. Main classes. {{{
@dataclasses.dataclass
class PriceLevelAdjustment:
    '''
    A price level adjustment specification for amortization schedules.

    This object has five fields.

      1. The market index used on this amortization. For now, only IPCA is supported. IGPM is planned.

      2. The first, or base date, of the date range used on the calculation of the price adjustment factor of the
      amortization. The factor will be the monthly accumulation of N indexes from the base date, where N is the
      range size, or period (see below).

      3. The period, or how many monthly indexes from the base date are accumulated to calculate the adjustment
      factor of the amortization. Should be greater than, or equal to one. Consider that the base date is March
      first 2022, and that the period is five.

             1          2          3          4          5
             ├──────────┼──────────┼──────────┼──────────┼──────────> 2022
            Mar        Apr        May        Jun        Jul

         In the example above, indexes from March to July would be accumulated.

      4. A shift, in months, for the price adjustment accumulation range.

        ▪︎ AUTO, don't shift.

        ▪︎ M-1 means start accumulating one month prior to the base date.

        ▪︎ M-2 means start accumulating two months prior to the base date.

         These are the effects of each shift option when applied to the previous example.

            -2         -1          1          2          3          4          5
             ├──────────├──────────┼──────────┼──────────┼──────────┼──────────┼──────────> 2022
                                  Mar        Apr        May        Jun        Jul    AUTO

                        Feb       Mar        Apr        May        Jun               M-1

            Jan         Feb       Mar        Apr        May                          M-2

      5. A boolean flag indicating whether the price adjustment will be amortized or incorporated in the debt.
    '''

    code: _PL_INDEX

    base_date: t.Optional[datetime.date] = None

    period: int = 0

    shift: _PL_SHIFT = 'M-1'

    amortizes_adjustment: bool = True

@dataclasses.dataclass
class DctOverride:
    '''
    An override for the DCT calculation. Has three fields.

      1. The date of the previous scheduled amortization.

      2. The date of the next scheduled amortization.

      3. A boolean stating if this override information predates the first scheduled amortization.
    '''

    date_from: datetime.date

    date_to: datetime.date

    predates_first_amortization: bool

@dataclasses.dataclass
class Amortization:
    '''
    A entry of an amortization schedule.

    Establishes what fraction of the initial debt should be paid at a given date.

    Some loans are more intricate than others: those with variable interest rates, price level adjustments, grace
    periods etc. The basic Amortization class does not provide enough information to create payment schedules for such
    cases. Enter the extension fields.

      • "price_level_adjustment", which is a “PriceLevelAdjustment” instance.

      • "dct_override", an override for the DCT calculation. See “DctOverride” below.

    The DCT override field is specific for 30/360 specs. We need to store extra override information for the DCT
    calculation to ensure that DCT is always the amount of days between two scheduled payments. In case an amortization
    is inserted on a schedule, DCT cannot be calculated as the difference in days between the insertion date and the
    previous payment date.
    '''

    @dataclasses.dataclass
    class Bare:
        '''
        A minimum amortization entry.

        This class is useful to specify prepayments. In this case, only the date and the amortization percentage are
        sufficient.
        '''

        # Maximum value. Ver “http://stackoverflow.com/a/28082106”.
        MAX_VALUE: t.ClassVar[decimal.Decimal] = decimal.Decimal(decimal.MAX_EMAX)

        # Base field, the bare amortization date.
        date: datetime.date

        # Base field, the bare amortization nominal value.
        value: decimal.Decimal = _0

        # Extension field.
        dct_override: t.Optional[DctOverride] = None

    # Base field, the amortization date.
    date: datetime.date

    # Base field, the amortization percentage. FIXME: should never be negative.
    amortization_ratio: decimal.Decimal = _0

    # Base field, whether the interest will be paid or will accumulate for a subsequent date.
    amortizes_interest: bool = True

    # Extension field.
    price_level_adjustment: t.Optional[PriceLevelAdjustment] = None

    # Extension field.
    dct_override: t.Optional[DctOverride] = None

@dataclasses.dataclass
class Payment:
    '''
    An entry of a payment schedule.

    It represents a payment at a given date.

      • "no" is the payment number;

      • "date" is the date the payment should be done;

      • "raw" is the raw value of the payment;

      • "tax" is the revenue tax to collect;

      • "net" is the net value to be payed;

      • "gain" is the yielded profit;

      • "amort" is the amortized value;

      • "bal" is the current loan balance.
    '''

    no: int = 0

    date: datetime.date = datetime.date.min

    raw: decimal.Decimal = _0

    tax: decimal.Decimal = _0

    net: decimal.Decimal = _0

    gain: decimal.Decimal = _0

    amort: decimal.Decimal = _0

    bal: decimal.Decimal = _0

@dataclasses.dataclass
class DailyReturn:
    no: int = 0

    period: int = 0

    date: datetime.date = datetime.date.min

    value: decimal.Decimal = _0

    bal: decimal.Decimal = _0

    fixed_factor: decimal.Decimal = _1

    variable_factor: decimal.Decimal = _1

@dataclasses.dataclass
class PriceAdjustedPayment(Payment):
    '''An entry of a payment schedule, with price level adjustment (IPCA or IGPM).'''

    pla: decimal.Decimal = _0

@dataclasses.dataclass
class LatePayment(Payment):
    '''An entry of a payment schedule, with extra gain, penalty and fine values.'''

    # Taxa mensal de juros moratórios (a.m.). MLFR = Montly Late Fee Rate.
    FEE_RATE: t.ClassVar[decimal.Decimal] = _1

    # Taxa de multa.
    FINE_RATE: t.ClassVar[decimal.Decimal] = _1 + _1

    extra_gain: decimal.Decimal = _0

    penalty: decimal.Decimal = _0

    fine: decimal.Decimal = _0

# Esta classe é herança da primeira implementação de atraso para IPCA. Essa implementação nunca foi usada, e foi
# removida em 26 de julho de 2024. Nunca confiamos em quaisquer implementações de IPCA na INCO. Foram muito mal
# especificadas. Vou deixar a classe aqui para referência em uma implementação futura.
#
@dataclasses.dataclass
class LatePriceAdjustedPayment(PriceAdjustedPayment):
    '''An entry of a price adjusted payment schedule, with extra gain, penalty and fine values.'''

    extra_gain: decimal.Decimal = _0

    penalty: decimal.Decimal = _0

    fine: decimal.Decimal = _0

@dataclasses.dataclass
class CalcDate:
    '''
    A calculation date for the "get_payments_table" function.

    When creating a payment table from an amortization schedule, the value specified in the date field of this class
    will establish where the calculations will stop. The returned table will only show payments up to that date.

    The runaway field, when true, dictates that the entire payments schedule should be returned.
    '''

    value: datetime.date

    runaway: bool = False
# }}}

# Public API. Variable index, and storage backend classes. {{{
class BackendError(Exception):
    pass

@dataclasses.dataclass
class DailyIndex:
    date: datetime.date = datetime.date.min

    value: decimal.Decimal = _0

@dataclasses.dataclass
class MonthlyIndex:
    date: datetime.date = datetime.date.min

    value: decimal.Decimal = _0

@dataclasses.dataclass
class RangedIndex:
    begin_date: datetime.date = datetime.date.min

    end_date: datetime.date = datetime.date.min

    value: decimal.Decimal = _0

class IndexStorageBackend:
    def get_cdi_indexes(self, begin: datetime.date, end: datetime.date) -> t.Iterable[DailyIndex]:
        '''
        Returns the list of CDI indexes between the begin and end date.

        The begin date is inclusive. The end date is exclusive.

        This method should project indexes in the future.
        '''

        raise NotImplementedError()

    def get_savings_indexes(self, begin: datetime.date, end: datetime.date) -> t.Iterable[RangedIndex]:
        '''
        Returns the list of Savings indexes between the begin and end date.

        This method should not project indexes in the future.
        '''

        raise NotImplementedError()

    def get_ipca_indexes(self, begin: datetime.date, end: datetime.date) -> t.Iterable[MonthlyIndex]:
        '''
        Returns the list of IPCA indexes between the begin and end date.

        This method should not project indexes in the future.
        '''

        raise NotImplementedError()

    def get_igpm_indexes(self, begin: datetime.date, end: datetime.date) -> t.Iterable[MonthlyIndex]:
        '''
        Returns the list of IGPM indexes between the begin and end date.

        This method should not project indexes in the future.
        '''

        raise NotImplementedError()

    @typeguard.typechecked
    def calculate_cdi_factor(self, begin: datetime.date, end: datetime.date, percentage: int = 100) -> types.SimpleNamespace:
        '''
        Calcula o fator de DI (CDI) a partir de um período.

        Os índices de correção CDI dos testes abaixo foram retirados do sítio do BACEN:

          https://www3.bcb.gov.br/CALCIDADAO/publico/exibirFormCorrecaoValores.do?method=exibirFormCorrecaoValores&aba=5

        >>> from math import isclose
        >>> from datetime import date
        >>>
        >>> bend = InMemoryBackend()
        >>>
        >>> idx1 = decimal.Decimal('1.10949606')
        >>> idx2 = bend.calculate_cdi_factor(date(2022, 1, 10), date(2022, 12, 1))
        >>> idx2.amount
        224
        >>> isclose(idx1, idx2.value, rel_tol=1e-8)
        True

        >>> idx1 = decimal.Decimal('1.06421360')
        >>> idx2 = bend.calculate_cdi_factor(date(2018, 1, 2), date(2019, 1, 2))
        >>> idx2.amount
        250
        >>> isclose(idx1, idx2.value, rel_tol=1e-8)
        True

        >>> idx1 = decimal.Decimal('1.20999561')
        >>> idx2 = bend.calculate_cdi_factor(date(2018, 1, 2), date(2022, 1, 3))
        >>> idx2.amount
        1005
        >>> isclose(idx1, idx2.value, rel_tol=1e-8)
        True

        Observe que não é possível escrever testes para índices projetados. Essa função vai pegar o último índice publicado
        pelo BACEN para estimar os futuros. Um novo índice pode ser publicado, alterando o resultado da computação do
        fator, e fazendo com que o teste falhe.
        '''

        if begin < end:
            pct = decimal.Decimal(percentage) / decimal.Decimal(100)
            end = end - datetime.timedelta(days=1)  # Último dia, sempre excludente.
            fac = _1
            cnt = 0

            for x in self.get_cdi_indexes(begin, end):
                fac = fac * (1 + pct * x.value / decimal.Decimal(100))

                cnt += 1

                _LOG.debug(x)

            return types.SimpleNamespace(value=fac, amount=cnt)

        return types.SimpleNamespace(value=_1, amount=0)

    @typeguard.typechecked
    def calculate_savings_factor(self, begin: datetime.date, end: datetime.date, percentage: int = 100) -> types.SimpleNamespace:
        '''Calcula o fator de Poupança a partir de um período.'''

        # Considera-se a data de aniversário das prestações com início nos dias 29, 30 e 31 como o dia 1° do mês seguinte.
        ini = begin if begin.day <= 28 else (begin + _MONTH).replace(day=1)
        pct = decimal.Decimal(percentage) / decimal.Decimal(100)
        fac = _1
        mem = []

        # Para cada mês, apenas um dos seus 28 índices será selecionado aqui. Lembrar que apenas nos primeiros 28 dias
        # do mês tem-se publicação de Poupança. Se a data "begin" cair após do dia 28, considera-se o dia primeiro do
        # mês subsequente. Considera como o índice do mês, M, aquele em que "M.begin_date.day" seja igual a
        # "begin.day".
        #
        for x in self.get_savings_indexes(ini, end):
            if ini.day == x.begin_date.day:
                fac = fac * (_1 + pct * x.value / decimal.Decimal(100))

                mem.append(x)

                _LOG.debug(x)

        return types.SimpleNamespace(value=fac, amount=len(mem))

    @typeguard.typechecked
    def calculate_ipca_factor(self, base: datetime.date, period: int, shift: _PL_SHIFT, ratio: decimal.Decimal = _1) -> decimal.Decimal:
        '''
        Calcula o fator de correção do IPCA.

        Toma como parâmetros a data base, o período, deslocamento e uma fração para a última taxa de correção.
        '''

        ini = base - _MONTH * t.get_args(_PL_SHIFT).index(shift)
        end = base + _MONTH * (period - 1) - _MONTH * t.get_args(_PL_SHIFT).index(shift)
        mem = list(self.get_ipca_indexes(ini, end))  # FIXME: try to avoid this conversion to list.
        fac = _1

        for i, x in enumerate(mem):
            exp = _1 if i != len(mem) - 1 else ratio

            fac = fac * (_1 + x.value / decimal.Decimal(100)) ** exp

        return fac

    @typeguard.typechecked
    def calculate_igpm_factor(self, base: datetime.date, period: int, shift: _PL_SHIFT, ratio: decimal.Decimal = _1) -> decimal.Decimal:
        '''Calcula o fator de correção do IGPM.'''

        raise NotImplementedError()

class InMemoryBackend(IndexStorageBackend):
    '''
    This backend simulates almost five years of BACEN API.

    Indexes for CDI, IPCA and Poupança, ranging from 2018-01-01 to 2022-11-15, are kept in memory.

    As this backend is mostly static, i.e., it does not update itself as new indexes are published, it isn't suited for
    production purposes.

    It is fast since all data sets for CDI, IPCA, and Poupança are kept in primary memory. But isn't particularly
    clever. For a given date range, no matter how small or large it is, the index fetching methods will always scan the
    entire data sets.
    '''

    _ignore_cdi = [
        datetime.date(2018, 1, 1),   datetime.date(2018, 2, 12),  datetime.date(2018, 2, 13),  datetime.date(2018, 3, 30),  # NOQA
        datetime.date(2018, 5, 1),   datetime.date(2018, 5, 31),  datetime.date(2018, 9, 7),   datetime.date(2018, 10, 12), # NOQA
        datetime.date(2018, 11, 2),  datetime.date(2018, 11, 15), datetime.date(2018, 12, 25), datetime.date(2019, 1, 1),   # NOQA
        datetime.date(2019, 3, 4),   datetime.date(2019, 3, 5),   datetime.date(2019, 4, 19),  datetime.date(2019, 5, 1),   # NOQA
        datetime.date(2019, 6, 20),  datetime.date(2019, 11, 15), datetime.date(2019, 12, 25), datetime.date(2020, 1, 1),   # NOQA
        datetime.date(2020, 2, 24),  datetime.date(2020, 2, 25),  datetime.date(2020, 4, 10),  datetime.date(2020, 4, 21),  # NOQA
        datetime.date(2020, 5, 1),   datetime.date(2020, 6, 11),  datetime.date(2020, 9, 7),   datetime.date(2020, 10, 12), # NOQA
        datetime.date(2020, 11, 2),  datetime.date(2020, 12, 25), datetime.date(2021, 1, 1),   datetime.date(2021, 2, 15),  # NOQA
        datetime.date(2021, 2, 16),  datetime.date(2021, 4, 2),   datetime.date(2021, 4, 21),  datetime.date(2021, 6, 3),   # NOQA
        datetime.date(2021, 9, 7),   datetime.date(2021, 10, 12), datetime.date(2021, 11, 2),  datetime.date(2021, 11, 15), # NOQA
        datetime.date(2022, 2, 28),  datetime.date(2022, 3, 1),   datetime.date(2022, 4, 15),  datetime.date(2022, 4, 21),  # NOQA
        datetime.date(2022, 6, 16),  datetime.date(2022, 9, 7),   datetime.date(2022, 10, 12), datetime.date(2022, 11, 2),  # NOQA
        datetime.date(2022, 11, 15), datetime.date(2023, 2, 20),  datetime.date(2023, 2, 21),  datetime.date(2023, 4, 7),   # NOQA
        datetime.date(2023, 4, 21),  datetime.date(2023, 5, 1),   datetime.date(2023, 6, 8)                                 # NOQA
    ]

    # A repository of CDI indexes.
    _registry_cdi = [
        (datetime.date(2017, 12, 29), datetime.date(2018, 2, 7),   decimal.Decimal('0.026444')),  # NOQA
        (datetime.date(2018, 2, 8),   datetime.date(2018, 3, 21),  decimal.Decimal('0.025515')),  # NOQA
        (datetime.date(2018, 3, 22),  datetime.date(2018, 9, 28),  decimal.Decimal('0.024583')),  # NOQA
        (datetime.date(2018, 10, 1),  datetime.date(2019, 7, 31),  decimal.Decimal('0.024620')),  # NOQA
        (datetime.date(2019, 8, 1),   datetime.date(2019, 9, 18),  decimal.Decimal('0.022751')),  # NOQA
        (datetime.date(2019, 9, 19),  datetime.date(2019, 10, 30), decimal.Decimal('0.020872')),  # NOQA
        (datetime.date(2019, 10, 31), datetime.date(2019, 12, 11), decimal.Decimal('0.018985')),  # NOQA
        (datetime.date(2019, 12, 12), datetime.date(2020, 2, 5),   decimal.Decimal('0.017089')),  # NOQA
        (datetime.date(2020, 2, 6),   datetime.date(2020, 3, 18),  decimal.Decimal('0.016137')),  # NOQA
        (datetime.date(2020, 3, 19),  datetime.date(2020, 5, 6),   decimal.Decimal('0.014227')),  # NOQA
        (datetime.date(2020, 5, 7),   datetime.date(2020, 6, 17),  decimal.Decimal('0.011345')),  # NOQA
        (datetime.date(2020, 6, 18),  datetime.date(2020, 8, 5),   decimal.Decimal('0.008442')),  # NOQA
        (datetime.date(2020, 8, 6),   datetime.date(2021, 3, 17),  decimal.Decimal('0.007469')),  # NOQA
        (datetime.date(2021, 3, 18),  datetime.date(2021, 5, 5),   decimal.Decimal('0.010379')),  # NOQA
        (datetime.date(2021, 5, 6),   datetime.date(2021, 6, 16),  decimal.Decimal('0.013269')),  # NOQA
        (datetime.date(2021, 6, 17),  datetime.date(2021, 8, 4),   decimal.Decimal('0.016137')),  # NOQA
        (datetime.date(2021, 8, 5),   datetime.date(2021, 9, 22),  decimal.Decimal('0.019930')),  # NOQA
        (datetime.date(2021, 9, 23),  datetime.date(2021, 10, 27), decimal.Decimal('0.023687')),  # NOQA
        (datetime.date(2021, 10, 28), datetime.date(2021, 12, 8),  decimal.Decimal('0.029256')),  # NOQA
        (datetime.date(2021, 12, 9),  datetime.date(2022, 2, 2),   decimal.Decimal('0.034749')),  # NOQA
        (datetime.date(2022, 2, 3),   datetime.date(2022, 3, 16),  decimal.Decimal('0.040168')),  # NOQA
        (datetime.date(2022, 3, 17),  datetime.date(2022, 5, 4),   decimal.Decimal('0.043739')),  # NOQA
        (datetime.date(2022, 5, 5),   datetime.date(2022, 6, 15),  decimal.Decimal('0.047279')),  # NOQA
        (datetime.date(2022, 6, 17),  datetime.date(2022, 8, 3),   decimal.Decimal('0.049037')),  # NOQA
        (datetime.date(2022, 8, 4),   datetime.date(2022, 11, 14), decimal.Decimal('0.050788'))   # NOQA
    ]

    # A repository of IPCA indexes.
    _registry_ipca = [
        (datetime.date(2018, 1, 1),  decimal.Decimal('0.29')),  (datetime.date(2018, 2, 1),  decimal.Decimal('0.32')),  # NOQA
        (datetime.date(2018, 3, 1),  decimal.Decimal('0.09')),  (datetime.date(2018, 4, 1),  decimal.Decimal('0.22')),  # NOQA
        (datetime.date(2018, 5, 1),  decimal.Decimal('0.40')),  (datetime.date(2018, 6, 1),  decimal.Decimal('1.26')),  # NOQA
        (datetime.date(2018, 7, 1),  decimal.Decimal('0.33')),  (datetime.date(2018, 8, 1),  decimal.Decimal('-0.09')), # NOQA
        (datetime.date(2018, 9, 1),  decimal.Decimal('0.48')),  (datetime.date(2018, 10, 1), decimal.Decimal('0.45')),  # NOQA
        (datetime.date(2018, 11, 1), decimal.Decimal('-0.21')), (datetime.date(2018, 12, 1), decimal.Decimal('0.15')),  # NOQA
        (datetime.date(2019, 1, 1),  decimal.Decimal('0.32')),  (datetime.date(2019, 2, 1),  decimal.Decimal('0.43')),  # NOQA
        (datetime.date(2019, 3, 1),  decimal.Decimal('0.75')),  (datetime.date(2019, 4, 1),  decimal.Decimal('0.57')),  # NOQA
        (datetime.date(2019, 5, 1),  decimal.Decimal('0.13')),  (datetime.date(2019, 6, 1),  decimal.Decimal('0.01')),  # NOQA
        (datetime.date(2019, 7, 1),  decimal.Decimal('0.19')),  (datetime.date(2019, 8, 1),  decimal.Decimal('0.11')),  # NOQA
        (datetime.date(2019, 9, 1),  decimal.Decimal('-0.04')), (datetime.date(2019, 10, 1), decimal.Decimal('0.10')),  # NOQA
        (datetime.date(2019, 11, 1), decimal.Decimal('0.51')),  (datetime.date(2019, 12, 1), decimal.Decimal('1.15')),  # NOQA
        (datetime.date(2020, 1, 1),  decimal.Decimal('0.21')),  (datetime.date(2020, 2, 1),  decimal.Decimal('0.25')),  # NOQA
        (datetime.date(2020, 3, 1),  decimal.Decimal('0.07')),  (datetime.date(2020, 4, 1),  decimal.Decimal('-0.31')), # NOQA
        (datetime.date(2020, 5, 1),  decimal.Decimal('-0.38')), (datetime.date(2020, 6, 1),  decimal.Decimal('0.26')),  # NOQA
        (datetime.date(2020, 7, 1),  decimal.Decimal('0.36')),  (datetime.date(2020, 8, 1),  decimal.Decimal('0.24')),  # NOQA
        (datetime.date(2020, 9, 1),  decimal.Decimal('0.64')),  (datetime.date(2020, 10, 1), decimal.Decimal('0.86')),  # NOQA
        (datetime.date(2020, 11, 1), decimal.Decimal('0.89')),  (datetime.date(2020, 12, 1), decimal.Decimal('1.35')),  # NOQA
        (datetime.date(2021, 1, 1),  decimal.Decimal('0.25')),  (datetime.date(2021, 2, 1),  decimal.Decimal('0.86')),  # NOQA
        (datetime.date(2021, 3, 1),  decimal.Decimal('0.93')),  (datetime.date(2021, 4, 1),  decimal.Decimal('0.31')),  # NOQA
        (datetime.date(2021, 5, 1),  decimal.Decimal('0.83')),  (datetime.date(2021, 6, 1),  decimal.Decimal('0.53')),  # NOQA
        (datetime.date(2021, 7, 1),  decimal.Decimal('0.96')),  (datetime.date(2021, 8, 1),  decimal.Decimal('0.87')),  # NOQA
        (datetime.date(2021, 9, 1),  decimal.Decimal('1.16')),  (datetime.date(2021, 10, 1), decimal.Decimal('1.25')),  # NOQA
        (datetime.date(2021, 11, 1), decimal.Decimal('0.95')),  (datetime.date(2021, 12, 1), decimal.Decimal('0.73')),  # NOQA
        (datetime.date(2022, 1, 1),  decimal.Decimal('0.54')),  (datetime.date(2022, 2, 1),  decimal.Decimal('1.01')),  # NOQA
        (datetime.date(2022, 3, 1),  decimal.Decimal('1.62')),  (datetime.date(2022, 4, 1),  decimal.Decimal('1.06')),  # NOQA
        (datetime.date(2022, 5, 1),  decimal.Decimal('0.47')),  (datetime.date(2022, 6, 1),  decimal.Decimal('0.67')),  # NOQA
        (datetime.date(2022, 7, 1),  decimal.Decimal('-0.68')), (datetime.date(2022, 8, 1),  decimal.Decimal('-0.36')), # NOQA
        (datetime.date(2022, 9, 1),  decimal.Decimal('-0.29')), (datetime.date(2022, 10, 1), decimal.Decimal('0.59')),  # NOQA
        (datetime.date(2022, 11, 1), decimal.Decimal('0.41'))
    ]

    # A repository of Poupança indexes.
    _registry_savs = [
        (datetime.date(2018, 1, 1),  [decimal.Decimal(x) for x in ['0.3994'] * 28]),                                  # NOQA
        (datetime.date(2018, 2, 1),  [decimal.Decimal(x) for x in ['0.3994'] * 7 + ['0.3855'] * 21]),                 # NOQA
        (datetime.date(2018, 3, 1),  [decimal.Decimal(x) for x in ['0.3855'] * 21 + ['0.3715'] * 7]),                 # NOQA
        (datetime.date(2018, 4, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2018, 5, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2018, 6, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2018, 7, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2018, 8, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2018, 9, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2018, 10, 1), [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2018, 11, 1), [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2018, 12, 1), [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2019, 1, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2019, 2, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2019, 3, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2019, 4, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2019, 5, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2019, 6, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2019, 7, 1),  [decimal.Decimal(x) for x in ['0.3715'] * 28]),                                  # NOQA
        (datetime.date(2019, 8, 1),  [decimal.Decimal(x) for x in ['0.3434'] * 28]),                                  # NOQA
        (datetime.date(2019, 9, 1),  [decimal.Decimal(x) for x in ['0.3434'] * 18 + ['0.3153'] * 10]),                # NOQA
        (datetime.date(2019, 10, 1), [decimal.Decimal(x) for x in ['0.3153'] * 28]),                                  # NOQA
        (datetime.date(2019, 11, 1), [decimal.Decimal(x) for x in ['0.2871'] * 28]),                                  # NOQA
        (datetime.date(2019, 12, 1), [decimal.Decimal(x) for x in ['0.2871'] * 11 + ['0.2588'] * 17]),                # NOQA
        (datetime.date(2020, 1, 1),  [decimal.Decimal(x) for x in ['0.2588'] * 28]),                                  # NOQA
        (datetime.date(2020, 2, 1),  [decimal.Decimal(x) for x in ['0.2588'] * 5 + ['0.2446'] * 23]),                 # NOQA
        (datetime.date(2020, 3, 1),  [decimal.Decimal(x) for x in ['0.2446'] * 18 + ['0.2162'] * 10]),                # NOQA
        (datetime.date(2020, 4, 1),  [decimal.Decimal(x) for x in ['0.2162'] * 28]),                                  # NOQA
        (datetime.date(2020, 5, 1),  [decimal.Decimal(x) for x in ['0.2162'] * 6 + ['0.1733'] * 22]),                 # NOQA
        (datetime.date(2020, 6, 1),  [decimal.Decimal(x) for x in ['0.1733'] * 17 + ['0.1303'] * 21]),                # NOQA
        (datetime.date(2020, 7, 1),  [decimal.Decimal(x) for x in ['0.1303'] * 28]),                                  # NOQA
        (datetime.date(2020, 8, 1),  [decimal.Decimal(x) for x in ['0.1303'] * 5 + ['0.1159'] * 23]),                 # NOQA
        (datetime.date(2020, 9, 1),  [decimal.Decimal(x) for x in ['0.1159'] * 28]),                                  # NOQA
        (datetime.date(2020, 10, 1), [decimal.Decimal(x) for x in ['0.1159'] * 28]),                                  # NOQA
        (datetime.date(2020, 11, 1), [decimal.Decimal(x) for x in ['0.1159'] * 28]),                                  # NOQA
        (datetime.date(2020, 12, 1), [decimal.Decimal(x) for x in ['0.1159'] * 28]),                                  # NOQA
        (datetime.date(2021, 1, 1),  [decimal.Decimal(x) for x in ['0.1159'] * 28]),                                  # NOQA
        (datetime.date(2021, 2, 1),  [decimal.Decimal(x) for x in ['0.1159'] * 28]),                                  # NOQA
        (datetime.date(2021, 3, 1),  [decimal.Decimal(x) for x in ['0.1159'] * 17 + ['0.1590'] * 11]),                # NOQA
        (datetime.date(2021, 4, 1),  [decimal.Decimal(x) for x in ['0.1590'] * 28]),                                  # NOQA
        (datetime.date(2021, 5, 1),  [decimal.Decimal(x) for x in ['0.1590'] * 5 + ['0.2019'] * 23]),                 # NOQA
        (datetime.date(2021, 6, 1),  [decimal.Decimal(x) for x in ['0.2019'] * 16 + ['0.2446'] * 12]),                # NOQA
        (datetime.date(2021, 7, 1),  [decimal.Decimal(x) for x in ['0.2446'] * 28]),                                  # NOQA
        (datetime.date(2021, 8, 1),  [decimal.Decimal(x) for x in ['0.2446'] * 4 + ['0.3012'] * 24]),                 # NOQA
        (datetime.date(2021, 9, 1),  [decimal.Decimal(x) for x in ['0.3012'] * 22 + ['0.3575'] * 6]),                 # NOQA
        (datetime.date(2021, 10, 1), [decimal.Decimal(x) for x in ['0.3575'] * 27 + ['0.4412']]),                     # NOQA
        (datetime.date(2021, 11, 1), [decimal.Decimal(x) for x in ['0.4412'] * 15 + [
                                                                   '0.4556', '0.4578', '0.4586', '0.4412', '0.4412',  # NOQA
                                                                   '0.4412', '0.4570', '0.4583', '0.4607', '0.4620',
                                                                   '0.4412', '0.4412', '0.4412']]),
        (datetime.date(2021, 12, 1), [decimal.Decimal(x) for x in ['0.4902', '0.4739', '0.4572', '0.4626', '0.4890',
                                                                   '0.5154', '0.5249', '0.5237', '0.5655', '0.5438',
                                                                   '0.5471', '0.5732', '0.5992', '0.6029', '0.6042',
                                                                   '0.5839', '0.5500', '0.5539', '0.5900', '0.6162',
                                                                   '0.6201', '0.6147', '0.5910', '0.5691', '0.5739',
                                                                   '0.6002', '0.6265', '0.6319']]),
        (datetime.date(2022, 1, 1),  [decimal.Decimal(x) for x in ['0.5608', '0.5872', '0.6138', '0.6158', '0.6146',  # NOQA
                                                                   '0.5908', '0.5660', '0.5677', '0.5946', '0.6215',
                                                                   '0.6249', '0.6255', '0.6000', '0.5751', '0.5764',
                                                                   '0.6036', '0.6310', '0.6324', '0.6340', '0.6107',
                                                                   '0.5845', '0.5877', '0.6156', '0.6435', '0.6443',
                                                                   '0.6371', '0.6119', '0.5480']]),
        (datetime.date(2022, 2, 1),  [decimal.Decimal(x) for x in ['0.5000'] * 28]),                                  # NOQA
        (datetime.date(2022, 3, 1),  [decimal.Decimal(x) for x in ['0.5976', '0.6304', '0.5997', '0.5673', '0.5779',  # NOQA
                                                                   '0.6017', '0.6355', '0.6393', '0.6422', '0.6129',
                                                                   '0.5855', '0.5938', '0.6274', '0.6513', '0.6559',
                                                                   '0.6260', '0.6063', '0.5748', '0.5762', '0.6095',
                                                                   '0.6329', '0.6021', '0.6046', '0.5839', '0.5512',
                                                                   '0.5524', '0.5856', '0.6089']]),
        (datetime.date(2022, 4, 1),  [decimal.Decimal(x) for x in ['0.5558', '0.5243', '0.5577', '0.5809', '0.5805',  # NOQA
                                                                   '0.5822', '0.5842', '0.5614', '0.5325', '0.5661',
                                                                   '0.5898', '0.5924', '0.5937', '0.5933', '0.5598',
                                                                   '0.5598', '0.5938', '0.6277', '0.6286', '0.6308',
                                                                   '0.6309', '0.6309', '0.5973', '0.6215', '0.6557',
                                                                   '0.6546', '0.6576', '0.6617']]),
        (datetime.date(2022, 5, 1),  [decimal.Decimal(x) for x in ['0.6671', '0.6919', '0.6914', '0.6947', '0.6646',  # NOQA
                                                                   '0.6408', '0.6411', '0.6660', '0.7011', '0.7013',
                                                                   '0.7033', '0.6672', '0.6414', '0.6425', '0.6674',
                                                                   '0.7025', '0.6692', '0.6697', '0.6441', '0.6084',
                                                                   '0.6067', '0.6418', '0.6667', '0.6724', '0.6719',
                                                                   '0.6462', '0.6112', '0.6118']]),
        (datetime.date(2022, 6, 1),  [decimal.Decimal(x) for x in ['0.6491', '0.6519', '0.6162', '0.5828', '0.6195',  # NOQA
                                                                   '0.6462', '0.6491', '0.6509', '0.6520', '0.6260',
                                                                   '0.5950', '0.6218', '0.6588', '0.6602', '0.6652',
                                                                   '0.6643', '0.6643', '0.6279', '0.6648', '0.6917',
                                                                   '0.6933', '0.6924', '0.6929', '0.6676', '0.6332',
                                                                   '0.6701', '0.6972', '0.6972']]),
        (datetime.date(2022, 7, 1),  [decimal.Decimal(x) for x in ['0.6639', '0.6643', '0.7013', '0.7284', '0.7281',  # NOQA
                                                                   '0.7278', '0.7008', '0.6642', '0.6659', '0.7031',
                                                                   '0.7303', '0.7307', '0.7324', '0.7058', '0.6696',
                                                                   '0.6710', '0.7083', '0.7358', '0.7373', '0.7372',
                                                                   '0.7100', '0.6724', '0.6730', '0.7105', '0.7381',
                                                                   '0.7385', '0.7386', '0.7132']]),
        (datetime.date(2022, 8, 1),  [decimal.Decimal(x) for x in ['0.7421', '0.7420', '0.7432', '0.7083', '0.6804',  # NOQA
                                                                   '0.6810', '0.7088', '0.7088', '0.7075', '0.7075',
                                                                   '0.6798', '0.6521', '0.6526', '0.6803', '0.7082',
                                                                   '0.7084', '0.7086', '0.6793', '0.6524', '0.6524',
                                                                   '0.6801', '0.7079', '0.7087', '0.7087', '0.6809',
                                                                   '0.6527', '0.6430', '0.6808']]),
        (datetime.date(2022, 9, 1),  [decimal.Decimal(x) for x in ['0.6814', '0.6432', '0.6152', '0.6430', '0.6809',  # NOQA
                                                                   '0.6809', '0.6817', '0.7097', '0.6818', '0.6440',
                                                                   '0.6819', '0.7097', '0.6819', '0.6830', '0.6835',
                                                                   '0.6470', '0.6198', '0.6477', '0.6859', '0.6850',
                                                                   '0.6845', '0.6824', '0.6512', '0.6142', '0.6520',
                                                                   '0.6797', '0.6779', '0.6777']]),
        (datetime.date(2022, 10, 1), [decimal.Decimal(x) for x in ['0.6501', '0.6778', '0.6778', '0.6789', '0.6796',
                                                                   '0.6520', '0.6136', '0.6137', '0.6514', '0.6790',
                                                                   '0.6811', '0.6798', '0.6798', '0.6516', '0.6515',
                                                                   '0.6515', '0.6791', '0.6789', '0.6794', '0.6513',
                                                                   '0.6143', '0.6147', '0.6524', '0.6801', '0.6794',
                                                                   '0.6791', '0.6516', '0.6136']]),
        (datetime.date(2022, 11, 1), [decimal.Decimal(x) for x in ['0.6515', '0.6515', '0.6792', '0.6519', '0.6139',
                                                                   '0.6516', '0.6793', '0.6799', '0.6801', '0.6796'] + ['0.6448'] * 18])  # As 17 taxas finais são estimadas.
    ]

    @typeguard.typechecked
    def get_cdi_indexes(self, begin: datetime.date, end: datetime.date) -> t.Iterable[DailyIndex]:
        if self._registry_cdi and self._registry_cdi[0] and begin >= self._registry_cdi[0][0] and end >= begin:
            dzro = self._registry_cdi[0][0]
            save = self._registry_cdi[0][2]

            for dzro, done, value in self._registry_cdi:
                while dzro <= done:
                    if dzro <= end:
                        save = value

                    if begin <= dzro <= end and dzro.weekday() < 5 and dzro not in self._ignore_cdi:
                        yield DailyIndex(date=dzro, value=value)

                    dzro += datetime.timedelta(days=1)

            while dzro <= end:
                if dzro >= begin and dzro.weekday() < 5 and dzro not in self._ignore_cdi:
                    yield DailyIndex(date=dzro, value=save)

                dzro += datetime.timedelta(days=1)

        elif self._registry_cdi and self._registry_cdi[0] and begin >= self._registry_cdi[0][0]:
            raise ValueError('the initial date must be greater than, or equal to, the end date')

        elif self._registry_cdi and self._registry_cdi[0]:
            raise ValueError('this backend cannot provide CDI indexes prior to 2018-01-01')

        else:
            raise ValueError('this backend has no CDI indexes')

    # FIXME: this method attempts to simulate the behaviour of the BACEN API. But the API is flawed. For a monthly
    # index, It can't even properly represent months, using their first days to represent them. For example,
    # "2018-01-01" represents January of 2018. Why not use simply "2018-01"???
    #
    # I do not think that fincore data structures, like MonthlyIndex, should expose these flaws internally. It should
    # be designed to best suit its use by this module.
    #
    @typeguard.typechecked
    def get_ipca_indexes(self, begin: datetime.date, end: datetime.date) -> t.Iterable[MonthlyIndex]:
        if self._registry_ipca and self._registry_ipca[0]:
            month = self._registry_ipca[0][0]

            for month, value in self._registry_ipca:
                if begin <= month <= end:
                    yield MonthlyIndex(date=month, value=value)

            while month < end:
                month += _MONTH

                yield MonthlyIndex(date=month, value=_0)

        else:
            raise ValueError('this backend has no IPCA indexes')

    # FIXME: this method simulates the behaviour of the BACEN API. But the API is pretty dumb. It returns redundant data,
    # like "2018-01-01" to represent January of 2018.
    #
    @typeguard.typechecked
    def get_savings_indexes(self, begin: datetime.date, end: datetime.date) -> t.Iterable[RangedIndex]:
        if self._registry_savs and self._registry_savs[0]:
            for d0, values in self._registry_savs:
                i, d = 0, d0

                while i < 28:
                    if begin <= d <= end:
                        yield RangedIndex(begin_date=d, end_date=d + _MONTH, value=values[i])

                    d += datetime.timedelta(days=1)
                    i += 1

        else:
            raise ValueError('this backend has no savings indexes')

@dataclasses.dataclass(frozen=True, eq=True)
class VariableIndex:
    code: t.Union[_VR_INDEX, _PL_INDEX] = 'CDI'

    percentage: int = 100

    backend: IndexStorageBackend = dataclasses.field(default=InMemoryBackend(), compare=False)
# }}}

# Public API, payments table. {{{
@typeguard.typechecked
def get_payments_table(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    amortizations: t.List[Amortization | Amortization.Bare], *,
    vir: t.Optional[VariableIndex] = None,
    capitalisation: _CAPITALISATION = '360',
    calc_date: t.Optional[CalcDate] = None,
    tax_exempt: t.Optional[bool] = False,
    gain_output: _GAIN_OUTPUT_MODE = 'current'
) -> t.Iterable[Payment]:
    '''
    Gera uma tabela de pagamentos para um determinado empréstimo.

    Para saber como invocar essa função, tome como base a frase abaixo.

      “ Retorne os pagamentos um empréstimo em um valor V, a uma taxa anual TA, nas datas D. ”

    Dessa elaboração saem os três parâmetros obrigatórios e posicionais dessa rotina:

      • "principal", é o valor principal do empréstimo, ou V.

      • "apy", é a taxa nominal anual de spread TA (annual percentage yield).

      • "amortizations", que é uma lista contendo as datas D em que amortizações devem ser realizadas.

    Os demais parâmetros são associativos.

      • "vir", é um índice variável, que pode ser de juros: CDI, ou Poupança; ou de correção monetária: IPCA, ou IGPM.
        Quando informado, os pagamentos retornados pela rotina vão incorrer, além da taxa fixa, "apy", de uma taxa
        variável que será computada de acordo com o valor do índice no período. Deve ser uma instância de
        VariableIndex. Se omitido, a taxa de juros será fixa.

      • "capitalisation", configura uma dentre quatro formas de composição dos juros.

        – "360" é a capitalização de juros diária em ano tem 360 dias corridos. Usada em operações pré-fixadas com
          modalidade Bullet.

        – "30/360" é a capitalização mensal em ano de 12 meses com 30 dias corridos. Usada em operações pré-fixadas com
          modalidade Juros mensais, Price, ou Livre.

        – "252" é a capitalização de juros em ano de 252 dias úteis. Usada em operações pós-fixadas CDI com quaisquer
          modalidade Bullet, Juros mensais, ou Livre.

        – "365" é a capitalização de juros em ano de 365 dias corridos. Esse modo não deve ser usado. Serve apenas
          para emular operações Bullet obsoletas, que adotaram essa forma de composição no passado. O Fincore vai
          emitir um aviso se esse modo for solicitado.

      • "calc_date", é uma data de corte para o cálculo dos pagamentos. Pagamentos posteriores à data informada não serão
        emitidos. Útil para saber a posição de um empréstimo em uma determinada data. Evita que pagamentos desnecessários
        sejam calculados.

      • "tax_exempt", quando verdadeiro, indica que os pagamentos são isentos de imposto de renda.

    • "gain_output", é o modo de saída para os juros.

        – "current" é o modo padrão. Faz com que, para cada pagamento P, apenas os juros incorridos no período entre o
          pagamento anterior e o atual sejam retornados.

        – "settled" faz com que, para cada pagamento P, os juros a serem pagos pelo devedor sejam retornados. Lembrar que
          os juros a serem pagos não são necessariamente iguais aos juros incorridos no período. Se houver carência, um
          determinado pagamento pode não ter acerto de juros. Ou um pagamento posterior a um período de carência pode
          apresentar um componente de juros acumulados, além do que incorreu no período.

        – "deferred" faz com que o juro acumulado no período atual, somado ao acumulado de períodos anteriores, seja
          retornado.

    Retorna uma lista em que cada objeto P contém as informações de um pagamento: sua data, o valor bruto a ser pago, o
    imposto, o valor líquido, o valor de amortização do principal, o valor dos juros etc. É uma instância de Payment,
    para operações sem correção monetária; ou de PriceAdjustedPayment, para operações corrigidas. Vide documentação
    dessas classes para maiores detalhes sobre essas estruturas de dados.
    '''

    def calc_balance() -> decimal.Decimal:
        val = principal * f_c + regs.interest.accrued - regs.principal.amortized.total * f_c - regs.interest.settled.total

        return t.cast(decimal.Decimal, val)

    # Primeiro gerador para valores de principal.
    #
    #  • "principal.amortization_ratio.current", é o percentual de amortização do período corrente.
    #  • "principal.amortized.current", é o valor amortizado no período corrente.
    #  • "principal.amortized.total", é o valor amortizado total (período corrente somado aos passados).
    #
    def track_principal_1() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            ratio = yield

            # Se o percentual de amortização atual somado ao acumulado ultrapassar 100%, um reajuste deve ser feito.
            if regs.principal.amortization_ratio.current + ratio > _1:
                ratio = _1 - regs.principal.amortization_ratio.current

            if ratio:
                regs.principal.amortization_ratio.current += ratio
                regs.principal.amortized = types.SimpleNamespace(current=ratio * principal, total=regs.principal.amortization_ratio.current * principal)

            else:
                regs.principal.amortized = types.SimpleNamespace(current=_0, total=regs.principal.amortized.total)

    # Segundo gerador para valores de principal.
    #
    #  • "principal.amortization_ratio.regular", é o percentual de amortização regular acumulado (período corrente somado a passados)
    #
    def track_principal_2() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            ratio = yield

            # Se o percentual de amortização regular somado ao acumulado ultrapassar 100%, um reajuste deve ser feito.
            if regs.principal.amortization_ratio.regular + ratio > _1:
                ratio = _1 - regs.principal.amortization_ratio.regular

            if ratio:
                regs.principal.amortization_ratio.regular += ratio

    # Gerador para valores de juros.
    #
    #   • "interest.current" são os juros incorridos (produzidos) no período corrente.
    #   • "interest.accrued" é o total de juros acumulado desde o dia zero do cronograma de pagamentos.
    #   • "interest.deferred" é o total de juros em aberto de períodos passados.
    #
    def track_interest_1() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            regs.interest.current = yield
            regs.interest.accrued += regs.interest.current
            regs.interest.deferred = regs.interest.accrued - (regs.interest.current + regs.interest.settled.total)

    # Gerador para valores de juros acertados entre devedor e credor.
    #
    #   • "interest.settled.current" são os juros acertados no período corrente.
    #   • "interest.settled.total" é o total de juros acertados desde o dia zero do cronograma de pagamentos.
    #
    def track_interest_2() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            regs.interest.settled = types.SimpleNamespace(current=(yield), total=regs.interest.settled.total)
            regs.interest.settled.total += regs.interest.settled.current

    # A. Valida e prepara para execução.
    gens = types.SimpleNamespace()
    regs = types.SimpleNamespace()
    aux = _0

    if principal == _0:
        return

    if principal < _CENTI:
        raise ValueError('principal value should be at least 0.01')

    if len(amortizations) < 2:
        raise ValueError('at least two amortizations are required: the start of the schedule, and its end')

    elif not vir and capitalisation == '252':
        raise ValueError('fixed interest rates should not use the 252 working days capitalisation')

    elif vir and vir.code == 'CDI' and capitalisation != '252':
        raise ValueError('CDI should use the 252 working days capitalisation')

    for i, x in enumerate(amortizations):
        if type(x) is Amortization:
            aux += x.amortization_ratio

        if vir and vir.code not in t.get_args(_PL_INDEX) and type(x) is Amortization and x.price_level_adjustment:
            raise TypeError(f"amortization {i} has price level adjustment, but either a variable index wasn't provided or it isn't IPCA nor IGPM")

        elif aux > _1 and not math.isclose(aux, _1):
            raise ValueError('the accumulated percentage of the amortizations overflows 1.0')

    if not math.isclose(aux, _1):
        raise ValueError('the accumulated percentage of the amortizations does not reach 1.0')

    if calc_date is None:
        calc_date = CalcDate(value=amortizations[-1].date, runaway=False)

    # Registradores.
    regs.interest = types.SimpleNamespace(current=_0, accrued=_0, settled=types.SimpleNamespace(current=_0, total=_0), deferred=_0)
    regs.principal = types.SimpleNamespace(amortization_ratio=types.SimpleNamespace(current=_0, regular=_0), amortized=types.SimpleNamespace(current=_0, total=_0))

    # Control, create generators.
    gens.interest_tracker_1 = track_interest_1()
    gens.interest_tracker_2 = track_interest_2()
    gens.principal_tracker_1 = track_principal_1()
    gens.principal_tracker_2 = track_principal_2()

    # Control, start generators.
    gens.principal_tracker_1.send(None)
    gens.principal_tracker_2.send(None)
    gens.interest_tracker_1.send(None)
    gens.interest_tracker_2.send(None)

    # B. Executa.
    for num, (ent0, ent1) in enumerate(itertools.pairwise(amortizations), 1):
        due = min(calc_date.value, ent1.date)
        f_s = f_c = _1

        # Fase B.0, FZA, ou Fase Zille-Anna.
        #
        #  • Calcula FS (fator de spread) para índice pré-fixado; e ambos FS e FC para índice de correção.
        #  • Calcula FS para índice pós-fixado (CDI, Poupança etc). Nesse caso não há correção.
        #
        if ent0.date < calc_date.value or ent1.date <= calc_date.value:
            if not vir and capitalisation == '360':  # Bullet.
                f_s = calculate_interest_factor(apy, decimal.Decimal((due - ent0.date).days) / decimal.Decimal(360))

            elif not vir and capitalisation == '365':  # Bullet in legacy mode.
                f_s = calculate_interest_factor(apy, decimal.Decimal((due - ent0.date).days) / decimal.Decimal(365))

            elif not vir and capitalisation == '30/360':  # Juros mensais, Price, Livre.
                dcp = (due - ent0.date).days
                dct = (ent1.date - ent0.date).days

                # Exclusivamente para a primeira data de aniversário o "DCT" será considerado como a diferença em
                # dias corridos entre o dia 24 anterior e o dia 24 posterior à data de integralização (início do
                # rendimento).
                #
                if ent1.dct_override and num == 1:
                    dct = _diff_surrounding_dates(ent0.date, 24)

                # Quando existirem entradas extraordinárias de adiantamento no plano, o "DCT" será calculado
                # utilizando as datas do fluxo regular.
                #
                elif ent1.dct_override:
                    dct = (ent1.dct_override.date_to - ent1.dct_override.date_from).days

                    if ent1.dct_override.predates_first_amortization:
                        dct = _diff_surrounding_dates(ent1.dct_override.date_from, 24)

                if ent0.dct_override:
                    dct = (ent1.date - ent0.dct_override.date_from).days

                    if ent0.dct_override.predates_first_amortization:
                        dct = _diff_surrounding_dates(ent0.dct_override.date_from, 24)

                f_s = calculate_interest_factor(apy, decimal.Decimal(dcp) / (12 * decimal.Decimal(dct)))

            elif vir and vir.code == 'CDI' and capitalisation == '252':  # Bullet, Juros mensais, Livre.
                f_v = vir.backend.calculate_cdi_factor(ent0.date, due, vir.percentage)  # Taxa (ou fator) variável, FV.
                f_s = calculate_interest_factor(apy, decimal.Decimal(f_v.amount) / decimal.Decimal(252)) * f_v.value

            elif vir and vir.code == 'Poupança' and capitalisation == '360':  # Poupança só suportada em Bullet.
                f_v = vir.backend.calculate_savings_factor(ent0.date, due, vir.percentage)  # Taxa (ou fator) variável, FV.
                f_s = calculate_interest_factor(apy, decimal.Decimal((due - ent0.date).days) / decimal.Decimal(360)) * f_v.value

            elif vir and vir.code == 'IPCA' and capitalisation == '360':  # Bullet.
                f_s = calculate_interest_factor(apy, decimal.Decimal((due - ent0.date).days) / decimal.Decimal(360))

                if type(ent1) is Amortization and ent1.price_level_adjustment:
                    kw1a: t.Dict[str, t.Any] = {}

                    kw1a['base'] = ent1.price_level_adjustment.base_date
                    kw1a['period'] = ent1.price_level_adjustment.period
                    kw1a['shift'] = ent1.price_level_adjustment.shift
                    kw1a['ratio'] = _1  # Ajuste para a última taxa de correção.

                    # Trava o fator de correção. O fator mínimo é um, ou seja, o valor da correção tem que ser positivo.
                    f_c = max(vir.backend.calculate_ipca_factor(**kw1a), _1)

                # Na antecipação a correção monetária tem que ser paga ("ent1" nem tem o atributo "price_level_adjustment").
                elif type(ent1) is Amortization.Bare:
                    kw1b: t.Dict[str, t.Any] = {}

                    kw1b['base'] = amortizations[0].date.replace(day=1)
                    kw1b['period'] = _delta_months(ent1.date, amortizations[0].date)
                    kw1b['shift'] = 'M-1'  # FIXME.
                    kw1b['ratio'] = _1  # Ajuste para a última taxa de correção.

                    # Trava o fator de correção. O fator mínimo é um, ou seja, o valor da correção tem que ser positivo.
                    f_c = max(vir.backend.calculate_ipca_factor(**kw1b), _1)

            elif vir and vir.code == 'IPCA' and capitalisation == '30/360':  # Juros mensais e Livre.
                dcp = (due - ent0.date).days
                dct = (ent1.date - ent0.date).days

                # Exclusivamente para a primeira data de aniversário o "DCT" será considerado como a diferença em
                # dias corridos entre o dia 24 anterior e o dia 24 posterior à data de integralização (início do
                # rendimento).
                #
                if ent1.dct_override and num == 1:
                    dct = _diff_surrounding_dates(ent0.date, 24)

                # Quando existirem entradas extraordinárias de adiantamento no plano, o "DCT" será calculado
                # utilizando as datas do fluxo regular.
                #
                elif ent1.dct_override:
                    dct = (ent1.dct_override.date_to - ent1.dct_override.date_from).days

                    if ent1.dct_override.predates_first_amortization:
                        dct = _diff_surrounding_dates(ent1.dct_override.date_from, 24)

                if ent0.dct_override:
                    dct = (ent1.date - ent0.dct_override.date_from).days

                    if ent0.dct_override.predates_first_amortization:
                        dct = _diff_surrounding_dates(ent0.dct_override.date_from, 24)

                f_s = calculate_interest_factor(apy, decimal.Decimal(dcp) / (12 * decimal.Decimal(dct)))

                if type(ent1) is Amortization.Bare or type(ent1) is Amortization and ent1.price_level_adjustment:
                    kw2: t.Dict[str, t.Any] = {}
                    dcp = (due - ent0.date).days  # Spec "30/360" needs a ratio for the IPCA factor.
                    dct = (ent1.date - ent0.date).days

                    if type(ent1) is Amortization and ent1.price_level_adjustment:
                        kw2['base'] = ent1.price_level_adjustment.base_date
                        kw2['period'] = ent1.price_level_adjustment.period
                        kw2['shift'] = ent1.price_level_adjustment.shift
                        kw2['ratio'] = _1  # Ajuste para a última taxa de correção.

                    else:
                        kw2['base'] = amortizations[0].date.replace(day=1)
                        kw2['period'] = _delta_months(ent1.date, amortizations[0].date)
                        kw2['shift'] = 'M-1'  # FIXME.
                        kw2['ratio'] = _1  # Ajuste para a última taxa de correção.

                    # Exclusivamente para a primeira data de aniversário o "DCT" será considerado como a diferença
                    # em dias corridos entre os dias 24 anterior e posterior à data de início do rendimento.
                    #
                    if ent1.dct_override and num == 1:
                        dct = _diff_surrounding_dates(ent0.date, 24)

                    # Quando existirem entradas extraordinárias de adiantamento no plano, o "DCT" será calculado
                    # utilizando as datas do fluxo regular.
                    #
                    elif ent1.dct_override:
                        dct = (ent1.dct_override.date_to - ent1.dct_override.date_from).days

                        if ent1.dct_override.predates_first_amortization:
                            dct = _diff_surrounding_dates(ent1.dct_override.date_from, 24)

                    if ent0.dct_override:
                        dct = (ent1.date - ent0.dct_override.date_from).days

                        if ent0.dct_override.predates_first_amortization:
                            dct = _diff_surrounding_dates(ent0.dct_override.date_from, 24)

                    kw2['ratio'] = decimal.Decimal(dcp) / decimal.Decimal(dct)

                    f_c = max(vir.backend.calculate_ipca_factor(**kw2), _1)  # Trava o fator de correção.

            elif vir:
                raise NotImplementedError(f'Combination of variable interest rate {vir} and capitalisation {capitalisation} unsupported')

            else:
                raise NotImplementedError(f'Unsupported capitalisation {capitalisation} for fixed interest rate')

        # Fase B.1, FRU, ou Fase Rafa Um.
        #
        # Usando os fatores calculados na fase anterior, calcula e registra as variações de principal, juros e correção
        # monetária.
        #
        # [FATOR-AJUSTE]
        #
        # A inserção de uma antecipação parcial na montagem do cronograma faz com que os percentuais de amortização do
        # principal posteriores à essa antecipação precisem ser atualizados. Essa atualização é feita de forma que o
        # novo percentual de amortização (Pn), de uma prestação arbitrária, deve ser igual ao percentual antigo (Pa)
        # multiplicado por um fator de ajuste (ADJ).
        #
        #                                                  ACUR
        #                                          ADJ = ————————
        #                                                  AREG
        #
        # Em que ACUR é o percentual de amortização restante do fluxo de pagamentos, em cima do principal e incluindo
        # as amortizações extraordinárias (antecipações), e AREG é o percentual de amortização restante do fluxo de
        # pagamentos ordinário.
        #
        if ent0.date < calc_date.value or ent1.date <= calc_date.value or calc_date.runaway:
            # Registra o valor do juros incorrido no período.
            gens.interest_tracker_1.send(calc_balance() * (f_s - _1))

            # Registra a correção do período (FIXME: implementar).
            # gens.price_level_tracker_1.send(…)

            # Caso de uma amortização regular.
            if type(ent1) is Amortization:
                adj = (_1 - regs.principal.amortization_ratio.current) / (_1 - regs.principal.amortization_ratio.regular)  # [FATOR-AJUSTE].

                # Registra o percentual de amortização do principal.
                gens.principal_tracker_1.send(ent1.amortization_ratio * adj)

                # Registra o percentual regular de amortização do principal.
                gens.principal_tracker_2.send(ent1.amortization_ratio)

                # Registra o valor de juros a pagar no período.
                if ent1.amortizes_interest:
                    gens.interest_tracker_2.send(regs.interest.current + regs.principal.amortization_ratio.current * regs.interest.deferred)

                # Registra o valor de correção a pagar no período (FIXME: implementar).
                # gens.price_level_tracker_2.send(…)

            # Caso de um adiantamento (amortização extraordinária).
            #
            # Lembre-se que um adiantamento apresenta apenas um valor bruto que será pago em uma determinada data. Esse
            # valor bruto será fatorado em diversos componentes da dívida, de forma ordenada. O primeiro componente da
            # dívida a ser amortizado é o juro (spread). Após o pagamento dos juros, o que sobra deve ser deduzido da
            # correção monetária. Finalmente, abate-se o valor restante do principal. No bloco de código abaixo,
            #
            #  • "val1" é o valor de juros a pagar.
            #
            #  • "val2" é o valor da correção a pagar. FIXME: a variável "plfv" deveria ser multiplicada pelo
            #    percentual de amortização do principal do período, e não pelo decimal um.
            #
            #  • "val3" é o valor a amortizar do principal.
            #
            # Observe que a ordem de cálculo dessas variáveis corresponde à ordem de fatoração do valor bruto da
            # antecipação.
            #
            else:
                ent1 = t.cast(Amortization.Bare, ent1)  # O Mypy não consegue inferir o tipo da variável "ent1" aqui.
                plfv = principal * (_1 - regs.principal.amortization_ratio.current) * (f_c - _1)  # Price level, full value.
                val0 = min(ent1.value, calc_balance())
                val1 = min(val0, regs.interest.accrued - regs.interest.settled.total)
                val2 = min(val0 - val1, plfv * _1)
                val3 = val0 - val1 - val2

                # Verifica se o valor do pagamento irregular não ultrapassa o saldo em aberto.
                if ent1.value != Amortization.Bare.MAX_VALUE and ent1.value > _Q(calc_balance()):
                    raise Exception(f'the value of the amortization, {ent1.value}, is greater than the remaining balance of the loan, {_Q(calc_balance())}')

                # Registra o percentual de amortização do principal.
                gens.principal_tracker_1.send(val3 / principal)

                # Registra o valor de juros a pagar no período.
                gens.interest_tracker_2.send(val1)

                # Registra o valor de correção a pagar no período (FIXME: implementar).
                # gens.price_level_tracker_2.send(val2)

        # Fase B.2, FRD, ou Fase Rafa Dois.
        #
        # Monta a instância do pagamento, saída da rotina. Faz arredondamentos.
        #
        if ent0.date < calc_date.value or ent1.date <= calc_date.value or calc_date.runaway:
            pmt = PriceAdjustedPayment() if vir and vir.code == 'IPCA' else Payment()

            # B.2.1. Monta o pagamento (PMT).
            pmt.no = num
            pmt.date = ent1.date

            if type(ent1) is Amortization:
                pmt.amort = regs.principal.amortized.current

                if gain_output == 'deferred':
                    pmt.gain = regs.interest.deferred + regs.interest.current

                elif gain_output == 'settled':
                    pmt.gain = regs.interest.settled.current if ent1.amortizes_interest else _0

                else:  # Implies "gain_output == 'current'."
                    pmt.gain = regs.interest.current

                pmt.bal = calc_balance()

                # Amortiza principal, não incorpora juros.
                if pmt.amort and ent1.amortizes_interest:
                    pmt.raw = pmt.amort + (j_f := regs.interest.settled.current if ent1.amortizes_interest else _0)
                    pmt.tax = j_f * calculate_revenue_tax(amortizations[0].date, due)

                # Amortiza principal, incorpora juros.
                elif pmt.amort:
                    pmt.raw = pmt.amort
                    pmt.tax = _0

                # Não amortiza principal, não incorpora juros.
                elif ent1.amortizes_interest:
                    pmt.raw = j_f = regs.interest.settled.current if ent1.amortizes_interest else _0
                    pmt.tax = j_f * calculate_revenue_tax(amortizations[0].date, due)

                # Não amortiza principal, incorpora juros.
                else:
                    pmt.raw = _0
                    pmt.tax = _0

            else:
                pmt.amort = regs.principal.amortized.current

                if gain_output == 'deferred':
                    pmt.gain = regs.interest.deferred + regs.interest.current

                elif gain_output == 'settled':
                    pmt.gain = regs.interest.settled.current

                else:  # Implies "gain_output == 'current'."
                    pmt.gain = regs.interest.current

                pmt.bal = calc_balance()
                pmt.raw = pmt.amort + (j_f := regs.interest.settled.current)
                pmt.tax = j_f * calculate_revenue_tax(amortizations[0].date, due)

            # Aplica a correção no bruto e no I.R.
            if vir and vir.code == 'IPCA':
                pmt = t.cast(PriceAdjustedPayment, pmt)

                pmt.pla = regs.principal.amortized.current * (f_c - _1)
                pmt.raw = pmt.raw + pmt.pla
                pmt.tax = pmt.tax + pmt.pla * calculate_revenue_tax(amortizations[0].date, due)

            # Sanity check.
            #
            # Esse teste de sanidade só é necessário caso três critérios sejam atendidos:
            #
            #   1. Que a entrada do cronograma seja uma antecipação, "Amortization.Bare".
            #
            #   2. Que a antecipação esteja na data de cálculo. Se não estiver, obviamente, os valores não vão bater.
            #
            #   3. Que o valor da antecipação não seja "Amortization.Bare.MAX_VALUE". Nesse caso a rotina usaria o
            #      saldo devedor na data do cálculo como valor da antecipação. Não haveria "input" a ser validado.
            #
            if type(ent1) is Amortization.Bare and ent1.date == calc_date.value and ent1.value < Amortization.Bare.MAX_VALUE:
                assert _Q(pmt.raw) == _Q(ent1.value)

            # B.2.2. Arredonda valores do pagamento, e calcula o seu valor líquido.
            if tax_exempt:
                pmt.tax = _0

            pmt.amort = _Q(pmt.amort)
            pmt.gain = _Q(pmt.gain)
            pmt.raw = _Q(pmt.raw)
            pmt.tax = _Q(pmt.tax)
            pmt.net = pmt.raw - pmt.tax
            pmt.bal = _Q(pmt.bal)

            if vir and vir.code == 'IPCA':
                pmt = t.cast(PriceAdjustedPayment, pmt)

                pmt.pla = _Q(pmt.pla)

            yield pmt

            if pmt.bal == _0:
                break  # Se o saldo é zero, o cronograma acabou.
# }}}

# Public API, daily returns. {{{
@typeguard.typechecked
def get_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    amortizations: t.List[Amortization | Amortization.Bare], *,
    vir: t.Optional[VariableIndex] = None,
    capitalisation: _CAPITALISATION = '360'
) -> t.Iterable[DailyReturn]:
    '''
    Gera uma tabela de rendimentos para um determinado empréstimo.

    Esta função tem assinatura semelhante a "fincore.get_payments_table". Para saber como invocar essa função, tome
    como base a frase abaixo.

      “ Retorne os rendimentos diários de um empréstimo em um valor V, a uma taxa anual TA, nas datas D. ”

    Dessa elaboração saem os três parâmetros obrigatórios e posicionais dessa rotina:

      • "principal", é o valor principal do empréstimo, ou V.

      • "apy", é a taxa nominal anual de spread TA (annual percentage yield).

      • "amortizations", que é uma lista contendo as datas D em que amortizações devem ser realizadas.

    Dois outros parâmetros são opcionais "vir", que especifica um índice variável, podendo ser CDI, Poupança, IPCA, ou
    IGPM; e "capitalisation", que configura a forma de composição dos juros. Veja a documentação da rotina
    "fincore.get_payments_table" para mais detalhes sobre esses parâmetros.

    Emite uma lista de objetos "DailyReturn", que contêm as informações diárias da posição do empréstimo:

      • "date", é a data do rendimento.

      • "value", é o valor rendimento do dia.

      • "bal", é o saldo devedor do empréstimo no final do dia, isto é, considerando o rendimento do dia, e pagamentos
        extraordinários porventura realizados. O saldo inicial do dia D, "D.bal", deve ser obviamente, igual ao valor
        do saldo o final do dia anterior, "D₋₁.bal".

        Fique atento pois a expressão "D.bal - D.value" não dá o valor do saldo inicial do dia. Por dois motivos:

        1. Erros de arredondamento. A saída dessa rotina é quantizada, mas sua memória interna não é. Espere diferença
           de um centavo esporadicamente.

        2. Vão ter dias em que pagamentos serão realizados, e essa rotina não os retorna. De fato, a fórmula do saldo
           inicial é "D.bal - Σ D.entradas + Σ D.saidas", sendo que "D.entradas" seriam as entradas do dia, ou seja, o
           rendimento; e "D.saidas" as saídas, ou pagamentos, do dia. Esse cálculo também padece de erros de
           arredondamentos, pelo mesmo motivo do item anterior: a rotina quantiza valores internos somente antes de
           retorná-los.

      • "fixed_factor", é o fator de juros usado para calcular o componente fixo do rendimento do dia.

      • "variable_factor", é o fator de juros usado para calcular o componente variável do rendimento do dia.
    '''

    # Some indexes are only published by supervisor bodies on business days. For example, Brazilian DI. On such cases
    # this function will fill in the gaps, i.e., provide a zero value if the upstream misses it.
    #
    def get_normalized_cdi_indexes(backend: IndexStorageBackend) -> t.Iterator[decimal.Decimal]:
        # Algumas implementações da função "get_cdi_indexes" retornam um gerador, outras retornam uma lista. Portanto,
        # estou forçando a conversão para lista para atender ambas as possibilidades.
        #
        lst = list(backend.get_cdi_indexes(amortizations[0].date, amortizations[-1].date))
        idx = 0

        for ref in _date_range(amortizations[0].date, amortizations[-1].date):
            if ref == lst[idx].date:
                yield lst[idx].value / decimal.Decimal(100)

                idx = min(idx + 1, len(lst) - 1)

            else:
                yield _0

    # Poupança is a monthly index. This function will normalize it to daily values.
    def get_normalized_savings_indexes(backend: IndexStorageBackend) -> t.Iterator[decimal.Decimal]:
        for ranged in backend.get_savings_indexes(amortizations[0].date, amortizations[-1].date):
            init = max(amortizations[0].date, ranged.begin_date)
            ends = min(amortizations[-1].date, ranged.end_date)
            days = (ranged.end_date - ranged.begin_date).days
            rate = calculate_interest_factor(ranged.value, _1 / decimal.Decimal(days))

            for _ in _date_range(init, ends):
                yield rate - _1

    # IPCA is a monthly index. This function will normalize it to daily values.
    def get_normalized_ipca_indexes(backend: IndexStorageBackend) -> t.Iterator[decimal.Decimal]:
        raise NotImplementedError()

    def calc_balance() -> decimal.Decimal:
        val = principal * f_c + regs.interest.accrued - regs.principal.amortized.total * f_c - regs.interest.settled.total

        return t.cast(decimal.Decimal, val)

    # Primeiro gerador para valores de principal.
    #
    #  • "principal.amortization_ratio.current", é o percentual de amortização do período corrente.
    #  • "principal.amortized.current", é o valor amortizado no período corrente.
    #  • "principal.amortized.total", é o valor amortizado total (período corrente somado aos passados).
    #
    def track_principal_1() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            ratio = yield

            # Se o percentual de amortização atual somado ao acumulado ultrapassar 100%, um reajuste deve ser feito.
            if regs.principal.amortization_ratio.current + ratio > _1:
                ratio = _1 - regs.principal.amortization_ratio.current

            if ratio:
                regs.principal.amortization_ratio.current += ratio
                regs.principal.amortized = types.SimpleNamespace(current=ratio * principal, total=regs.principal.amortization_ratio.current * principal)

            else:
                regs.principal.amortized = types.SimpleNamespace(current=_0, total=regs.principal.amortized.total)

    # Segundo gerador para valores de principal.
    #
    #  • "principal.amortization_ratio.regular", é o percentual de amortização regular acumulado (período corrente somado a passados)
    #
    def track_principal_2() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            ratio = yield

            # Se o percentual de amortização regular somado ao acumulado ultrapassar 100%, um reajuste deve ser feito.
            if regs.principal.amortization_ratio.regular + ratio > _1:
                ratio = _1 - regs.principal.amortization_ratio.regular

            if ratio:
                regs.principal.amortization_ratio.regular += ratio

    # Gerador para valores de juros.
    #
    #   • "interest.daily" são os juros incorridos (produzidos) no dia.
    #   • "interest.current" são os juros incorridos (produzidos) no período corrente.
    #   • "interest.accrued" é o total de juros acumulado desde o dia zero do cronograma de pagamentos.
    #   • "interest.deferred" é o total de juros em aberto de períodos passados.
    #
    def track_interest_1() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            regs.interest.daily = yield
            regs.interest.current += regs.interest.daily
            regs.interest.accrued += regs.interest.daily
            regs.interest.deferred = regs.interest.accrued - (regs.interest.current + regs.interest.settled.total)

    # Gerador para valores de juros acertados entre devedor e credor.
    #
    #   • "interest.settled.current" são os juros acertados no período corrente.
    #   • "interest.settled.total" é o total de juros acertados desde o dia zero do cronograma de pagamentos.
    #
    def track_interest_2() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            regs.interest.settled = types.SimpleNamespace(current=(yield), total=regs.interest.settled.total)
            regs.interest.settled.total += regs.interest.settled.current
            regs.interest.current -= regs.interest.settled.current

    # A. Valida e prepara para execução.
    gens = types.SimpleNamespace()
    regs = types.SimpleNamespace()
    aux = _0

    if principal == _0:
        return

    if principal < _CENTI:
        raise ValueError('principal value should be at least 0.01')

    if len(amortizations) < 2:
        raise ValueError('at least two amortizations are required: the start of the schedule, and its end')

    elif not vir and capitalisation == '252':
        raise ValueError('fixed interest rates should not use the 252 working days capitalisation')

    elif vir and vir.code == 'CDI' and capitalisation != '252':
        raise ValueError('CDI should use the 252 working days capitalisation')

    for i, x in enumerate(amortizations):
        if type(x) is Amortization:
            aux += x.amortization_ratio

        if vir and vir.code not in t.get_args(_PL_INDEX) and type(x) is Amortization and x.price_level_adjustment:
            raise TypeError(f"amortization {i} has price level adjustment, but a variable index wasn't provided, or isn't IPCA nor IGPM")

        elif aux > _1 and not math.isclose(aux, _1):
            raise ValueError('the accumulated percentage of the amortizations overflows 1.0')

    if not math.isclose(aux, _1):
        raise ValueError('the accumulated percentage of the amortizations does not reach 1.0')

    # Registradores.
    regs.interest = types.SimpleNamespace(current=_0, accrued=_0, settled=types.SimpleNamespace(current=_0, total=_0), deferred=_0)
    regs.principal = types.SimpleNamespace(amortization_ratio=types.SimpleNamespace(current=_0, regular=_0), amortized=types.SimpleNamespace(current=_0, total=_0))
    regs.correction = types.SimpleNamespace(current=_1, accrued=_1)

    # Control, create generators.
    gens.interest_tracker_1 = track_interest_1()
    gens.interest_tracker_2 = track_interest_2()
    gens.principal_tracker_1 = track_principal_1()
    gens.principal_tracker_2 = track_principal_2()

    # Control, start generators.
    gens.principal_tracker_1.send(None)
    gens.principal_tracker_2.send(None)
    gens.interest_tracker_1.send(None)
    gens.interest_tracker_2.send(None)

    # List of indexes.
    if vir and vir.code == 'CDI':
        idxs = get_normalized_cdi_indexes(vir.backend)

    elif vir and vir.code == 'Poupança':
        idxs = get_normalized_savings_indexes(vir.backend)

    elif vir:  # Implies "vir.code == 'IPCA'".
        idxs = get_normalized_ipca_indexes(vir.backend)

    # B. Executa.
    itr = iter(amortizations)
    tup = next(itr), next(itr)
    cnt = p = 1

    for ref in _date_range(amortizations[0].date, amortizations[-1].date):
        f_c = _1  # Taxa (ou fator) de correção, FC.
        f_v = _1  # Taxa (ou fator) variável, FV.
        f_s = _1  # Taxa (ou fator) fixo, FS.

        # Fase B.0, FZA, ou Fase Zille-Anna.
        #
        #  • Calcula FS (fator de spread) para índice pré-fixado; e ambos FS e FC para índice de correção.
        #  • Calcula FS para índice pós-fixado (CDI, Poupança etc). Nesse caso não há correção.
        #
        # Altamente alterada com relação à FZA da rotina "get_payments_table".
        #
        if not vir and capitalisation == '360':  # Bullet.
            f_s = calculate_interest_factor(apy, _1 / decimal.Decimal(360))

        elif not vir and capitalisation == '365':  # Bullet in legacy mode.
            f_s = calculate_interest_factor(apy, _1 / decimal.Decimal(365))

        elif not vir and capitalisation == '30/360':  # Juros mensais, Price, Livre.
            v01 = calculate_interest_factor(apy, _1 / decimal.Decimal(12)) - _1  # Fator mensal.

            # O período um tem tratamento especial aqui, para lidar com variações no aniversário do empréstimo.
            #
            # Exemplo, o projeto da Resolvvi de junho de 2023. O primeiro período tem 32 dias, em vez dos esperados 30
            # dias – de 19/06/2023, inclusive, a 21/07/2023, exclusive. A data final do período um foi deslocada em
            # decorrência da data de aniversário do projeto, que é 21/12/2025.
            #
            # Para contemplar os casos em que a data final do primeiro período do empréstimo foi adulterada em relação
            # ao seu início de rendimento, devido a alterações no aniversário do empréstimo, o cálculo do fator de
            # juro fixo emprega a diferença de dias entre as datas inicial e final do período.
            #
            # Em um outro período qualquer, basta saber a quantidade de dias que tem o mês em que ele se inicia.
            #
            # Observe que pagamentos extraordinários não definem os intervalos de um período de um cronograma de
            # amortizações. Por isso testa-se pelo tipo de "tup[1]" abaixo.
            #
            if p == 1 and (type(tup[1]) is Amortization.Bare or ref < tup[1].date):
                v02 = decimal.Decimal((amortizations[1].date - amortizations[0].date).days)  # Dias no período.

            elif ref == tup[1].date:
                v02 = decimal.Decimal(calendar.monthrange(tup[1].date.year, tup[1].date.month)[1])  # Dias do mês do período.

            else:
                v02 = decimal.Decimal(calendar.monthrange(tup[0].date.year, tup[0].date.month)[1])  # Dias do mês do período.

            f_s = calculate_interest_factor(v01, _1 / v02, False)  # Fator diário.

        elif vir and vir.code == 'CDI' and capitalisation == '252':  # Bullet, Juros mensais, Livre.
            f_v = next(idxs) * vir.percentage / decimal.Decimal(100) + _1

            # Lembrar que índice na base 252 só rende em dia útil. Assim funciona o CDI. Nesse caso o fator fixo
            # deve acompanhar o variável. Só deve ser calculado em dia útil.
            #
            # FIXME: se porventura o índice variável, "next(idxs)", for zero, e se tratar de um dia útil, o fator
            # fixo não será calculado. Nunca vi o CDI ser zero, mas vale contemplar esse caso. O correto abaixo é
            # testar se o dia é útil, e não se o valor do fator "f_c" é maior que um.
            #
            if f_v > _1:
                f_s = calculate_interest_factor(apy, _1 / decimal.Decimal(252))

        elif vir and vir.code == 'Poupança' and capitalisation == '360':  # Poupança só suportada em Bullet.
            f_s = calculate_interest_factor(apy, _1 / decimal.Decimal(360))
            f_v = next(idxs) * vir.percentage / decimal.Decimal(100) + _1

        elif vir and vir.code == 'IPCA' and capitalisation == '360':  # Bullet.
            raise NotImplementedError()  # FIXME: implementar.

        elif vir and vir.code == 'IPCA' and capitalisation == '30/360':  # Juros mensais e Livre.
            raise NotImplementedError()  # FIXME: implementar.

        elif vir:
            raise NotImplementedError(f'Combination of variable interest rate {vir} and capitalisation {capitalisation} unsupported')

        else:
            raise NotImplementedError(f'Unsupported capitalisation {capitalisation} for fixed interest rate')

        # Fase B.1, FRU, ou Fase Rafa Um. Levemente alterada com relação à FRU da rotina "get_payments_table".
        while ref == tup[1].date:
            if type(tup[1]) is Amortization:  # Caso de uma amortização regular.
                adj = (_1 - regs.principal.amortization_ratio.current) / (_1 - regs.principal.amortization_ratio.regular)  # [FATOR-AJUSTE].

                # Registra o percentual de amortização do principal.
                gens.principal_tracker_1.send(tup[1].amortization_ratio * adj)

                # Registra o percentual regular de amortização do principal.
                gens.principal_tracker_2.send(tup[1].amortization_ratio)

                # Registra o valor de juros a pagar no período.
                if tup[1].amortizes_interest:
                    gens.interest_tracker_2.send(regs.interest.current + regs.principal.amortization_ratio.current * regs.interest.deferred)

                # Registra o valor de correção a pagar no período (FIXME: implementar).
                # gens.price_level_tracker_2.send(…)

                # Encerra o acumulador de juros do período anterior.
                regs.interest.current = _0

                p += 1  # O período só incrementa em amortizações regulares.

                cnt = 1

            # Caso de um adiantamento (amortização extraordinária).
            #
            # Lembre-se que um adiantamento apresenta apenas um valor bruto que será pago em uma determinada data. Esse
            # valor bruto será fatorado em diversos componentes da dívida, de forma ordenada. O primeiro componente da
            # dívida a ser amortizado é o juro (spread). Após o pagamento dos juros, o que sobra deve ser deduzido da
            # correção monetária. Finalmente, abate-se o valor restante do principal. No bloco de código abaixo,
            #
            #  • "val1" é o valor de juros a pagar.
            #
            #  • "val2" é o valor da correção a pagar. FIXME: a variável "plfv" deveria ser multiplicada pelo
            #    percentual de amortização do principal do período, e não pelo decimal um.
            #
            #  • "val3" é o valor a amortizar do principal.
            #
            # Observe que a ordem de cálculo dessas variáveis corresponde à ordem de fatoração do valor bruto da
            # antecipação.
            #
            else:
                ent = t.cast(Amortization.Bare, tup[1])  # O Mypy não consegue inferir o tipo da variável "ent" aqui.
                plfv = principal * (_1 - regs.principal.amortization_ratio.current) * (f_c - _1)  # Price level, full value.
                val0 = min(ent.value, calc_balance())
                val1 = min(val0, regs.interest.accrued - regs.interest.settled.total)
                val2 = min(val0 - val1, plfv * _1)
                val3 = val0 - val1 - val2

                # Verifica se o valor do pagamento irregular não ultrapassa o saldo em aberto.
                if ent.value != Amortization.Bare.MAX_VALUE and ent.value > _Q(calc_balance()):
                    raise Exception(f'the value of the amortization, {ent.value}, is greater than the remaining balance of the loan, {_Q(calc_balance())}')

                # Registra o percentual de amortização do principal.
                gens.principal_tracker_1.send(val3 / principal)

                # Registra o valor de juros a pagar no período.
                gens.interest_tracker_2.send(val1)

                # Registra o valor de correção a pagar no período (FIXME: implementar).
                # gens.price_level_tracker_2.send(val2)

                # Encerra o acumulador de juros do período anterior.
                regs.interest.current = _0

            tup = tup[1], next(itr)

        # Registra o valor do juros incorrido no dia.
        gens.interest_tracker_1.send(calc_balance() * (f_s * f_v * f_c - _1))

        # Registra a correção do período (FIXME: implementar).
        # gens.price_level_tracker_1.send(…)

        # Se o saldo é zero, o cronograma acabou.
        if _Q(calc_balance()) == _0:
            break

        # Monta a instância de rendimento diário, saída da rotina. Faz arredondamentos.
        dr = DailyReturn()

        dr.no = cnt
        dr.period = p
        dr.date = ref
        dr.value = _Q(regs.interest.daily)
        dr.bal = _Q(calc_balance())

        dr.fixed_factor = f_s
        dr.variable_factor = f_v * f_c

        yield dr

        cnt += 1
# }}}

# Public API, factories. {{{
def preprocess_bullet(
    zero_date: datetime.date,
    term: int,
    insertions: t.List[Amortization.Bare] = [],
    anniversary_date: t.Optional[datetime.date] = None,
    capitalisation: _DAILY_CAPITALISATION = '360',
    vir: t.Optional[VariableIndex] = None,
    calc_date: t.Optional[CalcDate] = None  # Pass through.
) -> t.List[Amortization | Amortization.Bare]:
    sched: t.List[Amortization | Amortization.Bare] = []

    # 1. Valida.
    if term <= 0:  # See [ANNOTATED_TYPES] above.
        raise ValueError('"term" must be a greater than, or equal to, one')

    if anniversary_date and anniversary_date <= zero_date:
        raise ValueError(f'the "anniversary_date", {anniversary_date}, must be greater than "zero_date", {zero_date}')

    elif anniversary_date and abs((anniversary_date - (zero_date + _MONTH * term)).days) > 20:
        raise ValueError(f'the "anniversary_date", {anniversary_date}, is more than 20 days away from the regular payment date, {zero_date + _MONTH * term}')

    for i, x in enumerate(insertions):
        if x.value <= 0:
            raise ValueError(f'invalid value for insertion entry #{i} – should be positive')

        elif x.date <= zero_date:
            raise ValueError(f'"insertions[{i}].date", {x.date}, must succeed "zero_date", {zero_date}')

        elif not anniversary_date and x.date > (due := zero_date + _MONTH * term):
            raise ValueError(f'"insertions[{i}].date", {x.date}, succeeds the regular payment date, {due}')

        elif anniversary_date and x.date > anniversary_date:
            raise ValueError(f'"insertions[{i}].date", {x.date}, succeeds "anniversary_date", {anniversary_date}')

    # Base de cálculo 365 somente para pré-fixadas históricas. Recomenda-se o uso da base 360 para pré-fixadas.
    if capitalisation == '365':
        _LOG.warning('capitalising 365 days per year exists solely for legacy Bullet support – prefer 360 days')

    # 2.1. Cria as amortizações. Fluxo regular, sem inserções. Rápido.
    if not insertions and not vir:
        sched.append(Amortization(date=zero_date, amortizes_interest=False))
        sched.append(Amortization(date=anniversary_date or zero_date + _MONTH * term, amortization_ratio=_1))

        if anniversary_date:
            sched[-1].dct_override = DctOverride(anniversary_date, anniversary_date, predates_first_amortization=False)

    # 2.2. Cria as amortizações. Fluxo regular com Índice Nacional de Preços ao Consumidor Amplo, sem inserções. Rápido.
    elif not insertions and vir and vir.code == 'IPCA':
        dif = min(_delta_months(calc_date.value, zero_date), term) if calc_date else term
        pla = PriceLevelAdjustment('IPCA', base_date=zero_date.replace(day=1), period=dif)

        sched.append(Amortization(date=zero_date, amortizes_interest=False))
        sched.append(Amortization(date=anniversary_date or zero_date + _MONTH * term, amortization_ratio=_1, price_level_adjustment=pla))

        if anniversary_date:
            sched[-1].dct_override = DctOverride(anniversary_date, anniversary_date, predates_first_amortization=False)

    # 2.3. Cria as amortizações. Faz inserções no fluxo regular. Lento.
    else:
        lst = []

        lst.append(Amortization(date=zero_date, amortizes_interest=False))
        lst.append(Amortization(date=anniversary_date or zero_date + _MONTH * term, amortization_ratio=_1))

        for skel in _interleave(lst, insertions, key=lambda x: x.date):
            sched.append(skel.item)

            if skel.from_a and vir and vir.code == 'IPCA':
                dif = _delta_months(skel.item.date, zero_date)

                skel.item.price_level_adjustment = PriceLevelAdjustment('IPCA')

                skel.item.price_level_adjustment.base_date = zero_date.replace(day=1)
                skel.item.price_level_adjustment.period = dif
                skel.item.price_level_adjustment.amortizes_adjustment = skel.index_a == len(lst) - 1

            elif skel.from_b and anniversary_date:
                skel.item.dct_override = DctOverride(zero_date, anniversary_date, predates_first_amortization=True)

            elif skel.from_b:
                skel.item.dct_override = DctOverride(zero_date, zero_date + _MONTH * term, predates_first_amortization=True)

    return sched

def preprocess_jm(
    zero_date: datetime.date,
    term: int,
    insertions: t.List[Amortization.Bare] = [],
    anniversary_date: t.Optional[datetime.date] = None,
    vir: t.Optional[VariableIndex] = None
) -> t.List[Amortization] | t.List[Amortization | Amortization.Bare]:
    lst1 = []
    lst2 = []

    # 1. Valida.
    if term <= 0:  # See [ANNOTATED_TYPES] above.
        raise ValueError('"term" must be a greater than, or equal to, one')

    if anniversary_date and anniversary_date <= zero_date:
        raise ValueError(f'the "anniversary_date", {anniversary_date}, must be greater than "zero_date", {zero_date}')

    elif anniversary_date and abs((anniversary_date - (zero_date + _MONTH)).days) > 20:
        raise ValueError(f'the "anniversary_date", {anniversary_date}, is more than 20 days away from the regular payment date, {zero_date + _MONTH}')

    if vir and vir.code == 'Poupança':
        raise NotImplementedError('"Poupança" is currently unsupported')

    for i, x in enumerate(insertions):
        if x.date <= zero_date:
            raise ValueError(f'"insertions[{i}].date", {x.date}, must succeed "zero_date", {zero_date}')

        elif not anniversary_date and x.date > (due := zero_date + _MONTH * term):
            raise ValueError(f'"insertions[{i}].date", {x.date}, succeeds the last regular payment date, {due}')

        elif anniversary_date and x.date > (due := anniversary_date + _MONTH * (term - 1)):
            raise ValueError(f'"insertions[{i}].date", {x.date}, succeeds the last regular payment date, {due}')

    # 2. Cria as amortizações.
    if anniversary_date and anniversary_date == zero_date + _MONTH:
        anniversary_date = None

    # Fluxo regular, sem inserções. Rápido.
    lst1.append(Amortization(date=zero_date, amortizes_interest=False))  # Data zero (início do rendimento).

    for i in range(1, term + 1):
        due = anniversary_date + _MONTH * (i - 1) if anniversary_date else zero_date + _MONTH * i
        ent = Amortization(date=due, amortization_ratio=_0 if i != term else _1)

        if i == 1 and anniversary_date:
            ent.dct_override = DctOverride(anniversary_date, anniversary_date, predates_first_amortization=False)

        if vir and vir.code == 'IPCA':
            ent.price_level_adjustment = PriceLevelAdjustment('IPCA')

            ent.price_level_adjustment.base_date = zero_date.replace(day=1)
            ent.price_level_adjustment.period = i
            ent.price_level_adjustment.amortizes_adjustment = i == term

        lst1.append(ent)

    # Faz inserções no fluxo regular. Lento.
    if insertions:
        for skel in _interleave(lst1, insertions, key=lambda x: x.date):
            lst2.append(skel.item)

            if skel.from_a and vir and vir.code == 'IPCA':
                skel.item.price_level_adjustment = PriceLevelAdjustment('IPCA')

                skel.item.price_level_adjustment.base_date = zero_date.replace(day=1)
                skel.item.price_level_adjustment.period = skel.index_a
                skel.item.price_level_adjustment.amortizes_adjustment = skel.index_a == len(lst1) - 1

            if skel.from_b:
                date1 = lst1[skel.index_a - 1].date
                date2 = lst1[skel.index_a].date

                skel.item.dct_override = DctOverride(date1, date2, predates_first_amortization=skel.index_a == 1)

        return lst2

    return lst1

def preprocess_price(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int,
    insertions: t.List[Amortization.Bare] = [],
    anniversary_date: t.Optional[datetime.date] = None
) -> t.List[Amortization] | t.List[Amortization | Amortization.Bare]:
    lst1 = []
    lst2 = []

    # 1. Valida.
    if term <= 0:  # See [ANNOTATED_TYPES] above.
        raise ValueError('"term" must be a greater than, or equal to, one')

    if anniversary_date and anniversary_date <= zero_date:
        raise ValueError(f'the "anniversary_date", {anniversary_date}, must be greater than "zero_date", {zero_date}')

    elif anniversary_date and abs((anniversary_date - (zero_date + _MONTH)).days) > 20:
        raise ValueError(f'the "anniversary_date", {anniversary_date}, is more than 20 days away from the regular payment date, {zero_date + _MONTH}')

    for i, x in enumerate(insertions):
        if x.date <= zero_date:
            raise ValueError(f'"insertions[{i}].date", {x.date}, must succeed "zero_date", {zero_date}')

        elif not anniversary_date and x.date > (due := zero_date + _MONTH * term):
            raise ValueError(f'"insertions[{i}].date", {x.date}, succeeds the last regular payment date, {due}')

        elif anniversary_date and x.date > (due := anniversary_date + _MONTH * (term - 1)):
            raise ValueError(f'"insertions[{i}].date", {x.date}, succeeds the last regular payment date, {due}')

    # 2. Cria as amortizações.
    if anniversary_date and anniversary_date == zero_date + _MONTH:
        anniversary_date = None

    # Fluxo regular, sem inserções. Rápido.
    lst1.append(Amortization(date=zero_date, amortizes_interest=False))  # Data zero (início do rendimento).

    for i, y in enumerate(amortize_fixed(principal, apy, term), 1):
        due = anniversary_date + _MONTH * (i - 1) if anniversary_date else zero_date + _MONTH * i

        lst1.append(Amortization(date=due, amortization_ratio=y))

        if i == 1 and anniversary_date:
            lst1[-1].dct_override = DctOverride(anniversary_date, anniversary_date, predates_first_amortization=False)

    # Faz inserções no fluxo regular. Lento.
    if insertions:
        for skel in _interleave(lst1, insertions, key=lambda x: x.date):
            lst2.append(skel.item)

            if skel.from_b:
                date1 = lst1[skel.index_a - 1].date
                date2 = lst1[skel.index_a].date

                skel.item.dct_override = DctOverride(date1, date2, predates_first_amortization=skel.index_a == 1)

        return lst2

    return lst1

def preprocess_livre(
    amortizations: t.List[Amortization],
    insertions: t.List[Amortization.Bare] = [],
    vir: t.Optional[VariableIndex] = None
) -> t.List[Amortization | Amortization.Bare]:
    sched: t.List[Amortization | Amortization.Bare] = []
    aux = _0

    # 1. Valida.
    if len(amortizations) < 2:
        raise ValueError('at least two amortizations are required: the start of the schedule, and its end')

    if vir and vir.code == 'Poupança':
        raise NotImplementedError('"Poupança" is currently unsupported')

    for i, x in enumerate(amortizations):
        aux += x.amortization_ratio

        if vir and vir.code not in t.get_args(_PL_INDEX) and type(x) is Amortization and x.price_level_adjustment:
            raise TypeError(f"amortization {i} has price level adjustment, but a variable index wasn't provided, or isn't IPCA nor IGPM")

    for i, y in enumerate(insertions):
        if y.value <= 0:
            raise ValueError(f'invalid value for insertion entry #{i} – should be positive')

        elif y.date <= (zero_date := amortizations[0].date):
            raise ValueError(f'"insertions[{i}].date", {y.date}, must succeed "zero_date", {zero_date}')

        elif y.date > (due := amortizations[-1].date):
            raise ValueError(f'"insertions[{i}].date", {y.date}, succeeds the last regular payment date, {due}')

    if abs((amortizations[1].date - (amortizations[0].date + _MONTH)).days) > 20:
        raise ValueError(f'the first payment date, {amortizations[1].date}, is more than 20 days away from the regular payment date, {amortizations[0].date + _MONTH}')

    if len(set([z.date for z in amortizations])) != len(amortizations):
        raise ValueError('amortization dates must be unique.')

    if not math.isclose(aux, _1):
        raise ValueError('the accumulated percentage of the amortizations does not reach 1.0')

    # 2. Cria as amortizações.
    if not insertions:  # Fluxo regular, sem inserções.
        sched.extend(amortizations)

    else:  # Fluxo extraordinário, com inserções.
        for skel in _interleave(amortizations, insertions, key=lambda x: x.date):
            if skel.from_a:
                sched.append(skel.item)

            else:
                amort = Amortization.Bare(date=skel.item.date)
                date1 = amortizations[skel.index_a - 1].date
                date2 = amortizations[skel.index_a].date

                amort.value = skel.item.value
                amort.dct_override = DctOverride(date1, date2, predates_first_amortization=skel.index_a == 1)

                sched.append(amort)

    return sched

# FIXME: remove this class.
class PaymentFactory:
    @staticmethod
    @typeguard.typechecked
    def create(mode: _OP_MODES, **kwa: t.Any) -> t.Iterable[Payment]:
        if mode == 'Bullet':
            return build_bullet(**kwa)

        elif mode == 'Juros mensais':
            return build_jm(**kwa)

        elif mode == 'Price':
            return build_price(**kwa)

        else:
            return build(**kwa)

# FIXME: renomear para "get_bullet_payments".
@typeguard.typechecked
def build_bullet(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int, *,  # Junto com "zero_date", equivale ao "amortizations".

    # Optional list of non-scheduled amortizations, a.k.a. prepayments.
    insertions: t.List[Amortization.Bare] = [],

    # Etc.
    anniversary_date: t.Optional[datetime.date] = None,
    vir: t.Optional[VariableIndex] = None,
    calc_date: t.Optional[CalcDate] = None,  # Pass through.
    capitalisation: _DAILY_CAPITALISATION = '360',
    tax_exempt: t.Optional[bool] = False,
    gain_output: _GAIN_OUTPUT_MODE = 'current'
) -> t.Iterable[Payment]:
    '''
    Stereotypes a Bullet operation.

    In addition to the initial principal value and the annual percentage rate, "apy", this function receives the initial
    yield date, "zero_date", and its term, "term". With this, it generates a Bullet amortization schedule, and from it
    derives the payment values, by calling "fincore.get_payments_table". Note that Bullet is
    characterized by only one payment, but the regular schedule has two entries: the start of the yield and the
    final, total amortization.

    Furthermore, when you want to simulate one or more early payments, total or partial, this function performs the
    prerequisites.

      • Inserts the prepayments into the regular Bullet flow.

      • Applies the monetary correction informed in the "vir" parameter. Uses "M-1" shift automatically. The
        correction accumulates until the last payment, whether planned or a total prepayment.

      • Automatically uses the "360" adjustment for fixed-rate operations, and "252" for post-fixed. Accepts "365" for
        legacy operations. Parameter "capitalisation".

    Prepayments go in the "insertions" parameter. It is a list of "obj" objects, where,

      • "obj.date" is the prepayment date.

      • "obj.amortization_ratio" is the percentage of the initial principal that will be amortized in this prepayment.

    The "vir" and "calc_date" parameters are the same as in "fincore.get_payments_table".
    '''

    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_bullet(zero_date, term, insertions, anniversary_date, capitalisation, vir, calc_date)

    kwa['vir'] = vir
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else capitalisation

    kwa['calc_date'] = calc_date
    kwa['tax_exempt'] = tax_exempt
    kwa['gain_output'] = gain_output

    yield from get_payments_table(**kwa)

# FIXME: renomear para "get_jm_payments".
@typeguard.typechecked
def build_jm(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int, *,  # Junto com "zero_date", equivale ao "amortizations".

    # Optional list of non-scheduled amortizations, a.k.a. prepayments.
    insertions: t.List[Amortization.Bare] = [],

    # Etc.
    anniversary_date: t.Optional[datetime.date] = None,
    vir: t.Optional[VariableIndex] = None,
    calc_date: t.Optional[CalcDate] = None,  # Pass through.
    tax_exempt: t.Optional[bool] = False,
    gain_output: _GAIN_OUTPUT_MODE = 'current'
) -> t.Iterable[Payment]:
    '''
    Stereotypes a Monthly Interest operation.

    In addition to the initial principal value and the annual percentage rate, "apy", this function receives the initial
    yield date, "zero_date", and its term, "term". With this, it generates a Price amortization schedule, and from it
    derives the payment values, by calling "fincore.get_payments_table".

    Furthermore, when you want to simulate one or more early payments, total or partial, this function performs the
    prerequisites.

      • Interleaves the prepayments with the regular monthly interest flow in a consolidated schedule.

      • Applies the monetary correction informed in the "vir" parameter. Uses "M-1" shift automatically. The
        correction accumulates until the last payment, whether planned or a total prepayment.

      • Automatically uses the "30/360" quotient for fixed-rate operations, and "252" for post-fixed.

    Prepayments go in the "insertions" parameter. It is a list of "obj" objects, where,

      • "obj.date" is the prepayment date.

      • "obj.amortization_ratio" is the percentage of the initial principal that will be amortized in this prepayment.

    The "vir" and "calc_date" parameters are the same as in "fincore.get_payments_table".
    '''

    # 3. Gera o cronograma de pagamentos.
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_jm(zero_date, term, insertions, anniversary_date, vir)

    kwa['vir'] = vir
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else '30/360'

    kwa['calc_date'] = calc_date
    kwa['tax_exempt'] = tax_exempt
    kwa['gain_output'] = gain_output

    yield from get_payments_table(**kwa)

# FIXME: renomear para "get_price_payments".
@typeguard.typechecked
def build_price(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int, *,  # Junto com "zero_date", equivale ao "amortizations".

    # Optional list of non-scheduled amortizations, a.k.a. prepayments.
    insertions: t.List[Amortization.Bare] = [],

    # Etc.
    anniversary_date: t.Optional[datetime.date] = None,
    calc_date: t.Optional[CalcDate] = None,  # Pass through.
    tax_exempt: t.Optional[bool] = False,
    gain_output: _GAIN_OUTPUT_MODE = 'current'
) -> t.Iterable[Payment]:
    '''
    Stereotypes a Price operation.

    In addition to the initial principal value and the annual percentage rate, "apy", this function receives the initial
    yield date, "zero_date", and its term, "term". With this, it generates a Price amortization schedule, and from it
    derives the payment values, by calling "fincore.get_payments_table".

    Furthermore, when you want to simulate one or more early payments, total or partial, this function performs the
    prerequisites.

      • Interleaves the prepayments with the regular Price flow in a consolidated schedule.

      • Recalculates the amortization percentages after a partial prepayment. Ensures that the recalculated amortizations
        continue to convert into payments with constant value, characteristic of Price.

      • Uses the "30/360" quotient.

    Prepayments go in the "insertions" parameter. It is a list of "obj" objects, where,

      • "obj.date" is the prepayment date.

      • "obj.amortization_ratio" is the percentage of the initial principal that will be amortized in this prepayment.

    The "calc_date" parameter is the same as in "fincore.get_payments_table".
    '''

    # 3. Gera o cronograma de pagamentos.
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_price(principal, apy, zero_date, term, insertions, anniversary_date)

    kwa['capitalisation'] = '30/360'

    kwa['calc_date'] = calc_date
    kwa['tax_exempt'] = tax_exempt
    kwa['gain_output'] = gain_output

    yield from get_payments_table(**kwa)

# FIXME: renomear para "get_livre_payments".
@typeguard.typechecked
def build(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    amortizations: t.List[Amortization], *,

    # Optional list of amortizations.
    insertions: t.List[Amortization.Bare] = [],

    # Etc.
    vir: t.Optional[VariableIndex] = None,
    calc_date: t.Optional[CalcDate] = None,  # Pass through.
    tax_exempt: t.Optional[bool] = False,
    gain_output: _GAIN_OUTPUT_MODE = 'current'
) -> t.Iterable[Payment]:
    '''
    Builds a Free operation.

    In addition to the initial principal value and the annual percentage rate, "apy", this function receives two lists of
    amortizations: one with the regular flow, and another with the prepayments. It has two main utilities:

      1. Interleaves the flows in date order, before finally invoking "fincore.get_payments_table".

      2. Calculates the amortization percentages when there is an extra-regular amortization, i.e., a prepayment.
         The routine ensures that, if the prepayment is not total, the amortizations following it generate payments
         with proportional value.

    The "vir" and "calc_date" parameters are the same as in "fincore.get_payments_table".
    '''

    # 3. Gera o cronograma de amortizações a partir do esqueleto.
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_livre(amortizations, insertions, vir)

    kwa['vir'] = vir
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else '30/360'

    kwa['calc_date'] = calc_date
    kwa['tax_exempt'] = tax_exempt
    kwa['gain_output'] = gain_output

    yield from get_payments_table(**kwa)

@typeguard.typechecked
def get_bullet_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int, *,  # Junto com "zero_date", equivale ao "amortizations".

    # Optional list of non-scheduled amortizations, a.k.a. prepayments.
    insertions: t.List[Amortization.Bare] = [],

    # Etc.
    anniversary_date: t.Optional[datetime.date] = None,
    vir: t.Optional[VariableIndex] = None,
    capitalisation: _DAILY_CAPITALISATION = '360'
) -> t.Iterable[DailyReturn]:
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_bullet(zero_date, term, insertions, anniversary_date, capitalisation, vir, calc_date=None)
    kwa['vir'] = vir
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else capitalisation

    yield from get_daily_returns(**kwa)

@typeguard.typechecked
def get_jm_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int, *,  # Junto com "zero_date", equivale ao "amortizations".
    insertions: t.List[Amortization.Bare] = [],
    anniversary_date: t.Optional[datetime.date] = None,
    vir: t.Optional[VariableIndex] = None
) -> t.Iterable[DailyReturn]:
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_jm(zero_date, term, insertions, anniversary_date, vir)
    kwa['vir'] = vir
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else '30/360'

    yield from get_daily_returns(**kwa)

@typeguard.typechecked
def get_price_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int, *,  # Junto com "zero_date", equivale ao "amortizations".
    insertions: t.List[Amortization.Bare] = [],
    anniversary_date: t.Optional[datetime.date] = None
) -> t.Iterable[DailyReturn]:
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_price(principal, apy, zero_date, term, insertions, anniversary_date)
    kwa['capitalisation'] = '30/360'

    yield from get_daily_returns(**kwa)

@typeguard.typechecked
def get_livre_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    amortizations: t.List[Amortization], *,
    insertions: t.List[Amortization.Bare] = [],
    vir: t.Optional[VariableIndex] = None
) -> t.Iterable[DailyReturn]:
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['vir'] = vir
    kwa['amortizations'] = preprocess_livre(amortizations, insertions, vir)
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else '30/360'

    yield from get_daily_returns(**kwa)
# }}}

# Public API, helpers. {{{
@typeguard.typechecked
def calculate_revenue_tax(begin: datetime.date, end: datetime.date) -> decimal.Decimal:
    '''Calculates tax for fixed income.'''

    if end > begin:
        dif = (end - begin).days

        for minimum, maximum, rate in _REVENUE_TAX_BRACKETS:
            if minimum < dif <= maximum:
                return rate

    raise ValueError(f'end date, {end}, should be grater than the begin date, {begin}.')

@functools.cache
@typeguard.typechecked
def calculate_interest_factor(rate: decimal.Decimal, period: decimal.Decimal, percent: bool = True) -> decimal.Decimal:
    '''Calculates the interest factor given an annual percentage rate (APY) and a period.'''

    if percent:
        rate = decimal.Decimal(rate) / decimal.Decimal(100)

    return (1 + rate) ** decimal.Decimal(period)

@typeguard.typechecked
def calculate_iof(begin: datetime.date, term: int) -> decimal.Decimal:
    '''
    Calculates the IOF for a fixed income investment.

    Calculates the IOF for a fixed income investment, given its start date and
    its term in months.
    '''

    if term >= 12:
        return decimal.Decimal('1.88')

    else:
        data2 = begin + _MONTH * term
        delta = (data2 - begin).days

        return decimal.Decimal('0.38') + decimal.Decimal('0.00411') * delta

@typeguard.typechecked
def amortize_fixed(principal: decimal.Decimal, apy: decimal.Decimal, term: int) -> t.Generator[decimal.Decimal, None, None]:
    '''
    Builds an amortization table for a fixed income investment.

    Returns an iterator of amortization percentages.
    '''

    if term > 0:
        fac = calculate_interest_factor(apy, _1 / decimal.Decimal(12))
        pmt = (principal * (fac - _1)) / (_1 - pow(fac, -term))
        bal = principal

        while bal > 0:
            amr = pmt - (bal * (fac - _1)) if bal - pmt >= 0 else bal
            bal = bal - amr

            yield amr / principal

# FIXME: rotina não suporta IPCA.
@typeguard.typechecked
def get_delinquency_charges(
    outstanding_balance: decimal.Decimal,  # Unpaid principal plus interest.
    arrears_period: t.Tuple[datetime.date, datetime.date],  # Arrear, or delinquency period.

    loan_apy: decimal.Decimal,  # Taxa anual de juros remuneratórios a.a. (spread).
    loan_vir: t.Optional[VariableIndex] = None,  # Índice variável.

    fee_rate: decimal.Decimal = LatePayment.FEE_RATE,
    fine_rate: decimal.Decimal = LatePayment.FINE_RATE
) -> types.SimpleNamespace:
    '''
    Calcula cobranças extraordinárias para um empréstimo em atraso.

      • "arrears_period" (t.Tuple[datetime.date, datetime.date]): o período de inadimplência, representado como uma tupla
        com datas de início e fim.

      • "outstanding_balance" (decimal.Decimal): o saldo devedor do empréstimo, incluindo principal e juros não pagos, na data
        inicial.

      • "loan_apy" (decimal.Decimal): A taxa percentual anual do empréstimo (taxa de juros fixa).

      • "loan_zero_date" (datetime.date): A data inicial do cronograma de pagamentos do empréstimo.

      • "loan_vir" (t.Optional[VariableIndex], opcional): O índice variável, se aplicável. Padrão é None.

      • "fee_rate" (decimal.Decimal, opcional): a taxa de juros de mora. Padrão é LatePayment.FEE_RATE.

      • "fine_rate" (decimal.Decimal, opcional): taxa de multa. Padrão é LatePayment.FINE_RATE.

    Retorna um objeto contendo as cobranças de inadimplência calculadas, incluindo taxas de atraso, multas e outras
    penalidades relevantes.

    Exemplo de cálculo de juros, mora, e multa, para um empréstimo de R$ 10.000,00, com taxa de juros fixa de 5% a.a.,
    realizado em 1 de janeiro de 2022, e com pagamento atrasado de 1 de janeiro de 2023 a 1 de fevereiro de 2023:

        >>> get_delinquency_charges(  # doctest: +SKIP
                arrears_period=(datetime.date(2023, 1, 1), datetime.date(2023, 2, 1)),
                outstanding_balance=decimal.Decimal('10000.00'),
                loan_apy=decimal.Decimal('0.05'),
                loan_zero_date=datetime.date(2022, 1, 1)
            )
    '''

    # Fator de juros remuneratórios, "f_1"
    # ------------------------------------
    #
    # Calculado em cima da taxa fixa anual da operação (APY), mas:
    #
    # • Para operações pré-fixadas, considera os dias corridos entre a data prevista para o pagamento ordinário e a
    #   data do pagamento em atraso.
    #
    # • Para operações pós-fixadas CDI, considera os dias úteis bancários entre a data prevista para o pagamento
    #   ordinário e a data do pagamento em atraso.
    #
    # Fator de juros moratórios, "f_2"
    # --------------------------------
    #
    # Tanto para operações pré-fixadas, quanto pós-fixadas, é calculado a partir de uma taxa fixa mensal por atraso
    # ("fee_rate"), considerando os dias corridos entre a data prevista para o pagamento ordinário e a data do
    # pagamento em atraso. Observe, entretanto, que esse fator considera a fórmula de juros simples, e mês com duração
    # de 30 dias corridos.
    #
    # Fator de multa, "f_3"
    # ---------------------
    #
    # A multa é fixa ("fine_rate"). Não há variação do fator de acordo com a extensão do período em atraso.
    #
    f_1 = f_2 = f_3 = _1

    if not loan_vir:
        dcp = decimal.Decimal((arrears_period[1] - arrears_period[0]).days)
        f_1 = calculate_interest_factor(loan_apy, dcp / decimal.Decimal(360))
        f_2 = _1 + (fee_rate / decimal.Decimal(100)) * (dcp / decimal.Decimal(30))
        f_3 = _1 + (fine_rate / decimal.Decimal(100))

    elif loan_vir and loan_vir.code == 'CDI':
        dcp = decimal.Decimal((arrears_period[1] - arrears_period[0]).days)
        f_v = loan_vir.backend.calculate_cdi_factor(arrears_period[0], arrears_period[1], loan_vir.percentage)
        f_s = calculate_interest_factor(loan_apy, decimal.Decimal(f_v.amount) / decimal.Decimal(252))
        f_1 = f_v.value * f_s
        f_2 = _1 + (fee_rate / decimal.Decimal(100)) * (dcp / decimal.Decimal(30))
        f_3 = _1 + (fine_rate / decimal.Decimal(100))

    elif loan_vir:
        raise NotImplementedError()

    v_1 = (outstanding_balance) * (f_1 - _1)  # Valor de juros remuneratórios. ATENÇÃO: não quantizar aqui.
    v_2 = (outstanding_balance + v_1) * (f_2 - _1)  # Valor de juros moratórios. ATENÇÃO: não quantizar aqui.
    v_3 = (outstanding_balance + v_1 + v_2) * (f_3 - _1)  # Valor de multa. ATENÇÃO: não quantizar aqui.
    out = types.SimpleNamespace()  # FIXME: create a data class for this.

    out.extra_gain = _Q(v_1)
    out.penalty = _Q(v_2)
    out.fine = _Q(v_3)

    return out

# FIXME: remover essa rotina. Criar uma auxiliar nos módulos que precisem de lidar com uma prestação de atraso entrando
# e outra saindo. Tal auxiliar deve usar a rotina "get_delinquency_charges" para calcular os valores do atraso.
#
@typeguard.typechecked
def get_late_payment(
    in_pmt: t.Union[LatePayment, LatePriceAdjustedPayment],

    # Atraso, data do pagamento.
    calc_date: datetime.date,

    # Dados extras do pagamento. FIXME: os campos abaixo poderiam ser parte da classe Payment, como meta dados.
    apy: decimal.Decimal,  # Taxa anual de juros remuneratórios a.a. (spread).
    zero_date: datetime.date,  # Data inicial do cronograma de pagamentos, para cálculo do I.R.
    vir: t.Optional[VariableIndex] = None,  # Índice variável.

    # Atraso, taxas praticadas.
    fee_rate: decimal.Decimal = LatePayment.FEE_RATE,
    fine_rate: decimal.Decimal = LatePayment.FINE_RATE,

    # Dados extras para o índice de correção.
    pla_operations: t.List[t.Tuple[datetime.date, bool, PriceLevelAdjustment]] = []
) -> t.Union[LatePayment, LatePriceAdjustedPayment]:
    '''Generates a late payment output.'''

    f_1 = f_2 = f_3 = f_c = _1

    if not vir:
        dcp = decimal.Decimal((calc_date - in_pmt.date).days)
        f_1 = calculate_interest_factor(apy, dcp / decimal.Decimal(360))
        f_2 = _1 + (fee_rate / decimal.Decimal(100) * dcp / decimal.Decimal(30))
        f_3 = _1 + (fine_rate / decimal.Decimal(100)) if in_pmt.date < calc_date else _1

    elif vir and vir.code == 'CDI':
        dcp = decimal.Decimal((calc_date - in_pmt.date).days)
        f_v = vir.backend.calculate_cdi_factor(in_pmt.date, calc_date, vir.percentage)
        f_s = calculate_interest_factor(apy, decimal.Decimal(f_v.amount) / decimal.Decimal(252))
        f_1 = f_v.value * f_s
        f_2 = _1 + (fee_rate / decimal.Decimal(100) * dcp / decimal.Decimal(30))
        f_3 = _1 + (fine_rate / decimal.Decimal(100)) if in_pmt.date < calc_date else _1

    elif vir and vir.code == 'IPCA':
        dcp = decimal.Decimal((calc_date - in_pmt.date).days)
        f_1 = calculate_interest_factor(apy, dcp / decimal.Decimal(360))
        f_2 = _1 + (fee_rate / decimal.Decimal(100) * dcp / decimal.Decimal(30))
        f_3 = _1 + (fine_rate / decimal.Decimal(100)) if in_pmt.date < calc_date else _1
        f_c = _1

        # Composição do parâmetro "pla_operations":
        #
        # 1. Data de cálculo do fator de correção.
        # 2. Se deve considerar o período anterior ou posterior à data de cálculo.
        # 3. Informações adicionais para o cálculo do fator de correção (PLA).
        #
        for e_1 in pla_operations:
            if e_1[2].code == 'IPCA':
                e_2 = ((x := e_1[0].replace(day=1)), x + _MONTH)  # Armazena as datas do último e do próximo aniversário.
                dcp = decimal.Decimal((e_1[0] - e_2[0]).days) if e_1[1] else decimal.Decimal((e_2[1] - e_1[0]).days)
                dct = decimal.Decimal((e_2[1] - e_2[0]).days)
                kwa: t.Dict[str, t.Any] = {}

                kwa['base'] = e_1[2].base_date
                kwa['period'] = e_1[2].period
                kwa['shift'] = e_1[2].shift
                kwa['ratio'] = dcp / dct

                f_c = f_c * vir.backend.calculate_ipca_factor(**kwa)

            else:
                raise NotImplementedError()

    elif vir:
        raise NotImplementedError()

    if not vir or vir.code == 'CDI':
        v_1 = (in_pmt.raw) * (f_1 - _1)  # Valor de juros remuneratórios. ATENÇÃO: não quantizar aqui.
        v_2 = (in_pmt.raw + v_1) * (f_2 - _1)  # Valor de juros moratórios. ATENÇÃO: não quantizar aqui.
        v_3 = (in_pmt.raw + v_1 + v_2) * (f_3 - _1)  # Valor de multa. ATENÇÃO: não quantizar aqui.
        val = in_pmt.gain + in_pmt.extra_gain + in_pmt.penalty + in_pmt.fine + _Q(v_1) + _Q(v_2) + _Q(v_3)
        o_1 = LatePayment()

        o_1.no = in_pmt.no
        o_1.date = calc_date
        o_1.raw = in_pmt.amort + val
        o_1.tax = _Q(val * calculate_revenue_tax(zero_date, calc_date))
        o_1.net = o_1.raw - o_1.tax
        o_1.gain = in_pmt.gain
        o_1.amort = in_pmt.amort
        o_1.bal = in_pmt.bal
        o_1.extra_gain = _Q(v_1)
        o_1.penalty = _Q(v_2)
        o_1.fine = _Q(v_3)

        return o_1

    else:  # IPCA.
        o_2 = LatePriceAdjustedPayment()
        raw = _Q(in_pmt.raw * f_c)
        gain = _Q(in_pmt.gain * f_c)
        extra_gain = _Q(in_pmt.extra_gain * f_c)
        penalty = _Q(in_pmt.penalty * f_c)
        fine = _Q(in_pmt.fine * f_c)

        if type(in_pmt) is LatePriceAdjustedPayment:
            pla = _Q(in_pmt.pla + (in_pmt.amort + in_pmt.pla) * (f_c - _1))

        v_1 = (raw) * (f_1 - _1)  # Valor de juros remuneratórios.
        v_2 = (raw + v_1) * (f_2 - _1)  # Valor de juros moratórios.
        v_3 = (raw + v_1 + v_2) * (f_3 - _1)  # Valor de multa.

        v_1 = _Q(v_1)  # ATENÇÃO: deve quantizar aqui?
        v_2 = _Q(v_2)  # ATENÇÃO: deve quantizar aqui?
        v_3 = _Q(v_3)  # ATENÇÃO: deve quantizar aqui?

        v_4 = raw + (v_1 + v_2 + v_3)
        v_5 = gain + extra_gain + penalty + fine + (v_1 + v_2 + v_3) + pla

        o_2.no = in_pmt.no
        o_2.date = calc_date
        o_2.raw = v_4
        o_2.tax = _Q(v_5 * calculate_revenue_tax(zero_date, calc_date))
        o_2.net = o_2.raw - o_2.tax
        o_2.gain = in_pmt.gain
        o_2.amort = in_pmt.amort
        o_2.bal = in_pmt.bal

        if type(in_pmt) is LatePriceAdjustedPayment:
            o_2.pla = pla

        o_2.extra_gain = extra_gain + v_1 + (gain - in_pmt.gain)
        o_2.penalty = penalty + v_2
        o_2.fine = fine + v_3

        return o_2
# }}}

if __name__ == '__main__':
    import doctest

    doctest.testmod()

# vi:fdm=marker:
