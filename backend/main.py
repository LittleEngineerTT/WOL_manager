from routers.devices import devices as devices_router, status_checker
from schemas.devices import Device

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
# Create FastAPI instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    status_checker.devices = Device.get_devices()
    status_checker.run()
    yield

app = FastAPI(lifespan=lifespan)


# Add routers to main app
app.include_router(devices_router)

# Set CORS settings
origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["OPTIONS", "GET", "POST"],
    allow_headers=["OPTIONS", "GET", "POST", "X-API-Key"]
)


@app.get("/")
def read_root():
    return {"message": "Welcome to WOL manager"}


if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8000, workers=1)
