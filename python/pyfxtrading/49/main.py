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
    s = SignalEvent(time=now, product_code=settings.product_code, side=constants.BUY, price=100.0, units=1)
    s.save()

    signal_events = SignalEvent.get_signal_events_by_count(10)
    for signal_event in signal_events:
        print(signal_event.value)

    now = now - datetime.timedelta(minutes=10)
    signal_events = SignalEvent.get_signal_events_after_time(now)
    for signal_event in signal_events:
        print(signal_event.value)

    # streamThread = Thread(target=stream.stream_ingestion_data)
    # serverThread = Thread(target=start)

    # streamThread.start()
    # serverThread.start()

    # streamThread.join()
    # serverThread.join()