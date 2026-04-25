# Data Dictionary

This file documents every field in the dataset used across the analysis pipeline, Tableau dashboard, and KPI framework.

## Dataset Summary

| Item | Details |
|---|---|
| Dataset name | Retail Analysis Large Dataset |
| Source | [Link](https://www.kaggle.com/datasets/sahilprajapati143/retail-analysis-large-dataset) |
| Raw file name | `raw_retail_data.csv` |
| Cleaned file name | `cleaned_dataset.csv` |
| Tableau-ready file name | `tableau_ready_dataset.csv` |
| Last updated | 2 years ago (as of Kaggle listing) |
| Raw row count | 302,010 |
| Cleaned row count | 293,468 |
| Raw column count | 30 |
| Cleaned column count | 25 |
| Granularity | One row per transaction |

---

## Columns Dropped During Cleaning

The following 5 columns were removed in `02_cleaning.ipynb` as they were PII (personally identifiable information) not required for analysis:

| Column Dropped | Reason |
|---|---|
| `Name` | PII — not used in any analysis or KPI |
| `Email` | PII — not used in any analysis or KPI |
| `Phone` | PII — not used in any analysis or KPI |
| `Address` | PII — not used in any analysis or KPI |
| `Zipcode` | Redundant — Country/City/State used for geography |

---

## Column Definitions (Cleaned Dataset — 25 Columns)

| Column Name | Data Type | Description | Example Value | Used In | Cleaning Notes |
|---|---|---|---|---|---|
| `Transaction_ID` | Int64 | Unique identifier for each transaction | 8691788 | EDA / KPI | Cast from float64 to Int64. 1 null dropped. 7,544 duplicate Transaction IDs removed (kept first). |
| `Customer_ID` | Int64 | Unique identifier for each customer | 37249 | EDA / KPI | Cast from float64 to Int64. 296 nulls dropped as part of null row removal. |
| `City` | category | City where the customer is located | Dortmund | EDA / Tableau | Cast to category. 244 nulls dropped as part of null row removal. |
| `State` | category | State or region of the customer | Berlin | EDA / Tableau | Cast to category. 271 nulls dropped as part of null row removal. |
| `Country` | category | Country of the customer | Germany | EDA / KPI / Tableau | Cast to category. 266 nulls dropped as part of null row removal. |
| `Age` | Int64 | Age of the customer in years | 21 | EDA / Statistical Analysis | Cast from float64 to Int64. 169 nulls dropped. |
| `Gender` | category | Gender of the customer | Male | EDA / Tableau | Cast to category. 310 nulls dropped. |
| `Income` | category | Income bracket of the customer (Low / Medium / High) | Low | EDA / Tableau | Cast to category. 282 nulls dropped. |
| `Customer_Segment` | category | Customer loyalty segment (New / Regular / Premium) | Regular | EDA / KPI / Tableau | Cast to category. 208 nulls dropped. |
| `Date` | datetime64 | Date of the transaction | 2023-09-18 | EDA / KPI / Tableau | Converted from string using `pd.to_datetime()`. 351 nulls dropped via `dropna(subset=['Date'])`. |
| `Year` | Int64 | Year extracted from Date | 2023 | EDA / Tableau | Re-derived from cleaned Date column. Cast to Int64. |
| `Month` | object (ordered category) | Month name extracted from Date | September | EDA / Tableau | Re-derived from cleaned Date column. Set as ordered categorical (January → December) for correct sorting. |
| `Time` | object | Time of the transaction (HH:MM:SS) | 22:03:55 | EDA / KPI | Parsed using `pd.to_datetime` with `format='%H:%M:%S'`. 336 nulls coerced. |
| `Total_Purchases` | Int64 | Number of items purchased in the transaction | 3 | EDA / KPI | Cast from float64 to Int64. 354 nulls dropped. |
| `Amount` | float64 | Price per item (unit price) | 108.03 | EDA / KPI | Rounded to 2 decimal places. 347 nulls dropped. |
| `Total_Amount` | Float64 | Total transaction value (Amount × Total_Purchases) | 324.09 | EDA / KPI / Tableau | Rounded to 2 decimal places. 351 nulls dropped. |
| `Product_Category` | category | High-level product category | Clothing | EDA / KPI / Tableau | Cast to category. Nulls dropped as part of row removal. |
| `Product_Brand` | category | Brand of the product purchased | Nike | EDA / Tableau | Cast to category. Nulls dropped as part of row removal. |
| `Product_Type` | category | Specific product sub-type | Shorts | EDA / Tableau | Cast to category. No nulls in raw data. |
| `Feedback` | category | Customer feedback label (Excellent / Average / Bad / Good) | Excellent | EDA / KPI | Cast to category. Nulls dropped as part of row removal. |
| `Shipping_Method` | category | Delivery method used (Standard / Express / Same-Day) | Same-Day | EDA / Tableau | Cast to category. Nulls dropped as part of row removal. |
| `Payment_Method` | category | Payment method used (Credit Card / Debit Card / PayPal / Cash) | Debit Card | EDA / Tableau | Cast to category. Nulls dropped as part of row removal. |
| `Order_Status` | category | Current status of the order (Shipped / Processing / Delivered / Cancelled) | Shipped | EDA / Tableau | Cast to category. Nulls dropped as part of row removal. |
| `Ratings` | Int64 | Customer rating for the transaction (1–5) | 5 | EDA / KPI / Tableau | Cast from float64 to Int64. Nulls dropped as part of row removal. |
| `products` | category | Specific product name purchased | Cycling shorts | EDA / Tableau | Cast to category. No nulls in raw data. |

---

## Derived Columns (Added in `05_final_load_prep.ipynb`)

| Derived Column | Data Type | Logic | Business Meaning |
|---|---|---|---|
| `Month_Num` | int64 | `df['Date'].dt.month` | Numeric month (1–12) so Tableau sorts months chronologically instead of alphabetically |
| `Quarter` | object | `df['Date'].dt.quarter` mapped to Q1–Q4 | Groups transactions by business quarter for trend analysis |
| `Day_of_Week` | object | `df['Date'].dt.day_name()` | Day of the week (Monday–Sunday) for identifying peak transaction days |
| `Hour` | int64 | `pd.to_datetime(df['Time']).dt.hour` | Hour of transaction (0–23) for peak hour analysis in the dashboard |
| `Revenue_per_Purchase` | float64 | `Total_Amount / Total_Purchases` rounded to 2dp | Average basket value per item — measures spend efficiency per transaction |
| `High_Value_Flag` | int64 | 1 if `Total_Amount` > 75th percentile, else 0 | Flags the top 25% of transactions by spend for premium customer targeting |
| `Satisfied_Flag` | int64 | 1 if `Ratings` >= 4, else 0 | Binary satisfaction indicator — used to compute overall satisfaction rate KPI |
| `Feedback_Score` | int64 | Excellent=3, Average=2, Bad=1, Good=2 | Numeric encoding of feedback text for aggregation and correlation analysis |

---

## Data Quality Notes

- **7,548 rows removed** during deduplication: 4 fully duplicate rows and 7,544 rows with duplicate `Transaction_ID` values (first occurrence kept).
- **Null rows dropped** using `dropna()` on critical columns: `Transaction_ID`, `Customer_ID`, `Amount`, and `Date`. This cascaded and removed nulls across all other columns, resulting in a fully clean dataset with 0 nulls.
- **5 PII columns dropped**: `Name`, `Email`, `Phone`, `Address`, `Zipcode` — not required for any analysis or dashboard.
- **Final cleaned shape**: 293,468 rows × 25 columns (down from 302,010 × 30 in raw).
- **`Month` column** was re-derived from the cleaned `Date` column and set as an ordered categorical to ensure correct chronological sorting.
- **`Year` column** was re-derived from the cleaned `Date` column to overwrite the original float values.
- **Time period covered**: 2023–2024 based on `Year` values observed in the dataset.
- **`products` column** contains specific product names (e.g. "Cycling shorts", "Lenovo Tab") which are more granular than `Product_Type` and used for drill-down analysis only.