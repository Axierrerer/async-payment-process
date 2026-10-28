import asyncio
import sys

from entrypoints.consumer import main as consumer_main
from entrypoints.outbox_relay import main as outbox_relay_main
from entrypoints.uvicorn_run import main as uvicorn_main

if __name__ == "__main__":
    if "--uvicorn" in sys.argv:
        asyncio.run(uvicorn_main())
    elif "--outbox-relay" in sys.argv:
        asyncio.run(outbox_relay_main())
    elif "--consumer" in sys.argv:
        asyncio.run(consumer_main())
