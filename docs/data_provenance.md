# Data Provenance Documentation

## 1. Original Data Source

Dataset Name: Online Retail II\
Source: UCI Machine Learning Repository / Kaggle\
Original File Format: Microsoft Excel (.xlsx)

The original dataset contains two worksheets:

-   2009--2010\
-   2010--2011

This study uses only the 2010--2011 worksheet.

------------------------------------------------------------------------

## 2. Dataset Selection Rationale

The 2010--2011 sheet was selected to:

-   Ensure a consistent and continuous two-year observation window\
-   Avoid partial-period effects from the 2009--2010 sheet\
-   Maintain temporal coherence for daily aggregation and lag-based
    feature engineering\
-   Reduce cross-sheet structural inconsistencies

The dataset scope is therefore strictly limited to transactions
occurring within the 2010--2011 period.

No 2009 data is used anywhere in this study.

------------------------------------------------------------------------

## 3. Conversion Process

The 2010--2011 worksheet was exported from the original Excel file into
CSV format.

Conversion details:

-   File format changed from .xlsx to .csv\
-   Column names were preserved exactly as in the original worksheet\
-   No rows were removed\
-   No filtering was applied\
-   No data cleaning was performed\
-   No transformations were applied during export

The exported CSV represents the unmodified raw dataset used in Phase 1
inspection.

------------------------------------------------------------------------

## 4. Stored Raw File

Location within project:

data/raw/online_retail_II_2010_2011.csv

This file serves as the immutable raw data input for the experimental
pipeline.

All data cleaning and preprocessing operations occur only in subsequent
phases.

------------------------------------------------------------------------

## 5. Data Integrity Statement

The raw CSV file used in this study is a direct structural export of the
2010--2011 worksheet from the original Online Retail II dataset.

No analytical manipulation, filtering, or transformation occurred prior
to Phase 1 inspection.

This ensures:

-   Transparency of data lineage\
-   Reproducibility of experimental results\
-   Clear separation between raw data and processed data
