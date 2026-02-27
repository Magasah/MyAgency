from typing import List, Tuple, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from locales.texts import get_text


# В этом модуле собраны все инлайн-клавиатуры бота.


def _back_button(user_lang: str) -> InlineKeyboardButton:
    """Helper for a universal back-to-main button."""
    return InlineKeyboardButton(text=get_text(user_lang, "back_btn"), callback_data="back_to_main")


def language_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора языка.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tg"),
            ]
        ]
    )


def main_menu_kb(user_lang: str = "ru") -> InlineKeyboardMarkup:
    """Главное меню бота (локализовано)."""
    # profile button added
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_lang, "menu_order"), callback_data="menu_order")],
            [InlineKeyboardButton(text=get_text(user_lang, "menu_portfolio"), callback_data="menu_portfolio")],
            [InlineKeyboardButton(text="💬 Отзывы клиентов", callback_data="menu_reviews")],
            [InlineKeyboardButton(text=get_text(user_lang, "menu_support"), callback_data="menu_support")],
            [InlineKeyboardButton(text=get_text(user_lang, "menu_profile"), callback_data="menu_profile")],
        ]
    )


def services_order_kb(
    services: List[Tuple[int, str, str, int]],
    user_lang: str,
    rate_tjs_to_rub: float = 8.5,
) -> InlineKeyboardMarkup:
    """
    Динамическая клавиатура выбора услуги из каталога.
    price=0 → «Договорная»/«Шартномавӣ»; иначе цена в TJS или RUB.
    """
    buttons = []
    for svc_id, name, _, price_tjs in services:
        if price_tjs == 0:
            price_str = get_text(user_lang, "negotiable")
        elif user_lang in ("tg", "tj"):
            price_str = f"{price_tjs} TJS"
        else:
            price_rub = int(price_tjs * rate_tjs_to_rub)
            price_str = f"{price_rub} ₽"
        btn_text = f"{name} — {price_str}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"order_svc:{svc_id}")])
    buttons.append([InlineKeyboardButton(text=get_text(user_lang, "cancel_btn"), callback_data="order_cancel")])
    # back button row
    buttons.append([_back_button(user_lang)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_step_cancel_kb(user_lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка отмены на промежуточных шагах заказа."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_lang, "cancel_btn"), callback_data="order_cancel")],
            [_back_button(user_lang)],
        ]
    )


def order_confirm_kb(user_lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа перед отправкой админу."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text(user_lang, "confirm_btn"), callback_data="order_confirm"),
                InlineKeyboardButton(text=get_text(user_lang, "cancel_btn"), callback_data="order_cancel"),
            ],
            [_back_button(user_lang)],
        ]
    )


def admin_order_action_kb(order_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для администратора под уведомлением о новом заказе.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Открыть заказ в CRM",
                    callback_data=f"admin_order_view:{order_id}",
                )
            ],
        ]
    )


def admin_panel_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура панели администратора.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🗂 Управление услугами", callback_data="admin_services")],
            [InlineKeyboardButton(text="🖼 Управление портфолио", callback_data="admin_portfolio")],
            [InlineKeyboardButton(text="📋 Управление заказами", callback_data="admin_orders_manage")],
        ]
    )


def admin_services_menu_kb() -> InlineKeyboardMarkup:
    """
    Меню управления услугами.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить услугу", callback_data="admin_svc_add")],
            [InlineKeyboardButton(text="← Назад в админку", callback_data="admin_back")],
        ]
    )


def admin_services_list_kb(
    services: List[Tuple[int, str, str, int]],
) -> InlineKeyboardMarkup:
    """
    Список услуг с кнопками удаления и редактирования цены.
    price=0 → «Договорная».
    """
    buttons = []
    for svc_id, name, _, price_tjs in services:
        price_str = get_text("ru", "negotiable") if price_tjs == 0 else f"{price_tjs} TJS"
        row = [
            InlineKeyboardButton(text="🗑", callback_data=f"admin_svc_del:{svc_id}"),
            InlineKeyboardButton(text=f"✏️ {name} — {price_str}", callback_data=f"admin_svc_edit:{svc_id}"),
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="➕ Добавить услугу", callback_data="admin_svc_add")])
    buttons.append([InlineKeyboardButton(text="← Назад в админку", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# === Пользовательский профиль ===

def profile_kb(user_lang: str) -> InlineKeyboardMarkup:
    """Клавиатура в персональном кабинете."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_lang, "settings_btn"), callback_data="profile_settings")],
            [InlineKeyboardButton(text=get_text(user_lang, "my_orders_btn"), callback_data="profile_orders")],
            [_back_button(user_lang)],
        ]
    )


def profile_orders_kb(user_lang: str, orders: List[Tuple[int, str, str]]) -> InlineKeyboardMarkup:
    """Клавиатура списка заказов с кнопками для отмены заказа в допустимых статусах."""
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for order_id, otype, status in orders:
        if status in {"new", "awaiting_payment"}:
            kb.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"{get_text(user_lang, 'cancel_order_btn')} {order_id}",
                        callback_data=f"profile_cancel:{order_id}",
                    )
                ]
            )
    kb.inline_keyboard.append([_back_button(user_lang)])
    return kb


def portfolio_nav_kb(
    user_lang: str,
    current_index: int,
    total: int,
    demo_link: Optional[str],
) -> InlineKeyboardMarkup:
    """Клавиатура карусели портфолио с пагинацией."""
    counter_text = get_text(user_lang, "portfolio_index", current=current_index + 1, total=total)
    keyboard = [
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"portfolio_prev:{current_index}"),
            InlineKeyboardButton(text=counter_text, callback_data="portfolio_noop"),
            InlineKeyboardButton(text="➡️", callback_data=f"portfolio_next:{current_index}"),
        ],
        [InlineKeyboardButton(text=get_text(user_lang, "portfolio_order_similar"), callback_data="portfolio_order_similar")],
    ]

    if demo_link:
        keyboard.append(
            [InlineKeyboardButton(text=get_text(user_lang, "portfolio_demo_btn"), url=demo_link)]
        )

    keyboard.append(
        [InlineKeyboardButton(text=get_text(user_lang, "portfolio_back_menu"), callback_data="back_to_main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_portfolio_menu_kb() -> InlineKeyboardMarkup:
    """Меню управления портфолио."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить кейс", callback_data="admin_portfolio_add")],
            [InlineKeyboardButton(text="🗑 Удалить кейс", callback_data="admin_portfolio_delete")],
            [InlineKeyboardButton(text="← Назад в админку", callback_data="admin_back")],
        ]
    )


def admin_portfolio_delete_list_kb(items: List[Tuple[int, str, str]]) -> InlineKeyboardMarkup:
    """Список кейсов портфолио для удаления."""
    keyboard = []
    for item_id, title_ru, title_tj in items:
        label = title_ru or title_tj or f"ID {item_id}"
        keyboard.append(
            [InlineKeyboardButton(text=f"🗑 {label}", callback_data=f"admin_portfolio_del:{item_id}")]
        )
    keyboard.append([InlineKeyboardButton(text="← Назад", callback_data="admin_portfolio")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
