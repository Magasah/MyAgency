import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, ADMIN_ID
from database import init_db
from handlers.users import user_router
from handlers.order import order_router
from handlers.admin import admin_router
from handlers.profile import profile_router
from handlers.portfolio import portfolio_router


# Точка входа в приложение. Здесь настраивается бот, диспетчер и подключаются все роутеры.


async def set_bot_commands(bot: Bot) -> None:
    """
    Регистрация команд бота в интерфейсе Telegram.
    Стандартные команды доступны всем, а /admin видна только в чате администратора.
    """
    default_cmds = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="profile", description="Персональный кабинет"),
    ]
    admin_cmds = [BotCommand(command="admin", description="Админ-панель")]

    from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat

    # установить команды по умолчанию
    await bot.set_my_commands(default_cmds, scope=BotCommandScopeDefault())
    # /admin только для администратора
    await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=int(ADMIN_ID)))


async def main() -> None:
    """
    Главная асинхронная функция: инициализация БД, запуск бота и диспетчера.
    """
    await init_db()

    # Создаём бота с установкой parse_mode через DefaultBotProperties
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем все роутеры.
    dp.include_router(user_router)
    dp.include_router(portfolio_router)
    dp.include_router(order_router)
    dp.include_router(admin_router)
    dp.include_router(profile_router)

    # Удаляем возможный старый вебхук и сбрасываем апдейты.
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as exc:  # network problems should not stop the bot startup
        from aiogram.exceptions import TelegramNetworkError

        if isinstance(exc, TelegramNetworkError):
            print(f"Warning: webhook deletion failed: {exc!r}")
        else:
            raise
    await set_bot_commands(bot)

    # Запуск long polling.
    await dp.start_polling(bot, dispatcher=dp)


if __name__ == "__main__":
    asyncio.run(main())

