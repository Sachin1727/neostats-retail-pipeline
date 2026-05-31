#!/usr/bin/env python
# coding: utf-8

# ---
# ## Section 1 — Imports and Setup

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import hashlib
import warnings
import logging
import os
from datetime import datetime

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Plotting style
plt.rcParams['figure.figsize'] = (12, 6)
sns.set_style('whitegrid')

logger.info('Libraries loaded successfully.')
print('All libraries imported successfully.')


# ---
# ## Section 2 — Data Ingestion

# In[2]:


FILE_PATH = '../data/raw/USECASE_-_Data_Engineering.xlsx'

try:
    product_details = pd.read_excel(FILE_PATH, sheet_name='product_details')
    retail_data1    = pd.read_excel(FILE_PATH, sheet_name='retail_data1')
    retail_data2    = pd.read_excel(FILE_PATH, sheet_name='retail_data2')
    logger.info('All three datasets ingested successfully.')
    print('Data ingested successfully.')
except Exception as e:
    logger.error(f'Ingestion failed: {e}')
    raise

print(f'\nproduct_details : {product_details.shape}')
print(f'retail_data1    : {retail_data1.shape}')
print(f'retail_data2    : {retail_data2.shape}')


# In[3]:


# Preview product_details
print('=== Product Details (Dimension Table) ===')
display(product_details)


# In[4]:


# Preview retail_data1
print('=== retail_data1 — First 5 Rows ===')
display(retail_data1.head())


# In[5]:


# Preview retail_data2
print('=== retail_data2 — First 5 Rows ===')
display(retail_data2.head())


# ---
# ## Section 3 — Exploratory Data Analysis (EDA)
# Understanding the structure, quality, and distribution of the raw data before any transformations.

# In[6]:


# EDA — Data Quality Report
def eda_report(df, name):
    print(f"\n{'='*55}")
    print(f"  EDA Report: {name}")
    print(f"{'='*55}")
    print(f"Shape           : {df.shape}")
    print(f"Duplicate Rows  : {df.duplicated().sum()}")
    print(f"\nMissing Values:")
    print(df.isnull().sum())
    print(f"\nData Types:")
    print(df.dtypes)

eda_report(retail_data1, 'retail_data1')
eda_report(retail_data2, 'retail_data2')


# In[7]:


# ---- Inconsistent category values ----
print('Unique categories in retail_data1:')
print(retail_data1['category'].unique())

print('\nUnique categories in retail_data2:')
print(retail_data2['category'].unique())


# In[8]:


# ---- Invalid quantity records ----
print('retail_data1:')
print(f'  Negative quantity rows : {(retail_data1["quantity"] < 0).sum()}')
print(f'  Zero quantity rows     : {(retail_data1["quantity"] == 0).sum()}')

print('\nretail_data2:')
print(f'  Negative quantity rows : {(retail_data2["quantity"] < 0).sum()}')
print(f'  Zero quantity rows     : {(retail_data2["quantity"] == 0).sum()}')


# In[9]:


# ---- Mixed date format samples ----
print('Sample transaction_date values (retail_data1):')
print(retail_data1['transaction_date'].head(20).tolist())


# In[10]:


# ---- Payment status distribution ----
print('Payment Status — retail_data1:')
print(retail_data1['payment_status'].value_counts())

print('\nPayment Status — retail_data2:')
print(retail_data2['payment_status'].value_counts())


# ### EDA Summary — Data Quality Issues Found
# 
# | Issue | retail_data1 | retail_data2 |
# |---|---|---|
# | Missing prices | 404 rows | 405 rows |
# | Negative quantity | 34 rows | 31 rows |
# | Zero quantity | 16 rows | 12 rows |
# | Inconsistent category names | 12 variations | same |
# | Mixed date formats | Excel serial + MM-DD-YYYY | same |
# | Duplicate transaction IDs (failed payments) | Present | Present |
# | PII columns (email, phone) | Present | Present |

# ---
# ## Section 4 — Data Merging
# Combining both retail transaction datasets from the two source systems into a single unified dataset.

# In[11]:


# COMBINE BOTH SOURCE DATASETS

