from os import getenv

from fastapi import APIRouter

auth = APIRouter(
    prefix="",
    tags=["auth"]
)

@auth.get("/apiKey")
def get_api_key():
    apiKey = getenv("API_KEY")
    return {"apiKey": apiKey}
