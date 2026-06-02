# Запуск скрипта на Android

Telethon — это обычный Python, поэтому на Android он работает через **Termux**
(а не через официальное Telegram-приложение). Сессию Telegram-клиента
переиспользовать нельзя, но логин в Telethon делается один раз — дальше
скрипт запускается сам.

## 1. Установка

1. Поставь **Termux** из F-Droid (версия из Google Play устарела):
   https://f-droid.org/packages/com.termux/
2. (Опционально, для авто-старта при включении телефона) поставь
   **Termux:Boot** из того же F-Droid.
3. Открой Termux и выполни:

   ```sh
   pkg update -y
   pkg install -y python git
   termux-setup-storage   # даст доступ к памяти телефона
   git clone <URL твоего репозитория> ~/spamer
   cd ~/spamer
   pip install -r requirements.txt
   ```

## 2. Конфигурация

1. Создай `.env` из примера:

   ```sh
   cp .env.example .env
   nano .env
   ```

   Вставь `TG_API_ID` и `TG_API_HASH` с https://my.telegram.org.

2. Поправь `recipients.csv` (свой реальный список) и `template.txt`
   (текст поздравления).

## 3. Первый запуск (однократный логин)

```sh
cd ~/spamer
python send_greetings.py
```

Telethon спросит номер телефона и пришлёт код в Telegram (и/или SMS).
После ввода кода появится файл `greetings_session.session` — это твоя
сохранённая авторизация. Больше код вводить не нужно.

> Если включена двухфакторка — попросит ещё облачный пароль.

## 4. Авто-запуск

### Вариант A: один раз при включении телефона (Termux:Boot)

После установки Termux:Boot открой его один раз, чтобы дать разрешения, потом:

```sh
mkdir -p ~/.termux/boot
cp android/run_on_boot.sh ~/.termux/boot/spamer
chmod +x ~/.termux/boot/spamer
```

Скрипт `~/.termux/boot/spamer` будет запускаться при загрузке устройства.

### Вариант B: по расписанию (cron внутри Termux)

```sh
pkg install -y cronie termux-services
sv-enable crond
crontab -e
```

Добавь строку (запуск каждый день в 09:00):

```
0 9 * * * cd ~/spamer && /data/data/com.termux/files/usr/bin/python send_greetings.py >> send_log.txt 2>&1
```

### Вариант C: разовый запуск из ярлыка

Поставь **Termux:Widget** (F-Droid) и положи `android/run_on_boot.sh`
в `~/.shortcuts/spamer.sh` — на рабочем столе появится кнопка-ярлык.

## 5. Чтобы Android не убивал Termux в фоне

В системных настройках:

- Battery → Battery optimization → Termux → **Don't optimize**
- Auto-start / фоновая активность → разрешить для Termux
- Если есть Termux:Boot — то же самое для него

Без этого Android может выгрузить процесс до завершения отправки.

## 6. Если переносишь уже залогиненную сессию

Файл `greetings_session.session` (и `*.session-journal`, если есть) можно
скопировать с компьютера на телефон в `~/spamer/` — Telethon подхватит
авторизацию и не будет повторно спрашивать код.
