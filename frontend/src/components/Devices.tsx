import React, {useEffect, useState} from "react";
import {send_request} from "../utils/requests";
import { loadConfig } from '../utils/configLoader';
import {Config} from '../utils/types';

import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Grid from '@mui/material/Grid2';

import Device from '../utils/types';
import {DeviceCard} from "../utils/Devices/DeviceCard";
import {DeviceRegister} from "../utils/Devices/DeviceRegister";
import {DeviceHistory} from "../utils/Devices/DeviceHistory";


interface DevicesProps {

}

export const Devices: React.FC<DevicesProps> = () => {
    const [config, setConfig] = useState<Config>({})
    const [devices, setDevices] = useState<Array<Device>>([]);
    const [toUpdate, setToUpdate] = useState(false);

    useEffect(() => {
        const getConfig = async () => {
            const new_config = await loadConfig();
            setConfig(new_config)
            setToUpdate(true);
        };
        getConfig();
    }, [])

    const get_devices = async () => {
        const response = await send_request(config["backend_url"], "devices", {});
        const json_response = await response.json();

        if ("devices" in json_response)
        {
            setDevices(json_response["devices"]);
        }
    }

    useEffect(() => {
        if (toUpdate) {
            if (Object.keys(config).length > 0) {
                get_devices();
            }
            setToUpdate(false);
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
                <Grid padding={"10px"} container spacing={1} sx={{
                    backgroundColor: "#FFEE93"
                }}>
                    <DeviceHistory />
                </Grid>
            </Box>

        </Container>
    )
}