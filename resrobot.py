from pydantic import BaseModel
from typing import List


class Icon(BaseModel):
    res: str


class ProductAtStop(BaseModel):
    cls: str
    icon: Icon


class StopLocation(BaseModel):
    id: str
    extId: str
    name: str
    lon: float
    lat: float
    weight: int
    dist: int
    products: int
    timezoneOffset: int
    minimumChangeDuration: str
    productAtStop: List[ProductAtStop]
