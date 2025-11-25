# Создание и запуск контейнеров

## На локальном ПК.
### Копирование с локального пк на сервер в папку пользователя.
```bash
    scp -r dev_ops user@vps_server:~/velvet
```

## На сервере.
- Зайти в папку.
```bash
    cd velvet
```

- Создать или скопировать .env(смотри env.md)
```bash
    touch .env
```

- Создать докер сеть
```bash
    docker network create velvet
````

- Запуск контейнера postgresql
```bash
    docker run  --name postgresql-container \
        --env-file .env.docker \
        --network=velvet \
        -p 5432:5432 \
        --volume postgresql-data:/var/lib/postgresql/data \
        --restart always \
        -d postgres:16

```

- Запуск контейнера redis
```bash
    docker run --name redis-container \
        --network=velvet \
        -p 6379:6379 \
        --restart always \
        -d redis:7.4
```

- Запуск контейнера nginx
```bash
    docker run --name nginx-container \
        --volume ./nginx.conf:/etc/nginx/nginx.conf \
        --volume /etc/letsencrypt:/etc/letsencrypt \
        --network=velvet \
        --restart always \
        -d -p 80:80 -p 443:443 nginx
```

- Запуск контейнеров minio
```bash
    docker compose -f docker-compose-minio.yml up -d
```


- Подключить cron скрипт для обновления сертификата

```sh
    0 3 * * * /home/user_folder/velvet/certbot-renew.sh
```