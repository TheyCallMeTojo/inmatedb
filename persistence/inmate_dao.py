import os
from functools import reduce
from typing import List, Optional

from metaclasses.singleton import Singleton
from tinydb import Query, TinyDB

from persistence.data_models import *


def bundle_profile_data(record: dict) -> ProfileData:
    if record is None:
        return None
    
    name = Name(*record["name"].values())
    demos = Demographics(*record["demos"].values())
    status = InmateStatus(*record["status"].values())
    img_filepath = record["image_filepath"]
    profile_data = ProfileData(name, demos, status, img_filepath)
    return profile_data

def sort_profiles_by_date(profiles: List[ProfileData]) -> List[ProfileData]:
    on_bk_date = lambda p: p.status.booking_date_unformated
    return sorted(profiles, key=on_bk_date)

class QueryCondition:
    match_eq = lambda value: lambda query: query == value
    match_ne = lambda value: lambda query: query != value
    match_gt = lambda value: lambda query: query > value
    match_lt = lambda value: lambda query: query < value

    conditions = {
        "match_eq": match_eq,
        "match_ne": match_ne,
        "match_gt": match_gt,
        "match_lt": match_lt,
    }

class InmateDAO(metaclass=Singleton):

    def __init__(self, database_filepath="data/inmatedb.json"):
        if not os.path.exists("data"):
            os.makedirs("data")
        TinyDB.default_table_name = "inmates"
        self.db = TinyDB(database_filepath)

    def load_database(self, database_filepath):
        if self.db is not None:
            self.db.close()

        TinyDB.default_table_name = "inmates"
        self.db = TinyDB(database_filepath)

    def put_member(self, profile: Optional[ProfileData]):
        '''Inserts/Updates profile in the database.'''

        if profile is None:
            return None

        record = profile.as_dict()
        bk_number = profile.status.booking_number
        selector = Query().status.booking_number == bk_number
        return self.db.upsert(record, selector)

    def get_members_by_attribute(self, attribute: str, condition: QueryCondition) -> List[ProfileData]:
        '''Gets the profile of every member with a matching attribute.'''
        
        attrs = attribute.split('.')
        InmateAttribute = reduce(lambda query, attr: query[attr], attrs, Query())
        selector = condition(InmateAttribute)
        
        try:
            results = self.db.search(selector)
        except:
            return []
        
        profiles = list(map(bundle_profile_data, results))
        return sort_profiles_by_date(profiles)

    def get_members_by_firstname(self, first_name: str) -> List[ProfileData]:
        '''Gets the profile of every member with first_name.'''

        attribute = "name.first"
        condition = QueryCondition.match_eq(first_name)
        return self.get_members_by_attribute(attribute, condition)
    
    def get_members_by_lastname(self, last_name: str) -> List[ProfileData]:
        '''Gets the profile of every member with last_name.'''

        attribute = "name.last"
        condition = QueryCondition.match_eq(last_name)
        return self.get_members_by_attribute(attribute, condition)
    
    def get_all_current_inmates(self) -> List[ProfileData]:
        '''Gets the profile of every jailed member.'''

        attribute = "status.jailed"
        condition = QueryCondition.match_eq(True)
        return self.get_members_by_attribute(attribute, condition)

    def get_all_released_members(self) -> List[ProfileData]:
        '''Gets the profile of every released member.'''

        attribute = "status.jailed"
        condition = QueryCondition.match_eq(False)
        return self.get_members_by_attribute(attribute, condition)

    def get_all_members(self) -> List[ProfileData]: 
        '''Gets the profile of every member.'''
        profiles = list(map(bundle_profile_data, self.db.all()))
        return sort_profiles_by_date(profiles)

    def get_member_by_number(self, booking_number: int) -> Optional[ProfileData]:
        '''Gets the profile of a member by their booking_number.'''

        attribute = "status.booking_number"
        condition = QueryCondition.match_eq(booking_number)
        members = self.get_members_by_attribute(attribute, condition)
        if len(members) > 0:
            return members[0]
        
        return None
