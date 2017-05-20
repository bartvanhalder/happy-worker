
# non stdlib
import rethinkdb as r
import traceback
import random
import psutil
import time
import os

# my own imports
from happy-worker import log
# import log #for dev


class Happy-worker:
    def __init__(self, db="generic_work"):
        # common tunables
        self.db = db

        # worker tunables
        self.min_freemem = 3  # gb
        self.max_iterations = 100
        self.worker_name = "DEFAULT only run one worker or overwrite happy.worker_name"
        self.overload_sleep = 10  # time so sleep while the memory is overloaded
        # idle_sleep == time to sleep when a worker comes across a ticket that is already claimed.
        # keeps them from racing. Decrease this for decreaced latency but more overhead
        self.idle_sleep = 5
        self.ticket_lifetime = 5  # in minutes, the time a claim will be valid
        self.startup_delay = None  # if none happy-worker will sleep between 0 and 3 seconds

        # connect to rethinkdb on startup
        self.conn = r.connect()

    ###############################################################################
    # helper functions
    ###############################################################################
    # returns false if there is less than min_freemem gb ram free,
    # returns true when enough ram is available
    def memory_available(self):
        mem_free_bytes = psutil.virtual_memory().available
        needed_bytes = self.min_freemem * 1024 * 1024 * 1024  # min_freemem is in gb
        return mem_free_bytes > needed_bytes

    def fail(self, ticket, trace):
        log.debug(trace)
        # so the function we were running threw an exception, decrement the retries, store
        # this stacktrace, and reschedule in half the ticket_lifetime from now by putting
        # an invalid workername on it with a workertime ticket_lifetime/2 in the future
        ticket_patch = {
            "retry_left": ticket["retry_left"] - 1,
            "last_stacktrace": trace[-2048:],  # only store the last 2048 bytes
            "workername": self.worker_name + "_FAILED", #so this worker will try a new ticket
            "workertime": int(time.time() + (self.ticket_lifetime / 2) * 60)
        }
        r.db(self.db).table("tickets").get(ticket["id"]).update(ticket_patch).run(self.conn)

    # try to update the ticket with our name and time,
    # if rethinkdb acks the write other workers trying have failed and this worker won
    def get_claim(self, ticket):
        new_workertime = int(time.time()) + self.ticket_lifetime * 60
        ticket_patch = {"workername": self.worker_name, "workertime": new_workertime}

        result = r.db(self.db).table("tickets").get(ticket["id"]).update(
            r.branch(
                r.row["workername"].eq(ticket["workername"]).and_(r.row["workertime"].eq(ticket["workertime"])),
                ticket_patch,
                {}
            )
        ).run(self.conn)

        if result["replaced"] == 1:
            log.debug("Claim success!")
            return ticket

        log.debug("Claim failed :(")
        return None

    ###############################################################################
    # main workermodel implementation
    ###############################################################################
    # can return 2 things:
    # - a ticket if we have work to do (a dict)
    # - None if we failed to claim a job or there is no work
    def get_ticket(self):
        # get random assignment that still has retries left
        # if there is no work, sleep and continue
        tickets = r.db(self.db).table("tickets").filter(r.row["retry_left"].gt(0)).sample(1).run(self.conn)
        if tickets == []:
            log.debug("There are no jobs to do? maybe after a little nap?")
            time.sleep(self.idle_sleep)
            return None
        ticket = tickets[0]

        if ticket["workername"] == "":
            # unset name, try to claim it
            return self.get_claim(ticket)
        else:
            # name set
            log.debug("name is set")
            if ticket["workertime"] < int(time.time()):
                # claim on this ticket is expired, try to steal it
                return self.get_claim(ticket)

            else:
                # claim is not expired, is it mine?
                if ticket["workername"] == self.worker_name:
                    # mine, but try claiming again,
                    # updates the workertime to make sure no
                    # other worker steals it while i'm working
                    return self.get_claim(ticket)

                else:
                    # not mine, not expired, leave it alone
                    log.debug("tried claiming a ticket that was already valid, sleeping")
                    time.sleep(self.idle_sleep)
                    return None

        log.fatal("This should never be reached")

    # little function for waiting before starting up,
    # startup_delay can be overwritten by the user of the happy-worker
    def delayed_startup(self):
        if self.startup_delay is None:
            self.startup_delay = random.uniform(0.0, 3.0)
        time.sleep(self.startup_delay)

    ###############################################################################
    # function that invokes the worker model with the function to run as argument
    # part of the external api
    ###############################################################################
    def work(self, workfunc):
        log.debug("starting worker {}".format(self.worker_name))
        self.delayed_startup()
        for i in range(self.max_iterations):
            log.debug("happy-worker starting battle #{}".format(i))
            if self.memory_available():
                ticket = self.get_ticket()
                if ticket is not None:
                    # we have a ticket, it's valid and ours!
                    log.debug("running job with id: {}".format(ticket["id"]))
                    try:
                        workfunc(ticket["job"])
                    except Exception:
                        log.info("worker threw an exception:")
                        trace = traceback.format_exc()
                        self.fail(ticket, trace)
                        continue
                    # work has been completed, delete it!
                    r.db(self.db).table("tickets").get(ticket["id"]).delete().run(self.conn)
                else:
                    log.debug("There was no work, or claiming work failed, try again!")
                    continue
            else:
                log.info("This happy-worker does not have enough memory free to run its job")
                time.sleep(self.overload_sleep)
                continue

    ###############################################################################
    # submit work function
    # part of the external api
    ###############################################################################
    def submit(self, job, retries=1):
        ticket = {"workername": "",
                  "workertime": 0,
                  "retry_left": retries,
                  "last_stacktrace": "",
                  "job": job}
        # returns true if it was inserted.
        return r.db(self.db).table("tickets").insert(ticket).run(self.conn)["inserted"] > 0

    ###############################################################################
    # database creation helper
    # part of the external api
    ###############################################################################
    def create_db(self):
        try:
            r.db_create(self.db).run(self.conn)
            log.info("created database: {}".format(self.db))
        except r.errors.ReqlOpFailedError:
            log.info("exception during db_create, assuming it was an already exists error")

        # let's give the db time to settle
        time.sleep(0.5)

        try:
            r.db(self.db).table_create("tickets").run(self.conn)
            log.info("created tickets table")
            log.info("""PLEASE remember:
                set shards and replicas as by default you are in the DangerZone!""")
        except r.errors.ReqlOpFailedError:
            log.info("exception during table_create, assuming it was an already exists error")
