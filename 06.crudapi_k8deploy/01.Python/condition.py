age = 20

if age < 13:
    category = "child"
elif age < 20:
    category = "teen"
else:
    category = "adult"


# Comparison & logical operators:
"""
==, !=, <, >, <=, >=        # comparisons
and, or, not                # logical combination

if age >= 18 and has_id:
    print("Allowed in")

if not is_banned:
    print("Welcome")
"""
user = {
    "age": 20,
    "has_id": True,
    "is_banned": False
}
if user["age"]>18 and user["has_id"]:
    print("Allowed in")

if not user["is_banned"]:
    print("Welcome")


bio = ""
if bio:                 # False, because empty string is falsy
    print(bio)
else:
    print("No bio set")

# equivalent to: if bio != "" and bio is not None:


#ternary operator — concise if-else for simple cases
userData={
    "is_logged_in": True
}
status = "active" if userData["is_logged_in"] else "guest"

# In Js we would write:
# let status = userData.is_logged_in ? "active" : "guest";
# condition ? expressionIfTrue : expressionIfFalse;
