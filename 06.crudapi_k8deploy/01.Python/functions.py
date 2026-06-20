# A function is a reusable, named block of code.

def greet(name):
    return f"Hello, {name}!"

greet("Priya")     # "Hello, Priya!"


# Default arguments, multiple returns, type hints:

def create_post(caption, image_url, is_public=True):   # default value
    return {"caption": caption, "image_url": image_url, "is_public": is_public}

create_post("Sunset", "https://...")                # is_public defaults to True
create_post("Sunset", "https://...", is_public=False) # override the default

def divide(a, b):
    if b == 0:
        return None, "Cannot divide by zero"   # return multiple values as a tuple
    return a / b, None

result, error = divide(10, 2)


def add(a: int, b: int) -> int:    # type hints — purely documentation, not enforced at runtime
    return a + b


# Functions are first-class objects — you can pass them around like any other value:
def apply_twice(func, value):
    return func(func(value))

apply_twice(lambda x: x * 2, 5)   # 20  — lambda = small anonymous inline function
# This is exactly what powers decorators like @token_required — a decorator is a function that takes a function and returns a new (wrapped) function.


# 2. Define a standard, normal function
def double(x):
    return x * 2

# 3. Pass the normal function by its name
result = apply_twice(double, 5)

print(result)  # Output: 20
