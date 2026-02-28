from aiogram import Router, F, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID, PAYMENT_CARD
from database import (
    get_stats,
    get_all_user_ids,
    get_all_services_admin,
    add_service,
    delete_service,
    update_service_price,
    get_service_by_id,
    add_portfolio_item,
    get_all_portfolio_brief,
    delete_portfolio_item,
    update_order_status,
    get_order_user_id,
    get_user_language,
    get_active_orders,
    get_order_details,
    set_order_price_and_status,
    delete_order,
)
from handlers.users import PaymentStates
from keyboards.inline import (
    admin_services_menu_kb,
    admin_services_list_kb,
    admin_portfolio_menu_kb,
    admin_portfolio_delete_list_kb,
)
from locales.texts import get_text


# Маршрутизатор админ-панели.
admin_router = Router()


class BroadcastStates(StatesGroup):
    waiting_for_broadcast_text = State()


class AddServiceStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()


class EditServicePriceStates(StatesGroup):
    waiting_for_price = State()


class AddPortfolioStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_title_ru = State()
    waiting_for_title_tj = State()
    waiting_for_description_ru = State()
    waiting_for_description_tj = State()
    waiting_for_demo_link = State()


class AdminOrderStates(StatesGroup):
    admin_set_price = State()
    admin_deliver_work = State()


def _admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🗂 Управление услугами", callback_data="admin_services")],
            [InlineKeyboardButton(text="🖼 Управление портфолио", callback_data="admin_portfolio")],
            [InlineKeyboardButton(text="📋 Управление заказами", callback_data="admin_orders_manage")],
        ]
    )


def _review_stars_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 ⭐️", callback_data=f"review_star:{order_id}:1"),
                InlineKeyboardButton(text="2 ⭐️", callback_data=f"review_star:{order_id}:2"),
                InlineKeyboardButton(text="3 ⭐️", callback_data=f"review_star:{order_id}:3"),
                InlineKeyboardButton(text="4 ⭐️", callback_data=f"review_star:{order_id}:4"),
                InlineKeyboardButton(text="5 ⭐️", callback_data=f"review_star:{order_id}:5"),
            ]
        ]
    )


def _status_label(status: str) -> str:
    labels = {
        "new": "new",
        "awaiting_payment": "awaiting_payment",
        "verifying_receipt": "verifying_receipt",
        "in_progress": "in_progress",
        "completed": "completed",
        "cancelled": "cancelled",
    }
    return labels.get(status, status)


def _active_orders_kb(orders: list[tuple[int, int, str, str]]) -> InlineKeyboardMarkup:
    buttons = []
    for order_id, _, _, status in orders:
        buttons.append(
            [InlineKeyboardButton(text=f"Order #{order_id} | {_status_label(status)}", callback_data=f"admin_order_view:{order_id}")]
        )
    buttons.append([InlineKeyboardButton(text="← Назад в админку", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _order_details_kb(order_id: int, user_id: int, status: str) -> InlineKeyboardMarkup:
    rows = []
    if status == "new":
        rows.append([InlineKeyboardButton(text="💬 Написать клиенту", url=f"tg://user?id={user_id}")])
        rows.append([InlineKeyboardButton(text="💸 Запросить оплату", callback_data=f"admin_order_request_payment:{order_id}")])
    elif status == "verifying_receipt":
        rows.append(
            [
                InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"admin_receipt_confirm_order:{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить чек", callback_data=f"admin_receipt_reject_order:{order_id}"),
            ]
        )
    elif status == "in_progress":
        rows.append([InlineKeyboardButton(text="🏁 Сдать работу", callback_data=f"admin_order_deliver:{order_id}")])

    rows.append([InlineKeyboardButton(text="⬅️ Назад к заказам", callback_data="admin_orders_manage")])
    rows.append([InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"admin_order_cancel:{order_id}")])
    if status in {"completed", "cancelled"}:
        rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_order_delete:{order_id}")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render_order_details(callback: CallbackQuery, order_id: int) -> None:
    order = await get_order_details(order_id)
    if not order:
        await callback.message.edit_text("Заказ не найден.", reply_markup=_admin_panel_kb())
        return

    oid, user_id, service_type, description, budget, agreed_price, status = order
    waiting_text = "\n\n⏳ Waiting for client to pay." if status == "awaiting_payment" else ""
    text = (
        f"📦 <b>Заказ #{oid}</b>\n\n"
        f"👤 Клиент ID: <code>{user_id}</code>\n"
        f"🧩 Услуга: {service_type}\n"
        f"📝 Описание:\n<blockquote>{description}</blockquote>\n"
        f"💰 Бюджет клиента: {budget}\n"
        f"🤝 Agreed price: {agreed_price}\n"
        f"📍 Статус: <code>{status}</code>{waiting_text}"
    )
    await callback.message.edit_text(text, reply_markup=_order_details_kb(order_id=oid, user_id=user_id, status=status))


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """
    Команда /admin — вход в админ-панель.
    Доступна только администратору.
    """
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "🔐 Админ-панель.\n\nВыберите действие:",
        reply_markup=_admin_panel_kb(),
    )


