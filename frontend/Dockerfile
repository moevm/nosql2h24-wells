FROM ubuntu:22.04

RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

COPY . /var/www/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
