from aiogram import Router, F
from aiogram.types import CallbackQuery
import html

from config import ADMIN_ID
from database import get_user_language, get_user_orders, update_order_status
from keyboards.inline import profile_orders_kb, language_kb
from locales.texts import get_text


profile_router = Router()


STATUS_LABELS = {
    "new": "🆕 Новый",
    "awaiting_payment": "💸 Ожидает оплату",
    "verifying_receipt": "🧾 Проверка чека",
    "in_progress": "🛠 В работе",
    "completed": "✅ Выполнен",
    "cancelled": "❌ Отменён",
}


async def _render_orders(callback: CallbackQuery) -> None:
    """Helper to edit message with the user's order list in a nicely formatted style."""
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    orders = await get_user_orders(callback.from_user.id)

    title = get_text(user_lang, "order_list_title")
    if not orders:
        text = f"{title}\n\n<em>({get_text(user_lang, 'no_services')})</em>"
    else:
        parts = [f"<b>{title}</b>\n"]
        for oid, otype, status in orders:
            code = f"ORD-{oid:04d}"
            status_text = STATUS_LABELS.get(status, status)
            parts.append(
                f"<b>{code}</b>\n"
                f"Тип: {html.escape(otype)}\n"
                f"Статус: {html.escape(status_text)}\n"
                "\n"
            )
        text = "".join(parts)

    await callback.message.edit_text(
        text,
        reply_markup=profile_orders_kb(user_lang, orders),
        parse_mode="HTML",
    )
    await callback.answer()


@profile_router.callback_query(F.data == "profile_orders")
async def view_orders(callback: CallbackQuery) -> None:
    """Показать список заказов пользователя."""
    await _render_orders(callback)


@profile_router.callback_query(F.data.startswith("profile_cancel:"))
async def cancel_order(callback: CallbackQuery) -> None:
    """Отмена заказа пользователем, уведомление админа и обновление списка."""
    try:
        order_id = int(callback.data.split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID заказа.", show_alert=True)
        return

    await update_order_status(order_id, "cancelled")

    await callback.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"⚠️ Пользователь {callback.from_user.full_name} (ID: {callback.from_user.id}) "
            f"отменил заказ <code>ORD-{order_id:04d}</code>."
        ),
    )

    # перерисовываем список заказов
    await _render_orders(callback)


@profile_router.callback_query(F.data == "profile_settings")
async def change_language(callback: CallbackQuery) -> None:
    """Переход в клавиатуру выбора языка (повторно)."""
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    # просто покажем клавиатуру выбора языка снова
    await callback.message.edit_text(get_text(user_lang, "welcome"), reply_markup=language_kb())


# Note: language_chosen from users.router handles lang_ru/lang_tg callbacks for language updates
