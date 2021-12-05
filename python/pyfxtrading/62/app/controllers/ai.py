import datetime
import logging
import time

import numpy as np
import talib

from app.models.candle import factory_candle_class
from app.models.dfcandle import DataFrameCandle
from app.models.events import SignalEvents
from oanda.oanda import APIClient
from oanda.oanda import Order
from tradingalgo.algo import ichimoku_cloud

import constants
import settings

logger = logging.getLogger(__name__)


def duration_seconds(duration: str) -> int:
    if duration == constants.DURATION_5S:
        return 5
    if duration == constants.DURATION_1M:
        return 60
    if duration == constants.DURATION_1H:
        return 60 * 60
    else:
        return 0


class AI(object):

    def __init__(self, product_code, use_percent, duration, past_period, stop_limit_percent, back_test):
        self.API = APIClient(settings.access_token, settings.account_id)

        if back_test:
            self.signal_events = SignalEvents()
        else:
            self.signal_events = SignalEvents.get_signal_events_by_count(1)

        self.product_code = product_code
        self.use_percent = use_percent
        self.duration = duration
        self.past_period = past_period
        self.optimized_trade_params = None
        self.stop_limit = 0
        self.stop_limit_percent = stop_limit_percent
        self.back_test = back_test
        self.start_trade = datetime.datetime.utcnow()
        self.candle_cls = factory_candle_class(self.product_code, self.duration)
        self.update_optimize_params(False)

    def update_optimize_params(self, is_continue: bool):
        logger.info('action=update_optimize_params status=run')
        df = DataFrameCandle(self.product_code, self.duration)
        df.set_all_candles(self.past_period)
        if df.candles:
            self.optimized_trade_params = df.optimize_params()
        if self.optimized_trade_params is not None:
            logger.info(f'action=update_optimize_params params={self.optimized_trade_params.__dict__}')

        if is_continue and self.optimized_trade_params is None:
            time.sleep(10 * duration_seconds(self.duration))
            self.update_optimize_params(is_continue)

    def buy(self, candle):
        if self.back_test:
            could_buy = self.signal_events.buy(self.product_code, candle.time, candle.close, 1.0, save=False)
            return could_buy

        if self.start_trade > candle.time:
            logger.warning('action=buy status=false error=old_time')
            return False

        if not self.signal_events.can_buy(candle.time):
            logger.warning('action=buy status=false error=previous_was_buy')
            return False

        balance = self.API.get_balance()
        units = int(balance.available * self.use_percent)
        order = Order(self.product_code, constants.BUY, units)
        trade = self.API.send_order(order)
        could_buy = self.signal_events.buy(self.product_code, candle.time, trade.price, trade.units, save=True)
        return could_buy

    def sell(self, candle):
        if self.back_test:
            could_sell = self.signal_events.sell(self.product_code, candle.time, candle.close, 1.0, save=False)
            return could_sell

        if self.start_trade > candle.time:
            logger.warning('action=sell status=false error=old_time')
            return False

        if not self.signal_events.can_sell(candle.time):
            logger.warning('action=sell status=false error=previous_was_sell')
            return False

        trades = self.API.get_open_trade()
        sum_price = 0
        units = 0
        for trade in trades:
            closed_trade = self.API.trade_close(trade.trade_id)
            sum_price += closed_trade.price * abs(closed_trade.units)
            units += abs(closed_trade.units)

        could_sell = self.signal_events.sell(self.product_code, candle.time, sum_price/units, units, save=True)
        return could_sell
