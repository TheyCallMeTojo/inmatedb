from typing import List, NamedTuple, Optional

from persistence.model import Model


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
    charges: List[str]
    bond: Optional[float]
    jailed: bool

@Model
class ProfileData(NamedTuple):
    name: Name
    demos: Demographics
    status: InmateStatus
    image_filepath: str

