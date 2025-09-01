from fastapi import FastAPI
from mangum import Mangum
from app.routers import router

app = FastAPI(title="Twilio Call Forwarding API")
app.include_router(router)

handler = Mangum(app)
