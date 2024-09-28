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
#     • Covers 100% of cases in Custom Amortization mode.
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
#       kargs = { … }  # Options for a Custom Amortization System, including a calculation date.
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

Its main purpose is to generate payments for loans with a Bullet, Price, American Amortization, or Custom (constant
amortization, grace period, etc.) systems. Supports fixed-rate operations, or indexed to CDI, Brazilian Savings, or
IPCA. Accounts for interest in a 252 business day year for CDI; or 30/360 basis for fixed-rate and other indexes.

This library also generates daily returns tables for loans. It covers the same modalities and the same capitalization
forms as the payments generation routine.

The library supports not only regular flows, but also irregular ones, with prepayments, and assists in the calculation
of arrears.

You can find the code for this module in the IPython notebook "fincore-01.ipynb" located in the support folder.
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

# Income tax table for fixed income investments.
#
# I know that "sys.maxsize" is not the maximum value of an integer in Python 3, but rather the maximum word size in the
# architecture where the interpreter is running.
#
#   https://stackoverflow.com/a/7604981
#
# I don't care. What I want in the last entry of the table is just a sufficiently large number.
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
    2022-06-12, and the day of the month is 15, then the surrounding dates are
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
     (1, True, 1, False, 4),
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
    ValueError: iterable B, item "5" found multiple times

      ADENDUM: Here lies our problem with multiple prepayments on the same day, among other things. This error is good, because
      ADENDUM: at the moment the controllers are not well tested, and there was an attempt to submit a single prepayment
      ADENDUM: more than once. It happened with the Mariana Castro on August 1, 2023. She had a flow of total prepayment
      ADENDUM: generation interrupted by an error in the request. When trying to resume the process, in a subsequent request,
      ADENDUM: the controller passed again through investments that already had the prepayment generated, and tried to insert it again.
      ADENDUM: If it weren't for this protection, we would have a data schema error.
      ADENDUM:
      ADENDUM: As soon as we have better coverage in the prepayment generation controllers, partial payments, etc., we can
      ADENDUM: remove this limitation. After all, it is arbitrary. From the Fincore point of view, the order of two prepayments
      ADENDUM: on the same day is given by the position in the list. It is also necessary to have test cases for consecutive
      ADENDUM: prepayments with the various financial indexers supported by Fincore, before removing this lock.
      ADENDUM:
      ADENDUM: It is worth remembering that if there are multiple prepayments on the same day, the trivial approach would be to
      ADENDUM: sum up their gross values.

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
            raise ValueError(f'iterable A, item "{sav_a}" found multiple times')

        elif sav_b and val_b and key(sav_b) > key(val_b):
            raise ValueError('iterable B is not ordered')

        elif sav_b and val_b and key(sav_b) == key(val_b):  # Ver o adendo na "docstring" da rotina. FIXME.
            raise ValueError(f'iterable B, item "{sav_b}" found multiple times')

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

      • "price_level_adjustment", which is a "PriceLevelAdjustment" instance.

      • "dct_override", an override for the DCT calculation. See "DctOverride" below.

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

        # Maximum value. Ver "http://stackoverflow.com/a/28082106".
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

    FEE_RATE: t.ClassVar[decimal.Decimal] = _1  # Montly Late Fee Rate.

    FINE_RATE: t.ClassVar[decimal.Decimal] = _1 + _1  # Fine rate (single application).

    extra_gain: decimal.Decimal = _0

    penalty: decimal.Decimal = _0

    fine: decimal.Decimal = _0

# FIXME: remove this class.
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
        Returns the list of Brazilian Savings indexes between the begin and end date.

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
        Calculates the DI (CDI) factor for a given period.

        The CDI correction indices in the tests below were taken from the BACEN website:

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

        Note that it's not possible to write tests for projected indices. This function will use the last index published
        by BACEN to estimate future values. A new index may be published, changing the result of the factor computation,
        causing the test to fail.
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
        '''Calculates the Brazilian Savings factor for a given period.'''

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
        Calculates the IPCA correction factor.

        Takes as parameters the base date, period, shift, and a fraction for the last correction rate.
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
        '''Calculates the IGPM correction factor.'''

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

