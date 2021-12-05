import logging
import sys
from threading import Thread

from app.controllers.streamdata import stream
from app.controllers.webserver import start
import app.models

import settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    from app.models.events import SignalEvent
    import datetime
    import settings
    import constants

    now = datetime.datetime.utcnow()

    from app.models.dfcandle import DataFrameCandle
    df = DataFrameCandle()
    df.set_all_candles(limit=100)

    candle1 = df.candles[1]
    candle2 = df.candles[10]

    # s = SignalEvent(time=candle1.time, product_code=settings.product_code, side=constants.BUY, price=candle1.close, units=10)
    # s.save()
    # s = SignalEvent(time=candle2.time, product_code=settings.product_code, side=constants.SELL, price=candle2.close, units=10)
    # s.save()

    # streamThread = Thread(target=stream.stream_ingestion_data)
    serverThread = Thread(target=start)
    #
    # streamThread.start()
    serverThread.start()
    #
    # streamThread.join()
    serverThread.join()