import re
import urlparse
import datetime

from billy.scrape import NoDataForPeriod
from billy.scrape.legislators import LegislatorScraper, Legislator
from .utils import clean_committee_name

import lxml.html

class NVLegislatorScraper(LegislatorScraper):
    state = 'nv'

    def scrape(self, chamber, term_name):

        for t in self.metadata['terms']:
            if t['name'] == term_name:
                session = t['sessions'][-1]
                slug = self.metadata['session_details'][session]['slug']

        if chamber == 'upper':
            leg_url = 'http://www.leg.state.nv.us/Session/' + slug  + '/legislators/Senators/slist.cfm'
            num_districts = 22
        elif chamber == 'lower':
            leg_url = 'http://www.leg.state.nv.us/Session/' + slug  + '/legislators/Assembly/alist.cfm'
            num_districts = 43

        with self.urlopen(leg_url) as page:
            page = page.replace("&nbsp;", " ")
            root = lxml.html.fromstring(page)

            #Going through the districts
            for row_index in range(2, num_districts+1):
                namepath = 'string(//table[%s]/tr/td/table[1]/tr/td[2])' % row_index
                last_name = root.xpath(namepath).split()[0]
                last_name = last_name[0 : len(last_name) - 1]
                middle_name = ''

                if len(root.xpath(namepath).split()) == 2:
                    first_name = root.xpath(namepath).split()[1]
                elif len(root.xpath(namepath).split()) == 3:
                    first_name = root.xpath(namepath).split()[1]
                    middle_name = root.xpath(namepath).split()[2]
                elif len(root.xpath(namepath).split()) == 4:
                    first_name = root.xpath(namepath).split()[2]
                    middle_name = root.xpath(namepath).split()[3]
                    last_name = last_name + " " + root.xpath(namepath).split()[1]
                    last_name = last_name[0: len(last_name) - 1]

                if len(middle_name) > 0:
                    full_name = first_name + " " + middle_name + " " + last_name
                else:
                    full_name = first_name + " " + last_name

                partypath = 'string(//table[%s]/tr/td/table[1]/tr/td[3])' % row_index
                party = root.xpath(partypath).split()[-1]
                if party == 'Democrat':
                    party = 'Democratic'

                districtpath = 'string(//table[%s]/tr/td/table[1]/tr/td[4])' % row_index
                district = root.xpath(districtpath).strip()[11:]
                if district.startswith('No.'):
                    district = district[3:].strip()

                termpath = 'string(//table[%s]/tr/td/table[2]/tr/td[5])' % row_index
                end_date = root.xpath(termpath)[12: 21]
                email = root.xpath(termpath).split()[-1]

                addresspath = 'string(//table[%s]/tr/td/table[2]/tr/td[2])' % row_index
                address = root.xpath(addresspath)

                leg = Legislator(term_name, chamber, district, full_name,
                                 first_name, last_name, middle_name, party,
                                 email=email, address=address, url=leg_url)
                leg.add_source(leg_url)
                self.save_legislator(leg)


