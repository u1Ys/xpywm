#!/usr/bin/env python3

import sys

def log(object_, prefix, fmt, *args):
    print(str(object_), prefix,
          fmt % args if args else fmt,
          file=sys.stderr,
          flush=True)

def debug(object_, fmt, *args):
    log(object_, '** debug: ', fmt, *args)

def error(object_, fmt, *args):
    log(object_, '** error:', fmt, *args)
