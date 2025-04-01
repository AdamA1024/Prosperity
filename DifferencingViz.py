import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file using the semicolon as the delimiter
df = pd.read_csv("TutorialData.csv", delimiter=";")

# Filter for KELP
kelp_df = df[df['product'] == 'KELP'].copy()

# Compute the differenced series of mid_price
kelp_df["mid_price_diff"] = kelp_df["mid_price"].diff()

# Drop the first NaN caused by the diff()
kelp_df.dropna(subset=["mid_price_diff"], inplace=True)

# Create a figure with 2 subplots
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 6), sharex=True)

# --- Top Subplot: Differenced Mid Price ---
axes[0].plot(kelp_df["mid_price_diff"].reset_index(drop=True))
axes[0].set_title("KELP - Differenced Mid Price")
axes[0].set_ylabel("Difference")

# --- Bottom Subplot: Actual Mid Price Over Time ---
axes[1].plot(kelp_df["mid_price"].reset_index(drop=True))
axes[1].set_title("KELP - Actual Mid Price")
axes[1].set_xlabel("Time")
axes[1].set_ylabel("Mid Price")

plt.tight_layout()
plt.show()
