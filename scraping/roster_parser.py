import grequests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from logger.inmatedb_logger import InatedbLogger

from bs4 import BeautifulSoup
from scraping import scraping_utils as utils
import math
import re

from metaclasses.singleton import Singleton
from functools import partial


class RosterParse(metaclass=Singleton):

    def __init__(self):
        self.invalidate_cached_values()
        
        self.logger = InatedbLogger()

        s = grequests.Session()
        error_codes = list(range(400, 599))
        retries = Retry(total=5, backoff_factor=0.3, status_forcelist=error_codes, raise_on_status=True)
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))
        self.new_request = partial(grequests.get, session=s, timeout=1)


    def invalidate_cached_values(self):
        self.__roster_size = None
        self.__profile_urls = None
        self.__roster_urls = None
        self.__booking_nums = None
    
    def get_profile_url(self, booking_number):
        profile_url = f"https://www.capecountysheriff.org/roster_view.php?booking_num={booking_number}"
        return profile_url

    def get_roster_page_url(self, page_number):
        roster_url = f"https://www.capecountysheriff.org/roster.php?grp={page_number * 10}"
        return roster_url

    def load_roster_page(self, page_number):
        page_url = self.get_roster_page_url(page_number)
        roster_page = self.new_request(page_url).send().response        
        
        if roster_page is not None:
            return BeautifulSoup(roster_page.content, 'html.parser')
        
        self.logger.warning("Failed to load the roster page.")
        return None

    @property
    def roster_size(self):
        if self.__roster_size is not None:
            return self.__roster_size

        # If we don't know the roster size, then we know nothing... invalidate everything!
        self.invalidate_cached_values()

        roster_html = self.load_roster_page(1)
        # self.logger.debug("got this far.")
        if roster_html is None:
            return None
        
        is_roster_count = lambda string: utils.text_contains_word(string, "Inmate Roster")
        roster_count_elm = roster_html.find(attrs={"ptitles"}, string=is_roster_count)

        if roster_count_elm is not None:
            match_roster_count = re.compile(r"Inmate Roster \((\d*)\)")
            matches = match_roster_count.findall(roster_count_elm.text)

            if len(matches) != 0:
                self.__roster_size = int(matches[0])
                return self.__roster_size

        self.logger.critical("Failed to parse the inmate roster size.")
        return None
    
    @property
    def roster_page_count(self):
        if self.roster_size is None:
            return None
        
        return math.ceil(self.roster_size / 10)

    @property
    def roster_urls(self):
        if self.__roster_urls is not None:
            return self.__roster_urls

        if self.roster_page_count is None:
            return None

        roster_page_urls = []
        for page_number in range(1, self.roster_page_count+1):
            page_url = self.get_roster_page_url(page_number)
            roster_page_urls.append(page_url)
        
        self.__roster_urls = roster_page_urls
        return roster_page_urls
    
    def get_inmate_tables_on_page(self, roster_page):
        presentation_tables = roster_page.find_all(name="table", attrs={"role":"presentation"})
        main_table = presentation_tables[0]

        inmate_tables = []
        for tr in main_table.find_all(name="tr"):
            matches = tr.find_all(name="table", attrs={"class":"inmateTable"})
            if len(matches) > 0:
                inmate_tables.append(tr)
        
        return inmate_tables
    
    @property
    def inmate_booking_numbers(self):
        if self.__booking_nums is not None:
            return self.__booking_nums

        if self.roster_urls is None:
            return None
        
        requests = (self.new_request(url) for url in self.roster_urls)

        booking_nums = []
        for response in grequests.imap(requests, size=10):
            if response is None:
                self.logger.warning("Failed to read a page from the roster...")
                return None
            
            roster_page = BeautifulSoup(response.content, 'html.parser')
            inmate_tables = self.get_inmate_tables_on_page(roster_page)
            for inmate in inmate_tables:
                booking_num = utils.get_table_value(inmate, "Booking #")
                booking_nums.append(int(booking_num))
        
        self.__booking_nums = booking_nums
        return self.__booking_nums
    
    @property
    def profile_urls(self):
        if self.__profile_urls is not None:
            return self.__profile_urls
        
        if self.inmate_booking_numbers is None:
            return None
        
        urls = []
        for booking_number in self.inmate_booking_numbers:
            profile_url = self.get_profile_url(booking_number)
            urls.append(profile_url)
        
        self.__profile_urls = urls
        return self.__profile_urls

