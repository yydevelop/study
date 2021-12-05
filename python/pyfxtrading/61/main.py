import logging
import sys
from threading import Thread

from app.controllers.streamdata import stream
from app.controllers.webserver import start
import app.models

import settings


if __name__ == "__main__":

    from app.controllers.ai import  AI
    from app.models.dfcandle import DataFrameCandle
    from datetime import timedelta

    ai = AI(product_code=settings.product_code,
            use_percent=settings.use_percent,
            duration=settings.trade_duration,
            past_period=settings.past_period,
            stop_limit_percent=settings.stop_limit_percent,
            back_test=False)
    ai.start_trade -= timedelta(minutes=100)

    df = DataFrameCandle()
    df.set_all_candles(limit=1000)
    candle = df.candles[-1]
    ai.buy(candle)

    # # streamThread = Thread(target=stream.stream_ingestion_data)
    # serverThread = Thread(target=start)
    #
    # # streamThread.start()
    # serverThread.start()
    #
    # # streamThread.join()
    # serverThread.join()