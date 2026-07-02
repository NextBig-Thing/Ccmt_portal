# CCMT Admission Predictor 🎓

A professional Streamlit web application that predicts M.Tech admission chances based on CCMT 2024 & 2025 cutoff data.

## Features
- **Accurate Predictions**: Uses a weighted probability algorithm (2025 data weighted at 60%, 2024 at 40%).
- **Smart Filtering**: Automatically filters relevant M.Tech programs based on your chosen GATE Paper.
- **Categorized Chances**: Classifies colleges into 🟢 Extremely Safe, 🟢 Very Safe, 🟡 Safe, 🟠 Moderate, and 🔴 Dream.
- **PDF Report Generation**: Download a beautifully formatted, professional PDF summary of your top recommendations.
- **Excel Export**: Export the full prediction data table to Excel for offline analysis.

## Setup & Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit application:
```bash
streamlit run app.py
```

## Data Requirements
Make sure the `data/` directory contains:
- `CCMT_2024_All_Data.xlsx`
- `CCMT_2025_All_Data.xlsx`

## Tech Stack
- **Frontend/Backend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **PDF Generation**: ReportLab
