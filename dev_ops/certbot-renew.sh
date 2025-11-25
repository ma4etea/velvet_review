#!/bin/bash
set -e
source .env

send_telegram() {
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="TELEGRAM_CHAT_ID" \
        -d text="$message"
}

# Основной блок
{
    # Останавливаем контейнер, запускаем nginx на хосте
    docker stop nginx-container
    sudo systemctl start nginx

    sudo certbot renew --quiet --deploy-hook "./telegram-notify.sh"

    # Останавливаем хост nginx и запускаем контейнер обратно
    sudo systemctl stop nginx
    docker start nginx-container

} || {
    # Если любая команда упала, захватываем ошибку
    error_output=$(tail -n 10 /var/log/syslog)  # или можно просто stderr предыдущей команды
    send_telegram "❌ Ошибка обновления сертификатов!\n$error_output"
}
