"""
Строгий двуязычный словарь. Все пользовательские тексты бота.
Нет смешивания языков — только через этот модуль.
"""

TEXTS = {
    "ru": {
        # Приветствие
        "welcome": "👋 Добро пожаловать в IT Bot Development Agency!\n\nПожалуйста, выберите язык обслуживания:",
        "lang_set_ru": "✅ Язык установлен: Русский.\n\nВыберите действие в главном меню:",
        "lang_set_tj": "✅ Забон интихоб шуд: Тоҷикӣ.\n\nЛутфан аз менюи асосӣ амалро интихоб кунед:",
        # Главное меню
        "menu_order": "🛒 Заказать бота",
        "menu_portfolio": "💼 Портфолио",
        "menu_support": "❓ Помощь",
        # Каталог / заказ
        "choose_service": "🛒 Выберите услугу:\n\nВыберите тип бота из каталога:",
        "no_services": "📭 Пока нет доступных услуг. Обратитесь к администратору.",
        "negotiable": "🤝 Договорная",
        "ask_budget": "💰 Какой у вас примерный бюджет на проект?",
        # FSM шаги заказа (step numbers 2-7)
        "step_bot_name": "📝 Шаг 2/6: Как назовём вашего бота?",
        "step_core_features": "📝 Шаг 3/6: Опишите главные функции (например: корзина, админка, оплата)",
        "step_references": "📝 Шаг 4/6: Есть ли примеры ботов, которые вам нравятся? Ссылки?",
        "step_budget": "💰 Шаг 5/6: Какой у вас примерный бюджет на проект?",
        "step_contact_phone": "📞 Шаг 6/6: Отправьте ваш номер телефона (например: +79991234567)",
        # Валидация
        "enter_bot_name": "Пожалуйста, введите название бота.",
        "enter_features": "Пожалуйста, опишите основные функции.",
        "enter_references": "Пожалуйста, укажите примеры или напишите «нет».",
        "enter_budget": "Пожалуйста, укажите примерный бюджет.",
        "enter_phone": "Пожалуйста, отправьте номер телефона.",
        # Сводка заказа
        "summary_title": "🧾 Ваш заказ сформирован:",
        "summary_type": "Тип",
        "summary_price": "Цена",
        "summary_bot_name": "Имя бота",
        "summary_features": "Функции",
        "summary_references": "Примеры",
        "summary_budget": "Бюджет",
        "summary_confirm": "Всё верно?",
        "confirm_btn": "✅ Подтвердить и отправить",
        "cancel_btn": "❌ Отменить",
        # Результат
        "order_cancelled": "❌ Оформление заказа отменено.",
        "order_success": "✅ Спасибо! Ваш заказ успешно создан.\n\nНомер заказа: {order_code}\n\nМы свяжемся с вами в ближайшее время.",
        "order_bonus": "🎁 Бонус: бесплатная консультация при первом обращении!",
        # Поддержка
        "support_prompt": "✉️ Опишите ваш вопрос или проблему одним сообщением.\n\nПосле отправки администратор свяжется с вами.",
        "support_sent": "✅ Ваше сообщение отправлено администратору.\nМы постараемся ответить как можно скорее.",
        "support_describe": "Пожалуйста, опишите ваш вопрос текстом.",
        "faq_title": "❓ База знаний\n\nВыберите вопрос:",
        "faq_hosting_q": "Что с хостингом?",
        "faq_payment_q": "Как происходит оплата?",
        "faq_guarantee_q": "Какие гарантии?",
        "faq_hosting_a": "Мы берём на себя запуск и сопровождение. По желанию подключаем ваш VPS/облако и передаём доступы после сдачи.",
        "faq_payment_a": "Работаем поэтапно: после одобрения заказа вы вносите оплату, затем приступаем к разработке и показываем промежуточный результат.",
        "faq_guarantee_a": "Даём гарантийный период на исправление багов после релиза и техническую поддержку по договорённости.",
        "payment_approved": "✅ Ваш заказ одобрен!\n\nПожалуйста, переведите сумму на карту:\n<b>{card}</b>\n\nИ отправьте ФОТО чека в ответ на это сообщение.",
        "receipt_waiting_photo": "Ожидается фото чека. Пожалуйста, отправьте изображение.",
        "receipt_sent_to_admin": "✅ Чек отправлен на проверку. Ожидайте подтверждение оплаты.",
        "receipt_rejected": "❌ Чек отклонён. Пожалуйста, проверьте оплату и отправьте новое фото чека.",
        "payment_confirmed_client": "✅ Оплата получена, мы начали работу!",
        "review_request": "🎉 Ваш заказ успешно завершен!\n\nПожалуйста, оцените нашу работу:",
        "review_thanks": "Спасибо за вашу оценку! 🙌",
        # Портфолио
        "portfolio_title": "💼 Наше портфолио",
        "portfolio_discount": "🎁 При заказе через бота: <tg-spoiler>скидка 10%</tg-spoiler>",
        "portfolio_empty": "📭 Портфолио пока пустое. Скоро добавим кейсы.",
        "portfolio_index": "{current} / {total}",
        "portfolio_order_similar": "🛒 Заказать такой же",
        "portfolio_demo_btn": "🤖 Смотреть демо",
        "portfolio_back_menu": "🏠 В главное меню",
        "portfolio_caption": "<b>{title}</b>\n\n{description}",
        "portfolio_no_demo": "Демо-ссылка отсутствует.",
        "portfolio_open_demo": "Открыть демо: {link}",
        "admin_portfolio_menu": "🖼 Управление портфолио",
        "admin_portfolio_add": "➕ Добавить кейс",
        "admin_portfolio_delete": "🗑 Удалить кейс",
        "admin_portfolio_prompt_photo": "Отправьте скриншот/фото бота.",
        "admin_portfolio_prompt_title_ru": "Введите название (RU).",
        "admin_portfolio_prompt_title_tj": "Введите название (TJ).",
        "admin_portfolio_prompt_desc_ru": "Введите описание (RU).",
        "admin_portfolio_prompt_desc_tj": "Введите описание (TJ).",
        "admin_portfolio_prompt_demo": "Отправьте ссылку на демо-бота (или напишите '-/нет').",
        "admin_portfolio_saved": "✅ Кейс портфолио сохранён.",
        "admin_portfolio_empty": "Портфолио пустое.",
        "admin_portfolio_deleted": "Кейс удалён.",
        "admin_portfolio_need_photo": "Нужно отправить фото/скриншот.",
        # Ошибки
        "error_service": "Ошибка выбора услуги.",
        "error_service_not_found": "Услуга не найдена.",
        "back_btn": "⬅️ Назад",
        "menu_profile": "👤 Профиль",
        "profile_title": "👤 Ваш профиль",
        "profile_user_id": "ID: {user_id}",
        "profile_language": "Язык: {language}",
        "profile_orders_count": "Всего заказов: {count}",
        "settings_btn": "⚙️ Настройки",
        "my_orders_btn": "📦 Мои заказы",
        "order_list_title": "📦 Ваши заказы:",
        "cancel_order_btn": "❌ Отменить заказ",
        "main_menu_prompt": "Выберите действие в главном меню:",
        "language_ru": "Русский",
        "language_tj": "Тоҷикӣ",
    },
    "tj": {
        # Приветствие
        "welcome": "👋 Хуш омадед ба IT Bot Development Agency!\n\nЛутфан забони хидматро интихоб кунед:",
        "lang_set_ru": "✅ Язык установлен: Русский.\n\nВыберите действие в главном меню:",
        "lang_set_tj": "✅ Забон интихоб шуд: Тоҷикӣ.\n\nЛутфан аз менюи асосӣ амалро интихоб кунед:",
        # Главное меню
        "menu_order": "🛒 Фармоиши бот",
        "menu_portfolio": "💼 Портфолио",
        "menu_support": "❓ Кӯмак",
        # Каталог / заказ
        "choose_service": "🛒 Хидматро интихоб кунед:\n\nНамуди ботро аз каталог интихоб кунед:",
        "no_services": "📭 То ҳол хидматҳо мавҷуд нестанд. Ба админ муроҷиат кунед.",
        "negotiable": "🤝 Шартномавӣ",
        "ask_budget": "💰 Буҷети тахминии шумо барои лоиҳа чӣ қадар аст?",
        # FSM шаги заказа
        "step_bot_name": "📝 Қадам 2/6: Номи бот чист?",
        "step_core_features": "📝 Қадам 3/6: Кадом функсияҳо лозиманд? (мас.: корзина, админка, пардохт)",
        "step_references": "📝 Қадам 4/6: Мисолҳои ботҳо ё истинодҳо ҳастанд?",
        "step_budget": "💰 Қадам 5/6: Буҷети тахминии шумо барои лоиҳа чӣ қадар аст?",
        "step_contact_phone": "📞 Қадам 6/6: Рақами телефони худро фиристед (мас.: +992901234567)",
        # Валидация
        "enter_bot_name": "Лутфан номи ботро ворид кунед.",
        "enter_features": "Лутфан функсияҳои асосиро тавсиф кунед.",
        "enter_references": "Лутфан мисолҳо ё «не» нависед.",
        "enter_budget": "Лутфан буҷети тахминиро ворид кунед.",
        "enter_phone": "Лутфан рақами телефонро фиристед.",
        # Сводка заказа
        "summary_title": "🧾 Фармоиши шумо тайёр аст:",
        "summary_type": "Намуд",
        "summary_price": "Нарх",
        "summary_bot_name": "Номи бот",
        "summary_features": "Функсияҳо",
        "summary_references": "Мисолҳо",
        "summary_budget": "Буҷет",
        "summary_confirm": "Ҳама чиз дуруст аст?",
        "confirm_btn": "✅ Тасдиқ ва фиристодан",
        "cancel_btn": "❌ Бекор кардан",
        # Результат
        "order_cancelled": "❌ Фармоиш бекор карда шуд.",
        "order_success": "✅ Раҳмат! Фармоиши шумо муваффақона эҷод шуд.\n\nРақами фармоиш: {order_code}\n\nМо ба зудӣ бо шумо тамос мегирем.",
        "order_bonus": "🎁 Бонус: маслиҳати ройгон дар муроҷиати аввал!",
        # Поддержка
        "support_prompt": "✉️ Саволатонро дар як пайғом тавсиф кунед.\n\nПас аз фиристодан админ бо шумо тамос мегирад.",
        "support_sent": "✅ Паёми шумо ба админ фиристода шуд.\nМо кӯшиш мекунем ҳамчун имкон зуд ҷавоб диҳем.",
        "support_describe": "Лутфан саволатонро матнӣ тавсиф кунед.",
        "faq_title": "❓ Базаи дониш\n\nСаволро интихоб кунед:",
        "faq_hosting_q": "Бо хостинг чӣ мешавад?",
        "faq_payment_q": "Пардохт чӣ гуна аст?",
        "faq_guarantee_q": "Кадом кафолатҳо ҳастанд?",
        "faq_hosting_a": "Мо запуск ва дастгириро ба уҳда мегирем. Бо хоҳиши шумо VPS/облаки шуморо мепайвандем ва пас аз супориш дастрасиро месупорем.",
        "faq_payment_a": "Кор марҳилавӣ аст: баъд аз тасдиқи фармоиш пардохт мекунед, сипас мо корро оғоз мекунем ва натиҷаи мобайниро нишон медиҳем.",
        "faq_guarantee_a": "Баъд аз релиз давраи кафолатӣ барои ислоҳи хатогиҳо ва дастгирии техникӣ медиҳем.",
        "payment_approved": "✅ Фармоиши шумо тасдиқ шуд!\n\nЛутфан маблағро ба корт гузаронед:\n<b>{card}</b>\n\nВа ФОТО-и чекро ҳамчун ҷавоб ба ҳамин паём фиристед.",
        "receipt_waiting_photo": "Интизори акси чек ҳастем. Лутфан тасвир фиристед.",
        "receipt_sent_to_admin": "✅ Чек барои санҷиш ба админ фиристода шуд. Тасдиқи пардохтро интизор шавед.",
        "receipt_rejected": "❌ Чек рад шуд. Лутфан пардохтро санҷида, акси нави чек фиристед.",
        "payment_confirmed_client": "✅ Пардохт қабул шуд, мо корро оғоз кардем!",
        "review_request": "🎉 Фармоиши шумо бомуваффақият анҷом ёфт!\n\nЛутфан кори моро баҳогузорӣ кунед:",
        "review_thanks": "Ташаккур барои баҳогузорӣ! 🙌",
        # Портфолио
        "portfolio_title": "💼 Портфолиои мо",
        "portfolio_discount": "🎁 Ҳангоми фармоиш тавассути бот: <tg-spoiler>тахфиф 10%</tg-spoiler>",
        "portfolio_empty": "📭 Портфолио ҳоло холӣ аст. Ба зудӣ кейсҳо илова мекунем.",
        "portfolio_index": "{current} / {total}",
        "portfolio_order_similar": "🛒 Ҳаминхел фармоиш додан",
        "portfolio_demo_btn": "🤖 Дидани демо",
        "portfolio_back_menu": "🏠 Ба менюи асосӣ",
        "portfolio_caption": "<b>{title}</b>\n\n{description}",
        "portfolio_no_demo": "Истиноди демо нест.",
        "portfolio_open_demo": "Кушодани демо: {link}",
        "admin_portfolio_menu": "🖼 Идоракунии портфолио",
        "admin_portfolio_add": "➕ Иловаи кейс",
        "admin_portfolio_delete": "🗑 Ҳазфи кейс",
        "admin_portfolio_prompt_photo": "Скриншот/акси ботро фиристед.",
        "admin_portfolio_prompt_title_ru": "Номро ворид кунед (RU).",
        "admin_portfolio_prompt_title_tj": "Номро ворид кунед (TJ).",
        "admin_portfolio_prompt_desc_ru": "Тавсифро ворид кунед (RU).",
        "admin_portfolio_prompt_desc_tj": "Тавсифро ворид кунед (TJ).",
        "admin_portfolio_prompt_demo": "Истиноди демо-ботро фиристед (ё '-/нет' нависед).",
        "admin_portfolio_saved": "✅ Кейси портфолио нигоҳ дошта шуд.",
        "admin_portfolio_empty": "Портфолио холӣ аст.",
        "admin_portfolio_deleted": "Кейс ҳазф шуд.",
        "admin_portfolio_need_photo": "Лутфан фото/скриншот фиристед.",
        # Ошибки
        "error_service": "Хатоги дар интихоби хидмат.",
        "error_service_not_found": "Хидмат ёфт нашуд.",
        "back_btn": "⬅️ Бозгашт",
        "menu_profile": "👤 Профил",
        "profile_title": "👤 Профили шумо",
        "profile_user_id": "ID: {user_id}",
        "profile_language": "Забон: {language}",
        "profile_orders_count": "Ҷамъ: {count} фармоишҳо",
        "settings_btn": "⚙️ Танзимот",
        "my_orders_btn": "📦 Фармоишҳои ман",
        "order_list_title": "📦 Фармоишҳои шумо:",
        "cancel_order_btn": "❌ Ҳалли фармоиш",
        "main_menu_prompt": "Лутфан аз менюи асосӣ амалро интихоб кунед:",
        "language_ru": "Русский",
        "language_tj": "Тоҷикӣ",
    },
}


def _normalize_lang(lang: str) -> str:
    """Преобразует 'tg' в 'tj' для совместимости с БД."""
    if lang in ("tg", "tj"):
        return "tj"
    return "ru"


def get_text(lang: str, key: str, **format_kwargs) -> str:
    """
    Возвращает текст по ключу и языку.
    format_kwargs — для подстановки в строку (например, {order_code}).
    """
    norm = _normalize_lang(lang)
    text = TEXTS.get(norm, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))
    if format_kwargs:
        return text.format(**format_kwargs)
    return text
