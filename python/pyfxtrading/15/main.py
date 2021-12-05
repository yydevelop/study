import logging
import sys

from oanda.oanda import APIClient

import settings


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    api_client = APIClient(settings.access_token, settings.account_id)
    from functools import partial

    def trade(ticker):
        print(ticker.mid_price)
        print(ticker.ask)
        print(ticker.bid)

    callback = partial(trade)
    api_client.get_realtime_ticker(callback)
