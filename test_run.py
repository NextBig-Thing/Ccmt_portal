import predictor
import pandas as pd

print("Loading Data...")
df = predictor.load_data()
print(f"Data loaded successfully. Total records: {len(df)}")

print("\n--- Testing Prediction Algorithm ---")
print("GATE Score: 625")
print("Paper: CS - Computer Science & Information Technology")
print("Category: OPEN")
print("Round: Round 3")

# Get programs for CS
programs = predictor.get_programs_for_paper("CS - Computer Science & Information Technology", df)

# Predict
results = predictor.predict(
    gate_score=625,
    gate_paper="CS - Computer Science & Information Technology",
    category="OPEN",
    round_name="Round 3",
    selected_programs=programs,
    df=df,
    top_n=5
)

if not results.empty:
    print("\nTop 5 Recommendations:")
    print(results[["Institute", "Program", "Close_2025", "Close_2024", "Probability", "Chance"]].to_string())
else:
    print("\nNo results found.")
