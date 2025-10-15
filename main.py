from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, conint
from solution import search_grouped, load_grouped_listings
from models import Vehicle

app = FastAPI()
router = APIRouter()

@app.get("/")
def health():
    return {"ok": True}

@router.post("/")
async def search(vehicles: list[Vehicle]):
    vehicles_sorted = sorted(vehicles, key=lambda v: v.length, reverse=True)
    grouped = load_grouped_listings()    

    #actually search
    return search_grouped(grouped, vehicles_sorted)

app.include_router(router)