first = "Hello"
second = "World"

# 1. Plus operator
greeting = first + " " + second           # "Hello World"

# 2. f-strings (modern, preferred — supports inline expressions)
greeting = f"{first} {second}"             # "Hello World"
greeting = f"{first.upper()}, {2 + 2}!"     # "HELLO, 4!"

# 3. .format()
greeting = "{} {}".format(first, second)

# 4. join() — best for combining many strings (e.g. a list)
words = ["Hello", "World", "!"]
greeting = " ".join(words)                 # "Hello World !"