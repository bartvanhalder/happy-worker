# Happy worker
### because a happy worker is a productive worker

Happy-worker is a small(191 lines) distributed task runner built on top of RethinkDB for people who like to read/edit/adapt/maintain the code they depend on.

Features:
 * Submit a dict(a work description) from an api
 * Get the dict back in your function on a server somewhere only once.
 * Run multiple processes on each host by using a unique worker name for each process (ex. $hostname+"-a" and $hostname+"-b")

Examples can be found in examples/

### Quickstart

```bash
  # python setup.py install
```

Examples can be found in examples/


### Slightly deeper into the details

A client can simply submit a job of its own choosing as a dict with happy-worker.submit({"Your":"job"})

This job is wrapped in a ticket and stored in RethinkDB. Each worker will try to aquire a claim on a ticket. The worker that gets the lease gets the job dict back and is free to do with it what it wants (I suggest doing the job, but who am i to decide what your code does?) If the worker function throws an exception it will be stored in the database and the ticket's retry_left is decremented. When retry_left reaches 0 no worker will try to aquire a lease on this ticket so you can go and debug your code :) Maybe your monitoring system can monior the amount of dead tickets, or send an alert to the developer that created the bug ;)
