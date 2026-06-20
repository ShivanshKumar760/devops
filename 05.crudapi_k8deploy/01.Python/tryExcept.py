user_input = "abc"  # Imagine this came from input()
try:
    value = int(user_input)
except ValueError:
    print("That wasn't a valid number")
    while True:
        user_input = input("Please enter a number: ")
        try:
            value = int(user_input)
            break  # exit loop if conversion succeeds
        except ValueError:
            print("Still not a valid number, try again.")