const route_mapping = {
    devices: {
        route: "devices",
        method: "GET",
        content_type: "application/json",
        response_type: "json"
    },
    status: {
        route: "status",
        method: "POST",
        content_type: "application/json",
        response_type: "json"
    },
    start: {
        route: "start",
        method: "POST",
        content_type: "application/json",
        response_type: "json"
    },
    register: {
        route: "register",
        method: "POST",
        content_type: "application/json",
        response_type: "json"
    },
    delete: {
        route: "delete",
        method: "POST",
        content_type: "application/json",
        response_type: "json"
    },
    update: {
        route: "update",
        method: "POST",
        content_type: "application/json",
        response_type: "json"
    }
}


export async function send_request(url, target, data){
    const route_info = route_mapping[target];
    const route = route_info["route"];
    const method = route_info["method"];
    const content_type = route_info["content_type"];
    const apiKey = import.meta.env.VITE_API_KEY;

    let request_data = {};
    if (Object.keys(data).length > 0) {
        request_data = {
            method: method,
            headers: {
                "Content-Type": content_type,
                "X-API-Key": apiKey
            },
            body: JSON.stringify(data)
        }
    } else {
        request_data = {
            method: method,
            headers: {
                "X-API-Key": apiKey
            },
        }
    }

    return await fetch(url + "/" + route, request_data);
}