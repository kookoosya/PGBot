from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.deps import get_current_user, require_owner
from app.core.password_policy import validate_password
from app.core.rate_limit import limiter
from app.core.security import get_password_hash
from app.database import get_db
from app.models.enums import SERVICE_TYPE_LABELS, ServiceType, UserRole, VerificationStatus
from app.models.provider_busy import ProviderBusyBlock
from app.models.service import (
    ProviderSchedule,
    ProviderService,
    ServiceAppointment,
    ServiceProvider,
)
from app.models.user import Role, User
from app.schemas.service import (
    AppointmentResponse,
    BookAppointmentRequest,
    BusyBlockCreate,
    BusyBlockResponse,
    ProviderDetailResponse,
    ProviderListItem,
    ProviderRegisterRequest,
    ProviderServiceResponse,
    ScheduleResponse,
    ServiceItemInput,
    SlotsResponse,
    TimeSlot,
    UpdateScheduleRequest,
)
from app.services.notifications import notify_owner, notify_vk_user
from app.services.schedule import (
    DAY_LABELS,
    format_time,
    get_provider_slots,
    get_provider_status_today,
    parse_time,
)

router = APIRouter()
settings = get_settings()


def _service_resp(s: ProviderService) -> ProviderServiceResponse:
    return ProviderServiceResponse(
        id=s.id,
        service_type=s.service_type,
        service_label=SERVICE_TYPE_LABELS.get(s.service_type, s.service_type),
        name=s.name,
        description=s.description,
        duration_minutes=s.duration_minutes,
        price=s.price,
    )


@router.get("/types")
async def list_service_types():
    return [{"value": t.value, "label": SERVICE_TYPE_LABELS[t]} for t in ServiceType]


