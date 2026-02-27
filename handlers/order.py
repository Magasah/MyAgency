import asyncio
import html

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.utils.chat_action import ChatActionSender

from config import ADMIN_ID, EXCHANGE_RATE_TJS_TO_RUB
from database import add_order, get_service_by_id, get_user_language, get_all_services
from keyboards.inline import main_menu_kb, order_confirm_kb, order_step_cancel_kb
from locales.texts import get_text


order_router = Router()


class OrderStates(StatesGroup):
    choosing_type = State()
    bot_name = State()
    core_features = State()
    references = State()
    client_budget = State()
    contact_phone = State()
    awaiting_confirmation = State()


class SupportStates(StatesGroup):
    waiting_for_support_message = State()


def _format_price_for_summary(price_tjs: int, lang: str) -> str:
    if price_tjs == 0:
        return get_text(lang, "negotiable")
    if lang in ("tg", "tj"):
        return f"{price_tjs} TJS"
    price_rub = int(price_tjs * EXCHANGE_RATE_TJS_TO_RUB)
    return f"{price_rub} ₽"


def _build_summary_text(
    service_name: str,
    price_str: str,
    bot_name: str,
    core_features: str,
    references: str,
    client_budget: str,
    lang: str,
) -> str:
    t = lambda k: get_text(lang, k)
    return (
        f"{t('summary_title')}\n\n"
        f"{t('summary_type')}: {service_name}\n"
        f"{t('summary_price')}: {price_str}\n"
        f"{t('summary_bot_name')}: {bot_name}\n"
        f"{t('summary_features')}: {core_features}\n"
        f"{t('summary_references')}: {references}\n"
        f"{t('summary_budget')}: {client_budget}\n\n"
        f"{t('summary_confirm')}"
    )


@order_router.callback_query(OrderStates.choosing_type, F.data.startswith("order_svc:"))
async def order_service_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        service_id = int(callback.data.split(":", maxsplit=1)[1])
    except (ValueError, IndexError):
        await callback.answer(get_text("ru", "error_service"), show_alert=True)
        return

    service = await get_service_by_id(service_id)
    if not service:
        await callback.answer(get_text("ru", "error_service_not_found"), show_alert=True)
        return

    svc_id, name, _, price_tjs = service
    data = await state.get_data()
    user_lang = data.get("user_lang", "ru")

    await state.update_data(
        order_type=name,
        service_id=svc_id,
        price_tjs=price_tjs,
        edit_chat_id=callback.message.chat.id,
        edit_message_id=callback.message.message_id,
    )
    await state.set_state(OrderStates.bot_name)

    await callback.message.edit_text(
        get_text(user_lang, "step_bot_name"),
        reply_markup=order_step_cancel_kb(user_lang),
    )
    await callback.answer()


@order_router.callback_query(StateFilter(OrderStates), F.data == "order_cancel")
async def order_cancel_anywhere(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user_lang = data.get("user_lang", "ru")
    await state.clear()
    await callback.message.edit_text(
        get_text(user_lang, "order_cancelled"),
        reply_markup=main_menu_kb(user_lang),
    )
    await callback.answer()


@order_router.message(OrderStates.bot_name)
async def order_bot_name_received(message: Message, state: FSMContext) -> None:
    bot_name = (message.text or "").strip()
    data = await state.get_data()
    user_lang = data.get("user_lang", "ru")
    if not bot_name:
        await message.answer(get_text(user_lang, "enter_bot_name"))
        return

    chat_id = data["edit_chat_id"]
    msg_id = data["edit_message_id"]

    await state.update_data(bot_name=bot_name)
    await state.set_state(OrderStates.core_features)

    await message.bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=get_text(user_lang, "step_core_features"),
        reply_markup=order_step_cancel_kb(user_lang),
    )


@order_router.message(OrderStates.core_features)
async def order_core_features_received(message: Message, state: FSMContext) -> None:
    core_features = (message.text or "").strip()
    data = await state.get_data()
    user_lang = data.get("user_lang", "ru")
    if not core_features:
        await message.answer(get_text(user_lang, "enter_features"))
        return

    chat_id = data["edit_chat_id"]
    msg_id = data["edit_message_id"]

    await state.update_data(core_features=core_features)
    await state.set_state(OrderStates.references)

    await message.bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=get_text(user_lang, "step_references"),
        reply_markup=order_step_cancel_kb(user_lang),
    )


@order_router.message(OrderStates.references)
async def order_references_received(message: Message, state: FSMContext) -> None:
    references = (message.text or "").strip()
    data = await state.get_data()
    user_lang = data.get("user_lang", "ru")
    if not references:
        await message.answer(get_text(user_lang, "enter_references"))
        return

    chat_id = data["edit_chat_id"]
    msg_id = data["edit_message_id"]

    await state.update_data(references=references)
    await state.set_state(OrderStates.client_budget)

    await message.bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=get_text(user_lang, "step_budget"),
        reply_markup=order_step_cancel_kb(user_lang),
    )


