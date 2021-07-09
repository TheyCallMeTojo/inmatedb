import os
from typing import List, NamedTuple, Optional

import requests
from bs4 import BeautifulSoup

from scraping import scraping_utils as utils


class Name(NamedTuple):
    first: str
    last: str

class Demographics(NamedTuple):
    race: str
    age: int
    gender: str

class InmateStatus(NamedTuple):
    arresting_agency: str
    booking_number: int
    booking_date: str
    charges: List[str]
    bond: Optional[float]
    jailed: bool

class ProfileData(NamedTuple):
    name: Name
    demos: Demographics
    status: InmateStatus
    profile_image_filepath: str


class ProfileParse:

    def __init__(self, inmate_table):
        self.__booking_num = int(utils.get_table_value(inmate_table, "Booking #"))
        self.profile_html = self.reload_profile()
    
    def invalidate_cached_values(self):
        self.__profile_table = None
        self.__name = None
        self.__demos = None
        self.__status = None
        self.__data = None

    def reload_profile(self):
        self.invalidate_cached_values()

        profile_url = f"https://www.capecountysheriff.org/roster_view.php?booking_num={self.__booking_num}"
        page = requests.get(profile_url)
        self.profile_html = BeautifulSoup(page.content, 'html.parser')
        return self.profile_html

    @property
    def inmate_image_filepath(self):
        image_filepath = f"img/{self.status.booking_number}.jpg"

        if not os.path.exists("img"):
            os.makedirs("img")
        if not os.path.exists(image_filepath):
            inmate_image_elm = self.profile_table.find(name="img")
            image_relpath = inmate_image_elm['src']
            image_url = f"https://www.capecountysheriff.org/{image_relpath}"

            with open(image_filepath, "wb") as img_file:
                img_file.write(requests.get(image_url).content)
                utils.random_delay(min_delay=200, max_delay=500)        

        return image_filepath

    @property
    def profile_table(self):
        if self.__profile_table is not None:
            return self.__profile_table
        
        main_table = self.profile_html.find(name="table")
        profile_table = main_table.find_all(name="tr")[0]
        self.__profile_table = profile_table
        return profile_table
    
    @property
    def name(self):
        if self.__name is not None:
            return self.__name
        
        name_elm = self.profile_html.find(attrs={"class":"ptitles"})
        first, last = name_elm.text.strip().split()
        self.__name = Name(first, last)
        return self.__name

    @property
    def demos(self):
        if self.__demos is not None:
            return self.__demos
        
        race = utils.get_table_value(self.profile_html, "Race")
        age = int(utils.get_table_value(self.profile_html, "Age"))
        gender = utils.get_table_value(self.profile_html, "Gender")
        self.__demos = Demographics(race, age, gender)
        return self.__demos
    
    def fetch_inmate_charges(self):
        charges = []
        if self.profile_html is None:
            return charges
        
        charges_row = utils.search_table_by_text(self.profile_html, "Charges", row_offset=1).table_row
        if charges_row is None:
            return charges
            
        for new_charges in charges_row.strings:
            new_charges = new_charges.replace('\n', ' ')
            new_charges = new_charges.split(';')
            new_charges = [c.strip() for c in new_charges]
            new_charges = [c for c in new_charges if len(c) > 0]
            charges.extend(new_charges)

        if len(charges) == 0:
            charges.append(None)
        
        return charges
    
    @property
    def status(self):
        if self.__status is not None:
            return self.__status

        agency = utils.get_table_value(self.profile_table, "Arresting Agency")
        booking_num = int(utils.get_table_value(self.profile_table, "Booking #"))
        booking_date = utils.get_table_value(self.profile_table, "Booking Date")
        charges = self.fetch_inmate_charges()
        bond = utils.get_table_value(self.profile_table, "Bond")
        jailed = True # TODO: compare against current roster
        self.__status = InmateStatus(agency, booking_num, booking_date, charges, bond, jailed)
        return self.__status
    
    @property
    def data(self):
        if self.__data is not None:
            return self.__data
        
        name = self.name
        demos = self.demos
        status = self.status
        img_path = self.inmate_image_filepath
        self.__data = ProfileData(name, demos, status, img_path)
        return self.__data
