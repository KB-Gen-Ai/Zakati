import streamlit as st
import requests
import pandas as pd
from fpdf import FPDF
import os

# Load API keys from environment variables
METAL_API_KEY = st.secrets["METAL_API_KEY"]
EXCHANGE_API_KEY = st.secrets["EXCHANGE_API_KEY"]

# Function to fetch live gold/silver prices
def get_metal_price(metal_type="XAU", currency="SAR"):
    url = f"https://metals-api.com/api/latest?access_key={METAL_API_KEY}&base={currency}&symbols={metal_type}"
    response = requests.get(url).json()
    return response["rates"].get(metal_type, 0) if "rates" in response else 0

# Function to fetch exchange rates
def get_exchange_rate(base_currency, target_currency):
    url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
    response = requests.get(url).json()
    return response["rates"].get(target_currency, 1) if "rates" in response else 1

# Function to calculate zakat
def calculate_zakat(assets, liabilities, gold_weight, silver_weight, base_currency, output_currency):
    gold_price = get_metal_price("XAU", base_currency)
    silver_price = get_metal_price("XAG", base_currency)
    exchange_rate = get_exchange_rate(base_currency, output_currency)
    
    gold_value = gold_weight * gold_price
    silver_value = silver_weight * silver_price
    total_assets = sum(assets) + gold_value + silver_value
    total_liabilities = sum(liabilities)
    net_assets = total_assets - total_liabilities
    nisab = max(85 * gold_price, 595 * silver_price)  # Gold or Silver Nisab Equivalent
    zakat_due = 0.025 * net_assets if net_assets >= nisab else 0
    
    return round(zakat_due * exchange_rate, 2), round(total_assets * exchange_rate, 2), round(total_liabilities * exchange_rate, 2), round(nisab * exchange_rate, 2)

# PDF Report Generator
def generate_pdf(zakat_due, total_assets, total_liabilities, nisab, output_currency):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Zakat Calculation Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total Assets: {total_assets:.2f} {output_currency}", ln=True)
    pdf.cell(200, 10, txt=f"Total Liabilities: {total_liabilities:.2f} {output_currency}", ln=True)
    pdf.cell(200, 10, txt=f"Nisab Threshold: {nisab:.2f} {output_currency}", ln=True)
    pdf.cell(200, 10, txt=f"Zakat Due: {zakat_due:.2f} {output_currency}", ln=True)
    pdf.output("zakat_report.pdf")
    return "zakat_report.pdf"

# Streamlit UI
st.title("Zakati - Comprehensive Zakat Calculator")
st.sidebar.header("Enter Your Details")

# Currency selection
base_currency = st.sidebar.selectbox("Your Base Currency", ["SAR", "USD", "EUR", "PKR", "INR", "GBP"])
output_currency = st.sidebar.selectbox("Output Currency", ["SAR", "USD", "EUR", "PKR", "INR", "GBP"])

# Inputs
cash = st.sidebar.number_input("Cash in Hand (in Base Currency)", min_value=0.0, value=0.0)
bank_savings = st.sidebar.number_input("Bank Savings (in Base Currency)", min_value=0.0, value=0.0)
investments = st.sidebar.number_input("Investments (Stocks, Bonds, etc.)", min_value=0.0, value=0.0)
livestock = st.sidebar.number_input("Livestock Value", min_value=0.0, value=0.0)
crops = st.sidebar.number_input("Agricultural Produce Value", min_value=0.0, value=0.0)
business_inventory = st.sidebar.number_input("Business Inventory Value", min_value=0.0, value=0.0)

gold_weight = st.sidebar.number_input("Gold (grams)", min_value=0.0, value=0.0)
silver_weight = st.sidebar.number_input("Silver (grams)", min_value=0.0, value=0.0)

debts = st.sidebar.number_input("Outstanding Debts (Loans, Payables)", min_value=0.0, value=0.0)

# Calculate Zakat
if st.sidebar.button("Calculate Zakat"):
    zakat_due, total_assets, total_liabilities, nisab = calculate_zakat(
        [cash, bank_savings, investments, livestock, crops, business_inventory],
        [debts], gold_weight, silver_weight, base_currency, output_currency
    )
    
    # Display Results
    st.subheader("Zakat Calculation Result")
    st.write(f"Total Assets: {total_assets:.2f} {output_currency}")
    st.write(f"Total Liabilities: {total_liabilities:.2f} {output_currency}")
    st.write(f"Nisab Threshold: {nisab:.2f} {output_currency}")
    st.write(f"Zakat Due: {zakat_due:.2f} {output_currency}")
    
    # Generate and Download Report
    report_path = generate_pdf(zakat_due, total_assets, total_liabilities, nisab, output_currency)
    with open(report_path, "rb") as f:
        st.download_button("Download Zakat Report", f, file_name="Zakat_Report.pdf", mime="application/pdf")
