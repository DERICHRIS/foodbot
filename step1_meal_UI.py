import streamlit as st
import pandas as pd
import os
from datetime import datetime

# -------- STEP 1: MEAL LOGGING UI -------- #

LOG_FILE = "daily_meal_logs.csv"

# Load or create log file
if os.path.exists(LOG_FILE):
    meal_df = pd.read_csv(LOG_FILE)
else:
    meal_df = pd.DataFrame(columns=["Timestamp", "Meal", "Entry"])

st.title("🥗 Daily Indian Meal Logger")
st.write("Log meals in free text (e.g., '2 idlis and sambar')")

# --- Input UI ---
meal_time = st.selectbox("Select Meal Time", ["Breakfast", "Lunch", "Dinner", "Snack", "Other"])
entry = st.text_input("What did you eat?")

if st.button("Add Meal"):
    if entry:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = {"Timestamp": now, "Meal": meal_time, "Entry": entry}
        meal_df = pd.concat([meal_df, pd.DataFrame([new_row])], ignore_index=True)
        meal_df.to_csv(LOG_FILE, index=False)
        st.success("Meal added!")
        st.rerun()
    else:
        st.warning("Please enter a meal description.")

# --- Display today's meals ---
st.subheader("📋 Today's Logged Meals")
today = datetime.now().strftime("%Y-%m-%d")
today_logs = meal_df[meal_df["Timestamp"].str.contains(today)]

if not today_logs.empty:
    st.dataframe(today_logs)
else:
    st.info("No meals logged today.")

if st.button("Clear Today’s Logs"):
    meal_df = meal_df[~meal_df["Timestamp"].str.contains(today)]
    meal_df.to_csv(LOG_FILE, index=False)
    st.success("Today's logs cleared.")
    st.rerun()

# -------- STEP 2: LOAD NUTRITION DATA -------- #

@st.cache_data
def load_nutrition_data():
    df = pd.read_csv("Indian_Food_Nutrition_with_Serving_Size.csv")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["dish_name"] = df["dish_name"].str.lower()
    return df

nutrition_df = load_nutrition_data()

# Sidebar Preview
st.sidebar.title("📊 Nutrition DB Preview")
if st.sidebar.checkbox("Show Indian Nutrition Table"):
    st.sidebar.dataframe(nutrition_df.head(20))
