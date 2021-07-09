import math
import re

import requests
from bs4 import BeautifulSoup

from scraping import scraping_utils as utils


class RosterParse:

    def __init__(self):
        self.load_roster_page(1)
    
    def invalidate_cached_values(self):
        self.roster_html = None
        self.__roster_length = None
        self.__inmate_tables = None

    def load_roster_page(self, page_number):
        self.invalidate_cached_values()

        roster_url = f"https://www.capecountysheriff.org/roster.php?grp={page_number * 10}"
        page = requests.get(roster_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        self.roster_html = soup
        return soup

    @property
    def roster_length(self):
        if self.__roster_length is not None:
            return self.__roster_length

        if self.roster_html is None:
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
    def inmate_tables(self):
        if self.__inmate_tables is not None:
            return self.__inmate_tables

        total_page_count = math.ceil(self.roster_length / 10)
        inmate_tables = []

        for page_num in range(1, total_page_count+1):
            utils.random_delay()
            self.load_roster_page(page_num)

            presentation_tables = self.roster_html.find_all(name="table", attrs={"role":"presentation"})
            main_table = presentation_tables[0]

            for tr in main_table.find_all(name="tr"):
                matches = tr.find_all(name="table", attrs={"class":"inmateTable"})
                if len(matches) > 0:
                    inmate_tables.append(tr)

        self.__inmate_tables = inmate_tables
        return self.__inmate_tables
    

    