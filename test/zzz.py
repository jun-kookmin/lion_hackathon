from itertools import product, permutations, combinations, combinations_with_replacement

n, m = map(int, input().split())
    
a = list(combinations_with_replacement([x for x in range(1,n+1)], m))

for e in a:
    print(*e)