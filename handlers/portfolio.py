import html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto

from config import EXCHANGE_RATE_TJS_TO_RUB
from database import get_portfolio_by_index, get_portfolio_count, get_user_language
from database import get_all_services
from handlers.order import OrderStates
from keyboards.inline import main_menu_kb, portfolio_nav_kb, services_order_kb
from locales.texts import get_text


portfolio_router = Router()


def _normalize_index(index: int, total: int) -> int:
    if total <= 0:
        return 0
    return index % total


def _portfolio_caption(
    user_lang: str,
    title_ru: str,
    title_tj: str,
    description_ru: str,
    description_tj: str,
) -> str:
    title = title_tj if user_lang in ("tg", "tj") else title_ru
    description = description_tj if user_lang in ("tg", "tj") else description_ru
    return get_text(
        user_lang,
        "portfolio_caption",
        title=html.escape(title),
        description=html.escape(description),
    )


@portfolio_router.callback_query(F.data == "menu_portfolio")
async def menu_portfolio(callback: CallbackQuery) -> None:
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    total = await get_portfolio_count()

    if total == 0:
        await callback.message.edit_text(
            get_text(user_lang, "portfolio_empty"),
            reply_markup=main_menu_kb(user_lang),
        )
        await callback.answer()
        return

    item = await get_portfolio_by_index(0)
    if not item:
        await callback.message.edit_text(
            get_text(user_lang, "portfolio_empty"),
            reply_markup=main_menu_kb(user_lang),
        )
        await callback.answer()
        return

    _, title_ru, title_tj, desc_ru, desc_tj, photo_file_id, demo_link = item
    caption = _portfolio_caption(user_lang, title_ru, title_tj, desc_ru, desc_tj)

    await callback.message.answer_photo(
        photo=photo_file_id,
        caption=caption,
        reply_markup=portfolio_nav_kb(
            user_lang=user_lang,
            current_index=0,
            total=total,
            demo_link=demo_link,
        ),
    )
    await callback.answer()


@portfolio_router.callback_query(F.data == "portfolio_noop")
async def portfolio_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@portfolio_router.callback_query(F.data.startswith("portfolio_prev:"))
@portfolio_router.callback_query(F.data.startswith("portfolio_next:"))
async def portfolio_paginate(callback: CallbackQuery) -> None:
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    total = await get_portfolio_count()

    if total == 0:
        await callback.answer(get_text(user_lang, "portfolio_empty"), show_alert=True)
        return

    if total == 1:
        await callback.answer()
        return

    parts = (callback.data or "").split(":", maxsplit=1)
    try:
        current_index = int(parts[1])
    except (IndexError, ValueError):
        current_index = 0

    if (callback.data or "").startswith("portfolio_prev:"):
        next_index = _normalize_index(current_index - 1, total)
    else:
        next_index = _normalize_index(current_index + 1, total)

    item = await get_portfolio_by_index(next_index)
    if not item:
        await callback.answer(get_text(user_lang, "portfolio_empty"), show_alert=True)
        return

    _, title_ru, title_tj, desc_ru, desc_tj, photo_file_id, demo_link = item
    caption = _portfolio_caption(user_lang, title_ru, title_tj, desc_ru, desc_tj)

    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=photo_file_id,
            caption=caption,
            parse_mode="HTML",
        ),
        reply_markup=portfolio_nav_kb(
            user_lang=user_lang,
            current_index=next_index,
            total=total,
            demo_link=demo_link,
        ),
    )
    await callback.answer()


@portfolio_router.callback_query(F.data == "portfolio_order_similar")
async def portfolio_order_similar(callback: CallbackQuery, state: FSMContext) -> None:
    user_lang = await get_user_language(callback.from_user.id) or "ru"
    services = await get_all_services()

    if not services:
        await callback.answer(get_text(user_lang, "no_services"), show_alert=True)
        return

    sent = await callback.message.answer(
        get_text(user_lang, "choose_service"),
        reply_markup=services_order_kb(
            services,
            user_lang=user_lang,
            rate_tjs_to_rub=EXCHANGE_RATE_TJS_TO_RUB,
        ),
    )

    await state.update_data(
        user_lang=user_lang,
        edit_chat_id=sent.chat.id,
        edit_message_id=sent.message_id,
    )
    await state.set_state(OrderStates.choosing_type)
    await callback.answer()
