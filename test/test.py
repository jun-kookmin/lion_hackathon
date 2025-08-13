n = int(input().strip())
dist = list(map(int, input().split()))   
prices = list(map(int, input().split()))   

min_price = prices[0]
total = 0

for i in range(n-1):
    total += min_price * dist[i]
    if prices[i + 1] < min_price:
        min_price = prices[i + 1]

print(total)