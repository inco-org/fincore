# Fincore

INCO financial core.

Financial calculation library for credit and investment operations.

Its main purpose is to generate payments for loans with a Bullet, Price, American Amortization, or Custom (constant amortization, grace period, etc.) systems. Supports fixed-rate operations, or indexed to CDI, Brazilian Savings, or IPCA. Accounts for interest in a 252 business day year for CDI; or 30/360 basis for fixed-rate and other indexes.

This library also generates daily returns tables for loans. It covers the same modalities and the same capitalization forms as the payments generation routine.

The library supports not only regular flows, but also irregular ones, with prepayments, and assists in the calculation of arrears.

## Coverage

[![Coverage badge](https://raw.githubusercontent.com/inco-org/fincore/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/inco-org/fincore/blob/python-coverage-comment-action-data/htmlcov/index.html)
