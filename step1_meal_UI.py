import streamlit as st
import pandas as pd
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# ---------- STEP 1: MEAL LOGGING UI ---------- #

LOG_FILE = "daily_meal_logs.csv"

# Load or create log file
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

# ---------- STEP 2: LOAD NUTRITION DATA ---------- #

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

# ---------- STEP 3: EMBEDDING + FAISS SEARCH ---------- #

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

# ----------- TEST UI FOR MATCHING (Optional) ----------- #
st.subheader("🔍 Test Food Matching")
test_query = st.text_input("Enter a food to match with nutrition data (test only):")
if test_query:
    match = find_closest_food(test_query.lower())
    st.success(f"Closest match in DB: **{match}**")
