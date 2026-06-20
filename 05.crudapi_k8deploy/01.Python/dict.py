user = {
    "username": "priya_d",
    "email": "priya@example.com",
    "age": 29,
}

user["username"]          # "priya_d"
user.get("bio")            # None — .get() doesn't raise an error if missing
user.get("bio", "N/A")     # "N/A" — provide a default
user["bio"] = "Photographer 📸"   # add or update a key
del user["age"]             # remove a key
"email" in user              # True/False — checks KEYS by default

#Iterating over a dict :


for key in user:
    print(key, user[key])

for key, value in user.items():
    print(key, value)

for value in user.values():
    print(value)


#dict comprehensions

squares = {n: n**2 for n in range(5)}   # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# Nested structures (very common in real APIs):
post = {
    "post_id": 101,
    "caption": "Beautiful sunset",
    "author": {"user_id": 1, "username": "elonmusk"},
    "likes": ["priya_d", "rahul99"],
}
post["author"]["username"]   # "elonmusk"