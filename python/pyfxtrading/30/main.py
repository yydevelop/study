import logging
import sys
from threading import Thread

from app.controllers.streamdata import stream
from app.controllers.webserver import start
import app.models

import settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":
    """
    streamThread = Thread(target=stream.stream_ingestion_data)
    streamThread.start()
    streamThread.join()
    """
    serverThread = Thread(target=start)
    serverThread.start()
    serverThread.join()

