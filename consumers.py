import httpx
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class Consumer:

    API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
    API_URL = "https://api.football-data.org/v4/competitions"
    competitions = ["FL1","BL1","PD","PL","SA","CL","ELC","PPL"]
    
    def __init__(self) -> None:
        self.last_updated = None
        self.is_updating = False
        self.data: dict[str, dict[str, dict]] = { l:{} for l in self.competitions}
    
    @property   
    def matches(self):
        matches = []
        for league, data in self.data.items():
            try:
                matches.extend(data["matches"]["matches"])
            except KeyError:
                pass
        return matches

    async def do_get(self, uri: str) -> dict | None:
        async with httpx.AsyncClient() as client:
            headers = {'X-Auth-Token': self.API_KEY}
            response = await client.get(f"{self.API_URL}{uri}", headers=headers)
            if response.status_code == 200:
                return response.json()
    
    async def do_operation(self, league: str, data_type: str):
        data = await self.do_get(f"/{league}{f'/{data_type}' if data_type != 'competition' else ''}")
        if data:
            self.data[league][data_type] = data
            return True
        
    async def get_competition(self, league: str):
        return await self.do_operation(league, 'competition')
    
    async def get_standings(self, league):
        return await self.do_operation(league, 'standings')
    
    async def get_matches(self, league: str):
        return await self.do_operation(league, 'matches')
    
    async def get_scorers(self, league: str):
        return await self.do_operation(league, 'scorers')
    
    async def run(self):
        self.is_updating = True
        for league in self.competitions:
            r1 = await self.get_competition(league)
            r2 = await self.get_matches(league)
            r3 = await self.get_standings(league)
            r4 = await self.get_scorers(league)
            
            if r1:
                print(f"{league}: Competition OK")
            if r2:
                print(f"{league}: Matches OK")
            if r3:
                print(f"{league}: Standings OK")
            if r4:
                print(f"{league}: Scorers OK")
            
            await asyncio.sleep(30)
        self.last_updated = datetime.now()
        self.is_updating = False