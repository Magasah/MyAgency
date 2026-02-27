import aiosqlite
from typing import List, Tuple, Optional

from config import DATABASE_PATH


ORDER_STATUSES = (
    "new",
    "awaiting_payment",
    "verifying_receipt",
    "in_progress",
    "completed",
    "cancelled",
)


# Все функции работы с базой данных собраны в этом модуле.
# База создаётся и мигрируется автоматически при старте бота.


async def init_db() -> None:
    """
    Инициализация базы данных и автоматическое создание таблиц.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Включаем поддержку внешних ключей
        await db.execute("PRAGMA foreign_keys = ON;")

        # Таблица пользователей
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                language TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Таблица услуг (каталог для заказа бота)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price_tjs INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Таблица заказов
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                description TEXT NOT NULL,
                budget TEXT NOT NULL,
                agreed_price INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """
        )

        # Миграции orders для старых установок
        cursor = await db.execute("PRAGMA table_info(orders);")
        order_columns_rows = await cursor.fetchall()
        order_columns = {row[1] for row in order_columns_rows}

        if "service_type" not in order_columns:
            await db.execute("ALTER TABLE orders ADD COLUMN service_type TEXT NOT NULL DEFAULT ''; ")
        if "budget" not in order_columns:
            await db.execute("ALTER TABLE orders ADD COLUMN budget TEXT NOT NULL DEFAULT ''; ")
        if "agreed_price" not in order_columns:
            await db.execute("ALTER TABLE orders ADD COLUMN agreed_price INTEGER NOT NULL DEFAULT 0; ")

        # Заполняем новые поля данными из старой схемы, если такие колонки были
        if "order_type" in order_columns:
            await db.execute(
                """
                UPDATE orders
                SET service_type = COALESCE(NULLIF(service_type, ''), order_type)
                WHERE service_type = '';
                """
            )

        # Нормализуем статусы к новой модели
        await db.execute("UPDATE orders SET status = 'new' WHERE status IN ('pending', 'accepted');")
        await db.execute("UPDATE orders SET status = 'awaiting_payment' WHERE status = 'waiting_for_payment';")
        await db.execute("UPDATE orders SET status = 'cancelled' WHERE status IN ('declined', 'rejected');")
        await db.execute(
            """
            UPDATE orders
            SET status = 'new'
            WHERE status IS NULL
               OR TRIM(status) = ''
               OR status NOT IN ('new', 'awaiting_payment', 'verifying_receipt', 'in_progress', 'completed', 'cancelled');
            """
        )

        # Таблица портфолио
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_ru TEXT NOT NULL,
                title_tj TEXT NOT NULL,
                description_ru TEXT NOT NULL,
                description_tj TEXT NOT NULL,
                photo_file_id TEXT NOT NULL,
                demo_link TEXT
            );
            """
        )

        # Таблица отзывов
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                stars INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, order_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            );
            """
        )

        await db.commit()

        # Дефолтные услуги для новых установок (если таблица пуста)
        cursor = await db.execute("SELECT COUNT(*) FROM services;")
        count_row = await cursor.fetchone()
        if count_row and int(count_row[0]) == 0:
            await db.execute(
                """
                INSERT INTO services (name, description, price_tjs) VALUES
                ('🛍 E-commerce бот', 'Магазин с корзиной и оплатой', 500),
                ('🎮 Игровой бот', 'Квиз, викторина или мини-игра', 400),
                ('🏢 Бизнес-бот', 'CRM, заявки, уведомления', 600),
                ('✨ Другое', 'Индивидуальная разработка', 350);
                """
            )
            await db.commit()


async def add_or_update_user(
    user_id: int,
    username: Optional[str],
    full_name: str,
    language: str,
) -> None:
    """
    Добавляет пользователя или обновляет его язык.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name, language)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                language = excluded.language;
            """,
            (user_id, username, full_name, language),
        )
        await db.commit()


async def add_order(
    user_id: int,
    service_type: str,
    description: str,
    budget: str,
    phone: str = "",
) -> int:
    """
    Создаёт новый заказ и возвращает его ID.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("PRAGMA table_info(orders);")
        columns = {row[1] for row in await cursor.fetchall()}

        insert_columns = ["user_id", "description"]
        insert_values = [user_id, description]

        if "service_type" in columns:
            insert_columns.append("service_type")
            insert_values.append(service_type)

        if "order_type" in columns:
            insert_columns.append("order_type")
            insert_values.append(service_type)

        if "budget" in columns:
            insert_columns.append("budget")
            insert_values.append(budget)

        if "status" in columns:
            insert_columns.append("status")
            insert_values.append("new")

        if "agreed_price" in columns:
            insert_columns.append("agreed_price")
            insert_values.append(0)

        if "phone" in columns:
            insert_columns.append("phone")
            insert_values.append(phone)

        placeholders = ", ".join(["?"] * len(insert_columns))
        sql = f"INSERT INTO orders ({', '.join(insert_columns)}) VALUES ({placeholders});"
        cursor = await db.execute(sql, tuple(insert_values))
        await db.commit()
        order_id = cursor.lastrowid
    return int(order_id)


async def update_order_status(order_id: int, status: str) -> None:
    """
    Обновляет статус заказа.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE orders SET status = ? WHERE id = ?;",
            (status, order_id),
        )
        await db.commit()


