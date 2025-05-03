import streamlit as st
import pandas as pd
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# ---------------- STEP 1: MEAL LOGGING UI ---------------- #

LOG_FILE = "daily_meal_logs.csv"

if os.path.exists(LOG_FILE):
    meal_df = pd.read_csv(LOG_FILE)
else:
    meal_df = pd.DataFrame(columns=["Timestamp", "Meal", "Entry"])

st.title("🥗 Daily Indian Meal Logger")
st.write("Log your meals (e.g., '2 idlis and sambar')")

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

# ---------------- STEP 2: LOAD NUTRITION DATA ---------------- #

@st.cache_data
def load_nutrition_data():
    df = pd.read_csv("Indian_Food_Nutrition_with_Serving_Size.csv")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["dish_name"] = df["dish_name"].str.lower()
    return df

nutrition_df = load_nutrition_data()

st.sidebar.title("📊 Nutrition DB Preview")
if st.sidebar.checkbox("Show Indian Nutrition Table"):
    st.sidebar.dataframe(nutrition_df.head(20))

# ---------------- STEP 3: EMBEDDING + FAISS SEARCH ---------------- #

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
    closest = food_list[I[0][0]]
    return closest

# Optional test tool
st.subheader("🔍 Test Food Matching")
test_query = st.text_input("Try matching a food name (optional test):")
if test_query:
    match = find_closest_food(test_query.lower())
    st.success(f"Closest match in DB: **{match}**")

# ---------------- STEP 4: NUTRIENT CALCULATION ---------------- #

st.subheader("🧮 Daily Nutrient Summary")

nutrients = [
    "calories_(kcal)", "protein_(g)", "carbohydrates_(g)", "fats_(g)",
    "free_sugar_(g)", "fibre_(g)", "vitamin_c_(mg)", "iron_(mg)", "calcium_(mg)"
]

def get_nutrients(dish_name):
    row = nutrition_df[nutrition_df["dish_name"] == dish_name]
    if not row.empty:
        values = row[nutrients].values[0]
        serving = row["estimated_serving_size_(g/ml)"].values[0]
        scaled = (serving / 100) * values
        return scaled
    else:
        return np.zeros(len(nutrients))

total_nutrients = np.zeros(len(nutrients))
matched_dishes = []

for entry in today_logs["Entry"]:
    possible_dishes = entry.lower().split(" and ")
    for dish in possible_dishes:
        matched = find_closest_food(dish.strip())
        matched_dishes.append(matched)
        total_nutrients += get_nutrients(matched)

if total_nutrients.sum() > 0:
    results = pd.DataFrame({
        "Nutrient": [n.replace("_", " ").title() for n in nutrients],
        "Total Intake": total_nutrients.round(2)
    })
    st.dataframe(results)

    st.info("Matched dishes from today's log:")
    for d in matched_dishes:
        st.markdown(f"✔️ {d}")
else:
    st.warning("No nutrients calculated yet. Add some food logs above.")
