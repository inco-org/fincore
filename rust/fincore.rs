use chrono::{Date, Datelike, Duration, NaiveDate, Utc};
use rust_decimal::Decimal;
use rust_decimal_macros::dec;
use std::cmp::min;
use std::collections::HashMap;
use serde_json::Value;

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

// The rest of the implementation (functions, methods, etc.) will follow...
