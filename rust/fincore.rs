use chrono::{Date, Datelike, Duration, NaiveDate, Utc};
use rust_decimal::Decimal;
use rust_decimal_macros::dec;
use std::cmp::min;
use std::collections::HashMap;
use serde_json::Value;

trait RoundingExt {
    fn round_dp(&self, decimal_places: u32) -> Self;
}

impl RoundingExt for Decimal {
    fn round_dp(&self, decimal_places: u32) -> Self {
        self.round_with_scale(decimal_places)
    }
}

// Constants
const CENTI: Decimal = dec!(0.01);
const ZERO: Decimal = dec!(0);
const ONE: Decimal = dec!(1);

const REVENUE_TAX_BRACKETS: [(i32, i32, Decimal); 4] = [
    (0, 180, dec!(0.225)),
    (180, 360, dec!(0.2)),
    (360, 720, dec!(0.175)),
    (720, i32::MAX, dec!(0.15)),
];

// Enums
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum OpModes {
    Bullet,
    JurosMensais,
    Price,
    Livre,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum VrIndex {
    CDI,
    Poupanca,
}


#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Capitalisation {
    Days252,
    Days360,
    Days365,
    Days30360,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum GainOutputMode {
    Current,
    Deferred,
    Settled,
}

// Structs

#[derive(Debug, Clone)]
pub struct DctOverride {
    pub date_from: NaiveDate,
    pub date_to: NaiveDate,
    pub predates_first_amortization: bool,
}

#[derive(Debug, Clone)]
pub struct Amortization {
    pub date: NaiveDate,
    pub amortization_ratio: Decimal,
    pub amortizes_interest: bool,
    pub price_level_adjustment: Option<PriceLevelAdjustment>,
    pub dct_override: Option<DctOverride>,
}

impl Amortization {
    #[derive(Debug, Clone)]
    pub struct Bare {
        pub date: NaiveDate,
        pub value: Decimal,
        pub dct_override: Option<DctOverride>,
    }
}

impl Amortization::Bare {
    pub const MAX_VALUE: Decimal = Decimal::MAX;
}

#[derive(Debug, Clone)]
pub struct Payment {
    pub no: i32,
    pub date: NaiveDate,
    pub raw: Decimal,
    pub tax: Decimal,
    pub net: Decimal,
    pub gain: Decimal,
    pub amort: Decimal,
    pub bal: Decimal,
}

#[derive(Debug, Clone)]
pub struct DailyReturn {
    pub no: i32,
    pub period: i32,
    pub date: NaiveDate,
    pub value: Decimal,
    pub bal: Decimal,
    pub fixed_factor: Decimal,
    pub variable_factor: Decimal,
}

#[derive(Debug, Clone)]
pub struct LatePayment {
    pub payment: Payment,
    pub extra_gain: Decimal,
    pub penalty: Decimal,
    pub fine: Decimal,
}

impl LatePayment {
    pub const FEE_RATE: Decimal = dec!(1);
    pub const FINE_RATE: Decimal = dec!(2);
}

#[derive(Debug, Clone)]
pub struct CalcDate {
    pub value: NaiveDate,
    pub runaway: bool,
}

// Helper functions
fn delta_months(d1: NaiveDate, d2: NaiveDate) -> i32 {
    (d1.year() - d2.year()) * 12 + d1.month() as i32 - d2.month() as i32
}

fn date_range(start_date: NaiveDate, end_date: NaiveDate) -> impl Iterator<Item = NaiveDate> {
    std::iter::successors(Some(start_date), move |&date| {
        if date < end_date {
            Some(date + Duration::days(1))
        } else {
            None
        }
    })
}

fn diff_days_to_same_day_on_prev_month(base: NaiveDate) -> i32 {
    (base - (base - Duration::days(base.day() as i64 - 1) - Duration::days(1))).num_days() as i32
}

fn diff_surrounding_dates(base: NaiveDate, day_of_month: u32) -> i32 {
    if base.day() >= day_of_month || base >= NaiveDate::from_ymd_opt(1, 2, 1).unwrap() {
        let d01 = base.with_day(day_of_month).unwrap();
        let d02 = if base.day() >= day_of_month {
            d01 + Duration::days(31)
        } else {
            d01 - Duration::days(31)
        };
        let dff = if base.day() >= day_of_month {
            d02 - d01
        } else {
            d01 - d02
        };
        dff.num_days() as i32
    } else {
        panic!("can't find a date prior to the base of {} on day {}", base, day_of_month);
    }
}

// Public API. Variable index, and storage backend classes.
#[derive(Debug)]
pub struct BackendError;

#[derive(Debug, Clone)]
pub struct DailyIndex {
    pub date: NaiveDate,
    pub value: Decimal,
}

pub trait IndexStorageBackend {
    fn get_cdi_indexes(&self, begin: NaiveDate, end: NaiveDate) -> Result<Vec<DailyIndex>, BackendError>;
    fn calculate_cdi_factor(&self, begin: NaiveDate, end: NaiveDate, percentage: i32) -> Result<(Decimal, i32), BackendError>;
}

#[derive(Debug, Clone)]
pub struct VariableIndex {
    pub code: VrIndex,
    pub percentage: i32,
    pub backend: Box<dyn IndexStorageBackend>,
}

pub struct InMemoryBackend {
    _ignore_cdi: Vec<NaiveDate>,
    _registry_cdi: HashMap<NaiveDate, Decimal>,
}

impl InMemoryBackend {
    pub fn new() -> Self {
        let mut backend = InMemoryBackend {
            _ignore_cdi: Vec::new(),
            _registry_cdi: HashMap::new(),
        };
        backend.initialize_data();
        backend
    }

    fn initialize_data(&mut self) {
        self._ignore_cdi = vec![
            NaiveDate::from_ymd_opt(2018, 1, 1).unwrap(),
            NaiveDate::from_ymd_opt(2018, 2, 12).unwrap(),
            NaiveDate::from_ymd_opt(2018, 2, 13).unwrap(),
            NaiveDate::from_ymd_opt(2018, 3, 30).unwrap(),
            NaiveDate::from_ymd_opt(2018, 5, 1).unwrap(),
            NaiveDate::from_ymd_opt(2018, 5, 31).unwrap(),
            NaiveDate::from_ymd_opt(2018, 9, 7).unwrap(),
            NaiveDate::from_ymd_opt(2018, 10, 12).unwrap(),
            NaiveDate::from_ymd_opt(2018, 11, 2).unwrap(),
            NaiveDate::from_ymd_opt(2018, 11, 15).unwrap(),
            NaiveDate::from_ymd_opt(2018, 12, 25).unwrap(),
            NaiveDate::from_ymd_opt(2019, 1, 1).unwrap(),
            NaiveDate::from_ymd_opt(2019, 3, 4).unwrap(),
            NaiveDate::from_ymd_opt(2019, 3, 5).unwrap(),
            NaiveDate::from_ymd_opt(2019, 4, 19).unwrap(),
            NaiveDate::from_ymd_opt(2019, 5, 1).unwrap(),
            NaiveDate::from_ymd_opt(2019, 6, 20).unwrap(),
            NaiveDate::from_ymd_opt(2019, 11, 15).unwrap(),
            NaiveDate::from_ymd_opt(2019, 12, 25).unwrap(),
            NaiveDate::from_ymd_opt(2020, 1, 1).unwrap(),
            NaiveDate::from_ymd_opt(2020, 2, 24).unwrap(),
            NaiveDate::from_ymd_opt(2020, 2, 25).unwrap(),
            NaiveDate::from_ymd_opt(2020, 4, 10).unwrap(),
            NaiveDate::from_ymd_opt(2020, 4, 21).unwrap(),
            NaiveDate::from_ymd_opt(2020, 5, 1).unwrap(),
            NaiveDate::from_ymd_opt(2020, 6, 11).unwrap(),
            NaiveDate::from_ymd_opt(2020, 9, 7).unwrap(),
            NaiveDate::from_ymd_opt(2020, 10, 12).unwrap(),
            NaiveDate::from_ymd_opt(2020, 11, 2).unwrap(),
            NaiveDate::from_ymd_opt(2020, 12, 25).unwrap(),
            NaiveDate::from_ymd_opt(2021, 1, 1).unwrap(),
            NaiveDate::from_ymd_opt(2021, 2, 15).unwrap(),
            NaiveDate::from_ymd_opt(2021, 2, 16).unwrap(),
            NaiveDate::from_ymd_opt(2021, 4, 2).unwrap(),
            NaiveDate::from_ymd_opt(2021, 4, 21).unwrap(),
            NaiveDate::from_ymd_opt(2021, 6, 3).unwrap(),
            NaiveDate::from_ymd_opt(2021, 9, 7).unwrap(),
            NaiveDate::from_ymd_opt(2021, 10, 12).unwrap(),
            NaiveDate::from_ymd_opt(2021, 11, 2).unwrap(),
            NaiveDate::from_ymd_opt(2021, 11, 15).unwrap(),
            NaiveDate::from_ymd_opt(2022, 2, 28).unwrap(),
            NaiveDate::from_ymd_opt(2022, 3, 1).unwrap(),
            NaiveDate::from_ymd_opt(2022, 4, 15).unwrap(),
            NaiveDate::from_ymd_opt(2022, 4, 21).unwrap(),
            NaiveDate::from_ymd_opt(2022, 6, 16).unwrap(),
            NaiveDate::from_ymd_opt(2022, 9, 7).unwrap(),
            NaiveDate::from_ymd_opt(2022, 10, 12).unwrap(),
            NaiveDate::from_ymd_opt(2022, 11, 2).unwrap(),
            NaiveDate::from_ymd_opt(2022, 11, 15).unwrap(),
            NaiveDate::from_ymd_opt(2023, 2, 20).unwrap(),
            NaiveDate::from_ymd_opt(2023, 2, 21).unwrap(),
            NaiveDate::from_ymd_opt(2023, 4, 7).unwrap(),
            NaiveDate::from_ymd_opt(2023, 4, 21).unwrap(),
            NaiveDate::from_ymd_opt(2023, 5, 1).unwrap(),
            NaiveDate::from_ymd_opt(2023, 6, 8).unwrap(),
        ];

        self._registry_cdi = vec![
            (NaiveDate::from_ymd_opt(2017, 12, 29).unwrap(), NaiveDate::from_ymd_opt(2018, 2, 7).unwrap(), dec!(0.026444)),
            (NaiveDate::from_ymd_opt(2018, 2, 8).unwrap(), NaiveDate::from_ymd_opt(2018, 3, 21).unwrap(), dec!(0.025515)),
            (NaiveDate::from_ymd_opt(2018, 3, 22).unwrap(), NaiveDate::from_ymd_opt(2018, 9, 28).unwrap(), dec!(0.024583)),
            (NaiveDate::from_ymd_opt(2018, 10, 1).unwrap(), NaiveDate::from_ymd_opt(2019, 7, 31).unwrap(), dec!(0.024620)),
            (NaiveDate::from_ymd_opt(2019, 8, 1).unwrap(), NaiveDate::from_ymd_opt(2019, 9, 18).unwrap(), dec!(0.022751)),
            (NaiveDate::from_ymd_opt(2019, 9, 19).unwrap(), NaiveDate::from_ymd_opt(2019, 10, 30).unwrap(), dec!(0.020872)),
            (NaiveDate::from_ymd_opt(2019, 10, 31).unwrap(), NaiveDate::from_ymd_opt(2019, 12, 11).unwrap(), dec!(0.018985)),
            (NaiveDate::from_ymd_opt(2019, 12, 12).unwrap(), NaiveDate::from_ymd_opt(2020, 2, 5).unwrap(), dec!(0.017089)),
            (NaiveDate::from_ymd_opt(2020, 2, 6).unwrap(), NaiveDate::from_ymd_opt(2020, 3, 18).unwrap(), dec!(0.016137)),
            (NaiveDate::from_ymd_opt(2020, 3, 19).unwrap(), NaiveDate::from_ymd_opt(2020, 5, 6).unwrap(), dec!(0.014227)),
            (NaiveDate::from_ymd_opt(2020, 5, 7).unwrap(), NaiveDate::from_ymd_opt(2020, 6, 17).unwrap(), dec!(0.011345)),
            (NaiveDate::from_ymd_opt(2020, 6, 18).unwrap(), NaiveDate::from_ymd_opt(2020, 8, 5).unwrap(), dec!(0.008442)),
            (NaiveDate::from_ymd_opt(2020, 8, 6).unwrap(), NaiveDate::from_ymd_opt(2021, 3, 17).unwrap(), dec!(0.007469)),
            (NaiveDate::from_ymd_opt(2021, 3, 18).unwrap(), NaiveDate::from_ymd_opt(2021, 5, 5).unwrap(), dec!(0.010379)),
            (NaiveDate::from_ymd_opt(2021, 5, 6).unwrap(), NaiveDate::from_ymd_opt(2021, 6, 16).unwrap(), dec!(0.013269)),
            (NaiveDate::from_ymd_opt(2021, 6, 17).unwrap(), NaiveDate::from_ymd_opt(2021, 8, 4).unwrap(), dec!(0.016137)),
            (NaiveDate::from_ymd_opt(2021, 8, 5).unwrap(), NaiveDate::from_ymd_opt(2021, 9, 22).unwrap(), dec!(0.019930)),
            (NaiveDate::from_ymd_opt(2021, 9, 23).unwrap(), NaiveDate::from_ymd_opt(2021, 10, 27).unwrap(), dec!(0.023687)),
            (NaiveDate::from_ymd_opt(2021, 10, 28).unwrap(), NaiveDate::from_ymd_opt(2021, 12, 8).unwrap(), dec!(0.029256)),
            (NaiveDate::from_ymd_opt(2021, 12, 9).unwrap(), NaiveDate::from_ymd_opt(2022, 2, 2).unwrap(), dec!(0.034749)),
            (NaiveDate::from_ymd_opt(2022, 2, 3).unwrap(), NaiveDate::from_ymd_opt(2022, 3, 16).unwrap(), dec!(0.040168)),
            (NaiveDate::from_ymd_opt(2022, 3, 17).unwrap(), NaiveDate::from_ymd_opt(2022, 5, 4).unwrap(), dec!(0.043739)),
            (NaiveDate::from_ymd_opt(2022, 5, 5).unwrap(), NaiveDate::from_ymd_opt(2022, 6, 15).unwrap(), dec!(0.047279)),
            (NaiveDate::from_ymd_opt(2022, 6, 17).unwrap(), NaiveDate::from_ymd_opt(2022, 8, 3).unwrap(), dec!(0.049037)),
            (NaiveDate::from_ymd_opt(2022, 8, 4).unwrap(), NaiveDate::from_ymd_opt(2022, 11, 14).unwrap(), dec!(0.050788)),
        ];
    }
}

impl IndexStorageBackend for InMemoryBackend {
    fn get_cdi_indexes(&self, begin: NaiveDate, end: NaiveDate) -> Result<Vec<DailyIndex>, BackendError> {
        let mut result = Vec::new();
        for date in date_range(begin, end) {
            if !self._ignore_cdi.contains(&date) {
                if let Some(&value) = self._registry_cdi.get(&date) {
                    result.push(DailyIndex { date, value });
                } else {
                    // If the date is not in the registry, use the last known value
                    let last_known_value = self._registry_cdi.iter()
                        .filter(|(&d, _)| d < date)
                        .max_by_key(|(&d, _)| d)
                        .map(|(_, &v)| v)
                        .unwrap_or(ZERO);
                    result.push(DailyIndex { date, value: last_known_value });
                }
            }
        }
        Ok(result)
    }

    fn calculate_cdi_factor(&self, begin: NaiveDate, end: NaiveDate, percentage: i32) -> Result<(Decimal, i32), BackendError> {
        let indexes = self.get_cdi_indexes(begin, end)?;
        let mut factor = ONE;
        let mut count = 0;

        for index in indexes {
            if !self._ignore_cdi.contains(&index.date) {
                factor *= ONE + (index.value * Decimal::from(percentage) * CENTI);
                count += 1;
            }
        }

        Ok((factor, count))
    }
}

// The rest of the implementation (functions, methods, etc.) will follow...

pub fn get_payments_table(
    principal: Decimal,
    apy: Decimal,
    amortizations: Vec<Amortization>,
    vir: Option<VariableIndex>,
    capitalisation: Capitalisation,
    calc_date: Option<CalcDate>,
    tax_exempt: Option<bool>,
    gain_output: GainOutputMode,
) -> Result<Vec<Payment>, String> {
    // Helper function to calculate balance
    fn calc_balance(
        principal: Decimal,
        f_c: Decimal,
        interest_accrued: Decimal,
        principal_amortized_total: Decimal,
        interest_settled_total: Decimal,
    ) -> Decimal {
        principal * f_c + interest_accrued - principal_amortized_total * f_c - interest_settled_total
    }

    // Validation
    if principal == ZERO {
        return Ok(Vec::new());
    }

    if principal < CENTI {
        return Err("principal value should be at least 0.01".to_string());
    }

    if amortizations.len() < 2 {
        return Err("at least two amortizations are required: the start of the schedule, and its end".to_string());
    }

    if vir.is_none() && capitalisation == Capitalisation::Days252 {
        return Err("fixed interest rates should not use the 252 working days capitalisation".to_string());
    }

    if let Some(ref v) = vir {
        if v.code == VrIndex::CDI && capitalisation != Capitalisation::Days252 {
            return Err("CDI should use the 252 working days capitalisation".to_string());
        }
    }

    let mut aux = ZERO;
    for (i, x) in amortizations.iter().enumerate() {
        aux += x.amortization_ratio;

        // TODO: Implement price level adjustment check

        if aux > ONE && !aux.is_close_to(ONE, Some(dec!(1e-9))) {
            return Err("the accumulated percentage of the amortizations overflows 1.0".to_string());
        }
    }

    if !aux.is_close_to(ONE, Some(dec!(1e-9))) {
        return Err("the accumulated percentage of the amortizations does not reach 1.0".to_string());
    }

    let calc_date = calc_date.unwrap_or(CalcDate {
        value: amortizations.last().unwrap().date,
        runaway: false,
    });

    // Initialize registers
    let mut regs = Registers::new();

    // Main calculation phases
    let mut payments = Vec::new();
    for (num, (ent0, ent1)) in amortizations.windows(2).enumerate() {
        let due = min(calc_date.value, ent1.date);
        let mut f_s = ONE;
        let mut f_c = ONE;

        // Phase B.0: Calculate spread and correction factors
        if ent0.date < calc_date.value || ent1.date <= calc_date.value {
            match (&vir, capitalisation) {
                (None, Capitalisation::Days360) => {
                    let days = (due - ent0.date).num_days() as Decimal;
                    f_s = calculate_interest_factor(apy, days / dec!(360), false);
                },
                (None, Capitalisation::Days365) => {
                    let days = (due - ent0.date).num_days() as Decimal;
                    f_s = calculate_interest_factor(apy, days / dec!(365), false);
                },
                (None, Capitalisation::Days30360) => {
                    let mut dcp = (due - ent0.date).num_days() as Decimal;
                    let mut dct = (ent1.date - ent0.date).num_days() as Decimal;

                    // Handle DCT override cases
                    if let Some(override_data) = &ent1.dct_override {
                        if num == 0 {
                            dct = diff_surrounding_dates(ent0.date, 24) as Decimal;
                        } else {
                            dct = (override_data.date_to - override_data.date_from).num_days() as Decimal;
                            if override_data.predates_first_amortization {
                                dct = diff_surrounding_dates(override_data.date_from, 24) as Decimal;
                            }
                        }
                    }

                    if let Some(override_data) = &ent0.dct_override {
                        dct = (ent1.date - override_data.date_from).num_days() as Decimal;
                        if override_data.predates_first_amortization {
                            dct = diff_surrounding_dates(override_data.date_from, 24) as Decimal;
                        }
                    }

                    f_s = calculate_interest_factor(apy, dcp / (dec!(12) * dct), false);
                },
                (Some(v), Capitalisation::Days252) if v.code == VrIndex::CDI => {
                    let f_v = v.backend.calculate_cdi_factor(ent0.date, due, v.percentage).unwrap();
                    let f_s_temp = calculate_interest_factor(apy, Decimal::from(f_v.1) / dec!(252), false);
                    f_s = f_s_temp * f_v.0;
                },
                // Add other cases here as needed
                _ => return Err("Unsupported combination of variable interest rate and capitalisation".to_string()),
            }
        }

        // Phase B.1: Register variations in principal, interest, and monetary correction
        if ent0.date < calc_date.value || ent1.date <= calc_date.value || calc_date.runaway {
            // Register accrued interest
            regs.interest.current = calc_balance(principal, f_c, regs.interest.accrued, regs.principal.amortized.total, regs.interest.settled.total) * (f_s - ONE);
            regs.interest.accrued += regs.interest.current;
            regs.interest.deferred = regs.interest.accrued - (regs.interest.current + regs.interest.settled.total);

            match ent1 {
                Amortization { amortization_ratio, amortizes_interest, .. } => {
                    // Regular amortization
                    let adj = (ONE - regs.principal.amortization_ratio.current) / (ONE - regs.principal.amortization_ratio.regular);
                    let amortization = amortization_ratio * adj;

                    // Register principal amortization
                    regs.principal.amortization_ratio.current += amortization;
                    regs.principal.amortized.current = amortization * principal;
                    regs.principal.amortized.total = regs.principal.amortization_ratio.current * principal;

                    // Register regular amortization
                    regs.principal.amortization_ratio.regular += *amortization_ratio;

                    // Register interest to be paid
                    if *amortizes_interest {
                        regs.interest.settled.current = regs.interest.current + regs.principal.amortization_ratio.current * regs.interest.deferred;
                        regs.interest.settled.total += regs.interest.settled.current;
                    }
                },
                Amortization::Bare { value, .. } => {
                    // Prepayment (extraordinary amortization)
                    let plfv = principal * (ONE - regs.principal.amortization_ratio.current) * (f_c - ONE);
                    let val0 = value.min(&calc_balance(principal, f_c, regs.interest.accrued, regs.principal.amortized.total, regs.interest.settled.total));
                    let val1 = val0.min(&(regs.interest.accrued - regs.interest.settled.total));
                    let val2 = (val0 - val1).min(&plfv);
                    let val3 = val0 - val1 - val2;

                    // Register principal amortization
                    regs.principal.amortization_ratio.current += val3 / principal;
                    regs.principal.amortized.current = val3;
                    regs.principal.amortized.total += val3;

                    // Register interest to be paid
                    regs.interest.settled.current = val1;
                    regs.interest.settled.total += val1;
                }
            }
        }

        // Phase B.2: Assemble the payment instance and perform rounding
        if ent0.date < calc_date.value || ent1.date <= calc_date.value || calc_date.runaway {
            let mut payment = Payment {
                no: num as i32 + 1,
                date: ent1.date,
                raw: ZERO,
                tax: ZERO,
                net: ZERO,
                gain: ZERO,
                amort: ZERO,
                bal: ZERO,
            };

            // Assemble the payment
            payment.amort = regs.principal.amortized.current;
            payment.gain = match gain_output {
                GainOutputMode::Deferred => regs.interest.deferred + regs.interest.current,
                GainOutputMode::Settled => if matches!(ent1, Amortization { amortizes_interest: true, .. }) { regs.interest.settled.current } else { ZERO },
                GainOutputMode::Current => regs.interest.current,
            };
            payment.bal = calc_balance(principal, f_c, regs.interest.accrued, regs.principal.amortized.total, regs.interest.settled.total);

            // Calculate raw value and tax
            if matches!(ent1, Amortization { amortizes_interest: true, .. }) {
                payment.raw = payment.amort + regs.interest.settled.current;
                payment.tax = regs.interest.settled.current * calculate_revenue_tax(amortizations[0].date, due);
            } else if payment.amort > ZERO {
                payment.raw = payment.amort;
                payment.tax = ZERO;
            } else if matches!(ent1, Amortization { amortizes_interest: true, .. }) {
                payment.raw = regs.interest.settled.current;
                payment.tax = regs.interest.settled.current * calculate_revenue_tax(amortizations[0].date, due);
            } else {
                payment.raw = ZERO;
                payment.tax = ZERO;
            }

            // Apply tax exemption if applicable
            if tax_exempt.unwrap_or(false) {
                payment.tax = ZERO;
            }

            // Round values
            payment.amort = payment.amort.round_dp(2);
            payment.gain = payment.gain.round_dp(2);
            payment.raw = payment.raw.round_dp(2);
            payment.tax = payment.tax.round_dp(2);
            payment.net = (payment.raw - payment.tax).round_dp(2);
            payment.bal = payment.bal.round_dp(2);

            payments.push(payment);

            // Break if balance is zero
            if payment.bal == ZERO {
                break;
            }
        }
    }

    Ok(payments)
}

pub fn get_daily_returns(
    principal: Decimal,
    apy: Decimal,
    amortizations: Vec<Amortization>,
    vir: Option<VariableIndex>,
    capitalisation: Capitalisation,
) -> Result<Vec<DailyReturn>, String> {
    // Internal functions
    fn get_normalized_cdi_indexes(backend: &dyn IndexStorageBackend) -> impl Iterator<Item = Decimal> + '_ {
        backend.get_cdi_indexes(amortizations[0].date, amortizations.last().unwrap().date)
            .unwrap()
            .into_iter()
            .map(|index| index.value / dec!(100))
    }

    fn get_normalized_savings_indexes(backend: &dyn IndexStorageBackend) -> impl Iterator<Item = Decimal> + '_ {
        backend.get_savings_indexes(amortizations[0].date, amortizations.last().unwrap().date)
            .unwrap()
            .into_iter()
            .flat_map(|ranged| {
                let init = amortizations[0].date.max(ranged.begin_date);
                let ends = amortizations.last().unwrap().date.min(ranged.end_date);
                let days = (ranged.end_date - ranged.begin_date).num_days() as Decimal;
                let rate = calculate_interest_factor(ranged.value, ONE / days, false);
                date_range(init, ends).map(move |_| rate - ONE)
            })
    }

    fn calc_balance(
        principal: Decimal,
        f_c: Decimal,
        interest_accrued: Decimal,
        principal_amortized_total: Decimal,
        interest_settled_total: Decimal,
    ) -> Decimal {
        principal * f_c + interest_accrued - principal_amortized_total * f_c - interest_settled_total
    }

    // A. Validate and prepare for execution
    if principal == ZERO {
        return Ok(Vec::new());
    }

    if principal < CENTI {
        return Err("principal value should be at least 0.01".to_string());
    }

    if amortizations.len() < 2 {
        return Err("at least two amortizations are required: the start of the schedule, and its end".to_string());
    }

    if vir.is_none() && capitalisation == Capitalisation::Days252 {
        return Err("fixed interest rates should not use the 252 working days capitalisation".to_string());
    }

    if let Some(ref v) = vir {
        if v.code == VrIndex::CDI && capitalisation != Capitalisation::Days252 {
            return Err("CDI should use the 252 working days capitalisation".to_string());
        }
    }

    let mut aux = ZERO;
    for (i, x) in amortizations.iter().enumerate() {
        aux += x.amortization_ratio;
        // TODO: Implement price level adjustment check
        if aux > ONE && !aux.is_close_to(ONE, Some(dec!(1e-9))) {
            return Err("the accumulated percentage of the amortizations overflows 1.0".to_string());
        }
    }

    if !aux.is_close_to(ONE, Some(dec!(1e-9))) {
        return Err("the accumulated percentage of the amortizations does not reach 1.0".to_string());
    }

    let mut regs = Registers::new();
    let mut gens = Generators::new();

    // Initialize indexes
    let idxs = match &vir {
        Some(v) if v.code == VrIndex::CDI => Box::new(get_normalized_cdi_indexes(&*v.backend)) as Box<dyn Iterator<Item = Decimal>>,
        Some(v) if v.code == VrIndex::Poupanca => Box::new(get_normalized_savings_indexes(&*v.backend)) as Box<dyn Iterator<Item = Decimal>>,
        Some(_) => return Err("Unsupported variable index".to_string()),
        None => Box::new(std::iter::repeat(ZERO)) as Box<dyn Iterator<Item = Decimal>>,
    };

    // B. Execute
    let mut daily_returns = Vec::new();
    let mut amortization_iter = amortizations.iter();
    let mut current_amortization = amortization_iter.next().unwrap();
    let mut next_amortization = amortization_iter.next().unwrap();
    let mut period = 1;
    let mut count = 1;

    for ref_date in date_range(amortizations[0].date, amortizations.last().unwrap().date) {
        let mut f_c = ONE;
        let mut f_v = ONE;
        let mut f_s = ONE;

        // B.0. Calculate spread and correction factors
        match (vir.as_ref(), capitalisation) {
            (None, Capitalisation::Days360) => {
                f_s = calculate_interest_factor(apy, ONE / dec!(360), false);
            },
            (None, Capitalisation::Days365) => {
                f_s = calculate_interest_factor(apy, ONE / dec!(365), false);
            },
            (None, Capitalisation::Days30360) => {
                let v01 = calculate_interest_factor(apy, ONE / dec!(12), false) - ONE;
                let v02 = if period == 1 && ref_date < next_amortization.date {
                    Decimal::from((amortizations[1].date - amortizations[0].date).num_days())
                } else if ref_date == next_amortization.date {
                    Decimal::from(next_amortization.date.days_in_month())
                } else {
                    Decimal::from(current_amortization.date.days_in_month())
                };
                f_s = calculate_interest_factor(v01, ONE / v02, false);
            },
            (Some(v), Capitalisation::Days252) if v.code == VrIndex::CDI => {
                f_v = idxs.next().unwrap() * Decimal::from(v.percentage) / dec!(100) + ONE;
                if f_v > ONE {
                    f_s = calculate_interest_factor(apy, ONE / dec!(252), false);
                }
            },
            (Some(v), Capitalisation::Days360) if v.code == VrIndex::Poupanca => {
                f_s = calculate_interest_factor(apy, ONE / dec!(360), false);
                f_v = idxs.next().unwrap() * Decimal::from(v.percentage) / dec!(100) + ONE;
            },
            _ => return Err("Unsupported combination of variable interest rate and capitalisation".to_string()),
        }

        // B.1. Register variations in principal, interest, and monetary correction
        while ref_date == next_amortization.date {
            match next_amortization {
                Amortization { amortization_ratio, amortizes_interest, .. } => {
                    let adj = (ONE - regs.principal.amortization_ratio.current) / (ONE - regs.principal.amortization_ratio.regular);
                    gens.principal_tracker_1.send(amortization_ratio * adj);
                    gens.principal_tracker_2.send(*amortization_ratio);
                    if *amortizes_interest {
                        gens.interest_tracker_2.send(regs.interest.current + regs.principal.amortization_ratio.current * regs.interest.deferred);
                    }
                    regs.interest.current = ZERO;
                    period += 1;
                    count = 1;
                },
                Amortization::Bare { value, .. } => {
                    let plfv = principal * (ONE - regs.principal.amortization_ratio.current) * (f_c - ONE);
                    let val0 = value.min(&calc_balance(principal, f_c, regs.interest.accrued, regs.principal.amortized.total, regs.interest.settled.total));
                    let val1 = val0.min(&(regs.interest.accrued - regs.interest.settled.total));
                    let val2 = (val0 - val1).min(&plfv);
                    let val3 = val0 - val1 - val2;
                    gens.principal_tracker_1.send(val3 / principal);
                    gens.interest_tracker_2.send(val1);
                    regs.interest.current = ZERO;
                },
            }
            current_amortization = next_amortization;
            next_amortization = amortization_iter.next().unwrap_or(current_amortization);
        }

        gens.interest_tracker_1.send(calc_balance(principal, f_c, regs.interest.accrued, regs.principal.amortized.total, regs.interest.settled.total) * (f_s * f_v * f_c - ONE));

        // B.2. Assemble the daily return instance and perform rounding
        if calc_balance(principal, f_c, regs.interest.accrued, regs.principal.amortized.total, regs.interest.settled.total).round_dp(2) == ZERO {
            break;
        }

        let daily_return = DailyReturn {
            no: count,
            period,
            date: ref_date,
            value: regs.interest.daily.round_dp(2),
            bal: calc_balance(principal, f_c, regs.interest.accrued, regs.principal.amortized.total, regs.interest.settled.total).round_dp(2),
            fixed_factor: f_s,
            variable_factor: f_v * f_c,
        };

        daily_returns.push(daily_return);
        count += 1;
    }

    Ok(daily_returns)
}

