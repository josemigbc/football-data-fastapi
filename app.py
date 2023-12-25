from fastapi import FastAPI, HTTPException, BackgroundTasks
from consumers import Consumer
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import json

consumer = Consumer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with open('data.json') as data:
            consumer.data = json.load(data)
    
    except FileNotFoundError:
        await update_data()
    yield

app = FastAPI(lifespan=lifespan)

async def update_data() -> None:
    if consumer.is_updating:
        return
    if (not consumer.last_updated) or consumer.last_updated + timedelta(minutes=30) < datetime.now():
        await consumer.run()

@app.get('/api/{league}/{data_type}')
async def response(league: str, data_type: str, background_tasks: BackgroundTasks) -> dict:
    try:
        data = consumer.data[league][data_type]
    except KeyError:
        raise HTTPException(404, "League or info not found.")
    background_tasks.add_task(update_data)
    return data