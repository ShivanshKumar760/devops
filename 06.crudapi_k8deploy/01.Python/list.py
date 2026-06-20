fruits = ["apple", "banana", "cherry"]

fruits[0]          # "apple"  — indexing starts at 0
fruits[-1]         # "cherry" — negative index counts from the end
fruits[1:3]        # ["banana", "cherry"] — slicing [start:stop]

#Common operations:

fruits.append("mango")        # add to the end
fruits.insert(1, "kiwi")      # insert at a specific index
fruits.remove("banana")       # remove by value (first match)
fruits.pop()                  # remove & return the last item
fruits.pop(0)                 # remove & return item at index 0
len(fruits)                   # number of items
"apple" in fruits              # membership check -> True/False
fruits.sort()                  # sort in place
fruits.reverse()               # reverse in place


# List comprehensions — concise way to create lists

squares = [n**2 for n in range(5)]          # [0, 1, 4, 9, 16]
evens = [n for n in range(10) if n % 2 == 0]  # [0, 2, 4, 6, 8]

#Mutablity

a = [1, 2, 3]
b = a            # b points to the SAME list, not a copy
b.append(4)
print(a)         # [1, 2, 3, 4]  — a changed too!

c = a.copy()     # an actual independent copy