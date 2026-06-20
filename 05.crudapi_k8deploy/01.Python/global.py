# counter = 0

# def increment():
#     counter = counter + 1   # ❌ UnboundLocalError! Python sees the assignment
#                             #    and treats `counter` as local for the whole function

# increment()
# print(counter)  # Still 0, because the function never successfully increments it


counter = 0

def increment():
    global counter
    counter += 1

increment()
increment()
print(counter)   # 2

latest_event = {"version": 0, "type": None, "data": None}

print(latest_event)  # {'version': 0, 'type': None, 'data': None}
# This is exactly the pattern from the Flask long-polling code:
import threading
lock = threading.Lock()   # to ensure thread safety when mutating the shared dict
def publish_event(event_type, data):
    global latest_event           # not even strictly required here since we're
    with lock:                    # mutating the dict in place, not reassigning it —
        latest_event["version"] += 1   # but it signals intent clearly
        latest_event["type"] = event_type
        latest_event["data"] = data
# Important subtlety: global is only required when reassigning a variable, not when mutating an object like a dict or list. So if we were to do latest_event = {...} instead of modifying it in place, we would need the global statement.
publish_event("new_message", {"text": "Hello, world!"})
print(latest_event)  # {'version': 1, 'type': 'new_message', 'data': {'text': 'Hello, world!'}}