import re

from billy.scrape.legislators import LegislatorScraper, Legislator

import lxml.html


class WYLegislatorScraper(LegislatorScraper):
    state = 'wy'

    def scrape(self, chamber, term):
        chamber_abbrev = {'upper': 'S', 'lower': 'H'}[chamber]

        url = ("http://legisweb.state.wy.us/LegislatorSummary/LegislatorList"
               ".aspx?strHouse=%s&strStatus=N" % chamber_abbrev)
        page = lxml.html.fromstring(self.urlopen(url))
        page.make_links_absolute(url)

        for link in page.xpath("//a[contains(@href, 'LegDetail')]"):
            name = link.text.strip()
            leg_url = link.get('href')

            email_address = link.xpath("../../../td[1]//a")[0].attrib['href']
            email_address = link.xpath("../../../td[2]//a")[0].attrib['href']
            email_address = email_address.split('Mailto:')[1]

            party = link.xpath("string(../../../td[3])").strip()
            if party == 'D':
                party = 'Democratic'
            elif party == 'R':
                party = 'Republican'

            district = link.xpath(
                "string(../../../td[4])").strip().lstrip('HS0')

            leg_page = lxml.html.fromstring(self.urlopen(leg_url))
            leg_page.make_links_absolute(leg_url)
            img = leg_page.xpath(
                "//img[contains(@src, 'LegislatorSummary/photos')]")[0]
            photo_url = img.attrib['src']

            leg = Legislator(term, chamber, district, name, party=party,
                             email=email_address, photo_url=photo_url,
                             url=leg_url)
            leg.add_source(url)

            self.save_legislator(leg)
