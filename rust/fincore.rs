use chrono::NaiveDate;
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;

// Constants
const CENTI: Decimal = Decimal::from_parts(1, 0, 0, false, 2); // 0.01
const ZERO: Decimal = Decimal::ZERO;
const ONE: Decimal = Decimal::ONE;

// Structs
#[derive(Debug, Clone)]
pub struct PriceLevelAdjustment {
    code: String,
    base_date: Option<NaiveDate>,
    period: i32,
    shift: String,
    amortizes_adjustment: bool,
}

fn main() {
    println!("Hello from Rust fincore!");
}

#[derive(Debug, Clone)]
pub struct DctOverride {
    date_from: NaiveDate,
    date_to: NaiveDate,
    predates_first_amortization: bool,
}

#[derive(Debug, Clone)]
pub struct Amortization {
    date: NaiveDate,
    amortization_ratio: Decimal,
    amortizes_interest: bool,
    price_level_adjustment: Option<PriceLevelAdjustment>,
    dct_override: Option<DctOverride>,
}

pub struct VariableIndex {
    // Add fields as needed
}

pub struct CalcDate {
    // Add fields as needed
}

#[derive(Debug, Clone)]
pub struct Payment {
    no: i32,
    date: NaiveDate,
    raw: Decimal,
    tax: Decimal,
    net: Decimal,
    gain: Decimal,
    amort: Decimal,
    bal: Decimal,
}

// Helper functions
fn calculate_revenue_tax(begin: NaiveDate, end: NaiveDate) -> Decimal {
    if end <= begin {
        panic!("End date should be greater than the begin date.");
    }

    let diff = end.signed_duration_since(begin).num_days();
    let tax_brackets = [
        (0, 180, Decimal::new(225, 3)),
        (180, 360, Decimal::new(2, 1)),
        (360, 720, Decimal::new(175, 3)),
        (720, i64::MAX, Decimal::new(15, 2)),
    ];

    for &(minimum, maximum, rate) in &tax_brackets {
        if minimum < diff && diff <= maximum {
            return rate;
        }
    }

    panic!("No matching tax bracket found.");
}

fn calculate_interest_factor(rate: Decimal, period: Decimal, percent: bool) -> Decimal {
    let rate = if percent { rate / Decimal::from(100) } else { rate };
    (ONE + rate).pow(period)
}

// Main functions (to be implemented)
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub enum VariableIndex {
    CDI(Decimal),
    Poupanca(Decimal),
    IPCA(Decimal),
    IGPM(Decimal),
}

#[derive(Debug, Clone)]
pub struct CalcDate {
    pub value: NaiveDate,
    pub runaway: bool,
}

pub fn get_payments_table(
    principal: Decimal,
    apy: Decimal,
    amortizations: Vec<Amortization>,
    vir: Option<VariableIndex>,
    capitalisation: String,
    calc_date: Option<CalcDate>,
    tax_exempt: Option<bool>,
    gain_output: String,
) -> Vec<Payment> {
    if principal == Decimal::zero() {
        return Vec::new();
    }

    if principal < Decimal::new(1, 2) {
        panic!("Principal value should be at least 0.01");
    }

    if amortizations.len() < 2 {
        panic!("At least two amortizations are required: the start of the schedule, and its end");
    }

    let calc_date = calc_date.unwrap_or(CalcDate {
        value: amortizations.last().unwrap().date,
        runaway: false,
    });

    let mut payments = Vec::new();
    let mut balance = principal;
    let mut accrued_interest = Decimal::zero();
    let mut total_amortized = Decimal::zero();

    for (i, amortization) in amortizations.iter().enumerate().skip(1) {
        let previous = &amortizations[i - 1];
        let due_date = calc_date.value.min(amortization.date);

        // Calculate factors
        let (f_s, f_c) = calculate_factors(
            &previous.date,
            &due_date,
            &apy,
            &vir,
            &capitalisation,
        );

        // Calculate interest
        let interest = balance * (f_s * f_c - ONE);
        accrued_interest += interest;

        // Calculate amortization
        let amortization_amount = principal * amortization.amortization_ratio;
        total_amortized += amortization_amount;

        // Create payment
        let payment = Payment {
            no: i as i32,
            date: amortization.date,
            raw: amortization_amount + interest,
            tax: if tax_exempt.unwrap_or(false) { Decimal::zero() } else { interest * calculate_revenue_tax(amortizations[0].date, due_date) },
            net: Decimal::zero(), // Will be calculated later
            gain: match gain_output.as_str() {
                "current" => interest,
                "deferred" => accrued_interest,
                "settled" => if amortization.amortizes_interest { accrued_interest } else { Decimal::zero() },
                _ => panic!("Invalid gain_output value"),
            },
            amort: amortization_amount,
            bal: balance - amortization_amount,
        };

        // Update balance
        balance = payment.bal;

        // Calculate net value
        let payment = Payment {
            net: payment.raw - payment.tax,
            ..payment
        };

        payments.push(payment);

        if balance == Decimal::zero() {
            break;
        }
    }

    payments
}

fn calculate_factors(
    start_date: &NaiveDate,
    end_date: &NaiveDate,
    apy: &Decimal,
    vir: &Option<VariableIndex>,
    capitalisation: &str,
) -> (Decimal, Decimal) {
    let f_s = match capitalisation {
        "360" => calculate_interest_factor(*apy, Decimal::from((end_date - start_date).num_days()) / Decimal::from(360), true),
        "365" => calculate_interest_factor(*apy, Decimal::from((end_date - start_date).num_days()) / Decimal::from(365), true),
        "30/360" => {
            let days = Decimal::from((end_date - start_date).num_days());
            calculate_interest_factor(*apy, days / Decimal::from(360), true)
        },
        "252" => {
            if let Some(VariableIndex::CDI(percentage)) = vir {
                let working_days = Decimal::from(252); // This should be calculated properly
                calculate_interest_factor(*apy, working_days / Decimal::from(252), true) * (ONE + percentage / Decimal::from(100))
            } else {
                panic!("CDI index required for 252 capitalisation");
            }
        },
        _ => panic!("Unsupported capitalisation method"),
    };

    let f_c = match vir {
        Some(VariableIndex::IPCA(factor)) | Some(VariableIndex::IGPM(factor)) => *factor,
        _ => ONE,
    };

    (f_s, f_c)
}

// Other functions and implementations would follow...