# Tag each record with its source before merging
retail_data1['source'] = 'retail_data1'
retail_data2['source'] = 'retail_data2'

raw_combined = pd.concat([retail_data1, retail_data2], ignore_index=True)

logger.info(f'Combined dataset shape: {raw_combined.shape}')
print(f'Combined dataset: {raw_combined.shape[0]} rows, {raw_combined.shape[1]} columns')


# ---
# ## Section 5 — Data Cleaning & Transformation
# Applying all preprocessing steps to produce a clean, reliable dataset.

# In[12]:


# Work on a copy to preserve the raw data
df = raw_combined.copy()
print(f'Starting shape: {df.shape}')


# In[13]:


# 5.1 — Remove Failed Payment Records
# Assumption: Same transaction_id appearing with 'failed' payment_status represents a failed payment retry.
# Only 'successful' transactions are valid for analytics.

before = len(df)
df = df[df['payment_status'] == 'successful'].copy()
after = len(df)

logger.info(f'Removed {before - after} failed payment records.')
print(f'Failed payments removed: {before - after} rows dropped.')
print(f'Remaining rows: {len(df)}')


# In[14]:


# 5.2 — Remove Full Duplicate Rows

before = len(df)
df.drop_duplicates(inplace=True)
after = len(df)

logger.info(f'Removed {before - after} duplicate rows.')
print(f'Duplicates removed: {before - after} rows dropped.')
print(f'Remaining rows: {len(df)}')


# In[15]:


# 5.3 — Fix Mixed Date Formats
# Two date formats observed:
#   - Excel serial numbers (e.g., 45997)
#   - String dates (e.g., '02-19-2026' in MM-DD-YYYY format)
# Both are converted to standard datetime format.

def parse_mixed_dates(val):
    if isinstance(val, (int, float)):
        try:
            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(val))
        except:
            return pd.NaT
    elif isinstance(val, str):
        try:
            return pd.to_datetime(val, format='%m-%d-%Y')
        except:
            return pd.NaT
    elif isinstance(val, datetime):
        return pd.Timestamp(val)
    else:
        return pd.NaT

df['transaction_date'] = df['transaction_date'].apply(parse_mixed_dates)
df['transaction_date'] = pd.to_datetime(df['transaction_date'])

null_dates = df['transaction_date'].isnull().sum()
logger.info(f'Date parsing complete. Null dates remaining: {null_dates}')
print(f'Date formats standardized. Null dates remaining: {null_dates}')
print(f'Sample dates after fix:')
print(df['transaction_date'].head(5).tolist())


# In[16]:


# 5.4 — Fill Missing Prices from product_details
# Assumption: Where price is missing in transaction data,
# the standard price from the product dimension table is used.

price_map = product_details.set_index('product_id')['price'].to_dict()

df['price'] = df.apply(
    lambda row: price_map.get(row['product_id'], row['price'])
    if pd.isnull(row['price']) else row['price'],
    axis=1
)

remaining_null = df['price'].isnull().sum()
logger.info(f'Missing prices filled. Remaining nulls: {remaining_null}')
print(f'Missing prices filled from product_details. Remaining nulls: {remaining_null}')


# In[17]:


# 5.5 — Remove Invalid Quantity Records
# Assumption: Rows with quantity <= 0 are invalid entries.
# Negative quantities likely represent erroneous return entries.
# Zero quantities represent incomplete/cancelled transactions.

before = len(df)
df = df[df['quantity'] > 0].copy()
after = len(df)

logger.info(f'Removed {before - after} rows with quantity <= 0.')
print(f'Invalid quantity rows removed: {before - after} rows dropped.')
print(f'Remaining rows: {len(df)}')


# In[18]:


# 5.6 — Standardize Category Names
# Multiple inconsistent variations observed:
# 'ELEC', 'electronics', 'Electronics' → 'Electronics'
# 'CLOTH', 'clothing', 'Clothing'      → 'Clothing'
# 'FURN', 'furniture', 'Furniture'     → 'Furniture'
# 'HOME', 'home appliances'            → 'Home Appliances'

