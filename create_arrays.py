import csv

# Read the CSV file
data = []
with open('final_df.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append({
            'Ticker': row['Ticker'],
            'Composite Score': float(row['Composite Score'])
        })

# Sort by Composite Score in descending order
data_sorted = sorted(data, key=lambda x: x['Composite Score'], reverse=True)

# Create top100 array with top 100 tickers
top100 = [item['Ticker'] for item in data_sorted[:100]]

# Create bottom100 array with bottom 100 tickers
bottom100 = [item['Ticker'] for item in data_sorted[-100:]]

# Print the arrays
print("top100 =", top100)
print("\nbottom100 =", bottom100)

# Print summary
print(f"\nTop 100 companies by composite score (highest: {data_sorted[0]['Composite Score']:.2f})")
print(f"Bottom 100 companies by composite score (lowest: {data_sorted[-1]['Composite Score']:.2f})")
