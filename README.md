# 🛒 Mancino Market  
## Synthetic Grocery Retail Dataset  
<br>

This repository contains a comprehensive synthetic dataset that simulates the operations of a fictitious grocery retail chain in Manhattan, New York City.  

The **Mancino Market** dataset has been carefully designed to reflect the complexity of real-world retail environments while ensuring that all data is fully anonymized and safe for public use.  

The dataset includes store information, product catalogs, customer profiles, inventory coverage, and detailed transaction histories across both in-store and online channels.  

It captures essential dynamics of modern grocery retailing such as store-level assortment differences, customer home store allocations, multi-channel sales, realistic basket sizes, and reconciled financials with tax calculations.  

This project is an open-source sandbox for data professionals, educators, and students who want to explore retail analytics, practice database design, or build predictive and prescriptive models in a risk-free environment.  

---

## 🚀 Key Use Cases  
<br>

You can leverage this dataset for a wide range of analytical and educational projects:  

- **Business Analytics & Visualization**: Build dashboards and reports to analyze store performance, category sales, and customer behavior.  
- **Data Mining & Machine Learning**: Train models for tasks like basket analysis, churn prediction, or demand forecasting.  
- **Database Design & SQL Practice**: Model relational schemas and practice complex joins, constraints, and queries across interrelated entities.  
- **Retail Simulation & Forecasting**: Simulate promotions, test pricing rules, or develop dynamic assortment strategies.  
- **Teaching & Workshops**: Provide students with a realistic dataset for hands-on projects and case studies.  

---

## 🌆 About Mancino Market  
<br>

**MANCINO** is a made-up acronym for **M**idtown **A**rea to **N**oHo, **C**helsea, **I**nter-village, and **N**olita.  

The grocery chain operates **5 urban-format stores** across Manhattan, each with its own unique catchment area and customer base.  

The store locations include:  

1. Midtown  
2. NoHo  
3. Chelsea  
4. Greenwich Village  
5. Nolita  

---

## 📊 Dataset Overview  
<br>

This release (**v1_2025-08-24**) contains the following CSV files:  

| File | Records | Description |
|------|---------|-------------|
| `stores.csv` | **5** | Store master data (IDs, names, addresses, borough, geo coordinates, sqft). |
| `products.csv` | **2,000** | Product catalog across 15 grocery categories, with brand, size, tax codes, and price. |
| `product_store_inventory.csv` | **≈8,000** | Store-level inventory coverage (on-hand units, reorder points, price overrides). |
| `customers.csv` | **5,000** | Synthetic customers with realistic NYC addresses, ZIPs, and lat/long sampled inside neighborhood boundaries. |
| `transactions.csv` | **~33,000** | Transaction headers for **2025-07-01 → 2025-08-24**, across in-store and online channels. |
| `transaction_items.csv` | **~200,000+** | Line-level detail; basket sizes 3–12 items; reconciled totals per transaction. |
| `meta.json` | — | Metadata about dataset size, time window, and generation parameters. |

🔹 **Totals always reconcile**: transaction headers = sum of line items + tax.  
🔹 **Geo consistency**: store coordinates match listed addresses; customers sampled inside catchment neighborhoods.  
🔹 **Currency**: all prices in cents (integers).  

---

## 📂 Repository Structure  
<br>

The dataset is organized to be intuitive and easy to navigate. Here’s a quick overview of the key directories and files you’ll find:  

- `data/`: Contains all the synthetic data files in CSV format, organized by entity (e.g., `stores.csv`, `products.csv`, `customers.csv`, `transactions.csv`).  
- `notebooks/`: Includes example Jupyter notebooks with SQL queries and Python scripts to help you get started with basic analysis and visualization.  

---

## ⚙️ Getting Started  
<br>

1. **Clone the repository**:  
   ```bash
   git clone https://github.com/jrmst102/mancino.git
