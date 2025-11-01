with open('tickers.txt', 'r') as file:
    # Read all lines into a list
    lines = file.readlines()

# Optionally strip newline characters
lines = [line.strip() for line in lines]

# Print the list
print(lines)