async def set_order_price_and_status(order_id: int, agreed_price: int, status: str) -> None:
    """
    Обновляет согласованную цену и статус заказа.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE orders SET agreed_price = ?, status = ? WHERE id = ?;",
            (agreed_price, status, order_id),
        )
        await db.commit()


async def get_order_user_id(order_id: int) -> Optional[int]:
    """
    Возвращает user_id владельца заказа или None.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id FROM orders WHERE id = ?;",
            (order_id,),
        )
        row = await cursor.fetchone()
    return int(row[0]) if row else None


async def get_order_details(order_id: int) -> Optional[Tuple[int, int, str, str, str, int, str]]:
    """
    Возвращает детали заказа:
    (id, user_id, service_type, description, budget, agreed_price, status)
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, user_id, service_type, description, budget, agreed_price, status
            FROM orders
            WHERE id = ?;
            """,
            (order_id,),
        )
        row = await cursor.fetchone()
    if not row:
        return None
    return (int(row[0]), int(row[1]), row[2], row[3], row[4], int(row[5] or 0), row[6])


async def delete_order(order_id: int) -> None:
    """
    Полностью удаляет заказ из БД.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM orders WHERE id = ?;", (order_id,))
        await db.commit()


async def get_active_orders() -> List[Tuple[int, int, str, str]]:
    """
    Возвращает активные заказы (не completed и не cancelled):
    [(id, user_id, service_type, status), ...]
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, user_id, service_type, status
            FROM orders
            WHERE status NOT IN ('completed', 'cancelled')
            ORDER BY id DESC;
            """
        )
        rows = await cursor.fetchall()
    return [(int(r[0]), int(r[1]), r[2], r[3]) for r in rows]


async def add_review(user_id: int, order_id: int, stars: int) -> int:
    """
    Сохраняет или обновляет оценку клиента по заказу.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO reviews (user_id, order_id, stars)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, order_id) DO UPDATE SET
                stars = excluded.stars,
                created_at = CURRENT_TIMESTAMP;
            """,
            (user_id, order_id, stars),
        )
        await db.commit()
        return int(cursor.lastrowid or 0)


async def get_average_rating() -> Tuple[float, int]:
    """
    Возвращает средний рейтинг и количество отзывов: (avg_rating, total_reviews).
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT AVG(stars), COUNT(*) FROM reviews;")
        row = await cursor.fetchone()

    avg_value = float(row[0]) if row and row[0] is not None else 0.0
    total_reviews = int(row[1]) if row else 0
    return round(avg_value, 1), total_reviews


async def get_latest_reviews(limit: int = 3) -> List[Tuple[int, int, str, int]]:
    """
    Возвращает последние отзывы:
    [(user_id, order_id, service_type, stars), ...]
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("PRAGMA table_info(orders);")
        order_columns = {row[1] for row in await cursor.fetchall()}

        service_expr = "COALESCE(o.service_type, 'Не указано')"
        if "order_type" in order_columns:
            service_expr = "COALESCE(o.service_type, o.order_type, 'Не указано')"

        cursor = await db.execute(
            f"""
            SELECT
                r.user_id,
                r.order_id,
                {service_expr} AS service_name,
                r.stars
            FROM reviews r
            LEFT JOIN orders o ON o.id = r.order_id
            ORDER BY r.created_at DESC, r.id DESC
            LIMIT ?;
            """,
            (max(1, int(limit)),),
        )
        rows = await cursor.fetchall()

    return [(int(r[0]), int(r[1]), str(r[2]), int(r[3])) for r in rows]


async def get_stats() -> Tuple[int, int]:
    """
    Возвращает статистику: (кол-во пользователей, кол-во заказов).
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users;")
        users_count_row = await cursor.fetchone()
        users_count = int(users_count_row[0]) if users_count_row else 0

        cursor = await db.execute("SELECT COUNT(*) FROM orders;")
        orders_count_row = await cursor.fetchone()
        orders_count = int(orders_count_row[0]) if orders_count_row else 0

    return users_count, orders_count


