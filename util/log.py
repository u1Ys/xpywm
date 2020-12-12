#!/usr/bin/env python3

import logging

from xpywm.configure import LOG_FILE


logging.basicConfig(filename=LOG_FILE,
                    format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
                    level=logging.DEBUG)
