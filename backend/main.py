from routers.devices import devices as devices_router

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
# Create FastAPI instance
app = FastAPI()

# Add routers to main app
app.include_router(devices_router)

# Set CORS settings
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_credentials=True,
    allow_methods=["OPTIONS", "GET", "POST"],
    allow_headers=["OPTIONS", "GET", "POST"]
)

2

@app.get("/")
def read_root():
    return {"message": "Welcome to WOL manager"}


if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8000, workers=4)
