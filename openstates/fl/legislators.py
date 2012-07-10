import re
import urlparse

from billy.scrape import NoDataForPeriod
from billy.scrape.legislators import LegislatorScraper, Legislator

import lxml.html


class FLLegislatorScraper(LegislatorScraper):
    state = 'fl'

    def scrape(self, chamber, term):
        self.validate_term(term, latest_only=True)

        if chamber == 'upper':
            self.scrape_senators(term)
        else:
            self.scrape_reps(term)

    def scrape_senators(self, term):
        url = "http://www.flsenate.gov/Senators/"
        with self.urlopen(url) as page:
            page = lxml.html.fromstring(page)
            page.make_links_absolute(url)

            for link in page.xpath("//a[contains(@href, 'Senators/s')]"):
                name = link.text.strip()
                name = re.sub(r'\s+', ' ', name)
                leg_url = link.get('href')

                if 'Vacant' in name:
                    continue

                # Special case - name_tools gets confused
                # by 'JD', thinking it is a suffix instead of a first name
                if name == 'Alexander, JD':
                    name = 'JD Alexander'
                elif name == 'Vacant':
                    name = 'Vacant Seat'

                district = link.xpath("string(../../td[1])")
                party = link.xpath("string(../../td[2])")

                # for consistency
                if party == 'Democrat':
                    party = 'Democratic'

                photo_url = ("http://www.flsenate.gov/userContent/"
                             "Senators/2010-2012/photos/s%03d.jpg" % (
                                 int(district)))

                leg = Legislator(term, 'upper', district, name,
                                 party=party, photo_url=photo_url, url=leg_url)
                leg.add_source(url)

                self.save_legislator(leg)

    def scrape_reps(self, term):
        url = ("http://www.flhouse.gov/Sections/Representatives/"
               "representatives.aspx")

        with self.urlopen(url) as page:
            page = lxml.html.fromstring(page)
            page.make_links_absolute(url)

            for div in page.xpath('//div[@id="rep_icondocks2"]'):
                link = div.xpath('.//div[@class="membername"]/a')[0]
                name = link.text_content().strip()

                if 'Vacant' in name or 'Resigned' in name:
                    continue

                party = div.xpath('.//div[@class="partyname"]/text()')[0].strip()
                if party == 'Democrat':
                    party = 'Democratic'

                district = div.xpath('.//div[@class="districtnumber"]/text()')[0].strip()

                leg_url = link.get('href')
                split_url = urlparse.urlsplit(leg_url)
                member_id = urlparse.parse_qs(split_url.query)['MemberId'][0]
                photo_url = ("http://www.flhouse.gov/FileStores/Web/"
                             "Imaging/Member/%s.jpg" % member_id)

                leg = Legislator(term, 'lower', district, name,
                                 party=party, photo_url=photo_url, url=leg_url)
                leg.add_source(url)
                self.save_legislator(leg)
