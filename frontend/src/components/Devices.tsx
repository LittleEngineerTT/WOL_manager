import React, {useEffect, useState} from "react";
import {send_request} from "../utils/requests";
import config from "../config.d/config.yaml";

import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Grid from '@mui/material/Grid2';

import Device from '../utils/types';
import {DeviceCard} from "../utils/Devices/DeviceCard";
import {DeviceRegister} from "../utils/Devices/DeviceRegister";


interface DevicesProps {

}

export const Devices: React.FC<DevicesProps> = () => {
    const [devices, setDevices] = useState<Array<Device>>([]);
    const [toUpdate, setToUpdate] = useState(true);

    const get_devices = async () => {
        const response = await send_request(config.backend_url, "devices", {});
        const json_response = await response.json();

        if ("devices" in json_response)
        {
            setDevices(json_response["devices"]);
        }
    }

    useEffect(() => {
        if (toUpdate) {
            setToUpdate(false);
            get_devices();
        }
    }, [toUpdate])

    return (
        <Container sx={{
            alignItems: 'center',
            width: "80%",
            padding: "10px",
            justifyContent: 'center',
            display: "flex"
        }}>
            <Box sx={{
                width: '90%'
            }}>
                Devices
                <Grid padding={"10px"} container spacing={1} sx={{
                    border: "1px solid",
                    backgroundColor: "#FFEE93"
                }}>

                    {devices.map((device, index) => (
                        <Grid size={4} key={index} border={"1px solid"} spacing={1} sx={{
                            display: "flex",
                            justifyContent: 'center',
                            backgroundColor: '#FCF5C7'
                        }}>
                            <DeviceCard device={device} setToUpdate={setToUpdate}/>
                        </Grid>
                    ))}
                </Grid>

                    <DeviceRegister setToUpdate={setToUpdate}/>
            </Box>

        </Container>
    )
}