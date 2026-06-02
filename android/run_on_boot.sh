#!/data/data/com.termux/files/usr/bin/sh
# Стартовый скрипт для Termux:Boot и Termux:Widget.
# Кладётся в ~/.termux/boot/spamer  или  ~/.shortcuts/spamer.sh
# Не даёт телефону уснуть на время отправки.

termux-wake-lock 2>/dev/null

cd "$HOME/spamer" || exit 1

PY="/data/data/com.termux/files/usr/bin/python"
"$PY" send_greetings.py >> send_log.txt 2>&1

termux-wake-unlock 2>/dev/null
