from fastapi import APIRouter

from transport.api.v1.payments.views import router as payments_router

v1_router = APIRouter()
v1_router.include_router(payments_router)
