from scraping.roster_parser import RosterParse
from scraping.profile_parser import ProfileParse

from persistence.inmate_dao import InmateDAO, bundle_profile_data
from persistence.data_models import *

from event_scheduler import EventScheduler
from event_scheduler import TimeSlot, ScheduleItem

class ScraperApp:
    
    def __init__(self):
        self.roster = RosterParse()
        self.profile = ProfileParse()
        self.dao = InmateDAO()

    def scrape_data(self):
        '''
        Read the current roster. Insert any new inmates into the database.
        Update the 'jailed' flag as appropriate.
        '''

        self.roster.invalidate_cached_values()

        for inmate in self.roster.inmate_tables:
            self.profile.load_profile(inmate)
            print(f"saving data: {self.profile.data.status.booking_number}")
            self.dao.put_member(self.profile.data)
        
        for member in self.dao.get_all_members():
            bk_number = member.status.booking_number

            is_jailed = bk_number in self.roster.inmate_booking_numbers
            member_dict = member.as_dict()
            member_dict['status']['jailed'] = is_jailed
            member = bundle_profile_data(member_dict)
            print(f"updating data: {bk_number}")
            self.dao.put_member(member)
    
    def run(self):
        # Scrape data first on start-up
        self.scrape_data()

        scheduler = EventScheduler(silent=False)
        scraping_event = ScheduleItem(
            start=TimeSlot(minute_offset=30),
            callback=self.scrape_data,
            callback_args=()
        )

        # TODO: run scraper app in either a seperate process or thread
        while True:
            # While the app is running, scrape data regularly and on a schedule.
            scheduler.schedule_event(scraping_event)
            scheduler.run_schedule()

if __name__ == "__main__":
    app = ScraperApp()
    app.run()