# Retail Sales Data Processing and Business Insights Generation
**NeoStats Data Engineering Assignment — ABC Retail Solutions**

---

## Overview

This project builds an end-to-end data engineering pipeline for ABC Retail 
Solutions, a multinational retail company operating across multiple cities 
through online and offline sales channels. The pipeline ingests raw retail 
transaction data from two source systems, cleans and transforms it, 
calculates business KPIs, and delivers insights through an interactive 
Power BI dashboard.The project focuses on building a clean, reliable analytics dataset and translating it into actionable business insights.

---

## Problem Statement

The raw datasets contained several data quality issues including duplicate 
transactions, missing prices, inconsistent category names, invalid quantities, 
mixed date formats, and unmasked customer PII. Without fixing these, the 
business could not generate accurate revenue reports or make reliable 
data-driven decisions.

---

## Project Structure
neostats-retail-pipeline/
├── notebooks/
│   └── retail_pipeline.ipynb (Main Jupyter Notebook (full pipeline))
├── scripts/
│   └── retail_pipeline.py (Python script converted from notebook)
├── data/
│   ├── raw/
│   │   └── USECASE_-_Data_Engineering.xlsx
│   └── processed/
│       ├── cleaned_retail_data.csv
│       ├── kpi_revenue_by_category.csv
│       ├── kpi_revenue_by_city.csv
│       ├── kpi_top_products.csv
│       ├── rfm_segments.csv
│       └── kpi_mom_growth.csv
├── powerbi/
│   ├── retail_dashboard.pbix
│   └── dashboard_screenshot.png
├── docs/
│   └── documentation.docx
├── requirements.txt
└── README.md

---

## Tech Stack

| Area | Technology |
|---|---|
| Language | Python 3.x |
| Data Processing | Pandas, NumPy |
| EDA Visualization | Matplotlib, Seaborn |
| Dashboard | Microsoft Power BI Desktop |
| PII Protection | Python hashlib (SHA-256) |
| Cloud Storage | Microsoft Azure Blob Storage |
| IDE | Jupyter Notebook |
| Version Control | Git, GitHub |

---

## How to Run

**Step 1** — Clone the repository
```bash
git clone https://github.com/yourusername/neostats-retail-pipeline.git
cd neostats-retail-pipeline
```

**Step 2** — Install dependencies
```bash
pip install -r requirements.txt
```

**Step 3** — Place the raw data file
Copy `USECASE_-_Data_Engineering.xlsx` into the `data/raw/` folder

**Step 4** — Launch Jupyter Notebook
```bash
jupyter notebook
```
Open `notebooks/retail_pipeline.ipynb` and run all cells top to bottom

**Step 5** — Open the dashboard
Open `powerbi/retail_dashboard.pbix` in Power BI Desktop

---

## Pipeline Steps
The pipeline follows a clear, ordered flow to ensure data correctness at each stage.

1. **Data Ingestion** — Read all 3 sheets from Excel into Python DataFrames
2. **Data Merging** — Combine retail_data1 and retail_data2 into one dataset
3. **Remove Failed Payments** — Keep only successful transactions
4. **Deduplication** — Remove exact duplicate rows
5. **Date Standardization** — Parse mixed Excel serial and string date formats
6. **Price Imputation** — Fill missing prices from product_details reference table
7. **Quantity Validation** — Remove rows with quantity <= 0
8. **Category Standardization** — Map 12 variations to 4 standard categories
9. **Text Cleaning** — Standardize casing and remove whitespace
10. **PII Masking** — SHA-256 hash email and phone, drop originals
11. **Discount Validation** — Remove out-of-range discount values
12. **Feature Engineering** — Calculate revenue, date parts, RFM segments
13. **Save Outputs** — Write cleaned CSV files locally
14. **Azure Upload** — Upload raw and processed files to Azure Blob Storage

---

## Key Business KPIs

- Total Revenue
- Total Transactions
- Total Unique Customers
- Average Order Value
- Revenue by Category
- Revenue by City
- Month-over-Month Revenue Growth
- RFM Customer Segmentation (Champions, Loyal, Potential, At Risk)

---

## Power BI Dashboard Pages

| Page | What It Shows |
|---|---|
| Revenue Overview | Monthly trend, KPI cards, revenue by city |
| Product Performance | Top 10 products, category split, units sold |
| Category Trends | Monthly category breakdown, discount analysis |
| Regional Insights | City revenue, online vs offline, payment methods |

---

## Additional Enhancements

Beyond the core requirements, the following were added:
- **RFM Customer Segmentation** — classifies customers into 4 business segments
- **Month-over-Month Revenue Growth** — tracks revenue momentum over time
- **Discount Impact Analysis** — evaluates whether discounting drives revenue
- **Weekend vs Weekday Analysis** — identifies peak sales periods
- **Comprehensive logging** — every pipeline step is logged for traceability

---

## Documentation

Full technical documentation is available in `docs/documentation.docx` and covers:
- Architecture diagram
- Data flow diagram
- Data model
- Assumptions made
- Data cleaning strategy
- Transformation logic
- Visual insights

---

## Cloud Architecture

Azure Blob Storage is configured as the cloud storage layer.
Container: retail-pipeline
├── raw/retail_data.xlsx
└── processed/cleaned_retail_data.csv

The Azure connection string is stored in a local `.env` file and 
never committed to the repository.