#!/usr/bin/env python

import inspect
import sys

# by default debugging is on
# overwrite with log.debugging=False
debugging = True

##############################################################################
# little logging lib
##############################################################################


# loglevel that always prints, use sparingly
def info(msg):
    caller = inspect.stack()[1][3]
    if caller == "<module>":
        caller = "main"
    print("[ INFO ] {}: {}".format(caller, msg))


# prints message nicely formatted with the calling functions name attached
def debug(msg):
    if debugging:
        caller = inspect.stack()[1][3]
        if caller == "<module>":
            caller = "main"
        print("[ DEBUG ] {}: {}".format(caller, msg))


# prints message then exits. use for unrecoverable errors
def fatal(msg):
    print("[ FATAL ] {}".format(msg))
    sys.exit(1)
