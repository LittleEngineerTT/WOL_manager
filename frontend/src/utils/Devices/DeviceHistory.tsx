import React, {useEffect, useState} from "react";

import {send_request} from "../requests";
import {Config} from "../types";
import {loadConfig} from "../configLoader";


export const DeviceHistory = () => {
    const [config, setConfig] = useState<Config>({});
    const [isLoad, setIsLoad] = useState(false);
    const [historyContent, setHistoryContent] = useState<Array<string>>([]);

    useEffect(() => {
        const getConfig = async () => {
            const new_config = await loadConfig();
            setConfig(new_config);
            setIsLoad(true);
        };
        getConfig();
    }, [])


    useEffect(() => {
        const get_history = async () => {
            const response = await send_request(config["backend_url"], "history", {});
            const json_response = await response.json();
            setHistoryContent(json_response["history"]);
        }

        if (Object.keys(config).length > 0) {
            get_history();
        }
    }, [config]);

    if (historyContent.length > 0)
        return (
            <div>
              {historyContent.map((command, index) => (
                <div key={index}>
                  {command}
                </div>
              ))}
            </div>
        )
    else
        return (<></>)
}