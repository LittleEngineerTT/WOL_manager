import Device from "../types";
import React, {useEffect, useState} from "react";
import {Box} from "@mui/material";
import {Button} from "@mui/material";
import {send_request} from "../requests";
import config from "../../config.d/config.yaml";

interface DeviceCardProps {
    device: Device;
    setToUpdate: React.Dispatch<React.SetStateAction<boolean>>;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({device, setToUpdate}) => {

    const [status, setStatus] = useState(false);

    const get_status = async () => {
        const response = await send_request(config.backend_url, "status", device);
        const json_response = await response.json();

        if ("status" in json_response)
        {
            setStatus(json_response["status"]);
        }
    }

    const start_device = async () => {
        await send_request(config.backend_url, "start", device);
    }

    const delete_device = async () => {
        await send_request(config.backend_url, "delete", device);
        setToUpdate(true);
    }

    useEffect(() => {
        setInterval(get_status, 10000);
    }, [])

    return (
        <Box>
            <div>
                {device.hostname}
            </div>
            <div>
                status: {status ? "True" : "False"}
            </div>
            <div>
                ip: {device.ip}
            </div>
            <div>
                mac: {device.mac}
            </div>
            <Button variant={"text"} onClick={start_device} sx={{color: '#FFC09F'}}>
                Start
            </Button>

            <Button variant={"text"} onClick={delete_device} sx={{color: '#FFC09F'}}>
                Delete
            </Button>
        </Box>
    )
}