# Public API. Payments table. {{{
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
    Generates a payment schedule for a given loan.

    To understand how to invoke this function, consider the following sentence:

      "Return the payments for a loan of amount V, at an annual rate TA, on dates D."

    From this sentence, we can derive the three required and positional parameters for this routine:

      • "principal", which is the principal amount of the loan, or V.

      • "apy", which is the nominal annual spread TA (annual percentage yield).

      • "amortizations", which is a list containing the dates D when amortizations should occur.

    The remaining parameters are associative.

      • "vir", which is a variable index, which can be either a CDI or Brazilian Savings index; or a price level index:
      IPCA or IGPM. When provided, the returned payments will incur, in addition to the fixed rate "apy", a variable
      rate that will be computed according to the index value in the period. It should be an instance of VariableIndex.
      If omitted, the interest rate will be fixed.

      • "capitalisation", configures one of four interest composition methods.

        – "360" is daily capitalisation in a year with 360 days. Used in Bullet operations.

        – "30/360" is monthly capitalisation in a year with 12 months and 30 days. Used in fixed-rate operations with
          American Amortization, Price, or Custom System.

        – "252" is capitalisation of interest in a year with 252 business days. Used in post-fixed CDI operations with
          Bullet, American, or Custom System.

        – "365" is capitalisation of interest in a year with 365 days. This mode should not be used. It's only used to
          emulate legacy Bullet operations that adopted this composition method in the past. Fincore will issue a warning
          if this mode is requested.

      • "calc_date", is a cut-off date for payment calculation. Payments after the specified date will not be emitted.
        Useful to know the position of a loan on a given date. Avoids unnecessary payment calculation.

      • "tax_exempt", when true, indicates that the payments are tax-exempt.

    • "gain_output", is the interest output mode.

        – "current" is the default mode. Makes each payment P return only the interest accrued in the period between the
          previous payment and the current one.

        – "settled" makes each payment P return the interest to be paid by the borrower. Remember that the interest to be
          paid may not be equal to the interest accrued in the period. If there's a grace period, a certain payment may
          not have interest settlement. Or a payment after a grace period may have a deferred interest component, in
          addition to what accrued in the period.

        – "deferred" makes the interest accrued in the current period, plus the accrued from previous periods, be returned.

    Returns a list where each object P contains the information of a payment: its date, the gross amount to be paid, the
    tax, the net amount, the principal amortization value, the interest value, etc. It's an instance of Payment, for
    non-price-level-adjusted operations; or of PriceAdjustedPayment, for price-level-adjusted operations. See the
    documentation for these classes for more details about these data structures.
    '''

    def calc_balance() -> decimal.Decimal:
        val = principal * f_c + regs.interest.accrued - regs.principal.amortized.total * f_c - regs.interest.settled.total

        return t.cast(decimal.Decimal, val)

    # First principal generator.
    #
    #  • "principal.amortization_ratio.current", is the current period's amortization percentage.
    #  • "principal.amortized.current", is the principal amortized in the current period.
    #  • "principal.amortized.total", is the total principal amortized (current period plus past periods).
    #
    def track_principal_1() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            ratio = yield

            # If the current amortization percentage plus the accumulated percentage exceeds 100%, an adjustment must be made.
            if regs.principal.amortization_ratio.current + ratio > _1:
                ratio = _1 - regs.principal.amortization_ratio.current

            if ratio:
                regs.principal.amortization_ratio.current += ratio
                regs.principal.amortized = types.SimpleNamespace(current=ratio * principal, total=regs.principal.amortization_ratio.current * principal)

            else:
                regs.principal.amortized = types.SimpleNamespace(current=_0, total=regs.principal.amortized.total)

    # Second principal generator.
    #
    #  • "principal.amortization_ratio.regular", is the regular amortization percentage accumulated (current period plus past periods)
    #
    def track_principal_2() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            ratio = yield

            # If the regular amortization percentage plus the accumulated percentage exceeds 100%, an adjustment must be made.
            if regs.principal.amortization_ratio.regular + ratio > _1:
                ratio = _1 - regs.principal.amortization_ratio.regular

            if ratio:
                regs.principal.amortization_ratio.regular += ratio

    # Interest generator.
    #
    #   • "interest.current" is the interest accrued (produced) in the current period.
    #   • "interest.accrued" is the total interest accrued since the zero day of the payment schedule.
    #   • "interest.deferred" is the total deferred interest from past periods.
    #
    def track_interest_1() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            regs.interest.current = yield
            regs.interest.accrued += regs.interest.current
            regs.interest.deferred = regs.interest.accrued - (regs.interest.current + regs.interest.settled.total)

    # Interest settled generator between borrower and creditor.
    #
    #   • "interest.settled.current" is the interest settled in the current period.
    #   • "interest.settled.total" is the total interest settled since the zero day of the payment schedule.
    #
    def track_interest_2() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            regs.interest.settled = types.SimpleNamespace(current=(yield), total=regs.interest.settled.total)
            regs.interest.settled.total += regs.interest.settled.current

    # A. Validation and preparation.
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

    # Registers.
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

    # B. Execution.
    for num, (ent0, ent1) in enumerate(itertools.pairwise(amortizations), 1):
        due = min(calc_date.value, ent1.date)
        f_s = f_c = _1

        # Phase B.0, FZA, or Phase Zille-Anna.
        #
        #  • Calculates FS (spread factor) for fixed-rate index; and both FS and FC for price level index.
        #  • Calculates FS for post-fixed index (CDI, Brazilian Savings etc). In this case, there's no price level
        #  adjustment.
        #
        if ent0.date < calc_date.value or ent1.date <= calc_date.value:
            if not vir and capitalisation == '360':  # Bullet.
                f_s = calculate_interest_factor(apy, decimal.Decimal((due - ent0.date).days) / decimal.Decimal(360))

            elif not vir and capitalisation == '365':  # Bullet in legacy mode.
                f_s = calculate_interest_factor(apy, decimal.Decimal((due - ent0.date).days) / decimal.Decimal(365))

            elif not vir and capitalisation == '30/360':  # American Amortization, Price, Custom.
                dcp = (due - ent0.date).days
                dct = (ent1.date - ent0.date).days

                # Exclusively for the first anniversary date, "DCT" will be considered as the difference in calendar days
                # between the 24th day before and the 24th day after the disbursement date (start of accrual).
                #
                if ent1.dct_override and num == 1:
                    dct = _diff_surrounding_dates(ent0.date, 24)

                # When there are extraordinary advancements in the schedule, "DCT" will be calculated using the regular
                # flow dates.
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

            elif vir and vir.code == 'CDI' and capitalisation == '252':  # Bullet, American Amortization, Custom.
                f_v = vir.backend.calculate_cdi_factor(ent0.date, due, vir.percentage)  # Variable rate (or factor), FV.
                f_s = calculate_interest_factor(apy, decimal.Decimal(f_v.amount) / decimal.Decimal(252)) * f_v.value

            elif vir and vir.code == 'Poupança' and capitalisation == '360':  # Brazilian Savings only supported in Bullet.
                f_v = vir.backend.calculate_savings_factor(ent0.date, due, vir.percentage)  # Variable rate (or factor), FV.
                f_s = calculate_interest_factor(apy, decimal.Decimal((due - ent0.date).days) / decimal.Decimal(360)) * f_v.value

            elif vir and vir.code == 'IPCA' and capitalisation == '360':  # Bullet.
                f_s = calculate_interest_factor(apy, decimal.Decimal((due - ent0.date).days) / decimal.Decimal(360))

                if type(ent1) is Amortization and ent1.price_level_adjustment:
                    kw1a: t.Dict[str, t.Any] = {}

                    kw1a['base'] = ent1.price_level_adjustment.base_date
                    kw1a['period'] = ent1.price_level_adjustment.period
                    kw1a['shift'] = ent1.price_level_adjustment.shift
                    kw1a['ratio'] = _1  # Adjustment for the last correction rate.

                    # Lock the price level factor. The minimum factor is one, i.e., the correction value must be positive.
                    f_c = max(vir.backend.calculate_ipca_factor(**kw1a), _1)

                # In the case of an advancement, the price level adjustment must be paid ("ent1" doesn't have the "price_level_adjustment" attribute).
                elif type(ent1) is Amortization.Bare:
                    kw1b: t.Dict[str, t.Any] = {}

                    kw1b['base'] = amortizations[0].date.replace(day=1)
                    kw1b['period'] = _delta_months(ent1.date, amortizations[0].date)
                    kw1b['shift'] = 'M-1'  # FIXME.
                    kw1b['ratio'] = _1  # Adjustment for the last correction rate.

                    # Lock the price level factor. The minimum factor is one, i.e., the correction value must be positive.
                    f_c = max(vir.backend.calculate_ipca_factor(**kw1b), _1)

            elif vir and vir.code == 'IPCA' and capitalisation == '30/360':  # American and Custom Amortization systems.
                dcp = (due - ent0.date).days
                dct = (ent1.date - ent0.date).days

                # Exclusively for the first anniversary date, "DCT" will be considered as the difference in calendar days
                # between the 24th day before and the 24th day after the disbursement date (start of accrual).
                #
                if ent1.dct_override and num == 1:
                    dct = _diff_surrounding_dates(ent0.date, 24)

                # When there are extraordinary advancements in the schedule, "DCT" will be calculated using the regular
                # flow dates.
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
                    dcp = (due - ent0.date).days  # "30/360" spec needs a ratio for the IPCA factor.
                    dct = (ent1.date - ent0.date).days

                    if type(ent1) is Amortization and ent1.price_level_adjustment:
                        kw2['base'] = ent1.price_level_adjustment.base_date
                        kw2['period'] = ent1.price_level_adjustment.period
                        kw2['shift'] = ent1.price_level_adjustment.shift
                        kw2['ratio'] = _1  # Adjustment for the last correction rate.

                    else:
                        kw2['base'] = amortizations[0].date.replace(day=1)
                        kw2['period'] = _delta_months(ent1.date, amortizations[0].date)
                        kw2['shift'] = 'M-1'  # FIXME.
                        kw2['ratio'] = _1  # Adjustment for the last correction rate.

                    # Exclusively for the first anniversary date, "DCT" will be considered as the difference in calendar
                    # days between the 24th day before and the 24th day after the disbursement date (start of accrual).
                    #
                    if ent1.dct_override and num == 1:
                        dct = _diff_surrounding_dates(ent0.date, 24)

                    # When there are extraordinary advancements in the schedule, "DCT" will be calculated using the regular
                    # flow dates.
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

                    f_c = max(vir.backend.calculate_ipca_factor(**kw2), _1)  # Lock the price level factor.

            elif vir:
                raise NotImplementedError(f'Combination of variable interest rate {vir} and capitalisation {capitalisation} unsupported')

            else:
                raise NotImplementedError(f'Unsupported capitalisation {capitalisation} for fixed interest rate')

        # Phase B.1, FRU, or Phase Rafa Um.
        #
        # Using the factors calculated in the previous phase, calculates and registers the variations in principal, interest,
        # and price level adjustment.
        #
        # [ADJUSTMENT-FACTOR]
        #
        # Inserting a partial advancement in the payment schedule causes the principal amortization percentages after that
        # advancement to need to be updated. This update is done in such a way that the new amortization percentage (Pn)
        # of an arbitrary payment should be equal to the old percentage (Pa) multiplied by an adjustment factor (ADJ).
        #
        #                                                  ACUR
        #                                          ADJ = ————————
        #                                                  AREG
        #
        # Where ACUR is the remaining amortization percentage of the payment flow, including extraordinary amortizations
        # (advancements), and AREG is the remaining regular amortization percentage of the payment flow.
        #
        if ent0.date < calc_date.value or ent1.date <= calc_date.value or calc_date.runaway:
            # Register the interest accrued in the period.
            gens.interest_tracker_1.send(calc_balance() * (f_s - _1))

            # Register the price level adjustment for the period (FIXME: implement).
            # gens.price_level_tracker_1.send(…)

            # Case of a regular amortization.
            if type(ent1) is Amortization:
                adj = (_1 - regs.principal.amortization_ratio.current) / (_1 - regs.principal.amortization_ratio.regular)  # [ADJUSTMENT-FACTOR].

                # Register the principal amortization percentage.
                gens.principal_tracker_1.send(ent1.amortization_ratio * adj)

                # Register the regular principal amortization percentage.
                gens.principal_tracker_2.send(ent1.amortization_ratio)

                # Register the interest to be paid in the period.
                if ent1.amortizes_interest:
                    gens.interest_tracker_2.send(regs.interest.current + regs.principal.amortization_ratio.current * regs.interest.deferred)

                # Register the price level adjustment to be paid in the period (FIXME: implement).
                # gens.price_level_tracker_2.send(…)

            # Case of an advancement (extraordinary amortization).
            #
            # Remember that an advancement has only a gross value that will be paid on a certain date. This gross value
            # will be factored into various components of the debt, in a specific order. The first component of the debt
            # to be amortized is the spread. After paying the spread, the remaining amount should be deducted from the
            # price level adjustment. Finally, the remaining amount will be deducted from the principal. In the code
            # block below,
            #
            #  • "val1" is the interest to be paid.
            #
            #  • "val2" is the price level adjustment to be paid. FIXME: the variable "plfv" should be multiplied by the
            #    principal amortization percentage of the period, and not by the decimal one.
            #
            #  • "val3" is the principal to be amortized.
            #
            # Observe that the order of calculation of these variables corresponds to the order of factoring the gross
            # advancement value.
            #
            else:
                ent1 = t.cast(Amortization.Bare, ent1)  # Mypy can't infer the type of the "ent1" variable here.
                plfv = principal * (_1 - regs.principal.amortization_ratio.current) * (f_c - _1)  # Price level, full value.
                val0 = min(ent1.value, calc_balance())
                val1 = min(val0, regs.interest.accrued - regs.interest.settled.total)
                val2 = min(val0 - val1, plfv * _1)
                val3 = val0 - val1 - val2

                # Check if the irregular payment value doesn't exceed the remaining balance.
                if ent1.value != Amortization.Bare.MAX_VALUE and ent1.value > _Q(calc_balance()):
                    raise Exception(f'the value of the amortization, {ent1.value}, is greater than the remaining balance of the loan, {_Q(calc_balance())}')

                # Register the principal amortization percentage.
                gens.principal_tracker_1.send(val3 / principal)

                # Register the interest to be paid in the period.
                gens.interest_tracker_2.send(val1)

                # Register the price level adjustment to be paid in the period (FIXME: implement).
                # gens.price_level_tracker_2.send(val2)

        # Phase B.2, FRD, or Phase Rafa Dois.
        #
        # Builds the payment instance, output of the routine. Performs rounding.
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

                # Amortizes principal, does not incorporate interest.
                if pmt.amort and ent1.amortizes_interest:
                    pmt.raw = pmt.amort + (j_f := regs.interest.settled.current if ent1.amortizes_interest else _0)
                    pmt.tax = j_f * calculate_revenue_tax(amortizations[0].date, due)

                # Amortizes principal, incorporates interest.
                elif pmt.amort:
                    pmt.raw = pmt.amort
                    pmt.tax = _0

                # Does not amortize principal, does not incorporate interest.
                elif ent1.amortizes_interest:
                    pmt.raw = j_f = regs.interest.settled.current if ent1.amortizes_interest else _0
                    pmt.tax = j_f * calculate_revenue_tax(amortizations[0].date, due)

                # Does not amortize principal, incorporates interest.
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

            # Applies the price level adjustment to the gross value and the revenue tax.
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

# Public API. Daily returns. {{{
@typeguard.typechecked
def get_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    amortizations: t.List[Amortization | Amortization.Bare], *,
    vir: t.Optional[VariableIndex] = None,
    capitalisation: _CAPITALISATION = '360',
    is_bizz_day_cb: t.Callable[[datetime.date], bool] = lambda _: True
) -> t.Iterable[DailyReturn]:
    '''
    Generates a yield table for a given loan.

    This function has a signature similar to "fincore.get_payments_table". To understand how to invoke this function,
    use the following phrase as a basis:

      "Return the daily yields of a loan with a value V, at an annual rate AR, on dates D."

    From this elaboration, we get the three mandatory and positional parameters of this routine:

      • "principal", is the principal amount of the loan, or V.

      • "apy", is the nominal annual spread rate AR (annual percentage yield).

      • "amortizations", which is a list containing the dates D when amortizations should be made.

    Two other parameters are optional: "vir", which specifies a variable index, which can be CDI, Brazilian Savings,
    IPCA, or IGPM; and "capitalisation", which configures the form of interest compounding. See the documentation of
    the "fincore.get_payments_table" routine for more details on these parameters.

    Returns a list of "DailyReturn" objects, which contain daily information on the loan position:

      • "date", is the date of the yield.

      • "value", is the yield value for the day.

      • "bal", is the loan's outstanding balance at the end of the day, that is, considering the day's yield and any
        extraordinary payments made. The initial balance of day D, "D.bal", must obviously be equal to the balance at
        the end of the previous day, "D₋₁.bal".

        Be aware that the expression "D.bal - D.value" does not give the initial balance of the day. For two reasons:

        1. Rounding errors. The output of this routine is quantized, but its internal memory is not. Expect a difference
           of one cent sporadically.

        2. There will be days when payments are made, and this routine does not return them. In fact, the formula for
           the initial balance is "D.bal - Σ D.inflows + Σ D.outflows", where "D.inflows" would be the day's inflows,
           i.e., the yield; and "D.outflows" the outflows, or payments, of the day. This calculation also suffers from
           rounding errors, for the same reason as the previous item: the routine quantizes internal values only before
           returning them.

      • "fixed_factor", is the interest factor used to calculate the fixed component of the day's yield.

      • "variable_factor", is the interest factor used to calculate the variable component of the day's yield.
    '''

    # Some indexes are only published by supervisor bodies on business days. For example, Brazilian DI. On such cases
    # this function will fill in the gaps, i.e., provide a zero value if the upstream misses it.
    #
    def get_normalized_cdi_indexes(backend: IndexStorageBackend) -> t.Iterator[decimal.Decimal]:
        # Some implementations of the "get_cdi_indexes" function return a generator, others return a list. Therefore,
        # I'm forcing the conversion to a list to meet both possibilities.
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

    # First generator for principal values.
    #
    #  • "principal.amortization_ratio.current", is the percentage of amortization of the current period.
    #  • "principal.amortized.current", is the value amortized in the current period.
    #  • "principal.amortized.total", is the total amortized value (current period plus past periods).
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

    # Second generator for principal values.
    #
    #  • "principal.amortization_ratio.regular", is the regular amortization percentage accumulated (current period plus past periods)
    #
    def track_principal_2() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            ratio = yield

            # Se o percentual de amortização regular somado ao acumulado ultrapassar 100%, um reajuste deve ser feito.
            if regs.principal.amortization_ratio.regular + ratio > _1:
                ratio = _1 - regs.principal.amortization_ratio.regular

            if ratio:
                regs.principal.amortization_ratio.regular += ratio

    # Generator for interest values.
    #
    #   • "interest.daily" is the accrued interest (produced) on the day.
    #   • "interest.current" is the accrued interest (produced) on the current period.
    #   • "interest.accrued" is the total of accrued interest since the start of the payments schedule.
    #   • "interest.deferred" is the total of deferred interest from past periods.
    #
    def track_interest_1() -> t.Generator[None, decimal.Decimal | None, None]:
        while True:
            regs.interest.daily = yield
            regs.interest.current += regs.interest.daily
            regs.interest.accrued += regs.interest.daily
            regs.interest.deferred = regs.interest.accrued - (regs.interest.current + regs.interest.settled.total)

    # Generator for settled interest values.
    #
    #   • "interest.settled.current" are the settled interest on the current period.
    #   • "interest.settled.total" is the total of settled interest since the start of the payments schedule.
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

    # B. Execute.
    itr = iter(amortizations)
    tup = next(itr), next(itr)
    end = amortizations[-1].date
    cnt = p = 1
    buf = _0

    # Compensação para empréstimos que se encerram em dias não úteis.
    while not is_bizz_day_cb(end):
        end = end + datetime.timedelta(days=1)

    for ref in _date_range(amortizations[0].date, end):
        f_c = _1  # Taxa (ou fator) de correção, FC.
        f_v = _1  # Taxa (ou fator) variável, FV.
        f_s = _1  # Taxa (ou fator) fixo, FS.

        # Phase B.0, FZA, or Phase Zille-Anna.
        #
        #  • Calculate FS (spread factor) for fixed-rate index; and both FS and FC for price level index.
        #  • Calculate FS for post-fixed index (CDI, Brazilian Savings, etc). In this case there is no correction.
        #
        # Highly altered with respect to FZA from the "get_payments_table" routine.
        #
        if ref < amortizations[-1].date and not vir and capitalisation == '360':  # Bullet.
            f_s = calculate_interest_factor(apy, _1 / decimal.Decimal(360))

        elif ref < amortizations[-1].date and not vir and capitalisation == '365':  # Bullet in legacy mode.
            f_s = calculate_interest_factor(apy, _1 / decimal.Decimal(365))

        elif ref < amortizations[-1].date and not vir and capitalisation == '30/360':  # Juros mensais, Price, Livre.
            v01 = calculate_interest_factor(apy, _1 / decimal.Decimal(12)) - _1  # Fator mensal.

            # The first period has special handling here, to deal with variations in the loan anniversary.
            #
            # Example, the project of Resolvvi from June 2023. The first period has 32 days, instead of the expected 30
            # days – from 19/06/2023, inclusive, to 21/07/2023, exclusive. The end date of the first period was
            # shifted due to the loan anniversary, which is 21/12/2025.
            #
            # To account for cases where the start date of the loan's first period was altered in relation to its
            # start of yield, due to changes in the loan anniversary date, the calculation of the fixed interest rate
            # factor employs the difference in days between the start and end dates of the period.
            #
            # In any other period, it is sufficient to know the number of days in the month in which it begins.
            #
            # Observe that irregular amortizations do not define the intervals of a schedule's period. Therefore, the
            # following test is used to determine the period's interval.
            #
            if p == 1 and (type(tup[1]) is Amortization.Bare or ref < tup[1].date):
                v02 = decimal.Decimal((amortizations[1].date - amortizations[0].date).days)  # Dias no período.

            elif ref == tup[1].date:
                v02 = decimal.Decimal(calendar.monthrange(tup[1].date.year, tup[1].date.month)[1])  # Dias do mês do período.

            else:
                v02 = decimal.Decimal(calendar.monthrange(tup[0].date.year, tup[0].date.month)[1])  # Dias do mês do período.

            f_s = calculate_interest_factor(v01, _1 / v02, False)  # Fator diário.

        elif ref < amortizations[-1].date and vir and vir.code == 'CDI' and capitalisation == '252':  # Bullet, Juros mensais, Livre.
            f_v = next(idxs) * vir.percentage / decimal.Decimal(100) + _1

            # Note that the index on a 252 basis only earns on a business day. This is how the CDI works. In this case the
            # fixed factor must follow the variable. It should only be calculated on a business day.
            #
            # FIXME: if by chance the variable factor, "next(idxs)", is zero, and if it happens to be a business day, the
            # fixed factor will not be calculated. I've never seen the CDI be zero, but it's worth considering this case.
            # The correct thing to do below is to test if the day is a business day, not if the value of the factor "f_c"
            # is greater than one.
            #
            if f_v > _1:
                f_s = calculate_interest_factor(apy, _1 / decimal.Decimal(252))

        elif ref < amortizations[-1].date and vir and vir.code == 'Poupança' and capitalisation == '360':  # Poupança só suportada em Bullet.
            f_s = calculate_interest_factor(apy, _1 / decimal.Decimal(360))
            f_v = next(idxs) * vir.percentage / decimal.Decimal(100) + _1

        elif ref < amortizations[-1].date and vir and vir.code == 'IPCA' and capitalisation == '360':  # Bullet.
            raise NotImplementedError()  # FIXME: implementar.

        elif ref < amortizations[-1].date and vir and vir.code == 'IPCA' and capitalisation == '30/360':  # Juros mensais e Livre.
            raise NotImplementedError()  # FIXME: implementar.

        elif ref < amortizations[-1].date and vir:
            raise NotImplementedError(f'Combination of variable interest rate {vir} and capitalisation {capitalisation} unsupported')

        elif ref < amortizations[-1].date:
            raise NotImplementedError(f'Unsupported capitalisation {capitalisation} for fixed interest rate')

        # Phase B.1, FRU, or Phase Rafa Um. Slightly altered with respect to FRU from the "get_payments_table" routine.
        while ref < amortizations[-1].date and ref == tup[1].date:
            if not buf and not is_bizz_day_cb(ref):
                buf = _Q(calc_balance())

            if type(tup[1]) is Amortization:  # Case of a regular amortization.
                adj = (_1 - regs.principal.amortization_ratio.current) / (_1 - regs.principal.amortization_ratio.regular)  # [FATOR-AJUSTE].

                # Registers the principal amortization percentage.
                gens.principal_tracker_1.send(tup[1].amortization_ratio * adj)

                # Registers the regular principal amortization percentage.
                gens.principal_tracker_2.send(tup[1].amortization_ratio)

                # Registers the interest value to be paid in the period.
                if tup[1].amortizes_interest:
                    gens.interest_tracker_2.send(regs.interest.current + regs.principal.amortization_ratio.current * regs.interest.deferred)

                # Registers the price level value to be paid in the period (FIXME: implement).
                # gens.price_level_tracker_2.send(…)

                # Ends the interest accumulator from the previous period.
                regs.interest.current = _0

                p += 1  # The period only increments in the case of regular amortizations.

                cnt = 1

            # Case of an advance (extraordinary amortization).
            #
            # Remember that an advance presents only a gross value to be paid on a certain date. This gross value will be
            # factored into various components of the debt, in an ordered manner. The first component of the debt to be
            # amortized is the interest (spread). After payment of the interest, what remains must be deducted from the
            # monetary correction. Finally, subtract the remaining value of the principal. In the block of code below,
            #
            #  • "val1" is the value of interest to be paid.
            #
            #  • "val2" is the value of the correction to be paid. FIXME: the variable "plfv" should be multiplied by the
            #    principal amortization ratio of the period, and not by the decimal one.
            #
            #  • "val3" is the value to amortize the principal.
            #
            # Observe that the order of calculation of these variables corresponds to the order of factorisation of the
            # gross value of the advance.
            #
            else:
                ent = t.cast(Amortization.Bare, tup[1])  # O Mypy não consegue inferir o tipo da variável "ent" aqui.
                plfv = principal * (_1 - regs.principal.amortization_ratio.current) * (f_c - _1)  # Price level, full value.
                val0 = min(ent.value, calc_balance())
                val1 = min(val0, regs.interest.accrued - regs.interest.settled.total)
                val2 = min(val0 - val1, plfv * _1)
                val3 = val0 - val1 - val2

                # Checks if the value of the irregular amortization does not exceed the remaining balance.
                if ent.value != Amortization.Bare.MAX_VALUE and ent.value > _Q(calc_balance()):
                    raise Exception(f'the value of the amortization, {ent.value}, is greater than the remaining balance of the loan, {_Q(calc_balance())}')

                # Registers the principal amortization percentage.
                gens.principal_tracker_1.send(val3 / principal)

                # Registers the interest value to be paid in the period.
                gens.interest_tracker_2.send(val1)

                # Registers the correction value to be paid in the period (FIXME: implement).
                # gens.price_level_tracker_2.send(val2)

                # Ends the interest accumulator from the previous period.
                regs.interest.current = _0

            tup = tup[1], next(itr)

        # Registers the value of the accrued interest on the day.
        gens.interest_tracker_1.send(calc_balance() * (f_s * f_v * f_c - _1))

        # Registers the correction value to be paid in the period (FIXME: implement).
        # gens.price_level_tracker_1.send(…)

        # If the balance is zero, and the current day is a business day, the schedule is over.
        if _Q(calc_balance()) == _0 and is_bizz_day_cb(ref):
            break

        # Builds the daily return instance, output of the routine. Makes rounding.
        dr = DailyReturn()

        dr.no = cnt
        dr.period = p
        dr.date = ref
        dr.value = _Q(regs.interest.daily)

        if buf and not is_bizz_day_cb(ref):
            buf = buf + dr.value

            dr.bal = buf  # Balance at the end of the day.

        else:
            buf = _0

            dr.bal = _Q(calc_balance())  # Balance at the end of the day.

        dr.fixed_factor = f_s
        dr.variable_factor = f_v * f_c

        yield dr

        cnt += 1
# }}}

# Public API. Factories. {{{
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

    # 1. Validate.
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

    # Base of calculation 365 only for historical fixed-rate. Fincore recommends using 360 days instead.
    if capitalisation == '365':
        _LOG.warning('capitalising 365 days per year exists solely for legacy Bullet support – prefer 360 days')

    # 2.1. Create the amortizations. Regular flow, without insertions. Fast.
    if not insertions and not vir:
        sched.append(Amortization(date=zero_date, amortizes_interest=False))
        sched.append(Amortization(date=anniversary_date or zero_date + _MONTH * term, amortization_ratio=_1))

        if anniversary_date:
            sched[-1].dct_override = DctOverride(anniversary_date, anniversary_date, predates_first_amortization=False)

    # 2.2. Create the amortizations. Regular flow with National Index of Consumer Prices, without insertions. Fast.
    elif not insertions and vir and vir.code == 'IPCA':
        dif = min(_delta_months(calc_date.value, zero_date), term) if calc_date else term
        pla = PriceLevelAdjustment('IPCA', base_date=zero_date.replace(day=1), period=dif)

        sched.append(Amortization(date=zero_date, amortizes_interest=False))
        sched.append(Amortization(date=anniversary_date or zero_date + _MONTH * term, amortization_ratio=_1, price_level_adjustment=pla))

        if anniversary_date:
            sched[-1].dct_override = DctOverride(anniversary_date, anniversary_date, predates_first_amortization=False)

    # 2.3. Create the amortizations. Insertions in the regular flow. Slow.
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

    # 1. Validate.
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

    # 2. Create the amortizations.
    if anniversary_date and anniversary_date == zero_date + _MONTH:
        anniversary_date = None

    # Regular flow, without insertions. Fast.
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

    # Insertions in the regular flow. Slow.
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

    # 1. Validate.
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

    # 2. Create the amortizations.
    if anniversary_date and anniversary_date == zero_date + _MONTH:
        anniversary_date = None

    # Regular flow, without insertions. Fast.
    lst1.append(Amortization(date=zero_date, amortizes_interest=False))  # Data zero (início do rendimento).

    for i, y in enumerate(amortize_fixed(principal, apy, term), 1):
        due = anniversary_date + _MONTH * (i - 1) if anniversary_date else zero_date + _MONTH * i

        lst1.append(Amortization(date=due, amortization_ratio=y))

        if i == 1 and anniversary_date:
            lst1[-1].dct_override = DctOverride(anniversary_date, anniversary_date, predates_first_amortization=False)

    # Insertions in the regular flow. Slow.
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

    # 1. Validate.
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

    # 2. Create the amortizations.
    if not insertions:  # Regular flow, without insertions.
        sched.extend(amortizations)

    else:  # Extraordinary flow, with insertions.
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
    Stereotypes an American Amortization operation.

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

# FIXME: renomear para "get_custom_payments".
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
    Builds a Custom payments schedule.

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
    capitalisation: _DAILY_CAPITALISATION = '360',
    is_bizz_day_cb: t.Callable[[datetime.date], bool] = lambda _: True
) -> t.Iterable[DailyReturn]:
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_bullet(zero_date, term, insertions, anniversary_date, capitalisation, vir, calc_date=None)
    kwa['vir'] = vir
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else capitalisation
    kwa['is_bizz_day_cb'] = is_bizz_day_cb

    yield from get_daily_returns(**kwa)

@typeguard.typechecked
def get_jm_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int, *,  # Junto com "zero_date", equivale ao "amortizations".
    insertions: t.List[Amortization.Bare] = [],
    anniversary_date: t.Optional[datetime.date] = None,
    vir: t.Optional[VariableIndex] = None,
    is_bizz_day_cb: t.Callable[[datetime.date], bool] = lambda _: True
) -> t.Iterable[DailyReturn]:
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_jm(zero_date, term, insertions, anniversary_date, vir)
    kwa['vir'] = vir
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else '30/360'
    kwa['is_bizz_day_cb'] = is_bizz_day_cb

    yield from get_daily_returns(**kwa)

@typeguard.typechecked
def get_price_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    zero_date: datetime.date,
    term: int, *,  # Junto com "zero_date", equivale ao "amortizations".
    insertions: t.List[Amortization.Bare] = [],
    anniversary_date: t.Optional[datetime.date] = None,
    is_bizz_day_cb: t.Callable[[datetime.date], bool] = lambda _: True
) -> t.Iterable[DailyReturn]:
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['amortizations'] = preprocess_price(principal, apy, zero_date, term, insertions, anniversary_date)
    kwa['capitalisation'] = '30/360'
    kwa['is_bizz_day_cb'] = is_bizz_day_cb

    yield from get_daily_returns(**kwa)

@typeguard.typechecked
def get_livre_daily_returns(
    principal: decimal.Decimal,
    apy: decimal.Decimal,
    amortizations: t.List[Amortization], *,
    insertions: t.List[Amortization.Bare] = [],
    vir: t.Optional[VariableIndex] = None,
    is_bizz_day_cb: t.Callable[[datetime.date], bool] = lambda _: True
) -> t.Iterable[DailyReturn]:
    kwa: t.Dict[str, t.Any] = {}

    kwa['principal'] = principal
    kwa['apy'] = apy
    kwa['vir'] = vir
    kwa['amortizations'] = preprocess_livre(amortizations, insertions, vir)
    kwa['capitalisation'] = '252' if vir and vir.code == 'CDI' else '30/360'
    kwa['is_bizz_day_cb'] = is_bizz_day_cb

    yield from get_daily_returns(**kwa)
# }}}

# Public API. Helpers. {{{
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

# FIXME: the routine does not support IPCA.
@typeguard.typechecked
def get_delinquency_charges(
    outstanding_balance: decimal.Decimal,  # Unpaid principal plus interest.
    arrears_period: t.Tuple[datetime.date, datetime.date],  # Arrear, or delinquency period.

    loan_apy: decimal.Decimal,  # Annual interest rate for remuneratory interest (spread).
    loan_vir: t.Optional[VariableIndex] = None,  # Variable index.

    fee_rate: decimal.Decimal = LatePayment.FEE_RATE,
    fine_rate: decimal.Decimal = LatePayment.FINE_RATE
) -> types.SimpleNamespace:
    '''
    Calculates extra charges for a delinquent loan.

      • "arrears_period" (t.Tuple[datetime.date, datetime.date]): the delinquency period, represented as a tuple with
        start and end dates.

      • "outstanding_balance" (decimal.Decimal): the loan's outstanding balance, including unpaid principal and interest, at
        the initial date.

      • "loan_apy" (decimal.Decimal): the annual interest rate for remuneratory interest (spread).

      • "loan_zero_date" (datetime.date): the initial date of the loan's payment schedule.

      • "loan_vir" (t.Optional[VariableIndex], optional): O índice variável, se aplicável. Padrão é None.

      • "fee_rate" (decimal.Decimal, optional): the fee rate. Default is LatePayment.FEE_RATE.

      • "fine_rate" (decimal.Decimal, optional): the fine rate. Default is LatePayment.FINE_RATE.

    Returns an object containing the delinquency charges calculated, including interest, mora, and fine.

    Example calculation of interest, mora, and fine, for a loan of R$ 10,000.00, with a fixed interest rate of 5% a.a.,
    performed on January 1, 2022, and with a delayed payment from January 1, 2023 to January 1, 2023:

        > get_delinquency_charges(  # doctest: +SKIP
            arrears_period=(datetime.date(2023, 1, 1), datetime.date(2023, 2, 1)),
            outstanding_balance=decimal.Decimal('10000.00'),
            loan_apy=decimal.Decimal('0.05'),
            loan_zero_date=datetime.date(2022, 1, 1)
        )
    '''

    # Interest factor, "f_1"
    # ----------------------
    #
    # Calculated based on the fixed annual interest rate of the operation (APY), but:
    #
    # • For fixed-rate operations, considers the number of days between the scheduled payment date and the payment
    #   date in arrears.
    #
    # • For CDI-linked operations, considers the number of business days between the scheduled payment date and the
    #   payment date in arrears.
    #
    # Penalty interest factor, "f_2"
    # ------------------------------
    #
    # For both fixed-rate and CDI-linked operations, calculated from a fixed monthly fee rate by delay
    # ("fee_rate"), considering the number of days between the scheduled payment date and the payment date in arrears.
    # Note, however, that this factor considers the simple interest formula, with a month of 30 days.
    #
    # Fine factor, "f_3"
    # ---------------------
    #
    # The fine is fixed ("fine_rate"). The factor does not vary according to the length of the delay period.
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

    v_1 = (outstanding_balance) * (f_1 - _1)  # Value of remuneratory interest. ATENTION: do not quantize here.
    v_2 = (outstanding_balance + v_1) * (f_2 - _1)  # Value of penalty interest. ATENTION: do not quantize here.
    v_3 = (outstanding_balance + v_1 + v_2) * (f_3 - _1)  # Value of fine. ATENTION: do not quantize here.
    out = types.SimpleNamespace()  # FIXME: create a data class for this.

    out.extra_gain = _Q(v_1)
    out.penalty = _Q(v_2)
    out.fine = _Q(v_3)

    return out

# FIXME: remove this routine. Create an auxiliary in the modules that need to handle a delayed payment entering and
# exiting. Such auxiliary should use the "get_delinquency_charges" routine to calculate the values of the delay.
#
@typeguard.typechecked
def get_late_payment(
    in_pmt: t.Union[LatePayment, LatePriceAdjustedPayment],

    # Delay, payment date.
    calc_date: datetime.date,

    # Extra payment data. FIXME: the fields below could be part of the Payment class, as meta data.
    apy: decimal.Decimal,  # Annual remuneratory interest rate (spread).
    zero_date: datetime.date,  # Initial date of the payment schedule, for tax calculation.
    vir: t.Optional[VariableIndex] = None,  # Variable index.

    # Delay, fees and fines.
    fee_rate: decimal.Decimal = LatePayment.FEE_RATE,
    fine_rate: decimal.Decimal = LatePayment.FINE_RATE,

    # Extra data for the price level adjustment index.
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

        # Composition of the "pla_operations" parameter:
        #
        # 1. Calculation date of the correction factor.
        # 2. Whether to consider the period before or after the calculation date.
        # 3. Additional information for the calculation of the correction factor (PLA).
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
        v_1 = (in_pmt.raw) * (f_1 - _1)  # Value of remuneratory interest. ATENTION: do not quantize here.
        v_2 = (in_pmt.raw + v_1) * (f_2 - _1)  # Value of penalty interest. ATENTION: do not quantize here.
        v_3 = (in_pmt.raw + v_1 + v_2) * (f_3 - _1)  # Value of fine. ATENTION: do not quantize here.
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

        v_1 = (raw) * (f_1 - _1)  # Value of remuneratory interest.
        v_2 = (raw + v_1) * (f_2 - _1)  # Value of penalty interest.
        v_3 = (raw + v_1 + v_2) * (f_3 - _1)  # Value of fine.

        v_1 = _Q(v_1)  # ATENTION: should quantize here?
        v_2 = _Q(v_2)  # ATENTION: should quantize here?
        v_3 = _Q(v_3)  # ATENTION: should quantize here?

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
