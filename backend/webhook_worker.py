from __future__ import annotations

import signal
import time
from uuid import uuid4

from config import get_settings
from database import db_context
from services.webhook_delivery_service import run_once


def run_forever() -> None:
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    worker_id = str(uuid4())
    while not stopping:
        with db_context() as client:
            processed = run_once(client, worker_id)
        if not processed:
            time.sleep(1)


if __name__ == "__main__":
    get_settings()
    run_forever()
