from fastapi import FastAPI
from starlette.requests import Request

from limiter import RateLimit

app = FastAPI()


@app.get("/1")
async def root():
    return {"ping": "True"}


@app.get("/")
@RateLimit('m/3')
async def root(request: Request):
    return {"message": "Hello World"}


@app.get("/hello/{name}")
@RateLimit('m/3')
async def say_hello(request: Request, name: str):
    return {"message": f"Hello {name}"}
