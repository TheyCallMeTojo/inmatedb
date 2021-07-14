from scraping.profile_parser import ProfileParse
from scraping.roster_parser import RosterParse
from tqdm import tqdm

from persistence.inmate_dao import InmateDAO, bundle_profile_data
from persistence.data_models import *

from event_scheduler import EventScheduler, ScheduleItem, TimeSlot

from logger.inmatedb_logger import InmatedbLogger
from logger.push_handler import PushHandler, PushCredentials
import logging


class ScraperApp:
    
    def __init__(self, logger:InmatedbLogger):
        self.roster = RosterParse()
        self.profile = ProfileParse()
        self.dao = InmateDAO()
        self.logger = logger

        self.scrape_success = True
        

    def scrape_data(self):
        '''
        Read the current roster. Insert any new inmates into the database.
        Update the 'jailed' flag as appropriate.
        '''

        self.roster.invalidate_cached_values()

        profile_urls = self.roster.profile_urls
        if profile_urls is None:
            self.logger.warning("Failed to parse roster for profile urls!")
            self.scrape_success = False
            return None
        
        profile_requests = self.profile.request_profile_pages(profile_urls)
        for resp in tqdm(profile_requests, total=len(profile_urls), desc="scraping roster"):
            if resp is None:
                # (to be considered): Create a failed tasks queue to retry later.
                self.logger.warning("Failed to request a profile!")
                continue

            self.profile.parse_profile(resp.content)
            if self.profile.data is None:
                self.logger.warning("Failed to parse a profile!")
                continue
            
            self.dao.put_member(self.profile.data)
        
        self.scrape_success = True
        self.logger.info("Successfully scraped roster!")

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

        scraping_retry_event = ScheduleItem(
            start=TimeSlot(minute_offset=9),
            callback=self.scrape_data,
            callback_args=()
        )

        self.logger.info("Scraper app is starting up...")

        try:
            # Scrape data first on start-up
            self.scrape_data()

            while True:
                # Scrape data on a schedule
                if not self.scrape_success:
                    scheduler.schedule_event(scraping_retry_event)
                else:
                    scheduler.schedule_event(scraping_event)

                scheduler.run_schedule()
        except KeyboardInterrupt:
            pass
        except BaseException:
            self.logger.critical("Scraper failed!")
        
        self.logger.info("Scraper app has terminated...")


if __name__ == "__main__":
    # credentials = PushCredentials(
    #     api_key="YOUR_API_KEY",
    #     channel_tag="CHANNEL_TAG"
    # )
    # logger = InmatedbLogger(push_credentials=credentials)
    logger = InmatedbLogger(logging.DEBUG)


    ScraperApp(logger).run()
    logger.info("main thread exited")
