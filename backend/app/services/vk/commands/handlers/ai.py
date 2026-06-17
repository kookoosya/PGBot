"""AI assistant commands."""

from app.services.site_urls import public_site_url
from app.services.vk.ai_history import clear_ai_history
from app.services.vk.ai_mode import enter_ai_mode
from app.services.vk.context import VkRouteContext
from app.services.vk.helpers import AI_EXAMPLES, send_ai, send_welcome
from app.services.vk.messages import ai_enter_text, box


async def handle_ai_enter(ctx: VkRouteContext) -> None:
    await enter_ai_mode(ctx.db, ctx.peer_id)
    await send_ai(ctx, ai_enter_text())


async def handle_ai_examples(ctx: VkRouteContext) -> None:
    await send_ai(ctx, box("Примеры для ИИ", AI_EXAMPLES))


async def handle_ai_images(ctx: VkRouteContext) -> None:
    await send_ai(
        ctx,
        box(
            "Генерация картинок",
            f"На сайте: {public_site_url()}/ai → вкладка «Картинки»\n\n"
            "Модели: Flux, Turbo, Nano Banana.\n"
            "Пример: «Уютная изба в снегу» или «Усадьба на закате».\n"
            "Опишите сцену на русском — скачайте результат.",
        ),
    )


async def handle_ai_exit(ctx: VkRouteContext) -> None:
    await clear_ai_history(ctx.db, ctx.peer_id)
    await send_welcome(ctx, "Вернулись в меню 🪶")
