import streamlit as st
import pandas as pd
import os

# --- 1. CONFIG & PRICING ---
st.set_page_config(page_title="AI Kitchen Commander", layout="wide")

PRICES = {
    "Potatoes (g)": 0.0009, "Oil (ml)": 0.0025, "Salt (g)": 0.0005,
    "Buns": 0.25, "Patties": 1.10, "Cheese Slices": 0.15,
    "Dough (g)": 0.002, "Cheese (g)": 0.010, "Sauce (ml)": 0.005,
    "Pasta (g)": 0.004, "Parmesan (g)": 0.018, "Bread Slices": 0.08, "Butter (g)": 0.009
}

RECIPES = {
    "Burger": {"Buns": 1, "Patties": 1, "Cheese Slices": 1},
    "Pizza": {"Dough (g)": 200, "Cheese (g)": 100, "Sauce (ml)": 50},
    "Pasta": {"Pasta (g)": 150, "Sauce (ml)": 100, "Parmesan (g)": 20},
    "Fries": {"Potatoes (g)": 250, "Oil (ml)": 50, "Salt (g)": 5},
    "Sandwich": {"Bread Slices": 2, "Butter (g)": 10}
}

CSV_FILE = "restaurant_sales.csv"

# --- 2. DATA ENGINE ---
def load_fresh_data():
    if os.path.exists(CSV_FILE):
        data = pd.read_csv(CSV_FILE)
        # Force quantities to be numbers to prevent crashes
        data['quantity'] = pd.to_numeric(data['quantity'], errors='coerce').fillna(0)
        return data
    return pd.DataFrame(columns=['item', 'quantity', 'price', 'day', 'weather'])

# Resetting the data properly
if "df" not in st.session_state:
    st.session_state.df = load_fresh_data()

# --- 3. SIDEBAR: INVENTORY & CLEAR BUTTON ---
st.sidebar.header("📦 AI Inventory Manager")

# NEW: Clear Inventory Button
if st.sidebar.button("🗑️ Reset All Sales & Inventory"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE) # Deletes the old messy data
    st.session_state.df = pd.DataFrame(columns=['item', 'quantity', 'price', 'day', 'weather'])
    st.sidebar.warning("Inventory Wiped Clean!")
    st.rerun()

view_mode = st.sidebar.radio("Predict needs for:", ["Next 24 Hours (Daily)", "Next 7 Days (Weekly)"])

# Logic for Shopping List
current_df = st.session_state.df
num_days = len(current_df['day'].unique()) if not current_df.empty else 1
multiplier = 7 if "Weekly" in view_mode else 1

if not current_df.empty:
    total_used = {}
    for _, row in current_df.iterrows():
        item_name = str(row['item'])
        qty_val = float(row['quantity'])
        ingredients = RECIPES.get(item_name, {})
        for ing, amt in ingredients.items():
            total_used[ing] = total_used.get(ing, 0) + (amt * qty_val)
    
    shopping_rows = []
    total_cost = 0
    for ing, total_amt in total_used.items():
        predicted = (total_amt / num_days) * multiplier
        cost = predicted * PRICES.get(ing, 0)
        total_cost += cost
        unit = "kg/L" if "(g)" in ing or "(ml)" in ing else "pcs"
        disp_amt = f"{predicted/1000:.2f}" if unit == "kg/L" else f"{int(predicted)}"
        shopping_rows.append({"Item": ing, "Qty": disp_amt, "Unit": unit, "Cost": f"£{cost:.2f}"})
    
    st.sidebar.table(pd.DataFrame(shopping_rows))
    st.sidebar.metric("Total Estimated Cost", f"£{total_cost:.2f}")

# --- 4. MAIN PAGE: BILLING ---
st.title("🍴 Restaurant Billing & AI Forecasting")

col_bill, col_stats = st.columns([1, 1.2])

with col_bill:
    st.subheader("New Customer Sale")
    with st.form("billing_form", clear_on_submit=True):
        item_sel = st.selectbox("Menu Item", list(RECIPES.keys()))
        qty_sel = st.number_input("Quantity Sold", min_value=1, value=1)
        day_sel = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        weather_sel = st.selectbox("Weather", ["Sunny", "Rainy", "Cloudy"])
        
        if st.form_submit_button("Complete Sale"):
            # Prepare row to match CSV structure
            new_row_data = [item_sel, qty_sel, 10, day_sel, weather_sel]
            while len(new_row_data) < len(st.session_state.df.columns):
                new_row_data.append(0)
            
            # Save to CSV
            new_row_df = pd.DataFrame([new_row_data], columns=st.session_state.df.columns)
            new_row_df.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
            
            # Update current session state so it shows up IMMEDIATELY
            st.session_state.df = load_fresh_data()
            st.success("✅ Order Logged! Inventory Updated.")
            st.rerun()

with col_stats:
    st.subheader("Live Sales Chart")
    if not st.session_state.df.empty:
        chart_data = st.session_state.df.groupby("item")["quantity"].sum()
        st.bar_chart(chart_data)
    else:
        st.info("No sales recorded in this session.")
        