category_map = {
    'ELEC'           : 'Electronics',
    'electronics'    : 'Electronics',
    'Electronics'    : 'Electronics',
    'CLOTH'          : 'Clothing',
    'clothing'       : 'Clothing',
    'Clothing'       : 'Clothing',
    'FURN'           : 'Furniture',
    'furniture'      : 'Furniture',
    'Furniture'      : 'Furniture',
    'HOME'           : 'Home Appliances',
    'home appliances': 'Home Appliances',
    'Home Appliances': 'Home Appliances',
    'HOME APPLIANCES': 'Home Appliances'
}

df['category'] = df['category'].map(category_map).fillna(df['category'])

logger.info('Category names standardized.')
print(f'Categories standardized.')
print(f'Unique categories now: {df["category"].unique()}')


# In[19]:


# 5.7 — Standardize Product Names & Purchase Location

df['product_name']      = df['product_name'].str.title().str.strip()
df['purchase_location'] = df['purchase_location'].str.lower().str.strip()
df['customer_name']     = df['customer_name'].str.strip()
df['city']              = df['city'].str.strip()

logger.info('Product names and purchase location standardized.')
print(f'Product names standardized.')
print(f'Unique product names: {df["product_name"].unique()}')


# In[20]:


# 5.8 — PII Masking (Email & Phone)
# Personally Identifiable Information is masked using
# SHA-256 hashing (first 20 characters of the hash).
# Original PII columns are dropped after masking.

def hash_pii(value):
    if pd.isnull(value):
        return None
    return hashlib.sha256(str(value).encode()).hexdigest()[:20]

df['email_masked'] = df['email'].apply(hash_pii)
df['phone_masked'] = df['phone'].astype(str).apply(hash_pii)

# Drop raw PII columns
df.drop(columns=['email', 'phone'], inplace=True)

logger.info('PII masking applied. Original email and phone columns dropped.')
print('PII masking complete. Email and phone columns hashed and originals removed.')


# In[21]:


# 5.9 — Validate Discount Range
# Discount must be between 0 and 1 (0% to 100%)

invalid_discount = df[(df['discount'] < 0) | (df['discount'] > 1)]
logger.info(f'Invalid discount records found: {len(invalid_discount)}')
print(f'Invalid discount records: {len(invalid_discount)}')

df = df[(df['discount'] >= 0) & (df['discount'] <= 1)].copy()
print(f'Discount validation complete.')


# In[22]:


# 5.10 — Final Cleaned Dataset Summary

print('='*55)
print('CLEANED DATASET SUMMARY')
print('='*55)
print(f'Final Shape     : {df.shape}')
print(f'Null Values     :\n{df.isnull().sum()}')
print(f'\nData Types:\n{df.dtypes}')
display(df.head())


# ---
# ## Section 6 — Feature Engineering & KPI Calculation

# In[23]:


# FEATURE ENGINEERING

# Revenue = price * quantity * (1 - discount)
df['revenue'] = (df['price'] * df['quantity'] * (1 - df['discount'])).round(2)

# Date-based features
df['year']        = df['transaction_date'].dt.year
df['month']       = df['transaction_date'].dt.month
df['month_name']  = df['transaction_date'].dt.strftime('%b')
df['quarter']     = df['transaction_date'].dt.quarter
df['day_of_week'] = df['transaction_date'].dt.day_name()
df['is_weekend']  = df['day_of_week'].isin(['Saturday', 'Sunday'])

logger.info('Feature engineering complete.')
print('Features engineered: revenue, year, month, quarter, day_of_week, is_weekend')


# In[24]:


# CORE KPIs

total_revenue      = df['revenue'].sum()
total_transactions = df['transaction_id'].nunique()
total_customers    = df['customer_id'].nunique()
avg_order_value    = df['revenue'].mean()
avg_discount       = df['discount'].mean()
total_units_sold   = df['quantity'].sum()

print('='*55)
print('KEY BUSINESS KPIs')
print('='*55)
print(f'  Total Revenue          : ₹{total_revenue:,.2f}')
print(f'  Total Transactions     : {total_transactions:,}')
print(f'  Total Unique Customers : {total_customers:,}')
print(f'  Average Order Value    : ₹{avg_order_value:,.2f}')
print(f'  Average Discount       : {avg_discount*100:.1f}%')
print(f'  Total Units Sold       : {total_units_sold:,}')
print('='*55)


