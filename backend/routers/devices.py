from core.config import get_config
from libs.logger import setup_logger
from schemas.devices import Device
from workers.status_checker import StatusChecker

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

devices = APIRouter(
    prefix="",
    tags=["devices"]
)

# Get config
config = get_config()

# Set up logger
logger = setup_logger("history.log")

# Create status checker instance
status_checker = StatusChecker(config["network"], logger=logger)


@devices.get("/devices")
def retrieve_devices():
    devices = Device.get_devices()
    status_checker.devices = devices
    return {"devices": devices}


@devices.post("/status")
def get_status(device: Device):
    status = status_checker.devices_status[device.mac]
    return {"status": status}


@devices.post("/start")
def start_device(device: Device):
    logger.info("Starting device %s", device.hostname)
    device.start()
    return


@devices.post("/register")
def register_device(device: Device):
    logger.info("Registering device %s", device.hostname)
    status_code = device.register()

    if status_code != 200:
        raise HTTPException(status_code=status_code)

    return


@devices.post("/delete")
def delete_device(device: Device):
    logger.info("Deleting device %s", device.hostname)
    device.delete()
    return


@devices.post("/update")
def update_device(device: Device):
    logger.info(f"Updating device %s", device.hostname)
    device.update()
    return