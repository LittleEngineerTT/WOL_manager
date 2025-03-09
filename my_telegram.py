import json
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
from wake_me_up import *

from status_checker import *


help_text = "/add NAME MAC ROUTER_INTERFACE\n\n/delete DEVICE_NAME\n\n/devices\n\n/start DEVICE_NAME STARTING_TIME\n\n/status DEVICE_NAME"


def get_config():
    with open("config.yml", "r") as file:
        config = yaml.safe_load(file)
    return config


def is_a_valid_mac_address(message_text):
    splited_message = message_text.split(" ")
    return (
        True
        if re.match(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", splited_message[2])
        else False
    )


def store_new_pair(message, filename):
    """

    :param message:
    :param filename:
    :return:
    """
    splitted_message = message.split(" ")
    if not os.path.isfile(filename):
        with open(filename, "w"):
            pass
        name_to_mac = {}
    else:
        with open(filename, "r") as file1:
            try:
                name_to_mac = json.loads(file1.read())
            except json.decoder.JSONDecodeError:
                name_to_mac = {}
    name_to_mac[splitted_message[1]] = {
        "mac": splitted_message[2],
        "interface": splitted_message[3],
    }
    with open(filename, "w") as file1:
        file1.write(json.dumps(name_to_mac))


def get_devices(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as file1:
            file1.write("{}")
    with open(filename) as file1:
        all_pairs = json.loads(file1.read())
    return [k for k in all_pairs.keys()]


def get_data_from_name(name, filename):
    """
    Get mac or interface from name.
    :param name: str
    :param filename: str
    :param data: str (mac | interface)
    :return: str
    """
    if not os.path.exists(filename):
        return None, None
    with open(filename, "r") as file1:
        name_to_mac = json.loads(file1.read())
    try:
        return name_to_mac[name]["mac"], name_to_mac[name]["interface"]
    except:
        return None, None


def delete_mac_from_name(name, filename):
    with open(filename, "r") as file1:
        name_to_mac = json.loads(file1.read())
    if name in name_to_mac.keys():
        del name_to_mac[name]
        with open(filename, "w") as file1:
            file1.write(json.dumps(name_to_mac))
        return True
    return False


async def run_multiple_status(update: Update, device_names):
    for device in device_names:
        mac, interface = get_data_from_name(device, name_to_mac_file)
        started = status_checker(mac, 0, config)
        if not started:
            text = f"{device} is down"
            await update.message.reply_text(text)
        else:
            text = f"{device} Up"
            await update.message.reply_text(text)

async def run_multiple_start(update: Update, device_names):
    for device in device_names:
        mac, interface = get_data_from_name(device, name_to_mac_file)
        wake_me_up(mac, config, interface)
        text = f"Starting {device}"
        await update.message.reply_text(text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/status\s{1,}[^\s]+\s{0,}", last_message):
        device_name = last_message.split(" ")[-1] if last_message.split(" ")[-1] != "" else last_message.spliti(" ")[-2]
        if device_name == "all":
            device_names = get_devices(name_to_mac_file)
            await run_multiple_status(update, device_names)
        else:
            mac, interface = get_data_from_name(device_name, name_to_mac_file)
            started = status_checker(mac, 0, config)
            if not started:
                text = "This ressource is down"
                await update.message.reply_text(text)
            else:
                text = f"{device_name} is up"
                await update.message.reply_text(text)
    else:
        context.user_data["action"] = "status"
        device_names = get_devices(name_to_mac_file)
        if device_names:
            keyboard = [[device] for device in device_names]
            keyboard[0].append("all")
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "Which devices to check?:", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("Null bitch")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/start\s{1,}[^\s]+\s{0,}([0-9]+)?", last_message):
        message_text = last_message.split(" ")
        #starting_time = message_text[-1] if message_text[-1].isdigit() and len(message_text) == 3 else 40
        device_name = message_text[1]
        if device_name == "all":
            device_names = get_devices(name_to_mac_file)
            await run_multiple_start(update, device_names)
        else:
            mac, interface = get_data_from_name(device_name, name_to_mac_file)
            if not mac:
                text = "ERROR: device_name_not_in_database send /devices to print known devices"
                await update.message.reply_text(text)
            wake_me_up(mac, config, interface)
            text = "Starting device"
            await update.message.reply_text(text)
    else:
        context.user_data["action"] = "start"
        device_names = get_devices(name_to_mac_file)
        if device_names:
            keyboard = [[device] for device in device_names]
            keyboard[0].append("all")
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "Which devices to power on:", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("Null bitch.")


async def select_device(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    device_name = update.message.text
    mac, interface = get_data_from_name(device_name, name_to_mac_file)

    if not mac and device_name != "all":
        text = "ERROR: device_name_not_in_database send /devices to print known devices"
        await update.message.reply_text(text)
    else:
        device_names = get_devices(name_to_mac_file)
        if context.user_data.get("action") == "start":
            if device_name == "all":
                await run_multiple_start(update, device_names)
            else:
                wake_me_up(mac, config, interface)
                text = f"Starting {device_name}"
                await update.message.reply_text(text)
        elif context.user_data.get("action") == "status":
            if device_name == "all":
                await run_multiple_status(update, device_names)
            else:
                started = status_checker(mac, 0, config)
                if not started:
                    text = f"{device_name} is down"
                    await update.message.reply_text(text)
                else:
                    text = f"{device_name} is up"
                    await update.message.reply_text(text)
        context.user_data["action"] = None


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(help_text)


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/add [^\s]+ [^\s]+ [^\s]+", last_message):
        if is_a_valid_mac_address(last_message):
            store_new_pair(last_message, name_to_mac_file)
            text = "Successfully added"
            await update.message.reply_text(text)
        else:
            text = "ERROR: bad_message_format example: /add router_test a1:b6:23:dc:ff:99 eth0"
            await update.message.reply_text(text)
    else:
        await update.message.reply_text("Unknown command\n" + help_text)


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/delete [^\s]+", last_message):
        if delete_mac_from_name(last_message.split(" ")[1], name_to_mac_file):
            text = "Device deleted"
            await update.message.reply_text(text)
        else:
            text = "Device not found. See /devices"
            await update.message.reply_text(text)
    else:
        await update.message.reply_text("Unkown command\n" + help_text)


async def devices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    last_message = update.message.text
    if re.match(r"/devices", last_message):
        text = get_devices(name_to_mac_file)
        await update.message.reply_text(text)


def new_telegram_run():
    global ssh_file, bot_token, ssh_password, name_to_mac_file, last_message, config
    config = get_config()
    ssh_file = config["path_to_private_key"]
    bot_token = config["bot_token"]
    ssh_password = config["ssh_password"]
    name_to_mac_file = config["name_to_mac_file"]

    application = ApplicationBuilder().token(bot_token).read_timeout(10).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), select_device)
    )
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("devices", devices))

    application.run_polling()
