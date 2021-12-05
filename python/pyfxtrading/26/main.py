import logging
import sys
from threading import Thread

from app.controllers.streamdata import stream
import app.models

import settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == "__main__":

    streamThread = Thread(target=stream.stream_ingestion_data)
    streamThread.start()
    streamThread.join()
