import asyncio
import random
from dataclasses import dataclass

from domain.payments.entities import Payment

MIN_PROCESSING_SECONDS = 2.0
MAX_PROCESSING_SECONDS = 5.0
SUCCESS_RATE = 0.9


@dataclass
class EmulatedPaymentGateway:
    async def charge(self, payment: Payment) -> bool:
        await asyncio.sleep(random.uniform(MIN_PROCESSING_SECONDS, MAX_PROCESSING_SECONDS))
        return random.random() < SUCCESS_RATE
