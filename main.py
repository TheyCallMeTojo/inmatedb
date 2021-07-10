import logging
import time

from tqdm import tqdm

from event_scheduler import EventScheduler, ScheduleItem, TimeSlot
from logger.inmatedb_logger import InatedbLogger

from persistence.data_models import *
from persistence.inmate_dao import InmateDAO, bundle_profile_data

from scraping.profile_parser import ProfileParse
from scraping.roster_parser import RosterParse


class ScraperApp:
    
    def __init__(self, logger):
        self.roster = RosterParse()
        self.profile = ProfileParse()
        self.dao = InmateDAO()
        self.logger = logger

    def scrape_data(self):
        '''
        Read the current roster. Insert any new inmates into the database.
        Update the 'jailed' flag as appropriate.
        '''

        self.roster.invalidate_cached_values()

        for inmate in tqdm(self.roster.inmate_tables, desc="scraping roster"):
            self.profile.load_profile(inmate)
            self.dao.put_member(self.profile.data)
            time.sleep(100/1000)
        
        members = self.dao.get_all_members()
        for member in tqdm(members, desc="validating 'jailed' flags"):
            bk_number = member.status.booking_number
            is_jailed = bk_number in self.roster.inmate_booking_numbers
            member_dict = member.as_dict()
            member_dict['status']['jailed'] = is_jailed
            member = bundle_profile_data(member_dict)
            self.dao.put_member(member)
    
    def run(self):
        scheduler = EventScheduler(silent=False)
        scraping_event = ScheduleItem(
            start=TimeSlot(minute_offset=30),
            callback=self.scrape_data,
            callback_args=()
        )

        try:
            # Scrape data first on start-up
            self.scrape_data()

            # TODO: run scraper app in either a seperate process or thread
            while True:
                # While the app is running, scrape data regularly and on a schedule.
                scheduler.schedule_event(scraping_event)
                scheduler.run_schedule()
        except KeyboardInterrupt:
            pass
        except BaseException:
            # Just logging errors right now. TODO: add proper error handling
            self.logger.critical("Scraper failed!")

if __name__ == "__main__":
    # credentials = PushCredentials(
    #     api_key="YOUR_API_KEY",
    #     channel_tag="CHANNEL_TAG"
    # )
    # self.logger = InatedbLogger(push_credentials=credentials)

    logger = InatedbLogger(log_level=logging.DEBUG)
    logger.info("scraper starting...")

    ScraperApp(logger).run()
    logger.info("scraper terminated...")