async def get_all_user_ids() -> List[int]:
    """
    Возвращает список всех user_id для рассылки.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users;")
        rows = await cursor.fetchall()
    return [int(row[0]) for row in rows]


# === CRUD для услуг (services) ===

async def add_service(name: str, description: str, price_tjs: int) -> int:
    """
    Добавляет новую услугу. Возвращает ID созданной услуги.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO services (name, description, price_tjs) VALUES (?, ?, ?);",
            (name, description, price_tjs),
        )
        await db.commit()
        return int(cursor.lastrowid)


async def delete_service(service_id: int) -> None:
    """
    Удаляет услугу по ID.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM services WHERE id = ?;", (service_id,))
        await db.commit()


async def update_service_price(service_id: int, price_tjs: int) -> None:
    """
    Обновляет цену услуги.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE services SET price_tjs = ? WHERE id = ?;",
            (price_tjs, service_id),
        )
        await db.commit()


async def get_all_services() -> List[Tuple[int, str, str, int]]:
    """
    Возвращает все активные услуги: [(id, name, description, price_tjs), ...]
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, description, price_tjs FROM services WHERE is_active = 1 ORDER BY id;"
        )
        rows = await cursor.fetchall()
    return [(int(r[0]), r[1], r[2], int(r[3])) for r in rows]


async def get_all_services_admin() -> List[Tuple[int, str, str, int]]:
    """
    Возвращает все услуги для админки (включая неактивные): [(id, name, description, price_tjs), ...]
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, description, price_tjs FROM services ORDER BY id;"
        )
        rows = await cursor.fetchall()
    return [(int(r[0]), r[1], r[2], int(r[3])) for r in rows]


async def get_user_language(user_id: int) -> Optional[str]:
    """
    Возвращает язык пользователя из БД или None, если не найден.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT language FROM users WHERE user_id = ?;",
            (user_id,),
        )
        row = await cursor.fetchone()
    return row[0] if row else None


async def get_user_orders(user_id: int) -> List[Tuple[int, str, str]]:
    """
    Возвращает список заказов пользователя в виде
    [(id, service_type, status), ...] отсортированных по дате.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, service_type, status FROM orders WHERE user_id = ? ORDER BY created_at DESC;",
            (user_id,),
        )
        rows = await cursor.fetchall()
    return [(int(r[0]), r[1], r[2]) for r in rows]


async def get_service_by_id(service_id: int) -> Optional[Tuple[int, str, str, int]]:
    """
    Возвращает услугу по ID или None.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, description, price_tjs FROM services WHERE id = ?;",
            (service_id,),
        )
        row = await cursor.fetchone()
    if not row:
        return None
    return (int(row[0]), row[1], row[2], int(row[3]))


# === CRUD для портфолио ===

async def add_portfolio_item(
    title_ru: str,
    title_tj: str,
    description_ru: str,
    description_tj: str,
    photo_file_id: str,
    demo_link: Optional[str],
) -> int:
    """
    Добавляет элемент портфолио. Возвращает ID созданной записи.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO portfolio (
                title_ru, title_tj, description_ru, description_tj, photo_file_id, demo_link
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (title_ru, title_tj, description_ru, description_tj, photo_file_id, demo_link),
        )
        await db.commit()
        return int(cursor.lastrowid)


async def get_portfolio_count() -> int:
    """
    Возвращает количество записей в портфолио.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM portfolio;")
        row = await cursor.fetchone()
    return int(row[0]) if row else 0


async def get_portfolio_by_index(index: int) -> Optional[Tuple[int, str, str, str, str, str, Optional[str]]]:
    """
    Возвращает запись портфолио по индексу (0-based) в сортировке по id.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, title_ru, title_tj, description_ru, description_tj, photo_file_id, demo_link
            FROM portfolio
            ORDER BY id
            LIMIT 1 OFFSET ?;
            """,
            (index,),
        )
        row = await cursor.fetchone()
    if not row:
        return None
    return (int(row[0]), row[1], row[2], row[3], row[4], row[5], row[6])


async def get_all_portfolio_brief() -> List[Tuple[int, str, str]]:
    """
    Возвращает список портфолио для админки: [(id, title_ru, title_tj), ...]
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title_ru, title_tj FROM portfolio ORDER BY id;"
        )
        rows = await cursor.fetchall()
    return [(int(r[0]), r[1], r[2]) for r in rows]


async def delete_portfolio_item(portfolio_id: int) -> None:
    """
    Удаляет элемент портфолио по ID.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM portfolio WHERE id = ?;", (portfolio_id,))
        await db.commit()

