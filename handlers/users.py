import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.chat_action import ChatActionSender

from config import ADMIN_ID, EXCHANGE_RATE_TJS_TO_RUB
from database import (
    add_or_update_user,
    add_review,
    get_all_services,
    get_user_language,
    get_user_orders,
    update_order_status,
    get_average_rating,
    get_latest_reviews,
)
from keyboards.inline import language_kb, main_menu_kb, order_step_cancel_kb, services_order_kb, profile_kb
from locales.texts import get_text


# Маршрутизатор пользовательских команд и главного меню.
user_router = Router()


class PaymentStates(StatesGroup):
    client_send_receipt = State()


def _faq_kb(user_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_lang, "faq_hosting_q"), callback_data="faq_hosting")],
            [InlineKeyboardButton(text=get_text(user_lang, "faq_payment_q"), callback_data="faq_payment")],
            [InlineKeyboardButton(text=get_text(user_lang, "faq_guarantee_q"), callback_data="faq_guarantee")],
            [InlineKeyboardButton(text=get_text(user_lang, "faq_admin_btn"), url="https://t.me/vvewrix")],
            [InlineKeyboardButton(text=get_text(user_lang, "back_btn"), callback_data="back_to_main")],
        ]
    )


def _mask_user_id(user_id: int) -> str:
    uid = str(user_id)
    if len(uid) <= 3:
        return uid
    return f"{uid[:3]}***"


async def _main_menu_text(user_lang: str) -> str:
    avg_rating, total_reviews = await get_average_rating()
    if user_lang == "ru":
        return (
            "Добро пожаловать в нашу IT-студию!\n"
            f"🏆 Наш рейтинг: {avg_rating:.1f} ⭐️ (Отзывов: {total_reviews})\n"
            "Выберите действие:"
        )
    return (
        "Хуш омадед ба IT-студияи мо!\n"
        f"🏆 Рейтинги мо: {avg_rating:.1f} ⭐️ (Шумораи назарҳо: {total_reviews})\n"
        "Амалро интихоб кунед:"
    )


def _reviews_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]]
    )


