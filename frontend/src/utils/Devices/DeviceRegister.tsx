import {Device} from "../types";
import React, {useState} from "react";
import {Button, TextField} from "@mui/material";
import Grid from '@mui/material/Grid2';
import {send_request} from "../requests";
import config from "../../config.d/config.yaml";


interface FieldEntryProps {
    title: string;
    inputData: string;
    setInputData: React.Dispatch<React.SetStateAction<string>>;
}


const FieldEntry: React.FC<FieldEntryProps> = ({inputData, setInputData, title}) => {
    const handleInput = (event: React.ChangeEvent<HTMLInputElement>) => {
        setInputData(event.target.value);
    };

    return (
        <>
            <Grid size={4} sx={{
                display: 'flex',
                alignContent: 'center',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                {title}:
            </Grid>
            <Grid size={8} >
                <TextField fullWidth={true} value={inputData} onChange={handleInput}/>
            </Grid>
        </>
    )
}



interface DeviceRegisterProps {
    setDevices: React.Dispatch<React.SetStateAction<Array<Device>>>;
}

export const DeviceRegister: React.FC<DeviceRegisterProps> = ({setDevices}) => {
  const [hostname, setHostname] = useState<string>("");
  const [mac, setMac] = useState<string>("");
  const [deviceInterface, setDeviceInterface] = useState<string>("");

  const register_device = async () => {
        // Create device from form data
        const new_device: Device = {
            hostname: hostname,
            mac: mac,
            interface: deviceInterface
        }

        await send_request(config.backend_url, "register", new_device);
        setDevices([]);
    }

    return (
        <div style={{
            padding: '10px'
        }}>
            Register device
            <Grid container sx={{
                border: '1px solid',
                padding: '10px'
            }}>
                <FieldEntry inputData={hostname} setInputData={setHostname} title={"Hostname"}/>
                <FieldEntry inputData={mac} setInputData={setMac} title={"Mac"}/>
                <FieldEntry inputData={deviceInterface} setInputData={setDeviceInterface} title={"Interface"}/>
                <Button variant={"text"} onClick={register_device} sx={{color: '#FFC09F'}}>
                    Register
                </Button>
            </Grid>

        </div>
    );
}
