import grequests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from logger.inmatedb_logger import InmatedbLogger

import os
from bs4 import BeautifulSoup
from scraping import scraping_utils as utils
from persistence.data_models import *

from metaclasses.singleton import Singleton
from functools import partial
from datetime import datetime

from helpers.pathutils import get_project_dir, extend_relpath


class ProfileParse(metaclass=Singleton):

    def __init__(self):
        self.invalidate_cached_values()

        self.logger = InmatedbLogger()

        s = grequests.Session()
        error_codes = list(range(400, 599))
        retries = Retry(total=5, backoff_factor=0.3, status_forcelist=error_codes, raise_on_status=True)
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))
        self.new_request = partial(grequests.get, session=s, timeout=1)

    
    def invalidate_cached_values(self):
        self.profile_html = None
        self.__profile_table = None
        self.__name = None
        self.__demos = None
        self.__status = None
        self.__data = None
        self.__image_filepath = None

    def request_profile_pages(self, profile_urls):
        requests = (self.new_request(url) for url in profile_urls)
        return grequests.imap(requests, size=7)
   
    def parse_profile(self, profile_html):
        self.invalidate_cached_values()
        self.profile_html = BeautifulSoup(profile_html, 'html.parser')
        return self.profile_html

    @property
    def image_filepath(self):
        if self.__image_filepath is not None:
            return self.__image_filepath
        
        image_folderpath = extend_relpath("data/img/")
        image_filepath = os.path.join(image_folderpath, f"{self.status.booking_number}.jpg")

        if not os.path.exists(image_folderpath):
            os.makedirs(image_folderpath)
        
        if not os.path.exists(image_filepath):
            inmate_image_elm = self.profile_table.find(name="img")
            image_relpath = inmate_image_elm['src']
            image_url = f"https://www.capecountysheriff.org/{image_relpath}"

            request = self.new_request(image_url).send()
            if request.response is None:
                self.logger.warning("Failed to download a profile image")
                return None

            with open(image_filepath, "wb") as img_file:
                img_file.write(request.response.content)

        self.__image_filepath = image_filepath
        return self.__image_filepath

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
        booking_date_unformated = datetime.strptime(booking_date, "%m-%d-%Y - %I:%S %p").timestamp()
        charges = self.fetch_inmate_charges()
        bond = utils.get_table_value(self.profile_table, "Bond")
        jailed = True # True, because all profiles are pulled from the current roster.
        self.__status = InmateStatus(agency, booking_num, booking_date, booking_date_unformated, charges, bond, jailed)
        return self.__status
    
    @property
    def data(self):
        if self.__data is not None:
            return self.__data
        
        name = self.name
        demos = self.demos
        status = self.status
        img_path = self.image_filepath

        if None in [name, demos, status, img_path]:
            self.logger.warning("Failed to parse profile...")
            return None

        self.__data = ProfileData(name, demos, status, img_path)
        return self.__data
