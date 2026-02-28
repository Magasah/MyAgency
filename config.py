import os
import warnings

# Конфигурация бота только через переменные окружения.


def _require_env(name: str) -> str:
	value = (os.getenv(name) or "").strip()
	if not value:
		raise RuntimeError(f"Environment variable {name} is required")
	return value


def _validate_bot_token(token: str) -> str:
	token = token.strip()
	if ":" not in token:
		raise RuntimeError("BOT_TOKEN has invalid format")
	bot_id, secret = token.split(":", maxsplit=1)
	if not bot_id.isdigit() or len(secret) < 20:
		raise RuntimeError("BOT_TOKEN has invalid format")
	return token


def _read_int_env(name: str, default: str) -> int:
	raw = (os.getenv(name) or default).strip().strip('"').strip("'")
	try:
		return int(raw)
	except ValueError as exc:
		raise RuntimeError(f"Environment variable {name} must be integer, got: {raw!r}") from exc


def _read_float_env(name: str, default: str) -> float:
	raw = (os.getenv(name) or default).strip()
	try:
		return float(raw)
	except ValueError as exc:
		raise RuntimeError(f"Environment variable {name} must be float") from exc

# Токен телеграм-бота.
BOT_TOKEN: str = _validate_bot_token(_require_env("BOT_TOKEN"))

# ID администратора.
_admin_id_raw = (os.getenv("ADMIN_ID") or "").strip().strip('"').strip("'")
if not _admin_id_raw:
	warnings.warn(
		"Environment variable ADMIN_ID is not set. Admin features are disabled until ADMIN_ID is configured.",
		RuntimeWarning,
	)
	ADMIN_ID = 1
else:
	ADMIN_ID: int = _read_int_env("ADMIN_ID", _admin_id_raw)
	if ADMIN_ID <= 0:
		raise RuntimeError(f"Environment variable ADMIN_ID must be positive integer, got: {ADMIN_ID}")

# Имя файла базы данных SQLite.
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "myagency.db")

# Курс конвертации TJS → RUB для отображения цен пользователям с языком 'ru'.
EXCHANGE_RATE_TJS_TO_RUB: float = _read_float_env("EXCHANGE_RATE_TJS_TO_RUB", "8.5")
if EXCHANGE_RATE_TJS_TO_RUB <= 0:
	raise RuntimeError("Environment variable EXCHANGE_RATE_TJS_TO_RUB must be > 0")

# Карта для оплаты заказов.
PAYMENT_CARD: str = _require_env("PAYMENT_CARD")
if len(PAYMENT_CARD) < 8:
	raise RuntimeError("PAYMENT_CARD is too short")

