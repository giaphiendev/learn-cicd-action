# Intro This Project
- We learn about Continuous Integration - Continuous Delivery (CI-CD)
- How to implement automatically the app to ec2 - ecs

# INSTALLATION

* Copy `.env.example` to `.dkm` and edit it to your needs.
* `$ cp .env.example .env`

# WITH DOCKER

* `$ docker-compose -f docker/docker-compose.yml up -d --build`
* Open browser and go to `localhost:8000/api/doc/` to see swagger

## Migrate for the first time

* `docker-compose -f docker/docker-compose.yml exec backend python manage.py migrate`

### Get container's log

* `$ docker logs [container_name] -f`

### Seed data (Role)

* `$ docker-compose -f docker/docker-compose.yml exec backend python manage.py loaddata seed/0001_Role.json`

## Process signup and login

- call `api/auth/get-pin` to generate pin and get token for validate pin
- after that, call `api/auth/sign-up`  to sign up or `api/auth/login` to login

### Git

- `$ ssh-keygen`
- `$ eval 'ssh-agent -s'`
- `$ ssh-add ~/.ssh/id_rsa`
- `$ cat ~/.ssh/id_rsa.pub`

### acc git

- `giaphiendev`
- `h***0388******`

### To push noti django to mobile via expo - follow [this tutorial](https://docs.expo.dev/push-notifications/sending-notifications/)



# Configuration Nginx
- `$ sudo apt update`
- `$ sudo apt install nginx`