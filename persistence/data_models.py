from typing import List, NamedTuple, Optional
from datetime import datetime
from persistence.model import Model


__all__ = ["Name", "Demographics", "InmateStatus", "ProfileData"]

@Model
class Name(NamedTuple):
    first: str
    last: str

@Model
class Demographics(NamedTuple):
    race: str
    age: int
    gender: str

@Model
class InmateStatus(NamedTuple):
    arresting_agency: str
    booking_number: int
    booking_date: str
    booking_date_unformated: float
    charges: List[str]
    bond: Optional[str]
    jailed: bool

@Model
class ProfileData(NamedTuple):
    name: Name
    demos: Demographics
    status: InmateStatus
    image_filepath: str

