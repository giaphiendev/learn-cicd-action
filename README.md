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

- `$ sudo apt update`
- `$ sudo apt install nginx` -> check status `$ sudo systemctl status nginx` you can restart,... and more

### Configuration docker

- Follow [this](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04)

### Configuration docker-compose (Optional)

- Follow [this](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04)

## Authentication github action runners ()
