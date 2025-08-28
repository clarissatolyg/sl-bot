from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class Stop(BaseModel):
    id: str
    name: str
    lat: float
    lon: float


class Platform(BaseModel):
    id: str
    designation: str


class RouteEndpoint(BaseModel):
    id: str
    name: str


class Route(BaseModel):
    name: Optional[str]
    designation: str
    transport_mode_code: int
    transport_mode: str
    direction: str
    origin: RouteEndpoint
    destination: RouteEndpoint


class Trip(BaseModel):
    trip_id: str
    start_date: datetime
    technical_number: int


class Agency(BaseModel):
    id: str
    name: str
    operator: str


class Alert(BaseModel):
    type: str
    summary: str


class Departure(BaseModel):
    scheduled: datetime
    realtime: datetime
    delay: int
    canceled: bool
    route: Route
    trip: Trip
    agency: Agency
    stop: Stop
    scheduled_platform: Platform
    realtime_platform: Platform
    alerts: List[Alert]
    is_realtime: bool
