docker-compose up -d postgres redis rabbitmq
sleep 5
docker-compose up -d --build
