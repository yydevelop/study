import logging
import sys
from threading import Thread

from app.controllers.streamdata import stream
from app.controllers.webserver import start
import app.models

import settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    from app.models.events import SignalEvents
    import datetime
    import settings
    import constants

    now = datetime.datetime.utcnow()
    # s = SignalEvent(time=now, product_code=settings.product_code, side=constants.BUY, price=100.0, units=1)
    # s.save()

    signal_events = SignalEvents.get_signal_events_by_count(10)
    print(signal_events.value)

    # print(signal_events.sell(settings.product_code, now, 105.0, 1, True))

    # now = now - datetime.timedelta(minutes=1000)
    # signal_events = SignalEvents.get_signal_events_after_time(now)
    # print(signal_events.value)

    # streamThread = Thread(target=stream.stream_ingestion_data)
    # serverThread = Thread(target=start)

    # streamThread.start()
    # serverThread.start()

    # streamThread.join()
    # serverThread.join()