import re

from billy.scrape.legislators import LegislatorScraper, Legislator
import lxml.html

abbr = {'D': 'Democratic', 'R': 'Republican'}

class MILegislatorScraper(LegislatorScraper):
    state = 'mi'

    def scrape(self, chamber, term):
        self.validate_term(term, latest_only=True)
        if chamber == 'lower':
            return self.scrape_lower(chamber, term)
        return self.scrape_upper(chamber, term)

    def scrape_lower(self, chamber, term):
        url = 'http://www.house.mi.gov/mhrpublic/frmRepList.aspx'
        table = [
            "website",
            "district",
            "name",
            "party",
            "location",
            "phone",
            "email"
        ]
        with self.urlopen(url) as html:
            doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        # skip two rows at top
        for row in doc.xpath('//table[@id="grvRepInfo"]/*'):
            tds = row.xpath('.//td')
            if len(tds) == 0:
                continue
            metainf = {}
            for i in range(0, len(table)):
                metainf[table[i]] = tds[i]
            district = str(int(metainf['district'].text_content().strip()))
            party = metainf['party'].text_content().strip()
            office = metainf['location'].text_content().strip()
            phone = metainf['phone'].text_content().strip()
            email = metainf['email'].text_content().strip()
            leg_url = metainf['website'].xpath("./a")[0].attrib['href']
            name = metainf['name'].text_content().strip()
            leg = Legislator(term=term,
                             chamber=chamber,
                             full_name=name,
                             district=district,
                             party=abbr[party],
                             office=office,
                             phone=phone,
                             email=email,
                             url=leg_url)
            leg.add_source(url)
            self.save_legislator(leg)

    def scrape_upper(self, chamber, term):
        url = 'http://www.senate.michigan.gov/members/memberlist.htm'
        with self.urlopen(url) as html:
            doc = lxml.html.fromstring(html)
            for row in doc.xpath('//table[@width=550]/tr')[1:39]:
                # party, dist, member, office_phone, office_fax, office_loc
                party = abbr[row.xpath('td[1]/text()')[0]]
                district = row.xpath('td[2]/a/text()')[0]
                leg_url = row.xpath('td[3]/a/@href')[0]
                name = row.xpath('td[3]/a/text()')[0]
                office_phone = row.xpath('td[4]/text()')[0]
                office_fax = row.xpath('td[5]/text()')[0]
                office_loc = row.xpath('td[6]/text()')[0]
                leg = Legislator(term=term, chamber=chamber,
                                 district=district, full_name=name,
                                 party=party, office_phone=office_phone,
                                 url=leg_url,
                                 office_fax=office_fax,
                                 office_loc=office_loc)
                leg.add_source(url)
                self.save_legislator(leg)
