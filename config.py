import os

# Конфигурация бота только через переменные окружения.


def _require_env(name: str) -> str:
	value = (os.getenv(name) or "").strip()
	if not value:
		raise RuntimeError(f"Environment variable {name} is required")
	return value


def _read_int_env(name: str, default: str) -> int:
	raw = (os.getenv(name) or default).strip()
	try:
		return int(raw)
	except ValueError as exc:
		raise RuntimeError(f"Environment variable {name} must be integer") from exc


def _read_float_env(name: str, default: str) -> float:
	raw = (os.getenv(name) or default).strip()
	try:
		return float(raw)
	except ValueError as exc:
		raise RuntimeError(f"Environment variable {name} must be float") from exc

# Токен телеграм-бота.
BOT_TOKEN: str = _require_env("BOT_TOKEN")

# ID администратора.
ADMIN_ID: int = _read_int_env("ADMIN_ID", "0")
if ADMIN_ID <= 0:
	raise RuntimeError("Environment variable ADMIN_ID must be positive integer")

# Имя файла базы данных SQLite.
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "myagency.db")

# Курс конвертации TJS → RUB для отображения цен пользователям с языком 'ru'.
EXCHANGE_RATE_TJS_TO_RUB: float = _read_float_env("EXCHANGE_RATE_TJS_TO_RUB", "8.5")
if EXCHANGE_RATE_TJS_TO_RUB <= 0:
	raise RuntimeError("Environment variable EXCHANGE_RATE_TJS_TO_RUB must be > 0")

# Карта для оплаты заказов.
PAYMENT_CARD: str = _require_env("PAYMENT_CARD")

