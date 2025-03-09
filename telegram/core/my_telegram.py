from schemas.devices import Device

import json
import os
import re
import yaml

from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ApplicationBuilder,
    MessageHandler,
    filters,
)
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update


help_text = "/add NAME MAC IP\n\n/delete DEVICE_NAME\n\n/devices\n\n/start DEVICE_NAME\n\n/status DEVICE_NAME"


def get_config():
    with open("./config.yml", "r") as file:
        config = yaml.safe_load(file)
    return config


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/status\s{1,}[^\s]+\s{0,}", last_message):
        device_name = last_message.split(" ")[-1] if last_message.split(" ")[-1] != "" else last_message.spliti(" ")[-2]

        devices = Device.get_devices()
        selected_device = None
        for device in devices:
            if device.hostname == device_name:
                selected_device = device

        if not selected_device:
            text = "Device not found"
            await update.message.reply_text(text)
            return

        started = Device.get_status(selected_device)
        if not started:
            text = "This ressource is down"
            await update.message.reply_text(text)
        else:
            text = f"{device_name} is up"
            await update.message.reply_text(text)
    else:
        context.user_data["action"] = "status"
        devices = Device.get_devices()

        if devices:
            keyboard = [[device.hostname] for device in devices]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "Which devices to check?:", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("No devices")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/start\s{1,}[^\s]+\s{0,}", last_message):
        message_text = last_message.split(" ")
        device_name = message_text[1]

        devices = Device.get_devices()

        if device_name == "all":
            Device.start_device(devices)
            text = "Starting all devices"
            await update.message.reply_text(text)
            return


        selected_device = None
        for device in devices:
            if device.hostname == device_name:
                selected_device = device

        if not selected_device:
            text = "Device not found"
            await update.message.reply_text(text)
            return

        Device.start_device([selected_device])
        text = "Starting device"
        await update.message.reply_text(text)

    else:
        context.user_data["action"] = "start"
        devices = Device.get_devices()
        if devices:
            keyboard = [[device.hostname] for device in devices]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "Which devices to power on:", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("No devices")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(help_text)


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text

    if re.match(r"/add [^\s]+ [^\s]+ [^\s]+", last_message):
        message_text = last_message.split(" ")

        data = {
            "hostname": message_text[1],
            "mac": message_text[2],
            "ip": message_text[3]
        }
        device = Device(**data)

        if Device.register_device(device):
            text = "Successfully added"
            await update.message.reply_text(text)

        else:
            text = "ERROR: bad_message_format example: /add router_test a1:b6:23:dc:ff:99 10.0.0.2"
            await update.message.reply_text(text)
    else:
        await update.message.reply_text("Unknown command\n" + help_text)


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/delete [^\s]+", last_message):
        message_text = last_message.split(" ")
        device_name = message_text[-1]

        devices = Device.get_devices()

        if device_name == "all":
            Device.delete_device(devices)
            text = "Deleting all"
            await update.message.reply_text(text)
            return

        selected_device = None
        for device in devices:
            if device.hostname == device_name:
                selected_device = device

        if not selected_device:
            text = "Device not found"
            await update.message.reply_text(text)
            return

        if Device.delete_device([selected_device]):
            text = "Device deleted"
            await update.message.reply_text(text)
        else:
            text = "Device not found. See /devices"
            await update.message.reply_text(text)
    else:
        await update.message.reply_text("Unkown command\n" + help_text)


async def show_devices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/devices", last_message):
        devices = Device.get_devices()
        text = [str(device.dict()) for device in devices]
        await update.message.reply_text("\n\n".join(text))


async def select_device(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    device_name = update.message.text

    devices = Device.get_devices()
    selected_device = None
    for device in devices:
        if device.hostname == device_name:
            selected_device = device

    if not selected_device and device_name != "all":
        text = "ERROR: device_name_not_in_database send /devices to print known devices"
        await update.message.reply_text(text)
    else:
        if context.user_data.get("action") == "start":
            if device_name == "all":
                Device.start_device(devices)
                text = f"Starting all"
                await update.message.reply_text(text)
            else:
                Device.start_device([selected_device])
                text = f"Starting {device_name}"
                await update.message.reply_text(text)
        elif context.user_data.get("action") == "status":
            started = Device.get_status(selected_device)
            if not started:
                text = f"{device_name} is down"
                await update.message.reply_text(text)
            else:
                text = f"{device_name} is up"
                await update.message.reply_text(text)
        # TODO: Add delete
        context.user_data["action"] = None


def new_telegram_run():
    global last_message
    # Load config
    config = get_config()
    bot_token = config["bot_token"]

    application = ApplicationBuilder().token(bot_token).read_timeout(10).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), select_device)
    )
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("devices", show_devices))

    application.run_polling()
