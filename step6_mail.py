# ---------------------- FILE: app.py ----------------------
# Streamlit app: Logs meals, calculates nutrients, generates summary

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# ---------------- STEP 1: MEAL LOGGING ---------------- #
LOG_FILE = "daily_meal_logs.csv"

if os.path.exists(LOG_FILE):
    meal_df = pd.read_csv(LOG_FILE)
else:
    meal_df = pd.DataFrame(columns=["Timestamp", "Meal", "Entry"])

st.title("\U0001F957 Daily Indian Meal Logger")
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

today = datetime.now().strftime("%Y-%m-%d")
today_logs = meal_df[meal_df["Timestamp"].str.contains(today)]

st.subheader("\U0001F4CB Today's Logged Meals")
if not today_logs.empty:
    st.dataframe(today_logs)
else:
    st.info("No meals logged today.")

if st.button("Clear Today’s Logs"):
    meal_df = meal_df[~meal_df["Timestamp"].str.contains(today)]
    meal_df.to_csv(LOG_FILE, index=False)
    st.success("Today's logs cleared.")
    st.rerun()

# ---------------- STEP 2: LOAD NUTRITION DB ---------------- #
@st.cache_data
def load_nutrition_data():
    df = pd.read_csv("Indian_Food_Nutrition_with_Serving_Size.csv")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["dish_name"] = df["dish_name"].str.lower()
    return df

nutrition_df = load_nutrition_data()

# ---------------- STEP 3: EMBEDDING + FAISS ---------------- #
@st.cache_resource
def load_embedder_and_faiss(nutrition_df):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    food_names = nutrition_df["dish_name"].tolist()
    embeddings = model.encode(food_names, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return model, index, food_names

embedder, faiss_index, food_list = load_embedder_and_faiss(nutrition_df)

def find_closest_food(query):
    query_vec = embedder.encode([query])[0].reshape(1, -1)
    D, I = faiss_index.search(query_vec, k=1)
    return food_list[I[0][0]]

# ---------------- STEP 4: NUTRIENT CALCULATION ---------------- #
nutrients = [
    "calories_(kcal)", "protein_(g)", "carbohydrates_(g)", "fats_(g)",
    "free_sugar_(g)", "fibre_(g)", "vitamin_c_(mg)", "iron_(mg)", "calcium_(mg)"
]

def get_nutrients(dish_name):
    row = nutrition_df[nutrition_df["dish_name"] == dish_name]
    if not row.empty:
        values = row[nutrients].values[0]
        serving = row["estimated_serving_size_(g/ml)"].values[0]
        return (serving / 100) * values
    return np.zeros(len(nutrients))

total_nutrients = np.zeros(len(nutrients))
matched_dishes = []
for entry in today_logs["Entry"]:
    for dish in entry.lower().split(" and "):
        matched = find_closest_food(dish.strip())
        matched_dishes.append(matched)
        total_nutrients += get_nutrients(matched)

if total_nutrients.sum() > 0:
    results = pd.DataFrame({
        "Nutrient": [n.replace("_", " ").title() for n in nutrients],
        "Total Intake": total_nutrients.round(2)
    })
    st.subheader("\U0001F9EE Daily Nutrient Summary")
    st.dataframe(results)
else:
    results = None
    st.warning("No nutrients calculated yet. Add some food logs above.")

# ---------------- STEP 5: SUMMARY TEMPLATE ---------------- #
def generate_summary_from_totals(table_df):
    get = lambda name: table_df.loc[table_df["Nutrient"] == name, "Total Intake"].values[0]
    summary = f"""
\U0001F35D **Today's Nutrition Summary:**<br>
- \U0001F525 **Calories**: {get('Calories (Kcal)')} kcal<br>
- \U0001F4AA **Protein**: {get('Protein (G)')} g<br>
- \U0001F33E **Carbs**: {get('Carbohydrates (G)')} g<br>
- \U0001F951 **Fats**: {get('Fats (G)')} g<br>
- \U0001F36C **Sugar**: {get('Free Sugar (G)')} g<br>
- \U0001F331 **Fiber**: {get('Fibre (G)')} g<br>
- \U0001F34A **Vitamin C**: {get('Vitamin C (Mg)')} mg<br>
- \U0001F9EA **Iron**: {get('Iron (Mg)')} mg<br>
- \U0001F9C0 **Calcium**: {get('Calcium (Mg)')} mg<br>
<br>
🧃 Don't forget to hydrate! Aim for 2L+ water daily.
"""
    return summary

if results is not None:
    st.subheader("\U0001F4DD AI Summary of Your Day")
    summary_text = generate_summary_from_totals(results)
    st.markdown(summary_text, unsafe_allow_html=True)

# ---------------- STEP 6: EMAIL (external script) ---------------- #
# This step should be implemented in a separate file (e.g., daily_scheduler.py)
# that imports get_today_summary() and generate_summary_from_totals()
# and uses smtplib to send email at 11 PM.
# Use APScheduler for scheduling.
# Refer to previous instructions in chat for full setup.