@router.post("/register", status_code=201)
@limiter.limit(settings.REGISTER_RATE_LIMIT)
async def register_provider(
    request: Request,
    data: ProviderRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ok, msg = validate_password(data.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    existing = await db.execute(select(User).where((User.username == data.username) | (User.email == data.email)))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Логин или email уже заняты")

    role_result = await db.execute(select(Role).where(Role.name == UserRole.SERVICE_PROVIDER))
    role = role_result.scalar_one_or_none()
    if not role:
        role = Role(name=UserRole.SERVICE_PROVIDER, description="Мастер/специалист услуг")
        db.add(role)
        await db.flush()

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role_id=role.id,
        verification_status=VerificationStatus.PENDING,
        is_active=False,
    )
    db.add(user)
    await db.flush()

    provider = ServiceProvider(
        user_id=user.id,
        full_name=data.full_name,
        phone=data.phone,
        email=data.email,
        bio=data.bio,
        address=data.address,
        verification_status=VerificationStatus.PENDING,
        is_active=False,
    )
    db.add(provider)
    await db.flush()

    for svc in data.services:
        db.add(
            ProviderService(
                provider_id=provider.id,
                service_type=svc.service_type,
                name=svc.name,
                description=svc.description,
                duration_minutes=svc.duration_minutes,
                price=svc.price,
            )
        )

    for sch in data.schedule:
        db.add(
            ProviderSchedule(
                provider_id=provider.id,
                day_of_week=sch.day_of_week,
                start_time=parse_time(sch.start_time),
                end_time=parse_time(sch.end_time),
                is_working=sch.is_working,
            )
        )

    svc_names = ", ".join(s.name for s in data.services)
    await notify_owner(
        "💇 Новая заявка мастера\n\n"
        f"#{provider.id} · {data.full_name}\n"
        f"📞 {data.phone}\n"
        f"Услуги: {svc_names}\n\n"
        "Одобрите в админ-панели."
    )

    return {"id": provider.id, "message": "Заявка отправлена на проверку. После одобрения вы появитесь в каталоге."}


@router.get("/providers", response_model=list[ProviderListItem])
async def list_providers(
    db: Annotated[AsyncSession, Depends(get_db)],
    service_type: ServiceType | None = None,
):
    query = (
        select(ServiceProvider)
        .options(selectinload(ServiceProvider.services))
        .where(
            ServiceProvider.is_active.is_(True),
            ServiceProvider.verification_status == VerificationStatus.APPROVED,
        )
    )
    result = await db.execute(query.order_by(ServiceProvider.full_name))
    providers = result.scalars().all()
    items = []
    for p in providers:
        services = [_service_resp(s) for s in p.services if s.is_active]
        if service_type and not any(s.service_type == service_type for s in p.services):
            continue
        status, next_slot = await get_provider_status_today(db, p)
        items.append(
            ProviderListItem(
                id=p.id,
                full_name=p.full_name,
                phone=p.phone,
                bio=p.bio,
                address=p.address,
                avg_rating=p.avg_rating,
                review_count=p.review_count,
                services=services,
                status_today=status,
                next_free_slot=next_slot,
            )
        )
    return items


@router.get("/providers/pending/list")
async def list_pending_providers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await db.execute(
        select(ServiceProvider)
        .options(selectinload(ServiceProvider.services))
        .where(ServiceProvider.verification_status == VerificationStatus.PENDING)
    )
    return [
        {
            "id": p.id,
            "full_name": p.full_name,
            "phone": p.phone,
            "address": p.address,
            "services": [s.name for s in p.services],
        }
        for p in result.scalars().all()
    ]


@router.post("/providers/{provider_id}/approve")
async def approve_provider(
    provider_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await db.execute(select(ServiceProvider).where(ServiceProvider.id == provider_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404)
    p.verification_status = VerificationStatus.APPROVED
    p.is_active = True
    if p.user_id:
        user_result = await db.execute(select(User).where(User.id == p.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.verification_status = VerificationStatus.APPROVED
            user.is_active = True
            if user.vk_id:
                await notify_vk_user(
                    user.vk_id,
                    f"✅ Ваш профиль мастера одобрен!\n\n{p.full_name} — теперь в каталоге услуг посёлка.",
                )
    await notify_owner(f"✅ Мастер #{provider_id} «{p.full_name}» одобрен и опубликован.")
    return {"status": "approved"}


@router.post("/providers/{provider_id}/reject")
async def reject_provider(
    provider_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    reason: str = "Не подтверждены данные",
):
    result = await db.execute(select(ServiceProvider).where(ServiceProvider.id == provider_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404)
    p.verification_status = VerificationStatus.REJECTED
    p.is_active = False
    if p.user_id:
        user_result = await db.execute(select(User).where(User.id == p.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.verification_status = VerificationStatus.REJECTED
            user.is_active = False
            if user.vk_id:
                await notify_vk_user(
                    user.vk_id,
                    f"❌ Заявка мастера отклонена.\n{reason}",
                )
    await notify_owner(f"❌ Мастер #{provider_id} «{p.full_name}» отклонён: {reason}")
    return {"status": "rejected"}


@router.get("/providers/{provider_id}", response_model=ProviderDetailResponse)
async def get_provider(provider_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(ServiceProvider)
        .options(selectinload(ServiceProvider.services), selectinload(ServiceProvider.schedule))
        .where(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_active.is_(True),
            ServiceProvider.verification_status == VerificationStatus.APPROVED,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Мастер не найден")
    status, next_slot = await get_provider_status_today(db, p)
    schedule = [
        ScheduleResponse(
            day_of_week=s.day_of_week,
            day_label=DAY_LABELS[s.day_of_week],
            start_time=format_time(s.start_time),
            end_time=format_time(s.end_time),
            is_working=s.is_working,
        )
        for s in sorted(p.schedule, key=lambda x: x.day_of_week)
    ]
    return ProviderDetailResponse(
        id=p.id,
        full_name=p.full_name,
        phone=p.phone,
        bio=p.bio,
        address=p.address,
        avg_rating=p.avg_rating,
        review_count=p.review_count,
        services=[_service_resp(s) for s in p.services if s.is_active],
        status_today=status,
        next_free_slot=next_slot,
        schedule=schedule,
        verification_status=p.verification_status,
    )


@router.get("/providers/{provider_id}/slots", response_model=SlotsResponse)
async def get_slots(
    provider_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    appointment_date: date = Query(...),
    service_id: int = Query(...),
):
    svc_result = await db.execute(select(ProviderService).where(ProviderService.id == service_id))
    service = svc_result.scalar_one_or_none()
    if not service:
        raise HTTPException(404, "Услуга не найдена")

    prov_result = await db.execute(
        select(ServiceProvider).where(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_active.is_(True),
            ServiceProvider.verification_status == VerificationStatus.APPROVED,
        )
    )
    provider = prov_result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, "Мастер не найден")

    slots, hours = await get_provider_slots(db, provider_id, appointment_date, service.duration_minutes)
    return SlotsResponse(
        date=appointment_date,
        provider_id=provider_id,
        provider_name=provider.full_name,
        working_hours=hours,
        slots=[TimeSlot(**s) for s in slots],
    )


@router.post("/providers/{provider_id}/book", response_model=AppointmentResponse, status_code=201)
@limiter.limit(settings.BOOKING_RATE_LIMIT)
async def book_appointment(
    request: Request,
    provider_id: int,
    data: BookAppointmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc_result = await db.execute(
        select(ProviderService).where(
            ProviderService.id == data.service_id,
            ProviderService.provider_id == provider_id,
        )
    )
    service = svc_result.scalar_one_or_none()
    if not service:
        raise HTTPException(404, "Услуга не найдена")

    prov_result = await db.execute(
        select(ServiceProvider).where(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_active.is_(True),
            ServiceProvider.verification_status == VerificationStatus.APPROVED,
        )
    )
    provider = prov_result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, "Мастер недоступен для записи")

    start = parse_time(data.start_time)
    end_dt = datetime.combine(data.appointment_date, start) + timedelta(minutes=service.duration_minutes)
    end = end_dt.time()

    slots, _ = await get_provider_slots(db, provider_id, data.appointment_date, service.duration_minutes)
    slot = next((s for s in slots if s["time"] == data.start_time), None)
    if not slot or not slot["available"]:
        raise HTTPException(400, "Это время уже занято или недоступно")

    appt = ServiceAppointment(
        provider_id=provider_id,
        service_id=service.id,
        client_name=data.client_name,
        client_phone=data.client_phone,
        appointment_date=data.appointment_date,
        start_time=start,
        end_time=end,
        notes=data.notes,
        status="booked",
    )
    db.add(appt)
    await db.flush()

    date_str = appt.appointment_date.isoformat()
    time_str = format_time(appt.start_time)
    await notify_owner(
        "📅 Новая запись к мастеру!\n\n"
        f"Мастер: {provider.full_name}\n"
        f"Услуга: {service.name}\n"
        f"📆 {date_str} в {time_str}\n"
        f"👤 {appt.client_name} · 📞 {appt.client_phone}"
    )

    if provider.user_id:
        user_result = await db.execute(select(User).where(User.id == provider.user_id))
        provider_user = user_result.scalar_one_or_none()
        if provider_user and provider_user.vk_id:
            await notify_vk_user(
                provider_user.vk_id,
                f"📅 Новая запись!\n\n"
                f"{service.name} · {date_str} в {time_str}\n"
                f"Клиент: {appt.client_name}, {appt.client_phone}",
            )

    return AppointmentResponse(
        id=appt.id,
        provider_name=provider.full_name,
        service_name=service.name,
        appointment_date=appt.appointment_date,
        start_time=format_time(appt.start_time),
        end_time=format_time(appt.end_time),
        status=appt.status,
        client_name=appt.client_name,
    )


async def _get_my_provider(db: AsyncSession, user: User) -> ServiceProvider:
    role_name = user.role.name if hasattr(user.role, "name") else user.role
    if role_name != UserRole.SERVICE_PROVIDER:
        raise HTTPException(403, "Доступ только для мастеров")
    result = await db.execute(
        select(ServiceProvider)
        .options(
            selectinload(ServiceProvider.services),
            selectinload(ServiceProvider.schedule),
        )
        .where(ServiceProvider.user_id == user.id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, "Профиль мастера не найден")
    return provider


@router.get("/my/profile", response_model=ProviderDetailResponse)
async def my_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    p = await _get_my_provider(db, current_user)
    status, next_slot = await get_provider_status_today(db, p)
    schedule = [
        ScheduleResponse(
            day_of_week=s.day_of_week,
            day_label=DAY_LABELS[s.day_of_week],
            start_time=format_time(s.start_time),
            end_time=format_time(s.end_time),
            is_working=s.is_working,
        )
        for s in sorted(p.schedule, key=lambda x: x.day_of_week)
    ]
    return ProviderDetailResponse(
        id=p.id,
        full_name=p.full_name,
        phone=p.phone,
        bio=p.bio,
        address=p.address,
        avg_rating=p.avg_rating,
        review_count=p.review_count,
        services=[_service_resp(s) for s in p.services if s.is_active],
        status_today=status,
        next_free_slot=next_slot,
        schedule=schedule,
        verification_status=p.verification_status,
    )


@router.post("/my/busy", response_model=BusyBlockResponse, status_code=201)
async def add_busy_block(
    data: BusyBlockCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    provider = await _get_my_provider(db, current_user)
    block = ProviderBusyBlock(
        provider_id=provider.id,
        block_date=data.block_date,
        start_time=parse_time(data.start_time),
        end_time=parse_time(data.end_time),
        reason=data.reason,
        note=data.note,
    )
    db.add(block)
    await db.flush()
    return BusyBlockResponse(
        id=block.id,
        block_date=block.block_date,
        start_time=format_time(block.start_time),
        end_time=format_time(block.end_time),
        reason=block.reason,
        note=block.note,
    )


@router.get("/my/busy", response_model=list[BusyBlockResponse])
async def list_busy_blocks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    provider = await _get_my_provider(db, current_user)
    result = await db.execute(
        select(ProviderBusyBlock)
        .where(ProviderBusyBlock.provider_id == provider.id)
        .order_by(ProviderBusyBlock.block_date.desc())
        .limit(100)
    )
    return [
        BusyBlockResponse(
            id=b.id,
            block_date=b.block_date,
            start_time=format_time(b.start_time),
            end_time=format_time(b.end_time),
            reason=b.reason,
            note=b.note,
        )
        for b in result.scalars().all()
    ]


@router.delete("/my/busy/{block_id}")
async def delete_busy_block(
    block_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    provider = await _get_my_provider(db, current_user)
    result = await db.execute(
        select(ProviderBusyBlock).where(
            ProviderBusyBlock.id == block_id,
            ProviderBusyBlock.provider_id == provider.id,
        )
    )
    block = result.scalar_one_or_none()
    if not block:
        raise HTTPException(404)
    await db.delete(block)
    return {"status": "deleted"}


@router.post("/my/services", response_model=ProviderServiceResponse, status_code=201)
async def add_my_service(
    data: ServiceItemInput,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    provider = await _get_my_provider(db, current_user)
    svc = ProviderService(
        provider_id=provider.id,
        service_type=data.service_type,
        name=data.name,
        description=data.description,
        duration_minutes=data.duration_minutes,
        price=data.price,
    )
    db.add(svc)
    await db.flush()
    return _service_resp(svc)


@router.patch("/my/schedule")
async def update_my_schedule(
    data: UpdateScheduleRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    provider = await _get_my_provider(db, current_user)

    await db.execute(delete(ProviderSchedule).where(ProviderSchedule.provider_id == provider.id))
    await db.flush()

    for sch in data.schedule:
        db.add(
            ProviderSchedule(
                provider_id=provider.id,
                day_of_week=sch.day_of_week,
                start_time=parse_time(sch.start_time),
                end_time=parse_time(sch.end_time),
                is_working=sch.is_working,
            )
        )
    return {"status": "ok"}


@router.get("/my/appointments", response_model=list[AppointmentResponse])
async def my_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    provider = await _get_my_provider(db, current_user)

    appts = await db.execute(
        select(ServiceAppointment)
        .options(selectinload(ServiceAppointment.service))
        .where(ServiceAppointment.provider_id == provider.id)
        .order_by(ServiceAppointment.appointment_date.desc())
        .limit(50)
    )
    return [
        AppointmentResponse(
            id=a.id,
            provider_name=provider.full_name,
            service_name=a.service.name if a.service else "—",
            appointment_date=a.appointment_date,
            start_time=format_time(a.start_time),
            end_time=format_time(a.end_time),
            status=a.status,
            client_name=a.client_name,
        )
        for a in appts.scalars().all()
    ]
