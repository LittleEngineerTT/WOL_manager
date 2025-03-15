# WOL Manager

Simple WOL (Wake-on-lan) project that let you manage multiple devices. \
This WOL manager can take two forms. \
First is a web app, second is a telegram bot.

## Web App

### Requirements
- docker compose

### Configuration
- Fulfil `backend/config.d/config.yml` network field with your bot-id.
- Feel free to change default path of database_url
- Generate ssl certificate inside frontend/cert/ using `openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mydomain.local.key -out mydomain.local.crt`.


## Telegram

### Requirements
- docker compose

### Configuration
- In the root dir, edit .env file to select a very strong api-key
- Create a telegram bot using BotFather then claim its ID
- Fulfil `backend/config.d/config.yml` network field with your
- Talk to the bot using `/help` and see actions.

## Execution
- Exec `docker compose build && docker compose up -d`
