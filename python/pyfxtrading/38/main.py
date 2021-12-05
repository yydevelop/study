import logging
import sys
from threading import Thread

from app.controllers.streamdata import stream
from app.controllers.webserver import start
import app.models

import settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    '''
    from app.models.dfcandle import DataFrameCandle
    import talib
    import numpy as np

    df = DataFrameCandle(settings.product_code,
                         settings.trade_duration)
    df.set_all_candles(100)
    df.add_sma(7)
    print(df.value)
    '''
    # streamThread = Thread(target=stream.stream_ingestion_data)
    serverThread = Thread(target=start)

    # streamThread.start()
    serverThread.start()

    # streamThread.join()
    serverThread.join()
