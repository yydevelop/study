import logging
import sys

from oanda.oanda import APIClient

import settings


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    api_client = APIClient(settings.access_token, settings.account_id)
    ticker = api_client.get_ticker(settings.product_code)
    print(ticker.product_code)
    print(ticker.timestamp)
    print(ticker.ask)
    print(ticker.bid)
    print(ticker.volume)
    print(ticker.truncate_date_time('5s'))
    print(ticker.truncate_date_time(settings.trade_duration))
    print(ticker.truncate_date_time('1h'))
    print(ticker.mid_price)