@order_router.message(OrderStates.client_budget)
async def order_client_budget_received(message: Message, state: FSMContext) -> None:
    client_budget = (message.text or "").strip()
    data = await state.get_data()
    user_lang = data.get("user_lang", "ru")
    if not client_budget:
        await message.answer(get_text(user_lang, "enter_budget"))
        return

    chat_id = data["edit_chat_id"]
    msg_id = data["edit_message_id"]

    await state.update_data(client_budget=client_budget)
    await state.set_state(OrderStates.contact_phone)

    await message.bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=get_text(user_lang, "step_contact_phone"),
        reply_markup=order_step_cancel_kb(user_lang),
    )


@order_router.message(OrderStates.contact_phone)
async def order_contact_phone_received(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    data = await state.get_data()
    user_lang = data.get("user_lang", "ru")
    if not phone:
        await message.answer(get_text(user_lang, "enter_phone"))
        return

    order_type = data.get("order_type", "")
    price_tjs = data.get("price_tjs", 0)
    bot_name = data.get("bot_name", "")
    core_features = data.get("core_features", "")
    references = data.get("references", "")
    client_budget = data.get("client_budget", "")

    await state.update_data(contact_phone=phone)
    await state.set_state(OrderStates.awaiting_confirmation)

    price_str = _format_price_for_summary(price_tjs, user_lang)
    summary = _build_summary_text(
        service_name=order_type,
        price_str=price_str,
        bot_name=bot_name,
        core_features=core_features,
        references=references,
        client_budget=client_budget,
        lang=user_lang,
    )

    chat_id = data["edit_chat_id"]
    msg_id = data["edit_message_id"]

    await message.bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=summary,
        reply_markup=order_confirm_kb(user_lang),
    )


@order_router.callback_query(OrderStates.awaiting_confirmation, F.data == "order_confirm")
async def order_confirmed(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user_lang = data.get("user_lang", "ru")
    order_type = data.get("order_type", "")
    bot_name = data.get("bot_name", "")
    core_features = data.get("core_features", "")
    references = data.get("references", "")
    client_budget = data.get("client_budget", "")
    phone = data.get("contact_phone", "")

    description = (
        f"Имя бота: {bot_name}\n"
        f"Функции: {core_features}\n"
        f"Примеры: {references}\n"
        f"Бюджет: {client_budget}"
    )

    async with ChatActionSender.typing(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        initial_sleep=0,
    ):
        await asyncio.sleep(1.2)

    order_id = await add_order(
        user_id=callback.from_user.id,
        service_type=order_type,
        description=description,
        budget=client_budget,
        phone=phone,
    )

    await state.clear()

    order_code = f"ORD-{order_id:04d}"
    confirm_text = (
        get_text(user_lang, "order_success", order_code=order_code)
        + "\n\n<tg-spoiler>"
        + get_text(user_lang, "order_bonus")
        + "</tg-spoiler>"
    )
    await callback.message.edit_text(confirm_text, reply_markup=main_menu_kb(user_lang))

    admin_text = (
        f"📥 <b>Новый заказ</b> <code>{order_code}</code>\n\n"
        f"<b>👤 Пользователь:</b> {html.escape(callback.from_user.full_name)} (ID: {callback.from_user.id})\n"
        f"<b>💬 Username:</b> @{callback.from_user.username or 'нет'}\n\n"
        f"<b>Услуга:</b> {html.escape(order_type)}\n\n"
        f"<b>Имя бота:</b>\n<blockquote>{html.escape(bot_name)}</blockquote>\n"
        f"<b>Функции:</b>\n<blockquote>{html.escape(core_features)}</blockquote>\n"
        f"<b>Примеры:</b>\n<blockquote>{html.escape(references)}</blockquote>\n\n"
        f"<b>💰 БЮДЖЕТ КЛИЕНТА:</b>\n<blockquote>{html.escape(client_budget)}</blockquote>\n\n"
        f"<b>Телефон:</b> {html.escape(phone)}"
    )

    await callback.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
    )

    await callback.answer("Заказ отправлен!")
@order_router.message(SupportStates.waiting_for_support_message)
async def support_message_received(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    user_lang = await get_user_language(message.from_user.id) or "ru"
    if not text:
        await message.answer(get_text(user_lang, "support_describe"))
        return

    await message.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📩 <b>Сообщение в поддержку</b>\n\n"
            f"👤 {html.escape(message.from_user.full_name)} (ID: {message.from_user.id})\n"
            f"@{message.from_user.username or 'нет'}\n\n"
            f"<blockquote>{html.escape(text)}</blockquote>"
        ),
    )
    await state.clear()
    await message.answer(get_text(user_lang, "support_sent"), reply_markup=main_menu_kb(user_lang))
