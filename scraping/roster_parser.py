import math
import re

import requests
from bs4 import BeautifulSoup

from scraping import scraping_utils as utils
from metaclasses.singleton import Singleton


class RosterParse(metaclass=Singleton):

    def __init__(self):
        self.invalidate_cached_values()
    
    def invalidate_cached_values(self):
        self.roster_html = None
        self.__roster_length = None
        self.__inmate_tables = None
        self.__booking_nums = None

    def load_roster_page(self, page_number):
        # utils.random_delay()
        roster_url = f"https://www.capecountysheriff.org/roster.php?grp={page_number * 10}"
        page = requests.get(roster_url)
        self.roster_html = BeautifulSoup(page.content, 'html.parser')
        return self.roster_html

    def fetch_inmate_tables_on_page(self):
        if self.roster_html is None:
            return []
        
        presentation_tables = self.roster_html.find_all(name="table", attrs={"role":"presentation"})
        main_table = presentation_tables[0]

        inmate_tables = []
        for tr in main_table.find_all(name="tr"):
            matches = tr.find_all(name="table", attrs={"class":"inmateTable"})
            if len(matches) > 0:
                inmate_tables.append(tr)
        
        return inmate_tables

    @property
    def roster_length(self):
        if self.__roster_length is not None:
            return self.__roster_length

        if self.roster_html is None:
            self.invalidate_cached_values()
            self.load_roster_page(1)
        
        is_roster_count = lambda string: utils.text_contains_word(string, "Inmate Roster")
        roster_count_elm = self.roster_html.find(attrs={"ptitles"}, string=is_roster_count)

        if roster_count_elm is not None:
            match_roster_count = re.compile(r"Inmate Roster \((\d*)\)")
            matches = match_roster_count.findall(roster_count_elm.text)
            if len(matches) != 0:
                self.__roster_length = int(matches[0])
                return self.__roster_length

        return None

    @property
    def roster_page_length(self):
        return math.ceil(self.roster_length / 10)

    @property
    def inmate_booking_numbers(self):
        if self.__booking_nums is not None:
            return self.__booking_nums
        
        booking_nums = []
        for inmate_table in self.inmate_tables:
            booking_num = utils.get_table_value(inmate_table, "Booking #")
            booking_nums.append(int(booking_num))

        self.__booking_nums = booking_nums
        return self.__booking_nums

    @property
    def inmate_tables(self):
        if self.__inmate_tables is not None:
            return self.__inmate_tables

        self.invalidate_cached_values()

        inmate_tables = []
        for page_num in range(1, self.roster_page_length+1):
            self.load_roster_page(page_num)
            new_inmate_tables = self.fetch_inmate_tables_on_page()
            inmate_tables.extend(new_inmate_tables)

        self.__inmate_tables = inmate_tables
        return self.__inmate_tables
    