@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /start.
    Human-like: typing + пауза перед приветствием.
    """
    await state.clear()

    async with ChatActionSender.typing(
        bot=message.bot,
        chat_id=message.chat.id,
        initial_sleep=0,
    ):
        await asyncio.sleep(1.2)

    rating_text = await _main_menu_text("ru")
    await message.answer(f"{rating_text}\n\nПожалуйста, выберите язык обслуживания:", reply_markup=language_kb())


@user_router.callback_query(F.data.in_(["lang_ru", "lang_tg"]))
async def language_chosen(callback: CallbackQuery) -> None:
    """
    Сохраняет язык пользователя и показывает главное меню.
    Human-like: typing + пауза перед показом меню.
    """
    user = callback.from_user
    chosen_language = "ru" if callback.data == "lang_ru" else "tg"

    await add_or_update_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        language=chosen_language,
    )

    async with ChatActionSender.typing(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        initial_sleep=0,
    ):
        await asyncio.sleep(1.0)

    text = get_text(chosen_language, "lang_set_ru" if chosen_language == "ru" else "lang_set_tj")
    await callback.message.edit_text(text, reply_markup=main_menu_kb(chosen_language))
    await callback.answer()



@user_router.callback_query(F.data == "menu_profile")
async def menu_profile(callback: CallbackQuery) -> None:
    """Показать персональный кабинет пользователя."""
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    orders = await get_user_orders(callback.from_user.id)
    orders_count = len(orders)

    lang_label = get_text(user_lang, "language_ru") if user_lang == "ru" else get_text(user_lang, "language_tj")
    profile_text = (
        f"{get_text(user_lang, 'profile_title')}\n\n"
        f"{get_text(user_lang, 'profile_user_id', user_id=callback.from_user.id)}\n"
        f"{get_text(user_lang, 'profile_language', language=lang_label)}\n"
        f"{get_text(user_lang, 'profile_orders_count', count=orders_count)}"
    )
    await callback.message.edit_text(profile_text, reply_markup=profile_kb(user_lang))
    await callback.answer()


@user_router.callback_query(F.data == "menu_support")
async def menu_support(callback: CallbackQuery, state: FSMContext) -> None:
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    await state.clear()
    await callback.message.edit_text(
        get_text(user_lang, "faq_title"),
        reply_markup=_faq_kb(user_lang),
    )
    await callback.answer()


@user_router.callback_query(F.data.in_(["faq_hosting", "faq_payment", "faq_guarantee"]))
async def faq_answer(callback: CallbackQuery) -> None:
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    mapping = {
        "faq_hosting": "faq_hosting_a",
        "faq_payment": "faq_payment_a",
        "faq_guarantee": "faq_guarantee_a",
    }
    text_key = mapping.get(callback.data, "faq_hosting_a")
    await callback.message.edit_text(get_text(user_lang, text_key), reply_markup=_faq_kb(user_lang))
    await callback.answer()


@user_router.callback_query(F.data.startswith("client_paid:"))
async def client_paid_clicked(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    try:
        order_id = int(parts[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректный ID заказа", show_alert=True)
        return

    await state.set_state(PaymentStates.client_send_receipt)
    await state.update_data(receipt_order_id=order_id)
    await callback.message.edit_text("Отправьте фото чека по оплате заказа.")
    await callback.answer()


@user_router.message(PaymentStates.client_send_receipt, F.photo)
async def payment_receipt_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("receipt_order_id")
    if not order_id:
        await state.clear()
        return

    await update_order_status(int(order_id), "verifying_receipt")

    photo_file_id = message.photo[-1].file_id
    approve_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"admin_receipt_confirm:{order_id}:{message.from_user.id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"admin_receipt_reject:{order_id}:{message.from_user.id}",
                ),
            ]
        ]
    )

    await message.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=(
            f"🧾 Чек по заказу <code>ORD-{int(order_id):04d}</code>\n"
            f"👤 Клиент: {message.from_user.full_name} (ID: {message.from_user.id})"
        ),
        reply_markup=approve_kb,
    )

    user_lang = await get_user_language(message.from_user.id) or "ru"
    await message.answer(get_text(user_lang, "receipt_sent_to_admin"))
    await state.clear()


@user_router.message(PaymentStates.client_send_receipt)
async def payment_receipt_invalid(message: Message) -> None:
    user_lang = await get_user_language(message.from_user.id) or "ru"
    await message.answer(get_text(user_lang, "receipt_waiting_photo"))


@user_router.callback_query(F.data.startswith("review_star:"))
async def review_star_clicked(callback: CallbackQuery) -> None:
    parts = (callback.data or "").split(":")
    try:
        order_id = int(parts[1])
        stars = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка", show_alert=True)
        return

    if stars < 1 or stars > 5:
        await callback.answer("Некорректная оценка", show_alert=True)
        return

    await add_review(callback.from_user.id, order_id, stars)
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    await callback.message.edit_text(get_text(user_lang, "review_thanks"), reply_markup=main_menu_kb(user_lang))
    await callback.answer()


@user_router.callback_query(F.data == "menu_reviews")
async def menu_reviews(callback: CallbackQuery) -> None:
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    reviews = await get_latest_reviews(limit=3)
    if not reviews:
        text = "Пока отзывов нет. Станьте первым клиентом, кто оставит оценку!"
        await callback.message.edit_text(text, reply_markup=_reviews_back_kb())
        await callback.answer()
        return

    blocks = ["Последние отзывы наших клиентов:\n"]
    for review_user_id, order_id, service_name, stars in reviews:
        stars_line = "⭐️" * max(1, min(5, stars))
        blocks.append(
            f"{stars_line}\n"
            f"👤 ID: {_mask_user_id(review_user_id)}\n"
            f"Заказ: {service_name}\n"
            f"Код: ORD-{order_id:04d}\n"
        )

    await callback.message.edit_text("\n".join(blocks), reply_markup=_reviews_back_kb())
    await callback.answer()


@user_router.callback_query(F.data == "back_to_main")
async def global_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Global handler that returns user to main menu and clears FSM state.

    If an order flow is active, step backward through states instead of
    immediately cancelling.
    """
    from handlers.order import OrderStates
    from database import get_all_services

    current = await state.get_state()
    user_lang = await get_user_language(callback.from_user.id) or "ru"

    # only handle order-specific stepping when we are in an order state
    if current in (
        OrderStates.choosing_type.state,
        OrderStates.bot_name.state,
        OrderStates.core_features.state,
        OrderStates.references.state,
        OrderStates.client_budget.state,
        OrderStates.contact_phone.state,
        OrderStates.awaiting_confirmation.state,
    ):
        # mimic previous order_back logic
        if current == OrderStates.choosing_type.state:
            await state.clear()
            await callback.message.edit_text(
                get_text(user_lang, "order_cancelled"),
                reply_markup=main_menu_kb(user_lang),
            )
            await callback.answer()
            return

        if current == OrderStates.bot_name.state:
            await state.set_state(OrderStates.choosing_type)
            services = await get_all_services()
            await callback.message.edit_text(
                get_text(user_lang, "choose_service"),
                reply_markup=services_order_kb(
                    services,
                    user_lang=user_lang,
                    rate_tjs_to_rub=EXCHANGE_RATE_TJS_TO_RUB,
                ),
            )
        elif current == OrderStates.core_features.state:
            await state.set_state(OrderStates.bot_name)
            await callback.message.edit_text(
                get_text(user_lang, "step_bot_name"),
                reply_markup=order_step_cancel_kb(user_lang),
            )
        elif current == OrderStates.references.state:
            await state.set_state(OrderStates.core_features)
            await callback.message.edit_text(
                get_text(user_lang, "step_core_features"),
                reply_markup=order_step_cancel_kb(user_lang),
            )
        elif current == OrderStates.client_budget.state:
            await state.set_state(OrderStates.references)
            await callback.message.edit_text(
                get_text(user_lang, "step_references"),
                reply_markup=order_step_cancel_kb(user_lang),
            )
        elif current == OrderStates.contact_phone.state:
            await state.set_state(OrderStates.client_budget)
            await callback.message.edit_text(
                get_text(user_lang, "step_budget"),
                reply_markup=order_step_cancel_kb(user_lang),
            )
        elif current == OrderStates.awaiting_confirmation.state:
            await state.set_state(OrderStates.contact_phone)
            await callback.message.edit_text(
                get_text(user_lang, "step_contact_phone"),
                reply_markup=order_step_cancel_kb(user_lang),
            )
        await callback.answer()
        return

    # default behaviour: clear state and go to main menu
    await state.clear()
    await callback.message.edit_text(await _main_menu_text(user_lang), reply_markup=main_menu_kb(user_lang))
    await callback.answer()


@user_router.callback_query(F.data == "menu_order")
async def menu_order(callback: CallbackQuery, state: FSMContext) -> None:
    from handlers.order import OrderStates

    services = await get_all_services()
    user_lang = await get_user_language(callback.from_user.id) or "ru"

    if not services:
        await callback.message.edit_text(
            get_text(user_lang, "no_services"),
            reply_markup=main_menu_kb(user_lang),
        )
        await callback.answer()
        return

    await state.update_data(user_lang=user_lang)
    await state.set_state(OrderStates.choosing_type)

    await callback.message.edit_text(
        get_text(user_lang, "choose_service"),
        reply_markup=services_order_kb(
            services,
            user_lang=user_lang,
            rate_tjs_to_rub=EXCHANGE_RATE_TJS_TO_RUB,
        ),
    )
    await callback.answer()

