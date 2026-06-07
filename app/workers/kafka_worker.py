import logging
from collections.abc import Awaitable, Callable

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

class KafkaWorker:
    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        handler: Callable[[dict], Awaitable[None]],
    ):
        self._consumer = consumer
        self._handler = handler
        self._running = False

    async def start(self):
        await self._consumer.start()
        self._running = True
        logger.info("Worker started, waiting for messages...")
        try:
            await self._loop()
        finally:
            await self._consumer.stop()
            logger.info("Worker stopped.")

    async def _loop(self):
        async for message in self._consumer:
            if not self._running:
                break
            try:
                await self._handler(message.value)
                await self._consumer.commit()
            except Exception:
                logger.exception(
                    "Handler failed for message offset=%s — skipping commit",
                    message.offset,
                )

    async def stop(self):
        self._running = False