# Intro This Project

- We learn about Continuous Integration - Continuous Delivery (CI-CD)
- How to implement automatically the app to ec2 - ecs

# INSTALLATION

- Copy `.env.example` to `.env.dev` and edit it to your needs.
- `$ cp .env.example .env.dev`

# WITH DOCKER

- `$ docker-compose -f docker/docker-compose.yml up -d --build`

## Migrate for the first time

- `docker-compose -f docker/docker-compose.yml exec backend python manage.py migrate`

### Git

- `$ ssh-keygen`
- `$ eval 'ssh-agent -s'`
- `$ ssh-add ~/.ssh/id_rsa`
- `$ cat ~/.ssh/id_rsa.pub`

### acc git

- `giaphiendev`
- `h***0388******`

# Lauch instance ec2

## Prerequisites

### Configuration Nginx 
-[Followed by this](https://www.digitalocean.com/community/tutorials/how-to-configure-nginx-as-a-reverse-proxy-on-ubuntu-22-04)

- `$ sudo apt update`
- `$ sudo apt install nginx` -> check status `$ sudo systemctl status nginx` you can `restart` instead.
- `$ sudo ufw allow 'Nginx HTTP'`
- Configuration Nginx, it located in `/etc/nginx`
- Make a new file inside `/etc/nginx/sites-available` folder
```
server {
    listen 80;
    listen [::]:80;

    server_name _;
        
    location / {
        proxy_pass http://localhost:8000/;
        include proxy_params;
    }
}
```

### Configuration docker

- Follow [this](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04)

### Configuration docker-compose (Optional)

- Follow [this](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04)

## Authentication [github action runners](https://github.com/giaphiendev/learn-cicd-action/settings/actions/runners)
- After install github actions
- Install svc `$ sudo ./svc.sh install`
- To start svc `$ sudo ./svc.sh start`
- To stop svc `$ sudo ./svc.sh stop`