@admin_router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery) -> None:
    """
    Кнопка «Статистика» в админ-панели.
    """
    if callback.from_user.id != ADMIN_ID:
        return

    users_count, orders_count = await get_stats()
    text = (
        "📊 Статистика бота:\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"🛒 Заказов: {orders_count}"
    )
    await callback.message.edit_text(text, reply_markup=_admin_panel_kb())
    await callback.answer()


@admin_router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Кнопка «Рассылка» в админ-панели.
    Запускает FSM рассылки.
    """
    if callback.from_user.id != ADMIN_ID:
        return

    await state.set_state(BroadcastStates.waiting_for_broadcast_text)
    await callback.message.edit_text(
        "📢 Введите текст рассылки одним сообщением.\n\n"
        "Сообщение будет отправлено всем пользователям бота.",
        reply_markup=None,
    )
    await callback.answer()


@admin_router.message(BroadcastStates.waiting_for_broadcast_text)
async def admin_broadcast_send(message: Message, state: FSMContext) -> None:
    """
    Приём текста рассылки и её отправка всем пользователям.
    """
    if message.from_user.id != ADMIN_ID:
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Пожалуйста, отправьте непустой текст для рассылки.")
        return

    user_ids = await get_all_user_ids()

    from aiogram import Bot
    from config import BOT_TOKEN

    bot = Bot(token=BOT_TOKEN)
    sent = 0
    failed = 0

    # Отправляем сообщения по очереди, игнорируя ошибки доставки.
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception:
            failed += 1

    await bot.session.close()
    await state.clear()

    await message.answer(
        "✅ Рассылка завершена.\n\n"
        f"Отправлено: {sent}\n"
        f"Не доставлено: {failed}"
    )


# === Управление услугами ===


@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery) -> None:
    """Возврат в админ-панель."""
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text(
        "🔐 Админ-панель.\n\nВыберите действие:",
        reply_markup=_admin_panel_kb(),
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_services")
async def admin_services(callback: CallbackQuery) -> None:
    """Меню управления услугами."""
    if callback.from_user.id != ADMIN_ID:
        return

    services = await get_all_services_admin()
    if not services:
        text = "🗂 <b>Управление услугами</b>\n\nПока нет услуг. Добавьте первую:"
        kb = admin_services_menu_kb()
    else:
        text = "🗂 <b>Управление услугами</b>\n\nСписок услуг (🗑 удалить, ✏️ изменить цену):"
        kb = admin_services_list_kb(services)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@admin_router.callback_query(F.data == "admin_svc_add")
async def admin_svc_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало FSM добавления услуги."""
    if callback.from_user.id != ADMIN_ID:
        return

    await state.set_state(AddServiceStates.waiting_for_name)
    await callback.message.edit_text(
        "➕ <b>Добавление услуги</b>\n\nШаг 1/3: Введите название услуги:",
        reply_markup=None,
    )
    await callback.answer()


@admin_router.message(AddServiceStates.waiting_for_name)
async def admin_svc_add_name(message: Message, state: FSMContext) -> None:
    """Приём названия услуги."""
    if message.from_user.id != ADMIN_ID:
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("Введите непустое название.")
        return
    await state.update_data(name=name)
    await state.set_state(AddServiceStates.waiting_for_description)
    await message.answer("Шаг 2/3: Введите описание услуги:")


@admin_router.message(AddServiceStates.waiting_for_description)
async def admin_svc_add_description(message: Message, state: FSMContext) -> None:
    """Приём описания услуги."""
    if message.from_user.id != ADMIN_ID:
        return
    desc = (message.text or "").strip()
    if not desc:
        await message.answer("Введите непустое описание.")
        return
    await state.update_data(description=desc)
    await state.set_state(AddServiceStates.waiting_for_price)
    await message.answer(
        "Шаг 3/3: Введите цену в TJS (целое число).\n\n"
        "Или отправьте 0, если цена Договорная."
    )


