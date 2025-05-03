foodbot
vxaq iyop myyu ynbf



✅ Step-by-Step Build Plan
🔹Step 1: Build Streamlit UI to log meals
Simple input box: "What did you eat today?"

Show entries in a table below

Save logs for the day (locally)

🔹Step 2: Preprocess the Nutrition CSV
Clean names

Normalize units to 100g

Load into a local dataframe

🔹Step 3: Embed all food items for semantic search
Use SentenceTransformers (e.g., all-MiniLM-L6-v2)

Store in FAISS index

This helps match user logs like “chana masala” → “Chickpea curry”

🔹Step 4: Process meal logs
Parse food + quantity

Search the closest match in nutrition DB

Multiply nutrient values by estimated grams

🔹Step 5: Aggregate day’s nutrients
Sum calories, macros, vitamins

Display pie charts or tables

🔹Step 6: LLM-based summary
Use GPT-2 or DistilGPT2 locally

Generate a friendly text report

🔹Step 7: Email system
At 11 PM, send the daily report via smtplib or SendGrid