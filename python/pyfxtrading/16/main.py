import logging
import sys

from oanda.oanda import Order
from oanda.oanda import APIClient

import settings


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    api_client = APIClient(settings.access_token, settings.account_id)

    order = Order(
        product_code=settings.product_code,
        side='BUY',
        units=10,
    )

    api_client.send_order(order)