@admin_router.message(AddServiceStates.waiting_for_price)
async def admin_svc_add_price(message: Message, state: FSMContext) -> None:
    """Приём цены и сохранение услуги."""
    if message.from_user.id != ADMIN_ID:
        return
    try:
        price = int((message.text or "").strip())
        if price < 0:
            raise ValueError("negative")
    except ValueError:
        await message.answer("Введите корректное целое число (цена в TJS).")
        return

    data = await state.get_data()
    name = data["name"]
    description = data["description"]

    await add_service(name=name, description=description, price_tjs=price)
    await state.clear()

    price_display = "Договорная" if price == 0 else f"{price} TJS"
    await message.answer(f"✅ Услуга «{name}» добавлена. Цена: {price_display}.")


@admin_router.callback_query(F.data.startswith("admin_svc_del:"))
async def admin_svc_del(callback: CallbackQuery) -> None:
    """Удаление услуги."""
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        service_id = int(callback.data.split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка.", show_alert=True)
        return

    await delete_service(service_id)
    services = await get_all_services_admin()
    if not services:
        text = "🗂 <b>Управление услугами</b>\n\nУслуга удалена. Пока нет услуг."
        kb = admin_services_menu_kb()
    else:
        text = "🗂 <b>Управление услугами</b>\n\nУслуга удалена. Список услуг:"
        kb = admin_services_list_kb(services)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Услуга удалена.")


@admin_router.callback_query(F.data.startswith("admin_svc_edit:"))
async def admin_svc_edit_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало FSM редактирования цены услуги."""
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        service_id = int(callback.data.split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка.", show_alert=True)
        return

    service = await get_service_by_id(service_id)
    if not service:
        await callback.answer("Услуга не найдена.", show_alert=True)
        return

    await state.update_data(service_id=service_id, service_name=service[1])
    await state.set_state(EditServicePriceStates.waiting_for_price)
    curr_price = "Договорная" if service[3] == 0 else f"{service[3]} TJS"
    await callback.message.edit_text(
        f"✏️ Редактирование цены: <b>{service[1]}</b>\n\n"
        f"Текущая цена: {curr_price}\n\n"
        "Введите новую цену в TJS (целое число). Отправьте 0 для «Договорная»:",
        reply_markup=None,
    )
    await callback.answer()


@admin_router.message(EditServicePriceStates.waiting_for_price)
async def admin_svc_edit_price(message: Message, state: FSMContext) -> None:
    """Приём новой цены и обновление."""
    if message.from_user.id != ADMIN_ID:
        return
    try:
        price = int((message.text or "").strip())
        if price < 0:
            raise ValueError("negative")
    except ValueError:
        await message.answer("Введите корректное целое число (цена в TJS).")
        return

    data = await state.get_data()
    service_id = data["service_id"]
    await update_service_price(service_id, price)
    await state.clear()

    price_display = "Договорная" if price == 0 else f"{price} TJS"
    await message.answer(f"✅ Цена обновлена: {price_display}.")


# === Управление портфолио ===


@admin_router.callback_query(F.data == "admin_portfolio")
async def admin_portfolio_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Меню управления портфолио."""
    if callback.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await callback.message.edit_text(
        f"{get_text('ru', 'admin_portfolio_menu')}\n\nВыберите действие:",
        reply_markup=admin_portfolio_menu_kb(),
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_portfolio_add")
async def admin_portfolio_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Старт FSM добавления кейса портфолио."""
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AddPortfolioStates.waiting_for_photo)
    await callback.message.edit_text(get_text("ru", "admin_portfolio_prompt_photo"), reply_markup=None)
    await callback.answer()


@admin_router.message(AddPortfolioStates.waiting_for_photo)
async def admin_portfolio_photo(message: Message, state: FSMContext) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    if not message.photo:
        await message.answer(get_text("ru", "admin_portfolio_need_photo"))
        return

    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(AddPortfolioStates.waiting_for_title_ru)
    await message.answer(get_text("ru", "admin_portfolio_prompt_title_ru"))


@admin_router.message(AddPortfolioStates.waiting_for_title_ru)
async def admin_portfolio_title_ru(message: Message, state: FSMContext) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    value = (message.text or "").strip()
    if not value:
        await message.answer(get_text("ru", "admin_portfolio_prompt_title_ru"))
        return

    await state.update_data(title_ru=value)
    await state.set_state(AddPortfolioStates.waiting_for_title_tj)
    await message.answer(get_text("ru", "admin_portfolio_prompt_title_tj"))


@admin_router.message(AddPortfolioStates.waiting_for_title_tj)
async def admin_portfolio_title_tj(message: Message, state: FSMContext) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    value = (message.text or "").strip()
    if not value:
        await message.answer(get_text("ru", "admin_portfolio_prompt_title_tj"))
        return

    await state.update_data(title_tj=value)
    await state.set_state(AddPortfolioStates.waiting_for_description_ru)
    await message.answer(get_text("ru", "admin_portfolio_prompt_desc_ru"))


@admin_router.message(AddPortfolioStates.waiting_for_description_ru)
async def admin_portfolio_description_ru(message: Message, state: FSMContext) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    value = (message.text or "").strip()
    if not value:
        await message.answer(get_text("ru", "admin_portfolio_prompt_desc_ru"))
        return

    await state.update_data(description_ru=value)
    await state.set_state(AddPortfolioStates.waiting_for_description_tj)
    await message.answer(get_text("ru", "admin_portfolio_prompt_desc_tj"))


@admin_router.message(AddPortfolioStates.waiting_for_description_tj)
async def admin_portfolio_description_tj(message: Message, state: FSMContext) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    value = (message.text or "").strip()
    if not value:
        await message.answer(get_text("ru", "admin_portfolio_prompt_desc_tj"))
        return

    await state.update_data(description_tj=value)
    await state.set_state(AddPortfolioStates.waiting_for_demo_link)
    await message.answer(get_text("ru", "admin_portfolio_prompt_demo"))


@admin_router.message(AddPortfolioStates.waiting_for_demo_link)
async def admin_portfolio_demo_link(message: Message, state: FSMContext) -> None:
    if message.from_user.id != ADMIN_ID:
        return

    raw_demo = (message.text or "").strip()
    if raw_demo.lower() in {"-", "нет", "no", "none", "- / нет", "-/нет"}:
        demo_link = None
    else:
        demo_link = raw_demo if raw_demo else None

    data = await state.get_data()
    await add_portfolio_item(
        title_ru=data["title_ru"],
        title_tj=data["title_tj"],
        description_ru=data["description_ru"],
        description_tj=data["description_tj"],
        photo_file_id=data["photo_file_id"],
        demo_link=demo_link,
    )
    await state.clear()

    await message.answer(
        get_text("ru", "admin_portfolio_saved"),
        reply_markup=admin_portfolio_menu_kb(),
    )


@admin_router.callback_query(F.data == "admin_portfolio_delete")
async def admin_portfolio_delete_menu(callback: CallbackQuery) -> None:
    """Показывает список кейсов портфолио для удаления."""
    if callback.from_user.id != ADMIN_ID:
        return

    items = await get_all_portfolio_brief()
    if not items:
        await callback.message.edit_text(
            get_text("ru", "admin_portfolio_empty"),
            reply_markup=admin_portfolio_menu_kb(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "Выберите кейс для удаления:",
        reply_markup=admin_portfolio_delete_list_kb(items),
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_portfolio_del:"))
async def admin_portfolio_delete_item(callback: CallbackQuery) -> None:
    """Удаляет кейс портфолио по ID."""
    if callback.from_user.id != ADMIN_ID:
        return

    try:
        item_id = int(callback.data.split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка ID", show_alert=True)
        return

    await delete_portfolio_item(item_id)
    items = await get_all_portfolio_brief()

    if not items:
        await callback.message.edit_text(
            get_text("ru", "admin_portfolio_empty"),
            reply_markup=admin_portfolio_menu_kb(),
        )
    else:
        await callback.message.edit_text(
            f"{get_text('ru', 'admin_portfolio_deleted')} Выберите следующий кейс:",
            reply_markup=admin_portfolio_delete_list_kb(items),
        )

    await callback.answer(get_text("ru", "admin_portfolio_deleted"))


@admin_router.callback_query(F.data == "admin_orders_manage")
async def admin_orders_manage(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    orders = await get_active_orders()
    if not orders:
        await callback.message.edit_text(
            "📋 Активных заказов нет.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="← Назад в админку", callback_data="admin_back")]]
            ),
        )
        await callback.answer()
        return

    await callback.message.edit_text("📋 Управление заказами\n\nВыберите заказ:", reply_markup=_active_orders_kb(orders))
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_order_view:"))
async def admin_order_view(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        order_id = int((callback.data or "").split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    await _render_order_details(callback, order_id)
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_order_cancel:"))
async def admin_order_cancel(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        order_id = int((callback.data or "").split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    client_id = await get_order_user_id(order_id)
    if not client_id:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    await update_order_status(order_id, "cancelled")
    await callback.bot.send_message(chat_id=client_id, text="❌ Ваш заказ был отменён администратором.")
    await _render_order_details(callback, order_id)
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_order_delete:"))
async def admin_order_delete(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        order_id = int((callback.data or "").split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    order = await get_order_details(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    status = order[6]
    if status not in {"completed", "cancelled"}:
        await callback.answer("Удаление доступно только для completed/cancelled", show_alert=True)
        return

    await delete_order(order_id)
    orders = await get_active_orders()
    if orders:
        await callback.message.edit_text("📋 Управление заказами\n\nВыберите заказ:", reply_markup=_active_orders_kb(orders))
    else:
        await callback.message.edit_text(
            "📋 Активных заказов нет.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="← Назад в админку", callback_data="admin_back")]]
            ),
        )
    await callback.answer("Заказ удалён из БД")


@admin_router.callback_query(F.data.startswith("admin_order_request_payment:"))
async def admin_order_request_payment(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        order_id = int((callback.data or "").split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    await state.set_state(AdminOrderStates.admin_set_price)
    await state.update_data(
        admin_order_id=order_id,
        admin_chat_id=callback.message.chat.id,
        admin_message_id=callback.message.message_id,
    )
    await callback.message.edit_text(
        f"💸 Введите согласованную цену для заказа <code>ORD-{order_id:04d}</code> (целое число):"
    )
    await callback.answer()


@admin_router.message(AdminOrderStates.admin_set_price)
async def admin_set_price(message: Message, state: FSMContext) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    try:
        agreed_price = int((message.text or "").strip())
        if agreed_price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму (целое число больше 0).")
        return

    data = await state.get_data()
    order_id = int(data["admin_order_id"])
    chat_id = int(data["admin_chat_id"])
    message_id = int(data["admin_message_id"])

    order = await get_order_details(order_id)
    if not order:
        await state.clear()
        await message.answer("Заказ не найден.")
        return

    _, client_id, _, _, _, _, _ = order
    await set_order_price_and_status(order_id=order_id, agreed_price=agreed_price, status="awaiting_payment")

    client_text = (
        "🤝 Мы согласовали детали вашего заказа!\n"
        f"💰 К оплате: {agreed_price}\n"
        f"💳 Реквизиты для оплаты: {PAYMENT_CARD}\n"
        "Пожалуйста, совершите перевод и нажмите кнопку ниже."
    )
    await message.bot.send_message(
        chat_id=client_id,
        text=client_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"client_paid:{order_id}")]
            ]
        ),
    )

    await state.clear()
    await message.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=f"✅ Цена установлена. Заказ <code>ORD-{order_id:04d}</code> переведён в awaiting_payment.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="↩️ Открыть заказ", callback_data=f"admin_order_view:{order_id}")]]
        ),
    )


@admin_router.callback_query(F.data.startswith("admin_receipt_confirm:"))
async def admin_receipt_confirm(callback: CallbackQuery, dispatcher: Dispatcher) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    parts = (callback.data or "").split(":")
    try:
        order_id = int(parts[1])
        client_id = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные чека.", show_alert=True)
        return

    await update_order_status(order_id, "in_progress")
    client_lang = await get_user_language(client_id) or "ru"
    await callback.bot.send_message(chat_id=client_id, text="Оплата получена. Мы начали работу!")

    receipt_state = await dispatcher.fsm.get_context(
        bot=callback.bot,
        chat_id=client_id,
        user_id=client_id,
    )
    await receipt_state.clear()

    await callback.message.edit_caption(
        caption=f"✅ Оплата подтверждена. Заказ <code>ORD-{order_id:04d}</code> переведен в работу.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏁 Сдать работу", callback_data=f"admin_order_deliver:{order_id}")]]
        ),
    )
    await callback.answer("Оплата подтверждена.")


@admin_router.callback_query(F.data.startswith("admin_receipt_reject:"))
async def admin_receipt_reject(callback: CallbackQuery, dispatcher: Dispatcher) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    parts = (callback.data or "").split(":")
    try:
        order_id = int(parts[1])
        client_id = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("Некорректные данные чека.", show_alert=True)
        return

    await update_order_status(order_id, "awaiting_payment")
    receipt_state = await dispatcher.fsm.get_context(
        bot=callback.bot,
        chat_id=client_id,
        user_id=client_id,
    )
    await receipt_state.set_state(PaymentStates.client_send_receipt)
    await receipt_state.update_data(receipt_order_id=order_id)

    await callback.bot.send_message(
        chat_id=client_id,
        text="❌ Ваш чек не принят. Пожалуйста, проверьте данные и отправьте правильный скриншот оплаты.",
    )
    await callback.message.edit_caption(
        caption=f"❌ Чек отклонён администратором. Заказ <code>ORD-{order_id:04d}</code>.",
        reply_markup=None,
    )
    await callback.answer("Чек отклонён.")


@admin_router.callback_query(F.data.startswith("admin_receipt_confirm_order:"))
async def admin_receipt_confirm_from_order(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        order_id = int((callback.data or "").split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    order = await get_order_details(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    _, client_id, _, _, _, _, _ = order

    await update_order_status(order_id, "in_progress")
    await callback.bot.send_message(chat_id=client_id, text="Оплата получена. Мы начали работу!")
    await _render_order_details(callback, order_id)
    await callback.answer("Оплата подтверждена")


@admin_router.callback_query(F.data.startswith("admin_receipt_reject_order:"))
async def admin_receipt_reject_from_order(callback: CallbackQuery, dispatcher: Dispatcher) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        order_id = int((callback.data or "").split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    order = await get_order_details(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    _, client_id, _, _, _, _, _ = order

    await update_order_status(order_id, "awaiting_payment")
    receipt_state = await dispatcher.fsm.get_context(
        bot=callback.bot,
        chat_id=client_id,
        user_id=client_id,
    )
    await receipt_state.set_state(PaymentStates.client_send_receipt)
    await receipt_state.update_data(receipt_order_id=order_id)

    await callback.bot.send_message(
        chat_id=client_id,
        text="❌ Ваш чек не принят. Пожалуйста, проверьте данные и отправьте правильный скриншот оплаты.",
    )
    await _render_order_details(callback, order_id)
    await callback.answer("Чек отклонён")


@admin_router.callback_query(F.data.startswith("admin_order_deliver:"))
async def admin_order_deliver_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id != ADMIN_ID:
        return
    try:
        order_id = int((callback.data or "").split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    await state.set_state(AdminOrderStates.admin_deliver_work)
    await state.update_data(
        admin_order_id=order_id,
        admin_chat_id=callback.message.chat.id,
        admin_message_id=callback.message.message_id,
    )
    await callback.message.edit_text(
        f"🏁 Отправьте финальный текст для клиента по заказу <code>ORD-{order_id:04d}</code>."
    )
    await callback.answer()


@admin_router.message(AdminOrderStates.admin_deliver_work)
async def admin_order_deliver_finish(message: Message, state: FSMContext) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    delivery_text = (message.text or "").strip()
    if not delivery_text:
        await message.answer("Отправьте текст результата для клиента.")
        return

    data = await state.get_data()
    order_id = int(data["admin_order_id"])
    chat_id = int(data["admin_chat_id"])
    message_id = int(data["admin_message_id"])

    order = await get_order_details(order_id)
    if not order:
        await state.clear()
        await message.answer("Заказ не найден.")
        return

    _, client_id, _, _, _, _, _ = order
    await message.bot.send_message(
        chat_id=client_id,
        text=f"✅ Работа по заказу <code>ORD-{order_id:04d}</code> готова!\n\n{delivery_text}",
    )
    await update_order_status(order_id, "completed")

    client_lang = await get_user_language(client_id) or "ru"
    await message.bot.send_message(
        chat_id=client_id,
        text=get_text(client_lang, "review_request"),
        reply_markup=_review_stars_kb(order_id),
    )

    await state.clear()
    await message.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=f"🏁 Заказ <code>ORD-{order_id:04d}</code> сдан клиенту и закрыт.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📋 К заказам", callback_data="admin_orders_manage")]]
        ),
    )


@admin_router.callback_query(F.data == "admin_noop")
async def admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()


