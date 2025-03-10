import Device from "../types";
import React, {useState, useEffect} from "react";
import {Button, TextField} from "@mui/material";
import Grid from '@mui/material/Grid2';
import {send_request} from "../requests";
import { loadConfig } from '../configLoader';
import {Config} from '../types';




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
    setToUpdate: React.Dispatch<React.SetStateAction<boolean>>;
}

export const DeviceRegister: React.FC<DeviceRegisterProps> = ({setToUpdate}) => {
  const [config, setConfig] = useState<Config>({})
  const [hostname, setHostname] = useState<string>("");
  const [mac, setMac] = useState<string>("");
  const [deviceIP, setDeviceIP] = useState<string>("");
  const [configResolved, setConfigResolved] = useState(false);

  useEffect(() => {
        const getConfig = async () => {
            setConfig(await loadConfig());
            setConfigResolved(true);
        };
        getConfig();
    }, [])

  const register_device = async () => {

      if (configResolved) {
          // Create device from form data
          const new_device: Device = {
              hostname: hostname,
              mac: mac,
              ip: deviceIP
          }

          await send_request(config["backend_url"], "register", new_device);
          setToUpdate(true);
      }
    }

    const update_device = async () => {
      if (configResolved) {
          // Create device from form data
          const new_device: Device = {
              hostname: hostname,
              mac: mac,
              ip: deviceIP
          }

          await send_request(config["backend_url"], "update", new_device);
          setToUpdate(true);
      }
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
                <FieldEntry inputData={deviceIP} setInputData={setDeviceIP} title={"IP"}/>

                <Grid size={11} >
                    <Button variant={"text"} onClick={update_device} sx={{color: '#FFC09F'}}>
                        Update
                    </Button>
                </Grid>


                <Grid size={1} >
                    <Button variant={"text"} onClick={register_device} sx={{color: '#FFC09F',}}>
                        Register
                    </Button>
                </Grid>

            </Grid>

        </div>
    );
}
