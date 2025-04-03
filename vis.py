import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file using the semicolon as the delimiter
df = pd.read_csv("TutorialData.csv", delimiter=";")

# for product in df['product'].unique():
#     # Filter rows where the 'product' column matches the current product
#     product_df = df[df['product'] == product]

#     # Select the 'mid_price' and calculate the spread
#     product_midprice = product_df['mid_price']
#     product_spread = product_df['ask_price_1'] - product_df['bid_price_1']
#     product_df['SMA30']=product_df['mid_price'].rolling(window=30).mean()
#     product_df.dropna(inplace=True)

#     # Plot mid_price
#     plt.figure()
#     plt.plot(product_midprice)
#     plt.plot(product_df['SMA30'])
#     plt.title(f'Mid price of {product}')
#     plt.xlabel('Time')
#     plt.ylabel('Mid price')
#     plt.show()

#     print(f"Spread of {product}:")
#     print(product_spread.describe())
#     print(product_spread)
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file with semicolon as the delimiter
df = pd.read_csv("TutorialData.csv", delimiter=";")

# Filter the DataFrame for the KELP product
product = 'RAINFOREST_RESIN'
product_df = df[df['product'] == product].copy()
print(product_df['bid_price_1'].min())
print(product_df['bid_price_1'].max())
print(product_df['ask_price_1'].min())
print(product_df['ask_price_1'].max())
# Define moving average windows (e.g., 10 for short-term and 30 for long-term)
short_window = 30
long_window = 100

# Compute the short-term and long-term moving averages using the midpoint price
product_df['SMA_short'] = product_df['mid_price'].rolling(window=short_window).mean()
product_df['SMA_long'] = product_df['mid_price'].rolling(window=long_window).mean()
print(product_df['mid_price'].mean())
# Drop rows with NaN values (from rolling calculations)
plot_df = product_df.dropna(subset=['SMA_short', 'SMA_long'])

# Calculate the difference between the short and long moving averages
plot_df['diff'] = plot_df['SMA_short'] - plot_df['SMA_long']

# Identify the indices where the moving averages cross
# A crossover occurs when the sign of the difference changes
crossover_indices = np.where(np.diff(np.sign(plot_df['diff'])) != 0)[0] + 1  # adjust index due to diff

# Retrieve the time indices and corresponding prices for the crossover points
crossover_times = plot_df.index[crossover_indices]
crossover_prices = plot_df['mid_price'].iloc[crossover_indices]

# Plot the midpoint price and both moving averages
plt.figure(figsize=(12, 6))
plt.plot(product_df.index, product_df['mid_price'], label="Mid Price", color='black')
plt.plot(product_df.index, product_df['SMA_short'], label=f"SMA{short_window}", color='blue')
plt.plot(product_df.index, product_df['SMA_long'], label=f"SMA{long_window}", color='red')
plt.scatter(crossover_times, crossover_prices, label="Crossover", color='green', marker='o', s=100)
plt.title(f'Moving Average Crossover for {product}')
plt.xlabel('Time')
plt.ylabel('Price')
plt.legend()
plt.grid(True)
plt.show()
