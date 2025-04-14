#!/usr/bin/env python3
#
# Copyright (C) Inco - All Rights Reserved.
#
# Written by Rafael Viotti <viotti@inco.vc>, April 2025.
#

'''Fincore CLI.'''

# Python.
import os
import re
import abc
import csv
import sys
import lzma
import json
import locale
import typing
import decimal
import logging
import datetime
import textwrap
import zoneinfo
import functools
import fileinput
import dataclasses
import html.parser
import unicodedata
import urllib.parse

# Libs.
import sh2py
import tabulate

if typing.TYPE_CHECKING:
    import platformdirs

# Fincore.
import fincore

# Print helper.
_PR = functools.partial(print, file=sys.stderr, flush=True)

# Options for payment table without monetary correction.
_PAYMENT_LIST_OPTS = {
    'headers': ['Nº', 'Date', 'Interest', 'Amt.', 'Amt. %', 'Gross', 'I.R.', 'Net', 'Balance'],
    'colalign': ('right', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right')
}

# Options for payment table with monetary correction.
_PAYMENT_LIST_OPTS_2 = {
    'headers': ['Nº', 'Date', 'Interest', 'Corr.', 'Amt.', 'Amt. %', 'Gross', 'I.R.', 'Net', 'Balance'],
    'colalign': ('right', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right')
}

# Options for pre-fixed daily returns table, without monetary correction.
_DAILY_RETURNS_OPTS_PRE = {
    'headers': ['T', 'Nº', 'Date', 'Start Bal.', 'Return', 'Fixed Rate'],
    'colalign': ('right', 'right', 'center', 'right', 'right', 'right')
}

# Options for post-fixed daily returns table, without monetary correction.
_DAILY_RETURNS_OPTS_POS_1 = {
    'headers': ['T', 'Nº', 'Date', 'Start Bal.', 'Return', 'Fixed Rate', 'Var. Rate'],
    'colalign': ('right', 'right', 'center', 'right', 'right', 'right', 'right')
}

# Options for post-fixed daily returns table with monetary correction.
_DAILY_RETURNS_OPTS_POS_2 = {
    'headers': ['T', 'Nº', 'Date', 'Start Bal.', 'Return', 'Correction', 'Fixed Rate', 'Correction Rate'],
    'colalign': ('right', 'right', 'center', 'right', 'right', 'right', 'right', 'right')
}

# Slugy cleanup regular expression.
_RE_SLUGY1 = re.compile(r'[^\w\s_-]')

# Slugy regular expression for separator substitution.
_RE_SLUGY2 = re.compile(r'[\s_-]+')

# A logger for this module.
_LOG = logging.getLogger('fincore_cli')

# GMT-3.
_BRT = zoneinfo.ZoneInfo('America/Sao_Paulo')

# Simpler split result.
_SSR = functools.partial(urllib.parse.SplitResult, 'https', query='', fragment='')

# BACEN API URL.
_BACEN_API = functools.partial(_SSR, 'api.bcb.gov.br')

# Today in Brazilian Regional Time (BRT).
_TODAY: typing.Callable[[], datetime.date] = lambda: datetime.datetime.now(zoneinfo.ZoneInfo('America/Sao_Paulo')).date()

# Function to find sibling files.
_FILE = functools.partial(os.path.join, os.path.dirname(os.path.abspath(__file__)))

def _date_range(start_date: datetime.date, end_date: datetime.date) -> typing.Generator[datetime.date, None, None]:
    iterator = start_date

    while iterator <= end_date:
        yield iterator

        iterator += datetime.timedelta(days=1)

@functools.cache
def _get_bacen_holidays() -> typing.List[datetime.date]:
    '''
    This method returns an object with all BACEN holidays from 2010 to 2078.

    >>> datetime.date(2022, 1, 1) in _get_bacen_holidays()
    True
    >>> datetime.date(2022, 12, 25) in _get_bacen_holidays()
    True
    >>> datetime.date(2022, 1, 2) in _get_bacen_holidays()
    False
    >>> datetime.date(2022, 1, 2) in _get_bacen_holidays()
    False
    >>> datetime.date(2023, 2, 20) in _get_bacen_holidays()
    True
    >>> datetime.date(2023, 2, 21) in _get_bacen_holidays()
    True
    >>> datetime.date(2023, 2, 22) in _get_bacen_holidays()
    False
    '''

    lst = []

    with lzma.open(_FILE('finmore_holidays.json.xz'), mode='rt') as file:
        data = json.load(file)

        for row in data:
            lst.append(datetime.date.fromisoformat(row['date']))

    return lst

# FIXME: perform a binary search here. This way the "cache" could be dispensed with.
@functools.cache
def _is_bacen_holiday(day: datetime.date) -> bool:
    return day in _get_bacen_holidays()

@functools.cache
def _get_business_days(begin: datetime.date, end: datetime.date) -> typing.List[datetime.date]:
    '''
    Returns a list of business days between two dates.

    Beginning and ending dates are inclusive.

    >>> from datetime import date
    >>> len(_get_business_days(date(2010, 1, 1), date(2020, 1, 1)))
    2512
    >>> lst = _get_business_days(date(2023, 1, 10), date(2023, 3, 2))
    >>> [x.isoformat() for x in lst]  # doctest: +NORMALIZE_WHITESPACE # Example output
    ['2023-01-10', '2023-01-11', '2023-01-12', '2023-01-13', '2023-01-16', '2023-01-17',
     '2023-01-18', '2023-01-19', '2023-01-20', '2023-01-23', '2023-01-24', '2023-01-25',
     '2023-01-26', '2023-01-27', '2023-01-30', '2023-01-31', '2023-02-01', '2023-02-02',
     '2023-02-03', '2023-02-06', '2023-02-07', '2023-02-08', '2023-02-09', '2023-02-10',
     '2023-02-13', '2023-02-14', '2023-02-15', '2023-02-16', '2023-02-17', '2023-02-22',
     '2023-02-23', '2023-02-24', '2023-02-27', '2023-02-28', '2023-03-01', '2023-03-02']
    >>> _get_business_days(date(2024, 7, 12), date(2024, 7, 15))  # From Friday to Monday, two biz days.
    [datetime.date(2024, 7, 12), datetime.date(2024, 7, 15)]
    '''

    day = begin
    rep = []

    while (end - day).days >= 0:
        if day.weekday() < 5 and not _is_bacen_holiday(day):
            rep.append(day)

        day += datetime.timedelta(days=1)

    return rep

def _make_variable_index(name, percentage=100):
    '''
    Creates a variable index using the "util.finmore.LocalDirectoryBackend" storage class.
    '''

    # The BACEN API is slow and unstable. Here it's not possible to store responses from calls to this API in the
    # database, so they will be saved to disk. This will prevent every Icicle command call involving the
    # retrieval of variable indexers, such as "gera_relatorio_3040" and "gera_relatorios_reinf", from needing to make a
    # call to BACEN, and eventually, any other API.
    #
    return fincore.VariableIndex(name, percentage, backend=LocalDirectoryBackend('fincore'))

def _slugy(value: str, connector: str = '') -> str:
    '''Create a "slugyfied" version of a string.'''

    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ASCII', 'ignore').decode()
    value = _RE_SLUGY1.sub('', value).strip().lower()

    if connector:
        return _RE_SLUGY2.sub(connector, value)

    else:
        return value

# From http://stackoverflow.com/a/55825140 and http://stackoverflow.com/a/64051246.
class _HtmlFilter(html.parser.HTMLParser, abc.ABC):
    '''A simple no deps HTML -> TEXT converter.'''

    def __init__(self):
        super().__init__()

        self._in_head = self._in_style = False
        self.collected_text = []

    def handle_starttag(self, tag: str, _: list[tuple[str, str | None]]) -> None:
        if tag == 'head':
            self._in_head = True

        elif tag == 'style':
            self._in_style = True

    def handle_data(self, data: str) -> None:
        if self._in_head or self._in_style:
            return

        elif text := data.strip():
            self.collected_text.append(' '.join(text.split()))

    def handle_endtag(self, tag):
        if tag == 'head':
            self._in_head = False

        elif tag == 'style':
            self._in_style = False

class LocalDirectoryBackend(fincore.IndexStorageBackend):
    '''
    Another BACEN index retrieval backend, using the "platformdirs" Python package for persistence.

    Caching means that on a given day, a single HTTP request will be sent to BACEN. The first response will be stored
    on disk, and used on subsequent calls. This has the disadvantage that if an index is published in the middle of
    the day, this backend will not consider it.

    The empty constructor will create a backend instance with platform storage.

        disk_backend = util.finmore.LocalDirectoryBackend('app_dir')
    '''

    def __init__(self, app_name: str, author_name: str = 'Inco') -> None:
        import platformdirs

        self._platform = platformdirs.PlatformDirs(app_name, author_name)

    # BACEN responds with HTML in some cases of internal failure. Apparently, this causes a
    # "requests.exceptions.JSONDecodeError" exception, chained with "simplejson.errors.JSONDecodeError" in the
    # Requests library. See:
    #
    #   http://inco-investimentos.sentry.io/issues/3735738306/events/bcd52939aa394de2b0296219839a3ee3
    #
    @staticmethod
    def _retrieve_bacen_response(url: str, query_string: typing.Dict[str, str], platform: 'platformdirs.api.PlatformDirsABC', index_name: str) -> typing.Any:
        '''
        Retrieves the data from a BACEN API response for a given indexer.

        The indexer comes from the "url" parameter.

          • for CDI, "/dados/serie/bcdata.sgs.12/dados" (six decimal places);
          • for IPCA, "/dados/serie/bcdata.sgs.433/dados" (two decimal places); and
          • for Savings, "/dados/serie/bcdata.sgs.195/dados" (four decimal places).

        The "query_string" parameter configures the response format and the start and end dates of the period to query.
        Example:

          {'formato': 'json', 'dataInicial': '10/10/2020', 'dataFinal': '12/12/2022'}

        This function will save the HTTP API response in JSON format to a local directory if it can communicate
        with BACEN. This directory comes from the "platform" parameter, which in turn comes from the "self._platform" member,
        where "self" is an instance of the LocalDirectoryBackend class. In future invocations, if the file is found,
        the response will come from it, instead of from a new HTTP request. Note that the file changes its name
        daily, so a response from a previous day cannot be reused. A file per indexer will be generated
        in the local directory to avoid collisions, obviously.

        The algorithm is as follows.

          1. Search for today's data on disk.

            1.1. If the data is found, return it.

            1.2. If there is no data on disk, make a request to the BACEN API.

              1.2.1. If the response is valid, save it to disk and return it.

              1.2.2. If the response is not valid, raise an exception.
        '''

        import requests

        try:
            name = f'{platform.user_cache_dir}/bacen_{_slugy(index_name)}_{_TODAY().strftime("%Y%m%d")}.json'
            docs: typing.List[typing.Any] = []

            _LOG.info(f'Searching for a cache file named “{name}”…')

            with open(name, 'r') as f:
                docs = json.loads(f.read())

                _LOG.info(f'Cache file “{name}” was found.')

            return docs

        except FileNotFoundError:
            _LOG.info(f'Cache file “{name}” was not found! Will query the BACEN API and dump the response to it…')

            rep = requests.get(url, params=query_string)

            if rep.ok and 'content-type' in rep.headers and 'json' in rep.headers['content-type']:
                if docs := rep.json():
                    try:
                        with open(name, 'w') as f:
                            f.write(json.dumps(docs))

                            _LOG.info(f'Cache file “{name}” written to disk.')

                    except FileNotFoundError:
                        _LOG.warning(f'Cache file “{name}” could not be written to disk.')

                    return docs

                return []

            elif rep.ok:  # Assuming BACEN returned 2XX with some HTML content.
                parser = _HtmlFilter()

                parser.feed(rep.text)
                parser.close()

                raise Exception(f'BACEN did not respond with a JSON object:\n\n{" ".join(parser.collected_text)}')

            else:
                rep.raise_for_status()

    # CDI. {{{
    @staticmethod
    @functools.cache  # This helper must return a list so it can be cached. Do not attempt to convert it to a generator.
    def _query_bacen_cdi(platform: 'platformdirs.api.PlatformDirsABC') -> typing.List[fincore.DailyIndex]:
        '''
        Queries the CDI indexer on the BACEN API.
        '''

        qry = {'formato': 'json', 'dataInicial': '01/01/2018', 'dataFinal': _TODAY().strftime('%d/%m/%Y')}
        url = _BACEN_API('/dados/serie/bcdata.sgs.12/dados').geturl()
        bit = False  # See [ERROS-BACEN] above.
        mem = []

        for x in LocalDirectoryBackend._retrieve_bacen_response(url, qry, platform, 'CDI'):
            if not bit and 'valor' in x and x['valor'].strip():
                idx = fincore.DailyIndex()

                idx.value = decimal.Decimal(x['valor'])
                idx.date = datetime.datetime.strptime(x['data'], '%d/%m/%Y').date()

                mem.append(idx)

            elif not bit:
                _LOG.warning(f'Invalid response for the BACEN CDI API request, “{x}”.')

                bit = True  # Recovered from an error. Iteration must stop now, otherwise this method should fail.

            else:
                raise fincore.BackendError('The CDI API respondend with invalid data in an unrecoverable way.')

        if not mem:
            raise fincore.BackendError('the “util.finmore.LocalDirectoryBackend” backend was unable to retrieve any CDI indexes')

        return mem

    @staticmethod
    def _get_cdi_indexes(begin: datetime.date, end: datetime.date, platform: 'platformdirs.api.PlatformDirsABC') -> typing.Generator[fincore.DailyIndex, None, None]:
        '''
        Read CDI indexes from a BACEN API cached response on the local disk.

        This method is just a helper for "LocalDirectoryBackend.get_cdi_indexes".
        '''

        data = {x.date: x for x in LocalDirectoryBackend._query_bacen_cdi(platform)}
        bizz = _get_business_days(begin, end)
        dmin = min(data.keys())
        dmax = max(data.keys())
        last = data[dmax]

        if dmin <= begin <= dmax:
            dmax = max(data.keys())

            for dt in _date_range(begin, end):
                if dt in data:  # Business day.
                    yield data[dt]

                elif dt <= dmax:  # Weekend and bank holiday.
                    yield fincore.DailyIndex(date=dt, value=decimal.Decimal())

                elif dt in bizz and last:  # Business day, after the last indexer.
                    _LOG.warning(f'CDI index for business day {dt} was not found in upstream, filling with value "{last.value}" from date {last.date}')

                    yield fincore.DailyIndex(date=dt, value=last.value, projected=True)

                    last = None  # Prevents more than one index compensation.

                else:
                    _LOG.info(f'CDI index for date {dt} was not found in upstream')

        elif begin > dmax:
            for dt in _date_range(begin, end):
                if dt in bizz:
                    _LOG.warning(f'CDI index for business day {dt} was not found in upstream, filling with value "{last.value}" from date {last.date}')

                    yield fincore.DailyIndex(date=dt, value=last.value, projected=True)

                    break

        else:
            raise fincore.BackendError(f'the initial date, {begin} precedes the first upstream published index date, {dmin}')

    # This method must be a generator so it complies with the signature of "fincore.IndexStorageBackend.get_cdi_indexes".
    def get_cdi_indexes(self, begin: datetime.date, end: datetime.date, **_) -> typing.Generator[fincore.DailyIndex, None, None]:
        '''
        Returns the list of CDI indexes between the begin and end date.

        Read CDI indexes from a BACEN API cached response on the local disk.

        The begin and end dates are inclusive.

        This method will automatically compensate for the absence of a single CDI index.

        >>> backend = LocalDirectoryBackend('doctest')
        >>> list(backend.get_cdi_indexes(datetime.date(2017, 12, 31), _TODAY()))
        Traceback (most recent call last):
        ...
        fincore.BackendError: the “util.finmore.LocalDirectoryBackend” backend cannot retrieve CDI indexes prior to 2018-01-01
        '''

        if datetime.date(2018, 1, 1) <= begin <= end:
            yield from self._get_cdi_indexes(begin, end, self._platform)

        elif begin >= datetime.date(2018, 1, 1):
            raise ValueError('the initial date must be greater than, or equal to, the end date')

        else:
            raise fincore.BackendError('the “util.finmore.LocalDirectoryBackend” backend cannot retrieve CDI indexes prior to 2018-01-01')
    # }}}

    # IPCA. {{{
    @staticmethod
    @functools.cache  # This helper must return a list so it can be cached. Do not attempt to convert it to a generator.
    def _query_bacen_ipca(platform: 'platformdirs.api.PlatformDirsABC') -> typing.List[fincore.MonthlyIndex]:
        '''
        Queries IPCA indexers on the BACEN API.
        '''

        qry = {'formato': 'json', 'dataInicial': '01/01/2018', 'dataFinal': _TODAY().strftime('%d/%m/%Y')}
        url = _BACEN_API('/dados/serie/bcdata.sgs.433/dados').geturl()
        bit = False  # See [ERROS-BACEN] above.
        mem = []

        for x in LocalDirectoryBackend._retrieve_bacen_response(url, qry, platform, 'IPCA'):
            if not bit and 'valor' in x and x['valor'].strip():
                idx = fincore.MonthlyIndex()

                idx.value = decimal.Decimal(x['valor'])
                idx.date = datetime.datetime.strptime(x['data'], '%d/%m/%Y').date()

                mem.append(idx)

            elif not bit:
                _LOG.warning(f'Invalid response for the BACEN IPCA API request, “{x}”.')

                bit = True  # Recovered from an error. Iteration must stop now, otherwise this method should fail.

            else:
                raise fincore.BackendError('The IPCA API respondend with invalid data in an unrecoverable way.')

        if not mem:
            raise fincore.BackendError('the “util.finmore.LocalDirectoryBackend” backend was unable to retrieve any IPCA indexes')

        return mem

    @staticmethod
    def _get_ipca_indexes(begin: datetime.date, end: datetime.date, platform: 'platformdirs.api.PlatformDirsABC') -> typing.Generator[fincore.MonthlyIndex, None, None]:
        '''
        Read IPCA indexes from a BACEN API cached response on the local disk.

        This method is just a helper for "LocalDirectoryBackend.get_ipca_indexes".
        '''

        for entry in LocalDirectoryBackend._query_bacen_ipca(platform):
            if end and begin <= entry.date <= end:
                yield entry

    # This method must be a generator so it complies with the signature of "fincore.IndexStorageBackend.get_ipca_indexes".
    def get_ipca_indexes(self, begin: datetime.date, end: datetime.date) -> typing.Generator[fincore.MonthlyIndex, None, None]:
        '''
        Read IPCA indexes from a BACEN API cached response on the local disk.

        >>> backend = LocalDirectoryBackend('doctest')
        >>> list(backend.get_ipca_indexes(datetime.date(2017, 12, 31), _TODAY()))
        Traceback (most recent call last):
        ...
        fincore.BackendError: the “util.finmore.LocalDirectoryBackend” backend cannot retrieve IPCA indexes prior to 2018-01-01
        '''

        if begin >= datetime.date(2018, 1, 1):
            yield from self._get_ipca_indexes(begin, end, self._platform)

        else:
            raise fincore.BackendError('the “util.finmore.LocalDirectoryBackend” backend cannot retrieve IPCA indexes prior to 2018-01-01')
    # }}}

    # Savings. {{{
    @staticmethod
    @functools.cache  # This helper must return a list so it can be cached. Do not attempt to convert it to a generator.
    def _query_bacen_savings(platform: 'platformdirs.api.PlatformDirsABC') -> typing.List[fincore.RangedIndex]:
        '''
        Queries the Savings indexer on the BACEN API.
        '''

        qry = {'formato': 'json', 'dataInicial': '01/01/2018', 'dataFinal': _TODAY().strftime('%d/%m/%Y')}
        url = _BACEN_API('/dados/serie/bcdata.sgs.195/dados').geturl()
        bit = False  # See [ERROS-BACEN] above.
        mem = []

        for x in LocalDirectoryBackend._retrieve_bacen_response(url, qry, platform, 'Poupança'):
            if not bit and 'valor' in x and x['valor'].strip():
                idx = fincore.RangedIndex()

                idx.value = decimal.Decimal(x['valor'])
                idx.begin_date = datetime.datetime.strptime(x['data'], '%d/%m/%Y').date()

                if 'dataFim' in x:  # See [ERROS-BACEN] above.
                    idx.end_date = datetime.datetime.strptime(x['dataFim'], '%d/%m/%Y').date()

                else:  # Implies "'datafim' in x".
                    idx.end_date = datetime.datetime.strptime(x['datafim'], '%d/%m/%Y').date()

                mem.append(idx)

            elif not bit:
                _LOG.warning(f'Invalid response for the BACEN Savings API request, “{x}”.')

                bit = True  # Recovered from an error. Iteration must stop now, otherwise this method should fail.

            else:
                raise fincore.BackendError('The Savings API respondend with invalid data in an unrecoverable way.')

        if not mem:
            raise fincore.BackendError('the “util.finmore.LocalDirectoryBackend” backend was unable to retrieve any Brazilian Savings indexes')

        return mem

    @staticmethod
    def _get_savings_indexes(begin: datetime.date, end: datetime.date, platform: 'platformdirs.api.PlatformDirsABC') -> typing.Generator[fincore.RangedIndex, None, None]:
        '''
        Read Brazilian Savings indexes from a BACEN API cached response on the local disk.

        This method is just a helper for "LocalDirectoryBackend.get_savings_indexes".
        '''

        for entry in LocalDirectoryBackend._query_bacen_savings(platform):
            if end and begin <= entry.begin_date <= end and begin <= entry.end_date <= end:
                yield entry

    # This method must be a generator so it complies with the signature of "fincore.IndexStorageBackend.get_savings_indexes".
    def get_savings_indexes(self, begin: datetime.date, end: datetime.date) -> typing.Generator[fincore.RangedIndex, None, None]:
        '''
        Read Brazilian Savings indexes from a BACEN API cached response on the local disk.

        >>> backend = LocalDirectoryBackend('doctest')
        >>> list(backend.get_savings_indexes(datetime.date(2017, 12, 31), _TODAY()))
        Traceback (most recent call last):
        ...
        fincore.BackendError: the “util.finmore.LocalDirectoryBackend” backend cannot retrieve Brazilian Savings indexes prior to 2018-01-01
        '''

        if begin >= datetime.date(2018, 1, 1):
            yield from self._get_savings_indexes(begin, end, self._platform)

        else:
            raise fincore.BackendError('the “util.finmore.LocalDirectoryBackend” backend cannot retrieve Brazilian Savings indexes prior to 2018-01-01')
    # }}}

def ajuda(command=''):
    '''
    Supported commands:

    - "calcula_fatores_za", debugs Zille-Anna factors;
    - "gera_pagamentos", generates a payment schedule for a given operation;
    - "gera_rendimentos_diarios", generates a daily returns table for an operation.
    '''

    dic = globals()

    if command and command in dic and dic[command].__doc__ and command != 'ajuda':
        _PR(textwrap.dedent(dic[command].__doc__))

    else:
        _PR(textwrap.dedent(str(ajuda.__doc__)))

    return sh2py.HALT

def gera_pagamentos(modalidade, principal, taxa_fixa, inicio_prazo='', aniversario='', csv_cronograma='', **kwargs):
    r'''
    Generates a payment schedule using the financial library.

    Parameters for Bullet, Monthly Interest, and Price:

      • "modalidade", operation modality. Must be Bullet, Monthly Interest, Price or Free;

      • "principal", loan amount;

      • "taxa_fixa", nominal annual interest rate, fixed;

      • "inicio_prazo", a date in the format "D+N", where D is an ISO 8601 date and N is a positive
        integer. Simultaneously informs the start date of the return and the investment term. Should only be
        used in Bullet, Monthly Interest or Price modalities.

      • "aniversario", optional, investment anniversary date;

    In the Free modality, the "inicio_prazo" and "aniversario" parameters should not be provided. Use "csv_cronograma":

      • "csv_cronograma", the operation's amortization schedule. Must be the path to a file in CSV format. If
        this file is not provided, standard input will be read.

    Optional parameters:

      • "indice_variavel", variable index. Can be CDI, Savings, IPCA or IGPM;

      • "indice_variavel_percentual", percentage of the index used in the variable return calculation;

      • "antecipacoes", for Bullet, Monthly Interest, and Price modalities. In these modalities, since a
        file with a payment schedule is not provided, prepayments come as a list of DATE+VALUE separated by
        semicolons. Example Palazzo Saldanha operation - Monthly Interest - 9 months.

          icicle gera_pagamentos Juros\ mensais 4000000 6 2023-09-29+9 aniversario=2023-11-07 indice_variavel=CDI \
                 antecipacoes='2024-01-05+676127;2024-01-08+53022;2024-04-26+2908097;2024-05-27+447711.21'

      • "calc_date", calculation limit date. Has a special syntax to indicate that the entire schedule should be
        printed: "D+R". Example

         icicle gera_pagamentos Livre 145000 10 csv_cronograma=cronograma_asad.csv indice_variavel=IPCA calc_date=2022-12-01+R

      • "gain_output", output mode for the engine's interest. Can be current, deferred or settled, the default is always current;

      • "tax_exempt", optional, indicates if there is income tax exemption on payments.

      • "first_dct_rule", optional, rule for the first DCT. Can be 30, 31 or AUTO.

      • "formato", the output format. Besides the formats supported by the Python Tabulate library, see
        "http://github.com/astanin/python-tabulate#table-format", this routine supports the "json" format, which emits the
        table in JSON format. The "raw" format is a synonym for the "json" format.
    '''

    if kwargs.get('debug', '').lower() in ['s', 'sim', 'y', 'yes']:
        logging.basicConfig(level=logging.DEBUG)

    # 0. Validate.
    if modalidade not in ['Bullet', 'Juros mensais', 'Price', 'Livre']:
        _PR(f'Error: modality "{modalidade}" not supported.')

        return sh2py.HALT

    # 1. Assemble the Fincore call.
    gen = None
    kwa = {}

    if modalidade == 'Bullet' or modalidade == 'Juros mensais':
        pct = int(kwargs.get('indice_variavel_percentual', '100'))
        vir = kwargs.get('indice_variavel', '')
        tup = inicio_prazo.split('+')

        kwa['principal'] = decimal.Decimal(principal)
        kwa['apy'] = decimal.Decimal(taxa_fixa)
        kwa['zero_date'] = datetime.date.fromisoformat(tup[0])
        kwa['term'] = int(tup[1])
        kwa['tax_exempt'] = kwargs.get('tax_exempt', 'não') in ['sim', 's', 'yes', 'y']
        kwa['first_dct_rule'] = kwargs.get('first_dct_rule', 'AUTO')

        if aniversario:
            kwa['anniversary_date'] = datetime.date.fromisoformat(aniversario)

        if 'antecipacoes' in kwargs:
            kwa['insertions'] = []

            for x in kwargs['antecipacoes'].split(';'):
                tup = x.split('+')
                ent = fincore.Amortization.Bare(date=datetime.date.fromisoformat(tup[0]))

                ent.value = decimal.Decimal(tup[1])

                kwa['insertions'].append(ent)

        if vir:
            kwa['vir'] = _make_variable_index(vir, pct)

        if 'calc_date' in kwargs:
            tup = kwargs['calc_date'].split('+')
            val = datetime.date.fromisoformat(tup[0])

            if len(tup) == 2 and tup[1] == 'R':
                kwa['calc_date'] = fincore.CalcDate(value=val, runaway=True)

            else:
                kwa['calc_date'] = fincore.CalcDate(value=val)

        if 'gain_output' in kwargs:
            kwa['gain_output'] = kwargs['gain_output']

        gen = fincore.build_bullet(**kwa) if modalidade == 'Bullet' else fincore.build_jm(**kwa)

    elif modalidade == 'Price':
        tup = inicio_prazo.split('+')

        kwa['principal'] = decimal.Decimal(principal)
        kwa['apy'] = decimal.Decimal(taxa_fixa)
        kwa['zero_date'] = datetime.date.fromisoformat(tup[0])
        kwa['term'] = int(tup[1])
        kwa['tax_exempt'] = kwargs.get('tax_exempt', 'não') in ['sim', 's', 'yes', 'y']
        kwa['first_dct_rule'] = kwargs.get('first_dct_rule', 'AUTO')

        if aniversario:
            kwa['anniversary_date'] = datetime.date.fromisoformat(aniversario)

        if 'antecipacoes' in kwargs:
            kwa['insertions'] = []

            for x in kwargs['antecipacoes'].split(';'):
                tup = x.split('+')
                ent = fincore.Amortization.Bare(date=datetime.date.fromisoformat(tup[0]))

                ent.value = decimal.Decimal(tup[1])

                kwa['insertions'].append(ent)

        if 'calc_date' in kwargs:
            tup = kwargs['calc_date'].split('+')
            val = datetime.date.fromisoformat(tup[0])

            if len(tup) == 2 and tup[1] == 'R':
                kwa['calc_date'] = fincore.CalcDate(value=val, runaway=True)

            else:
                kwa['calc_date'] = fincore.CalcDate(value=val)

        if 'gain_output' in kwargs:
            kwa['gain_output'] = kwargs['gain_output']

        gen = fincore.build_price(**kwa)

    else:  # Assumes "Livre".
        pct = int(kwargs.get('indice_variavel_percentual', '100'))
        lst = [csv_cronograma] if csv_cronograma else []
        vir = kwargs.get('indice_variavel', '')

        if not lst:
            _PR('Input file not specified. Reading data from standard input…')

        kwa['principal'] = decimal.Decimal(principal)
        kwa['apy'] = decimal.Decimal(taxa_fixa)
        kwa['tax_exempt'] = kwargs.get('tax_exempt', 'não') in ['sim', 's', 'yes', 'y']
        kwa['first_dct_rule'] = kwargs.get('first_dct_rule', 'AUTO')
        kwa['amortizations'] = []
        kwa['insertions'] = []

        with fileinput.input(lst, openhook=lambda f, _: open(f, newline='')) as file:
            for line in csv.reader(file):
                if line[0] == 'R':  # Regular flow.
                    ent = fincore.Amortization(date=datetime.date.fromisoformat(line[1]))

                    ent.amortization_ratio = decimal.Decimal(line[2])
                    ent.amortizes_interest = line[3] == 'y'

                    if len(line) > 4 and line[4] == 'IPCA':
                        pla = fincore.PriceLevelAdjustment(line[4])

                        pla.base_date = datetime.date.fromisoformat(line[5])
                        pla.period = int(line[6])
                        pla.shift = typing.cast(fincore._PL_SHIFT, line[7])  # FIXME: check if line[7] is a valid shift, instead of casting.
                        pla.amortizes_adjustment = line[8] == 'y'

                        ent.price_level_adjustment = pla

                    kwa['amortizations'].append(ent)

                elif line[0] == 'X':  # Extraordinary flow.
                    ent = fincore.Amortization.Bare(date=datetime.date.fromisoformat(line[1]))

                    ent.value = decimal.Decimal(line[2])

                    kwa['insertions'].append(ent)

                else:
                    raise ValueError()

        if vir:
            kwa['vir'] = _make_variable_index(vir, pct)

        if 'calc_date' in kwargs:
            tup = kwargs['calc_date'].split('+')
            val = datetime.date.fromisoformat(tup[0])

            if len(tup) == 2 and tup[1] == 'R':
                kwa['calc_date'] = fincore.CalcDate(value=val, runaway=True)

            else:
                kwa['calc_date'] = fincore.CalcDate(value=val)

        if 'gain_output' in kwargs:
            kwa['gain_output'] = kwargs['gain_output']

        gen = fincore.build(**kwa)

    # 2. Execute and format the results.
    if (fmt := kwargs.get('formato', 'fancy_outline')) in tabulate.tabulate_formats:
        func = functools.partial(locale.currency, symbol=False, grouping=True)
        data = []

        tabulate.PRESERVE_WHITESPACE = True  # Force Tabulate to preserve spaces (http://github.com/astanin/python-tabulate#text-formatting).

        for x in gen:
            out = []

            out.append(x.no)
            out.append(x.date.strftime('%x'))
            out.append(func(x.gain))

            if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
                out.append(func(pla := getattr(x, 'pla', decimal.Decimal())))

            out.append(func(x.amort))
            out.append(locale.str(round(x.amort * decimal.Decimal(100) / decimal.Decimal(principal), 5)))  # pyright: ignore[reportArgumentType]
            out.append(func(x.raw))
            out.append(func(x.tax))
            out.append(func(x.net))
            out.append(func(x.bal))

            data.append(out)

        _PR()

        if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
            _PR(tabulate.tabulate(data, tablefmt=fmt, **_PAYMENT_LIST_OPTS_2))

        else:
            _PR(tabulate.tabulate(data, tablefmt=fmt, **_PAYMENT_LIST_OPTS))

        _PR()

    elif fmt == 'json':
        data = []

        for x in gen:
            out = []

            out.append(x.no)
            out.append(x.date.isoformat())
            out.append(str(x.gain))

            if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
                out.append(str(getattr(x, 'pla', decimal.Decimal())))

            out.append(str(x.amort))
            out.append(str(round(x.amort * decimal.Decimal(100) / decimal.Decimal(principal), 10)))
            out.append(str(x.raw))
            out.append(str(x.tax))
            out.append(str(x.net))
            out.append(str(x.bal))

            data.append(out)

        print(json.dumps(data))

    elif fmt == 'csv':
        if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
            dev = csv.DictWriter(sys.stdout, [x for x in vars(fincore.PriceAdjustedPayment()) if not x.startswith('_')])

            dev.writeheader()

            for x in gen:
                dic = dataclasses.asdict(x)

                dic.pop('_regs')

                dev.writerow(dic)

        else:
            dev = csv.DictWriter(sys.stdout, [x for x in vars(fincore.Payment()) if not x.startswith('_')])

            dev.writeheader()

            for x in gen:
                dic = dataclasses.asdict(x)

                dic.pop('_regs')

                dev.writerow(dic)

    elif fmt == 'raw':
        for pmt in gen:
            print(pmt)

    else:
        _PR(f'Error, format "{fmt}" not supported.')

        return sh2py.HALT

def gera_rendimentos_diarios(modalidade, principal, taxa_fixa, inicio_prazo='', aniversario='', csv_cronograma='', **kwargs):
    r'''
    Generates a daily returns schedule using the financial library.

    Parameters for Bullet, Monthly Interest, and Price:

      • "modalidade", operation modality. Must be Bullet, Monthly Interest, Price or Free;

      • "principal", loan amount;

      • "taxa_fixa", nominal annual interest rate, fixed;

      • "inicio_prazo", a date in the format "D+N", where D is an ISO 8601 date and N is a positive
        integer. Simultaneously informs the start date of the return and the investment term. Should only be
        used in Bullet, Monthly Interest or Price modalities.

      • "aniversario", optional, investment anniversary date.

    In the Free modality, the "inicio_prazo" and "aniversario" parameters should not be provided. Use "csv_cronograma":

      • "csv_cronograma", the operation's amortization schedule. Must be the path to a file in CSV format. If
        this file is not provided, standard input will be read.

    Optional parameters:

      • "indice_variavel", variable index. Can be CDI, Savings, IPCA or IGPM;

      • "indice_variavel_percentual", percentage of the index used in the variable return calculation;

      • "antecipacoes", for Bullet, Monthly Interest, and Price modalities. In these modalities, since a
        file with a payment schedule is not provided, prepayments come as a list of DATE+VALUE separated by
        semicolons. Example Palazzo Saldanha operation - Monthly Interest - 9 months.

          icicle gera_pagamentos Juros\ mensais 4000000 6 2023-09-29+9 aniversario=2023-11-07 indice_variavel=CDI \
                 antecipacoes='2024-01-05+676127;2024-01-08+53022;2024-04-26+2908097;2024-05-27+447711.21'

      • "first_dct_rule", optional, rule for the first DCT. Can be 30, 31 or AUTO.

      • "formato", the output format. Besides the formats supported by the Python Tabulate library, see
        "http://github.com/astanin/python-tabulate#table-format", this routine supports the "json" format, which emits the
        table in JSON format. The "raw" format is a synonym for the "json" format.
    '''

    if kwargs.get('debug', '').lower() in ['s', 'sim', 'y', 'yes']:
        logging.basicConfig(level=logging.DEBUG)

    # 0. Validate.
    if modalidade not in ['Bullet', 'Juros mensais', 'Price', 'Livre']:
        _PR(f'Error: modality "{modalidade}" not supported.')

        return sh2py.HALT

    # 1. Assemble the Fincore call.
    fun = functools.partial(locale.currency, symbol=False, grouping=True)
    kwa = {}

    if modalidade == 'Bullet' or modalidade == 'Juros mensais':
        pct = int(kwargs.get('indice_variavel_percentual', '100'))
        vir = kwargs.get('indice_variavel', '')
        tup = inicio_prazo.split('+')

        kwa['principal'] = decimal.Decimal(principal)
        kwa['apy'] = decimal.Decimal(taxa_fixa)
        kwa['zero_date'] = datetime.date.fromisoformat(tup[0])
        kwa['term'] = int(tup[1])
        kwa['first_dct_rule'] = kwargs.get('first_dct_rule', 'AUTO')
        kwa['is_bizz_day_cb'] = lambda x: x.weekday() < 5 and not _is_bacen_holiday(x)

        if aniversario:
            kwa['anniversary_date'] = datetime.date.fromisoformat(aniversario)

        if vir:
            kwa['vir'] = _make_variable_index(vir, pct)

        if 'antecipacoes' in kwargs:
            kwa['insertions'] = []

            for x in kwargs['antecipacoes'].split(';'):
                tup = x.split('+')
                ent = fincore.Amortization.Bare(date=datetime.date.fromisoformat(tup[0]))

                ent.value = decimal.Decimal(tup[1])

                kwa['insertions'].append(ent)

    elif modalidade == 'Price':
        tup = inicio_prazo.split('+')

        kwa['principal'] = decimal.Decimal(principal)
        kwa['apy'] = decimal.Decimal(taxa_fixa)
        kwa['zero_date'] = datetime.date.fromisoformat(tup[0])
        kwa['term'] = int(tup[1])
        kwa['first_dct_rule'] = kwargs.get('first_dct_rule', 'AUTO')
        kwa['is_bizz_day_cb'] = lambda x: x.weekday() < 5 and not _is_bacen_holiday(x)

        if aniversario:
            kwa['anniversary_date'] = datetime.date.fromisoformat(aniversario)

        if 'antecipacoes' in kwargs:
            kwa['insertions'] = []

            for x in kwargs['antecipacoes'].split(';'):
                tup = x.split('+')
                ent = fincore.Amortization.Bare(date=datetime.date.fromisoformat(tup[0]))

                ent.value = decimal.Decimal(tup[1])

                kwa['insertions'].append(ent)

    else:  # Assumes "Livre".
        pct = int(kwargs.get('indice_variavel_percentual', '100'))
        lst = [csv_cronograma] if csv_cronograma else []
        vir = kwargs.get('indice_variavel', '')

        if not lst:
            _PR('Input file not specified. Reading data from standard input…')

        kwa['principal'] = decimal.Decimal(principal)
        kwa['apy'] = decimal.Decimal(taxa_fixa)
        kwa['first_dct_rule'] = kwargs.get('first_dct_rule', 'AUTO')
        kwa['is_bizz_day_cb'] = lambda x: x.weekday() < 5 and not _is_bacen_holiday(x)
        kwa['amortizations'] = []
        kwa['insertions'] = []

        with fileinput.input(lst, openhook=lambda f, _: open(f, newline='')) as file:
            for line in csv.reader(file):
                if line[0] == 'R':  # Regular flow.
                    ent = fincore.Amortization(date=datetime.date.fromisoformat(line[1]))

                    ent.amortization_ratio = decimal.Decimal(line[2])
                    ent.amortizes_interest = line[3] == 'y'

                    if len(line) > 4 and line[4] == 'IPCA':
                        pla = fincore.PriceLevelAdjustment(line[4])

                        pla.base_date = datetime.date.fromisoformat(line[5])
                        pla.period = int(line[6])
                        pla.shift = typing.cast(fincore._PL_SHIFT, line[7])  # FIXME: check if line[7] is a valid shift, instead of casting.
                        pla.amortizes_adjustment = line[8] == 'y'

                        ent.price_level_adjustment = pla

                    kwa['amortizations'].append(ent)

                elif line[0] == 'X':  # Extraordinary flow.
                    ent = fincore.Amortization.Bare(date=datetime.date.fromisoformat(line[1]))

                    ent.value = decimal.Decimal(line[2])

                    kwa['insertions'].append(ent)

                else:
                    raise ValueError()

        if vir:
            kwa['vir'] = _make_variable_index(vir, pct)

    # 2. Create the daily returns generator.
    if modalidade == 'Bullet':
        gene = fincore.get_bullet_daily_returns(**kwa)

    elif modalidade == 'Juros mensais':
        gene = fincore.get_jm_daily_returns(**kwa)

    elif modalidade == 'Price':
        gene = fincore.get_price_daily_returns(**kwa)

    else:  # Assumes "Livre".
        gene = fincore.get_livre_daily_returns(**kwa)

    # 3. Execute and format the results.
    bal = decimal.Decimal(principal)

    if (fmt := kwargs.get('formato', 'fancy_outline')) in tabulate.tabulate_formats:
        data = []

        tabulate.PRESERVE_WHITESPACE = True  # Force Tabulate to preserve spaces (http://github.com/astanin/python-tabulate#text-formatting).

        for x in gene:
            out = []

            out.append(x.period)
            out.append(x.no)
            out.append(x.date.strftime('%x'))
            out.append(fun(bal))
            out.append(fun(x.value))

            if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
                out.append(fun(typing.cast(fincore.PriceAdjustedPayment, x).pla))

            out.append(locale.str(round(x.sf, 8)))  # pyright: ignore[reportArgumentType]

            if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
                out.append(locale.str(round(typing.cast(fincore.PriceAdjustedPayment, x).cf, 8)))  # pyright: ignore[reportArgumentType]

            elif kwargs.get('indice_variavel', '') in typing.get_args(fincore._VR_INDEX):
                out.append(locale.str(round(x.vf, 8)))  # pyright: ignore[reportArgumentType]

            data.append(out)

            bal = x.bal  # Memorize the balance for the next iteration.

        if data and not kwargs.get('indice_variavel', ''):
            _PR(tabulate.tabulate(data, tablefmt=fmt, **_DAILY_RETURNS_OPTS_PRE))

        elif data and kwargs.get('indice_variavel', '') in typing.get_args(fincore._VR_INDEX):
            _PR(tabulate.tabulate(data, tablefmt=fmt, **_DAILY_RETURNS_OPTS_POS_1))

        elif data:
            _PR(tabulate.tabulate(data, tablefmt=fmt, **_DAILY_RETURNS_OPTS_POS_2))

    elif fmt == 'json':
        data = []

        for x in gene:
            out = []

            out.append(x.period)
            out.append(x.no)
            out.append(x.date.strftime('%x'))
            out.append(fun(bal))
            out.append(fun(x.value))

            if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
                out.append(fun(typing.cast(fincore.PriceAdjustedPayment, x).pla))

            out.append(locale.str(round(x.sf, 10)))  # pyright: ignore[reportArgumentType]

            if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
                out.append(locale.str(round(typing.cast(fincore.PriceAdjustedPayment, x).cf, 8)))  # pyright: ignore[reportArgumentType]

            elif kwargs.get('indice_variavel', '') in typing.get_args(fincore._VR_INDEX):
                out.append(locale.str(round(x.vf, 8)))  # pyright: ignore[reportArgumentType]

            data.append(out)

            bal = x.bal  # Memorize the balance for the next iteration.

        if data:
            print(json.dumps(data))

    elif fmt == 'csv':
        if kwargs.get('indice_variavel', '') in typing.get_args(fincore._PL_INDEX):
            dev = csv.DictWriter(sys.stdout, vars(fincore.PriceAdjustedDailyReturn()))

            dev.writeheader()
            dev.writerows((dataclasses.asdict(x) for x in gene))

        else:
            dev = csv.DictWriter(sys.stdout, vars(fincore.DailyReturn()))

            dev.writeheader()
            dev.writerows((dataclasses.asdict(x) for x in gene))

    elif fmt == 'raw':
        for dr in gene:
            print(dr)

    else:
        _PR(f'Error, format "{fmt}" not supported.')

        return sh2py.HALT

def calcula_fatores_za(indice, taxa_fixa, data_inicio, data_fim, indice_pct='100', debug='n'):
    '''
    Calculates Zille-Anna factors.

    Command to calculate factors used in variable indices.

    Used to facilitate debugging of indices used in post-fixed operations. Helps in creating test cases,
    building spreadsheets, and validating calculations in general.

      icicle calcula_fatores_za INDEX FIXED_RATE START_DATE END_DATE [indice_pct=100] [debug=yes/no]

    Provide the index, the fixed annual rate, the start date, and the end date of the period. Example for a
    Bullet CDI operation with a rate of 6.33% p.a., for eighteen months, from 2021-12-28 to 2023-06-28.

      icicle calcula_fatores_za CDI 6.33 2021-12-28 2023-06-28

    The "debug=s" argument will activate the "DEBUG" level in the "logging" module, and show the indices
    for the requested period, one by one.
    '''

    if debug.lower() in ['s', 'sim', 'y', 'yes']:
        logging.basicConfig(level=logging.DEBUG)

    fr = decimal.Decimal(taxa_fixa)  # Fixed rate, or Annual Percentage Yield (APY).
    d0 = datetime.date.fromisoformat(data_inicio)
    d1 = datetime.date.fromisoformat(data_fim)
    pc = int(indice_pct)

    if indice == 'CDI':
        vir = _make_variable_index('CDI', pc)
        f_v = vir.backend.calculate_cdi_factor(d0, d1, pc)
        f_s = fincore.calculate_interest_factor(fr, decimal.Decimal(f_v.amount) / 252)

        _PR(f'Period.............: {d0.strftime("%x")} to {d1.strftime("%x")}')
        _PR(f'Spread rate........: {locale.str(fr)}% p.a.')  # pyright: ignore[reportArgumentType]
        _PR(f'Spread factor (F1).: {locale.str(round(f_s, 10))}')  # pyright: ignore[reportArgumentType]
        _PR(f'CDI factor (F2)....: {locale.str(round(f_v.value, 10))}')
        _PR(f'Factor (F1×F2).....: {locale.str(round(f_s * f_v.value, 10))}')
        _PR(f'Indices............: {locale.str(round(f_v.amount, 10))}')
        _PR(f'Generation.........: {datetime.datetime.now(_BRT).strftime("%d/%m/%Y %H:%M:%S")}')

    elif indice == 'Poupança':  # 'Poupança' is Portuguese for Savings.
        vir = _make_variable_index('Poupança', pc)
        f_v = vir.backend.calculate_savings_factor(d0, d1, pc)
        f_s = fincore.calculate_interest_factor(fr, decimal.Decimal((d1 - d0).days) / 360)

        _PR(f'Period.............: {d0.strftime("%x")} to {d1.strftime("%x")}')
        _PR(f'Spread rate........: {locale.str(fr)}% p.a.')  # pyright: ignore[reportArgumentType]
        _PR(f'Spread factor (F1).: {locale.str(round(f_s, 10))}')  # pyright: ignore[reportArgumentType]
        _PR(f'Savings factor (F2): {locale.str(round(f_v.value, 10))}')
        _PR(f'Factor (F1×F2).....: {locale.str(round(f_s * f_v.value, 10))}')
        _PR(f'Indices............: {locale.str(round(f_v.amount, 10))}')
        _PR(f'Generation.........: {datetime.datetime.now(_BRT).strftime("%d/%m/%Y %H:%M:%S")}')

    else:
        raise ValueError(f'Unsupported index: {indice}.')  # FIXME: implement IPCA.

cli = sh2py.CommandLineMapper()

cli.add(ajuda)
cli.add(gera_pagamentos)
cli.add(gera_rendimentos_diarios)
cli.add(calcula_fatores_za)

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

if cli.run() is sh2py.HALT:
    exit(1)

# vi:fdm=marker:
