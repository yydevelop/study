import logging
import sys

from oanda.oanda import Order
from oanda.oanda import APIClient

import settings


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    import app.models
