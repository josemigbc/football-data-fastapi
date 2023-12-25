from fastapi import FastAPI, HTTPException, BackgroundTasks
from consumers import Consumer
from datetime import datetime, timedelta, date
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

@app.get('/api/match/{match_id}')
async def get_match_by_id(match_id: int):
    match = list(filter(lambda m: m["id"] == match_id, consumer.matches))[0]
    return match

@app.get('/api/match')
def get_match_by_filters(utcDate: date | None = None, team_id: int | None = None):
    if not (utcDate or team_id):
        return list(filter(lambda m: datetime.fromisoformat(m["utcDate"]).date() == date.today(), consumer.matches))
    
    r = consumer.matches.copy()
    
    if utcDate:
        r = filter(lambda m: datetime.fromisoformat(m["utcDate"]).date() == utcDate, r)

    if team_id:
        r = filter(lambda m: m["homeTeam"]["id"] == team_id or m["awayTeam"]["id"] == team_id, r)
    
    return list(r)

@app.get('/api/{league}/{data_type}')
async def response(league: str, data_type: str, background_tasks: BackgroundTasks) -> dict:
    try:
        data = consumer.data[league][data_type]
    except KeyError:
        raise HTTPException(404, "League or info not found.")
    background_tasks.add_task(update_data)
    return data