# In[25]:


# ---- Revenue by Category ----
rev_by_category = (
    df.groupby('category')['revenue']
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
rev_by_category.columns = ['Category', 'Total Revenue']
print('Revenue by Category:')
display(rev_by_category)


# In[26]:


# ---- Revenue by City ----
rev_by_city = (
    df.groupby('city')['revenue']
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
rev_by_city.columns = ['City', 'Total Revenue']
print('Revenue by City:')
display(rev_by_city)


# In[27]:


# ---- Monthly Revenue Trend ----
rev_by_month = (
    df.groupby(['year', 'month', 'month_name'])['revenue']
    .sum()
    .reset_index()
    .sort_values(['year', 'month'])
)
print('Monthly Revenue Trend:')
display(rev_by_month)


# In[28]:


# ---- Top Products ----
top_products = (
    df.groupby('product_name')
    .agg(
        Total_Revenue=('revenue', 'sum'),
        Units_Sold=('quantity', 'sum'),
        Transactions=('transaction_id', 'count')
    )
    .sort_values('Total_Revenue', ascending=False)
    .reset_index()
)
print('Top Products by Revenue:')
display(top_products)


# In[29]:


# ---- Revenue by Payment Method ----
rev_by_payment = (
    df.groupby('payment_method')['revenue']
    .sum()
    .reset_index()
)

# ---- Online vs Offline ----
rev_by_channel = (
    df.groupby('purchase_location')['revenue']
    .sum()
    .reset_index()
)

# ---- Weekend vs Weekday ----
rev_by_weekend = (
    df.groupby('is_weekend')['revenue']
    .sum()
    .reset_index()
)
rev_by_weekend['is_weekend'] = rev_by_weekend['is_weekend'].map({True: 'Weekend', False: 'Weekday'})

print('Payment Method Revenue:')
display(rev_by_payment)

print('\nOnline vs Offline Revenue:')
display(rev_by_channel)

print('\nWeekend vs Weekday Revenue:')
display(rev_by_weekend)


# ---
# ## Section 7 — Additional Enhancements
# ### 7.1 — RFM Customer Segmentation

# In[30]:


# RFM ANALYSIS — Customer Segmentation
# Recency   : Days since last purchase
# Frequency : Number of transactions
# Monetary  : Total revenue generated

snapshot_date = df['transaction_date'].max() + pd.Timedelta(days=1)

rfm = df.groupby('customer_id').agg(
    Recency   = ('transaction_date', lambda x: (snapshot_date - x.max()).days),
    Frequency = ('transaction_id', 'count'),
    Monetary  = ('revenue', 'sum')
).reset_index()

# Score each dimension 1-4
rfm['R_Score'] = pd.qcut(rfm['Recency'],   q=4, labels=[4,3,2,1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=4, labels=[1,2,3,4]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'),  q=4, labels=[1,2,3,4]).astype(int)
rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

def rfm_segment(score):
    if score >= 10:
        return 'Champions'
    elif score >= 7:
        return 'Loyal Customers'
    elif score >= 5:
        return 'Potential Loyalists'
    else:
        return 'At Risk'

rfm['Segment'] = rfm['RFM_Score'].apply(rfm_segment)

print('RFM Segment Distribution:')
print(rfm['Segment'].value_counts())
display(rfm.head(10))


# ### 7.2 — Month-over-Month Revenue Growth

# In[31]:


# MONTH-OVER-MONTH REVENUE GROWTH

mom = rev_by_month.copy()
mom['prev_revenue'] = mom['revenue'].shift(1)
mom['MoM_Growth_%'] = ((mom['revenue'] - mom['prev_revenue']) / mom['prev_revenue'] * 100).round(2)

print('Month-over-Month Revenue Growth:')
display(mom[['year', 'month_name', 'revenue', 'MoM_Growth_%']])


# ### 7.3 — Discount Impact Analysis

# In[32]:


# DISCOUNT IMPACT ANALYSIS
# Does higher discount lead to higher revenue? (checking the impact)

discount_impact = (
    df.groupby('category')
    .agg(
        Avg_Discount=('discount', 'mean'),
        Total_Revenue=('revenue', 'sum'),
        Total_Transactions=('transaction_id', 'count')
    )
    .reset_index()
)
discount_impact['Avg_Discount'] = (discount_impact['Avg_Discount'] * 100).round(1)

print('Discount Impact by Category:')
display(discount_impact)


# ---
# ## Section 8 — Visualizations

# In[33]:


# VISUALIZATION 1 — Sales Overview Dashboard

fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.suptitle('ABC Retail Solutions — Sales Overview', fontsize=18, fontweight='bold', y=1.01)

# 1. Revenue by Category
axes[0,0].bar(rev_by_category['Category'], rev_by_category['Total Revenue'],
              color=['#2196F3','#4CAF50','#FF9800','#9C27B0'])
axes[0,0].set_title('Revenue by Category', fontweight='bold')
axes[0,0].set_ylabel('Revenue (₹)')
axes[0,0].tick_params(axis='x', rotation=15)

# 2. Revenue by City
axes[0,1].bar(rev_by_city['City'], rev_by_city['Total Revenue'],
              color=['#FF5252','#FF4081','#E040FB','#40C4FF','#69F0AE'])
axes[0,1].set_title('Revenue by City', fontweight='bold')
axes[0,1].set_ylabel('Revenue (₹)')

# 3. Payment Method Distribution
axes[0,2].pie(rev_by_payment['revenue'], labels=rev_by_payment['payment_method'],
              autopct='%1.1f%%', startangle=90,
              colors=['#42A5F5','#66BB6A','#FFA726','#AB47BC'])
axes[0,2].set_title('Revenue by Payment Method', fontweight='bold')

# 4. Monthly Revenue Trend
axes[1,0].plot(range(len(rev_by_month)), rev_by_month['revenue'],
               marker='o', color='#26A69A', linewidth=2.5)
axes[1,0].fill_between(range(len(rev_by_month)), rev_by_month['revenue'], alpha=0.15, color='#26A69A')
axes[1,0].set_title('Monthly Revenue Trend', fontweight='bold')
axes[1,0].set_xticks(range(len(rev_by_month)))
axes[1,0].set_xticklabels(rev_by_month['month_name'], rotation=45)
axes[1,0].set_ylabel('Revenue (₹)')

# 5. Online vs Offline
axes[1,1].bar(rev_by_channel['purchase_location'], rev_by_channel['revenue'],
              color=['#5C6BC0','#26C6DA'])
axes[1,1].set_title('Online vs Offline Revenue', fontweight='bold')
axes[1,1].set_ylabel('Revenue (₹)')

# 6. Top 5 Products
top5 = top_products.head(5)
axes[1,2].barh(top5['product_name'], top5['Total_Revenue'], color='#EF5350')
axes[1,2].set_title('Top 5 Products by Revenue', fontweight='bold')
axes[1,2].set_xlabel('Revenue (₹)')
axes[1,2].invert_yaxis()

plt.tight_layout()
os.makedirs('../data/processed', exist_ok=True)
plt.savefig('../data/processed/eda_overview.png', dpi=150, bbox_inches='tight')
plt.show()
print('Overview chart saved.')


# In[34]:


# VISUALIZATION 2 — RFM Segment Distribution

segment_counts = rfm['Segment'].value_counts()

plt.figure(figsize=(8, 5))
bars = plt.bar(segment_counts.index, segment_counts.values,
               color=['#4CAF50','#2196F3','#FF9800','#F44336'])
plt.title('Customer Segmentation (RFM Analysis)', fontweight='bold', fontsize=14)
plt.ylabel('Number of Customers')
plt.xlabel('Segment')
for bar, val in zip(bars, segment_counts.values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
             str(val), ha='center', va='bottom', fontweight='bold')
plt.tight_layout()
plt.savefig('../data/processed/rfm_segments.png', dpi=150, bbox_inches='tight')
plt.show()


# In[35]:


# VISUALIZATION 3 — Weekend vs Weekday

day_revenue = df.groupby('day_of_week')['revenue'].sum().reindex(
    ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
)

colors = ['#EF9A9A' if d in ['Saturday','Sunday'] else '#90CAF9' for d in day_revenue.index]

plt.figure(figsize=(10, 5))
plt.bar(day_revenue.index, day_revenue.values, color=colors)
plt.title('Revenue by Day of Week (Blue=Weekday, Red=Weekend)', fontweight='bold')
plt.ylabel('Total Revenue (₹)')
plt.xlabel('Day of Week')
plt.tight_layout()
plt.savefig('../data/processed/revenue_by_day.png', dpi=150, bbox_inches='tight')
plt.show()


# ---
# ## Section 9 — Save Processed Data

# In[36]:


# SAVING ALL OUTPUT FILES

os.makedirs('../data/processed', exist_ok=True)

# Main cleaned dataset
df.to_csv('../data/processed/cleaned_retail_data.csv', index=False)
logger.info('Cleaned dataset saved.')

# KPI aggregates
rev_by_category.to_csv('../data/processed/kpi_revenue_by_category.csv', index=False)
rev_by_city.to_csv('../data/processed/kpi_revenue_by_city.csv', index=False)
top_products.to_csv('../data/processed/kpi_top_products.csv', index=False)
rfm.to_csv('../data/processed/rfm_segments.csv', index=False)
mom.to_csv('../data/processed/kpi_mom_growth.csv', index=False)

print('All files saved to ../data/processed/')
print(f'Final dataset shape: {df.shape}')


# ---
# ## Section 10 — Azure Blob Storage Upload
# Uploading raw and processed files to Azure Blob Storage for cloud-based scalability.

# In[37]:


import sys
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "azure-storage-blob", "python-dotenv"])

try:
    from azure.storage.blob import BlobServiceClient
    from dotenv import load_dotenv
    import os

    # Load connection string from .env file
    load_dotenv()
    AZURE_CONNECTION_STRING = os.getenv('AZURE_CONNECTION_STRING')
    CONTAINER_NAME = 'retail-pipeline'

    if not AZURE_CONNECTION_STRING:
        raise ValueError("Connection string not found in .env file")

    def upload_to_azure(local_path, blob_name):
        client = BlobServiceClient.from_connection_string(
                    AZURE_CONNECTION_STRING)
        container = client.get_container_client(CONTAINER_NAME)
        try:
            container.create_container()
        except:
            pass  # Container already exists
        with open(local_path, 'rb') as f:
            container.upload_blob(
                name=blob_name,
                data=f,
                overwrite=True
            )

        print(f'Uploaded: {blob_name}')

    # Upload raw file
    upload_to_azure(
        '../data/raw/USECASE_-_Data_Engineering.xlsx',
        'raw/retail_data.xlsx'
    )

    # Upload processed files
    upload_to_azure(
        '../data/processed/cleaned_retail_data.csv',
        'processed/cleaned_retail_data.csv'
    )
    upload_to_azure(
        '../data/processed/rfm_segments.csv',
        'processed/rfm_segments.csv'
    )
    upload_to_azure(
        '../data/processed/kpi_revenue_by_category.csv',
        'processed/kpi_revenue_by_category.csv'
    )
    upload_to_azure(
        '../data/processed/kpi_top_products.csv',
        'processed/kpi_top_products.csv'
    )

    print('')
    print('All files uploaded to Azure Blob Storage!')
    print(f'Container: {CONTAINER_NAME}')
    print(f'Storage Account: neostatsretail')

except Exception as e:
    print(f'Azure upload failed: {e}')


# ---
# ## Section 11 — Pipeline Summary

# In[38]:


print('='*60)
print('PIPELINE EXECUTION COMPLETE')
print('='*60)
print(f'  Raw records ingested    : {raw_combined.shape[0]:,}')
print(f'  Final cleaned records   : {df.shape[0]:,}')
print(f'  Total Revenue           : ₹{df["revenue"].sum():,.2f}')
print(f'  Unique Customers        : {df["customer_id"].nunique():,}')
print(f'  Unique Products         : {df["product_name"].nunique():,}')
print(f'  Cities Covered          : {df["city"].nunique()}')
print(f'  Date Range              : {df["transaction_date"].min().date()} to {df["transaction_date"].max().date()}')
print('='*60)


# In[ ]:




