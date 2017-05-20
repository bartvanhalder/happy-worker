from pprint import pprint as p
from happy-worker import Happy-worker
import time
import sys

import stateful

happy = Happy-worker("example_db")

# overwrite the defaults like this
happy.min_freemem = 0.1  # in gb
happy.startup_delay = 0  # leave at default for random between 1000 and 3000ms
happy.worker_name = sys.argv[1]  # name has to be unique for each worker!
#there are more defaults, they are in the  __init__ function of happy-worker/happy-worker.py
#feel free to experiment with them!

# quick dummy worker function that shows you the content it gets from the worker
# and demonstrate it can handle external state passed into it
def dummyworker(job):
    print("============= WORK FUNCTION ===============")
    p(job)
    print(stateful.something("and i can pass stuff in too!"))
    print("=== sleeping to imitate work being done ===")
    time.sleep(10)


if __name__ == "__main__":
    happy.work(dummyworker)
