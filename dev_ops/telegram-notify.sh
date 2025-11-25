#!/bin/bash
source .env

send_telegram() {
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="$TELEGRAM_CHAT_ID" \
        -d text="$message"
}

message="✅ Сертификаты обновлены! Домены: $RENEWED_DOMAINS"
send_telegram "$message"
