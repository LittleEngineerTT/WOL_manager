"""
This file is useful to abstract database implementation
"""

from core.database import get_db, Base

from typing import Self

from sqlalchemy import Column, String, func


class Device(Base):
    """
    Class to interact with a device inside the database.
    """

    __tablename__ = 'devices'
    hostname = Column(String, nullable=False)
    mac = Column(String, primary_key=True, nullable=False, unique=True)
    ip = Column(String, nullable=False, unique=True)


    @classmethod
    def get_devices(cls) -> list[Self]:
        """
        Get all devices
        """
        devices = None
        db = get_db()
        try:
            devices = db.query(cls).all()
        finally:
            db.close()
            return devices


    @classmethod
    def add_device(cls, device: Self) -> None:
        """
        Add device to the database.
        """
        db = get_db()
        try:
            device_instance = cls(**device)
            db.add(device_instance)

            # Save changes
            db.commit()
        finally:
            db.close()


    @classmethod
    def delete_device(cls, device: Self) -> None:
        """
        Delete device from the database.
        """
        db = get_db()
        try:
            device_instance = db.query(cls).filter(func.lower(cls.mac) == device["mac"].lower()).first()
            db.delete(device_instance)

            # Save changes
            db.commit()
        finally:
            db.close()


    @classmethod
    def update_device(cls, device: Self) -> None:
        """
        Delete device from the database.
        """
        db = get_db()
        try:
            device_instance = db.query(cls).filter(cls.mac == device["mac"].upper()).first()

            if device_instance:
                device_instance.hostname = device["hostname"]
                device_instance.ip = device["ip"]

                # Save changes
                db.commit()
        finally:
            db.close()
