# Add Docker's official GPG key:
    sudo apt-get update
    sudo apt-get install ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update

# To install the latest version, run:

    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify that the installation is successful by running the hello-world image:

    sudo docker run hello-world

# Install the package using apt:

    sudo apt-get update

    sudo apt-get install ./docker-desktop-amd64.deb

# Создание сети в докере
    docker network create booking-network

# Создание image
    docker build -t booking-app-image:0.7 .
    docker build --no-cache -t booking-app-image:0.7 .

# Создание контейнеров
    docker run --name nginx-booking \
        --volume ./nginx.conf:/etc/nginx/nginx.conf \
        --volume /etc/letsencrypt/live:/etc/letsencrypt/live \
        --volume /etc/letsencrypt:/etc/letsencrypt \
        --network=booking-network \
        -d -p 80:80 -p 443:443 nginx

    docker run  --name pg-booking \
        --env-file .env.docker \
        --network=booking-network \
        -p 6432:5432 \
        --volume pg-booking-data:/var/lib/postgresql/data \
        -d postgres:16


    docker run --name cont-booking-redis \
        --network=booking-network \
        -d redis:7.4
    
    docker run --name cont-booking-app \
        --env-file .env.docker \
        --network=booking-network \
        -p 8888:8000 \
        booking-app-image:0.7

    docker run --name cont-booking-app \
        --env-file .env.docker \
        --network=booking-network \
        -p 8888:8000 \
        booking-app-image:0.7


    docker run --name celery-worker \ 
        --env-file .env.docker \
        --network=booking-network \
        booking-app-image:0.7 \
        celery --app=src.celery_tasks.celery_app:celery_inst worker --loglevel INFO
    
    docker run --name celery-beat \
        --env-file .env.docker \
        --network=booking-network \
        booking-app-image:0.7 \
        celery --app=src.celery_tasks.celery_app:celery_inst beat --loglevel INFO

git config --local user.name "Alexander Borodin"
git config --local user.email "alexboradi@gmail.com"
