count = 0
while count < 5:
    print(count)
    count += 1     # without this, the loop never ends — infinite loop!

# Real example — exactly the pattern behind long polling:

import time
def something_changed():
    # Imagine this checks a server or file for change
    #make this randomly return True after a few seconds for testing
    return time.time() % 10 < 0.5  # randomly True about 5% of the time

start = time.time()
while time.time() - start < 25:    # keep checking for up to 25 seconds
    if something_changed():
        break
    #log when changes is not taking place 
    print("No change detected, checking again...")
    #so the seconds elasped on screen
    print(f"Seconds elapsed: {int(time.time() - start)}")
    time.sleep(0.5)


