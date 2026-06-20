age = 25            # int
price = 19.99        # float
name = "Alice"        # str
is_active = True      # bool
nothing = None        # NoneType — represents "no value"

x = 5
print(type(x))       # <class 'int'>
x = "now a string"
print(type(x))     # <class 'str'> — same variable, new type, totally legal


print(int("42"))      # 42
print(str(42))       # "42"
print(float("3.5")) # 3.5
print(bool(0))        # False — 0, "", None, [], {} are all "falsy"
print(bool(1))        # True — everything else is "truthy"