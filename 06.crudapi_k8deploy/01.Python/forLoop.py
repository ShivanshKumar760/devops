for fruit in ["apple", "banana", "cherry"]:
    print(fruit)

for i in range(5):           # 0, 1, 2, 3, 4
    print(i)

for i in range(2, 10, 2):    # start, stop, step -> 2, 4, 6, 8
    print(i)

for index, fruit in enumerate(["apple", "banana"]):
    print(index, fruit)      # 0 apple / 1 banana

for name, score in zip(["a", "b"], [90, 80]):
    print(name, score)       # pairs elements from two lists together


#break exits the loop entirely; continue skips to the next iteration:

for n in range(10):
    if n == 5:
        break        # stop the loop completely
    if n % 2 == 0:
        continue     # skip even numbers, keep going
    print(n)         # prints 1, 3

