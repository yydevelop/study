import datetime
import logging
import sys

import app.models
from app.models.candle import UsdJpyBaseCandle1M
import settings


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":

    # for i in range(200):
    #    now1 = datetime.datetime(2000+i, 1, 2, 3, 4, 5)
    #    UsdJpyBaseCandle1M.create(now1, 1.0, 2.0, 3.0, 4.0, 5)

    candles = UsdJpyBaseCandle1M.get_all_candles(3)
    for candle in candles:
        print(candle.value)
