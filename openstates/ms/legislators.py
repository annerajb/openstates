import urlparse
import lxml.etree

from billy.scrape import NoDataForPeriod
from billy.scrape.legislators import LegislatorScraper, Legislator
from .utils import clean_committee_name

import scrapelib

class MSLegislatorScraper(LegislatorScraper):
    state = 'ms'

    def scrape(self, chamber, term_name):
        self.validate_term(term_name, latest_only=True)
        self.scrape_legs(chamber, term_name)

    def scrape_legs(self, chamber, term_name):
        if chamber == 'upper':
            url = 'http://billstatus.ls.state.ms.us/members/ss_membs.xml'
            range_num = 5
        else:
            url = 'http://billstatus.ls.state.ms.us/members/hr_membs.xml'
            range_num = 6

        with self.urlopen(url) as leg_dir_page:
            root = lxml.etree.fromstring(leg_dir_page.bytes)
            for mr in root.xpath('//LEGISLATURE/MEMBER'):
                for num in range(1, range_num):
                    leg_path = "string(M%s_NAME)" % num
                    leg_link_path = "string(M%s_LINK)" % num
                    leg = mr.xpath(leg_path)
                    leg_link = mr.xpath(leg_link_path)
                    role = "member"
                    self.scrape_details(chamber, term_name, leg, leg_link, role)
            if chamber == 'lower':
                chair_name = root.xpath('string(//CHAIR_NAME)')
                chair_link = root.xpath('string(//CHAIR_LINK)')
                role = root.xpath('string(//CHAIR_TITLE)')
                self.scrape_details(chamber, term_name, chair_name, chair_link, role)
            else:
                #Senate Chair is the Governor. Info has to be hard coded
                chair_name = root.xpath('string(//CHAIR_NAME)')
                role = root.xpath('string(//CHAIR_TITLE)')
                # TODO: if we're going to hardcode the governor, do it better
                #district = "Governor"
                #leg = Legislator(term_name, chamber, district, chair_name,
                #                 first_name="", last_name="", middle_name="",
                #                 party="Republican", role=role)

            protemp_name = root.xpath('string(//PROTEMP_NAME)')
            protemp_link = root.xpath('string(//PROTEMP_LINK)')
            role = root.xpath('string(//PROTEMP_TITLE)')
            self.scrape_details(chamber, term_name, protemp_name, protemp_link, role)

    def scrape_details(self, chamber, term, leg_name, leg_link, role):
        if not leg_link:
            raise Exception("leg_link is null. something went wrong")
        try:
            url = 'http://billstatus.ls.state.ms.us/members/%s' % leg_link
            with self.urlopen(url) as details_page:
                root = lxml.etree.fromstring(details_page.bytes)
                party = root.xpath('string(//PARTY)')
                district = root.xpath('string(//DISTRICT)')

                home_phone = root.xpath('string(//H_PHONE)')
                bis_phone = root.xpath('string(//B_PHONE)')
                capital_phone = root.xpath('string(//CAP_PHONE)')
                other_phone = root.xpath('string(//OTH_PHONE)')
                org_info = root.xpath('string(//ORG_INFO)')
                email_name = root.xpath('string(//EMAIL_ADDRESS)')
                email = '%s@%s.ms.gov' % (email_name, chamber)
                if party == 'D':
                    party = 'Democratic'
                else:
                    party = 'Republican'

                leg = Legislator(term, chamber, district, leg_name,
                                 party=party,
                                 role=role,
                                 bis_phone=bis_phone,
                                 capital_phone=capital_phone,
                                 other_phone=other_phone,
                                 org_info=org_info,
                                 email=email,
                                 url=url)
                leg.add_source(url)
                self.save_legislator(leg)
        except scrapelib.HTTPError, e:
            self.warning(str(e))

