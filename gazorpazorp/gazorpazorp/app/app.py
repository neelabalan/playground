from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from common.load_data import load_characters
from common.logger import get_logger

logger = get_logger(__name__)

app = FastAPI()


characters = load_characters()


class Character(BaseModel):
    name: str
    status: str
    species: str


@app.get("/characters", response_model=List[Character])
def get_characters():
    logger.info("Getting characters...")
    return characters
