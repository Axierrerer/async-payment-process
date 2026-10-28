from uuid import UUID

from fastapi import APIRouter, Depends, status
from punq import Container

from domain.commands.payment import CreatePaymentCommand, GetPaymentCommand
from domain.use_cases.payment import CreatePaymentUseCase, GetPaymentUseCase
from transport.api.v1.depends import di_container, get_idempotency_key
from transport.api.v1.payments.schemas import CreatePaymentReq, CreatePaymentResp, PaymentResp
from transport.api.v1.schemas import ApiResponseSchema

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ApiResponseSchema[CreatePaymentResp],
)
async def create_payment(
    payment_in: CreatePaymentReq,
    idempotency_key: str = Depends(get_idempotency_key),
    container: Container = Depends(di_container),
) -> ApiResponseSchema[CreatePaymentResp]:
    use_case: CreatePaymentUseCase = container.resolve(CreatePaymentUseCase)
    payment = await use_case.execute(
        CreatePaymentCommand(entity=payment_in.to_entity(idempotency_key))
    )
    return ApiResponseSchema(data=CreatePaymentResp.from_entity(payment))


@router.get("/{payment_id}", response_model=ApiResponseSchema[PaymentResp])
async def get_payment(
    payment_id: UUID,
    container: Container = Depends(di_container),
) -> ApiResponseSchema[PaymentResp]:
    use_case: GetPaymentUseCase = container.resolve(GetPaymentUseCase)
    payment = await use_case.execute(GetPaymentCommand(payment_id=payment_id))
    return ApiResponseSchema(data=PaymentResp.from_entity(payment))
