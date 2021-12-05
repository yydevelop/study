from datetime import datetime
import logging

import dateutil.parser
from oandapyV20 import API
from oandapyV20.endpoints import accounts
from oandapyV20.endpoints.pricing import PricingInfo
from oandapyV20.exceptions import V20Error

logger = logging.getLogger(__name__)


class Balance(object):
    def __init__(self, currency, available):
        self.currency = currency
        self.available = available


class Ticker(object):
    def __init__(self, product_code, timestamp, bid, ask, volume):
        self.product_code = product_code
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask
        self.volume = volume


class APIClient(object):
    def __init__(self, access_token, account_id, environment='practice'):
        self.access_token = access_token
        self.account_id = account_id
        self.client = API(access_token=access_token, environment=environment)

    def get_balance(self) -> Balance:
        req = accounts.AccountSummary(accountID=self.account_id)
        try:
            resp = self.client.request(req)
        except V20Error as e:
            logger.error(f'action=get_balance error={e}')
            raise

        available = float(resp['account']['balance'])
        currency = resp['account']['currency']
        return Balance(currency, available)

    def get_ticker(self, product_code) -> Ticker:
        params = {
            'instruments': product_code
        }
        req = PricingInfo(accountID=self.account_id, params=params)
        try:
            resp = self.client.request(req)
        except V20Error as e:
            logger.error(f'action=get_ticker error={e}')
            raise

        timestamp = datetime.timestamp(
            dateutil.parser.parse(resp['time']))
        price = resp['prices'][0]
        instrument = price['instrument']
        bid = float(price['bids'][0]['price'])
        ask = float(price['asks'][0]['price'])
        volume = 11111
        return Ticker(instrument, timestamp, bid, ask, volume)





























