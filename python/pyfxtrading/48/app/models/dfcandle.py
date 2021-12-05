import numpy as np
import talib

from app.models.candle import factory_candle_class
import settings
from utils.utils import Serializer
from tradingalgo.algo import ichimoku_cloud


def nan_to_zero(values: np.asarray):
    values[np.isnan(values)] = 0
    return values


def empty_to_none(input_list):
    if not input_list:
        return None
    return input_list


class Sma(Serializer):
    def __init__(self, period: int, values: list):
        self.period = period
        self.values = values


class Ema(Serializer):
    def __init__(self, period: int, values: list):
        self.period = period
        self.values = values


class BBands(Serializer):
    def __init__(self, n: int, k: float, up: list, mid: list, down: list):
        self.n = n
        self.k = k
        self.up = up
        self.mid = mid
        self.down = down


class IchimokuCloud(Serializer):
    def __init__(self, tenkan: list, kijun: list, senkou_a: list,
                 senkou_b: list, chikou:list):
        self.tenkan = tenkan
        self.kijun = kijun
        self.senkou_a = senkou_a
        self.senkou_b = senkou_b
        self.chikou = chikou


class Rsi(Serializer):
    def __init__(self, period: int, values: list):
        self.period = period
        self.values = values


class Macd(Serializer):
    def __init__(self, fast_period:int, slow_period:int, signal_period:int, macd:list, macd_signal:list, macd_hist:list):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.macd = macd
        self.macd_signal = macd_signal
        self.macd_hist = macd_hist


class DataFrameCandle(object):

    def __init__(self, product_code=settings.product_code, duration=settings.trade_duration):
        self.product_code = product_code
        self.duration = duration
        self.candle_cls = factory_candle_class(self.product_code, self.duration)
        self.candles = []
        self.smas = []
        self.emas = []
        self.bbands = BBands(0, 0, [], [], [])
        self.ichimoku_cloud = IchimokuCloud([], [], [], [], [])
        self.rsi = Rsi(0, [])
        self.macd = Macd(0, 0, 0, [], [], [])

    def set_all_candles(self, limit=1000):
        self.candles = self.candle_cls.get_all_candles(limit)
        return self.candles

    @property
    def value(self):
        return {
            'product_code': self.product_code,
            'duration': self.duration,
            'candles': [c.value for c in self.candles],
            'smas': empty_to_none([s.value for s in self.smas]),
            'emas': empty_to_none([s.value for s in self.emas]),
            'bbands': self.bbands.value,
            'ichimoku': self.ichimoku_cloud.value,
            'rsi': self.rsi.value,
            'macd': self.macd.value,
        }

    @property
    def opens(self):
        values = []
        for candle in self.candles:
            values.append(candle.open)
        return values

    @property
    def closes(self):
        values = []
        for candle in self.candles:
            values.append(candle.close)
        return values

    @property
    def highs(self):
        values = []
        for candle in self.candles:
            values.append(candle.high)
        return values

    @property
    def lows(self):
        values = []
        for candle in self.candles:
            values.append(candle.low)
        return values

    @property
    def volumes(self):
        values = []
        for candle in self.candles:
            values.append(candle.volume)
        return values

    def add_sma(self, period: int):

        if len(self.closes) > period:
            values = talib.SMA(np.asarray(self.closes), period)
            sma = Sma(
                period,
                nan_to_zero(values).tolist()
            )
            self.smas.append(sma)
            return True
        return False

    def add_ema(self, period: int):

        if len(self.closes) > period:
            values = talib.EMA(np.asarray(self.closes), period)
            ema = Ema(
                period,
                nan_to_zero(values).tolist()
            )
            self.emas.append(ema)
            return True
        return False

    def add_bbands(self, n:int, k:float):
        if n <= len(self.closes):
            up, mid, down = talib.BBANDS(np.asarray(self.closes), n, k, k, 0)
            up_list = nan_to_zero(up).tolist()
            mid_list = nan_to_zero(mid).tolist()
            down_list = nan_to_zero(down).tolist()
            self.bbands = BBands(n, k, up_list, mid_list, down_list)
            return True
        return False

    def add_ichimoku(self):
        if len(self.closes) >= 9:
            tenkan, kijun, senkou_a, senkou_b, chikou = ichimoku_cloud(self.closes)
            self.ichimoku_cloud = IchimokuCloud(
                tenkan, kijun, senkou_a, senkou_b, chikou)
            return True
        return False

    def add_rsi(self, period: int):

        if len(self.closes) > period:
            values = talib.RSI(np.asarray(self.closes), period)
            rsi = Rsi(
                period,
                nan_to_zero(values).tolist()
            )
            self.rsi = rsi
            return True
        return False

    def add_macd(self, fast_period:int, slow_period:int, signal_period:int):
        if len(self.candles) > 1:
            macd, macd_signal, macd_hist = talib.MACD(
                np.asarray(self.closes), fast_period, slow_period, signal_period)
            macd_list = nan_to_zero(macd).tolist()
            macd_signal_list = nan_to_zero(macd_signal).tolist()
            macd_hist_list = nan_to_zero(macd_hist).tolist()
            self.macd = Macd(
                fast_period, slow_period, signal_period, macd_list, macd_signal_list, macd_hist_list)
            return True
        return False

