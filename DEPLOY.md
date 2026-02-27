# MyAgency Bot — Server Deploy

## 1) Подготовка сервера (Ubuntu)
- Обновить систему: `sudo apt update && sudo apt upgrade -y`
- Установить Python: `sudo apt install -y python3 python3-venv python3-pip`
- Создать каталог: `sudo mkdir -p /opt/myagency-bot && sudo chown -R $USER:$USER /opt/myagency-bot`

## 2) Копирование проекта
- Скопировать файлы проекта в `/opt/myagency-bot`
- Убедиться, что рядом с `main.py` есть `requirements.txt`

## 3) Виртуальное окружение
- `cd /opt/myagency-bot`
- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip install --upgrade pip`
- `pip install -r requirements.txt`

## 4) Конфигурация (секреты только в .env)
- Создать `.env` на основе `.env.example`
- Пример:
  - `BOT_TOKEN=...`
  - `ADMIN_ID=...`
  - `PAYMENT_CARD=...`
  - `DATABASE_PATH=/opt/myagency-bot/myagency.db`

Запуск через shell:
- `set -a; source .env; set +a; python main.py`

## 5) Systemd (production)
Создать `/etc/systemd/system/myagency-bot.service`:

```ini
[Unit]
Description=MyAgency Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/myagency-bot
EnvironmentFile=/opt/myagency-bot/.env
ExecStart=/opt/myagency-bot/.venv/bin/python /opt/myagency-bot/main.py
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Команды:
- `sudo systemctl daemon-reload`
- `sudo systemctl enable myagency-bot`
- `sudo systemctl start myagency-bot`
- `sudo systemctl status myagency-bot`
- `journalctl -u myagency-bot -f`

## 6) Безопасность
- Не коммитить `.env` и базу данных.
- Ограничить доступ к каталогу: `chmod 700 /opt/myagency-bot`.
- Регулярно менять токен бота при утечках.
- Делать бэкап файла БД по расписанию.

## 7) Docker Compose (альтернатива)
- Создать `.env` рядом с `docker-compose.yml` (по шаблону `.env.example`).
- Убедиться, что задано:
  - `BOT_TOKEN`
  - `ADMIN_ID`
  - `PAYMENT_CARD`
- Запуск:
  - `docker compose up -d --build`
- Логи:
  - `docker compose logs -f myagency-bot`
- Остановка:
  - `docker compose down`