fn calculate_revenue_tax(begin: NaiveDate, end: NaiveDate) -> Decimal {
    if end <= begin {
        panic!("end date should be greater than the begin date");
    }

    let diff = (end - begin).num_days();

    for &(minimum, maximum, rate) in REVENUE_TAX_BRACKETS.iter() {
        if minimum < diff && diff <= maximum {
            return rate;
        }
    }

    panic!("No matching tax bracket found");
}

struct Registers {
    interest: InterestRegisters,
    principal: PrincipalRegisters,
}

impl Registers {
    fn new() -> Self {
        Registers {
            interest: InterestRegisters::new(),
            principal: PrincipalRegisters::new(),
        }
    }
}

struct InterestRegisters {
    current: Decimal,
    accrued: Decimal,
    settled: SettledInterest,
    deferred: Decimal,
}

impl InterestRegisters {
    fn new() -> Self {
        InterestRegisters {
            current: ZERO,
            accrued: ZERO,
            settled: SettledInterest::new(),
            deferred: ZERO,
        }
    }
}

struct SettledInterest {
    current: Decimal,
    total: Decimal,
}

impl SettledInterest {
    fn new() -> Self {
        SettledInterest {
            current: ZERO,
            total: ZERO,
        }
    }
}

struct PrincipalRegisters {
    amortization_ratio: AmortizationRatio,
    amortized: AmortizedPrincipal,
}

impl PrincipalRegisters {
    fn new() -> Self {
        PrincipalRegisters {
            amortization_ratio: AmortizationRatio::new(),
            amortized: AmortizedPrincipal::new(),
        }
    }
}

struct AmortizationRatio {
    current: Decimal,
    regular: Decimal,
}

impl AmortizationRatio {
    fn new() -> Self {
        AmortizationRatio {
            current: ZERO,
            regular: ZERO,
        }
    }
}

struct AmortizedPrincipal {
    current: Decimal,
    total: Decimal,
}

impl AmortizedPrincipal {
    fn new() -> Self {
        AmortizedPrincipal {
            current: ZERO,
            total: ZERO,
        }
    }
}
