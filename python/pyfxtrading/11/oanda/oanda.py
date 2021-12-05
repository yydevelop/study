import logging

from oandapyV20 import API
from oandapyV20.endpoints import accounts
from oandapyV20.exceptions import V20Error

logger = logging.getLogger(__name__)


class Balance(object):
    def __init__(self, currency, available):
        self.currency = currency
        self.available = available


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

