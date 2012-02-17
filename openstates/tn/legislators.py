from billy.scrape import ScrapeError, NoDataForPeriod
from billy.scrape.legislators import LegislatorScraper, Legislator
import lxml.html

class TNLegislatorScraper(LegislatorScraper):
    state = 'tn'
    

    def scrape(self, chamber, term):
        self.validate_term(term, latest_only=False)
        root_url = 'http://www.capitol.tn.gov/'
        parties = {'D': 'Democratic', 'R': 'Republican', 'CCR': 'Carter County Republican'}

        #testing for chamber
        if chamber == 'upper':
            url_chamber_name = 'senate'
            abbr = 's'
        else:
            url_chamber_name = 'house'
            abbr = 'h'
        if term != self.metadata["terms"][-1]["sessions"][0]:
            chamber_url = root_url + url_chamber_name + '/archives/'+term+'GA/Members/index.html'
        else:
            chamber_url = root_url + url_chamber_name + '/members/'

        with self.urlopen(chamber_url) as page:
            page = lxml.html.fromstring(page)

            for row in page.xpath("//tr")[1:]:
                partyInit = row.xpath('td[2]')[0].text.split()[0]
                party = parties[partyInit]
                district = row.xpath('td[4]/a')[0].text.split()[1]
                phone = row.xpath('td[6]')[0].text
                #special case for Karen D. Camper
                if phone == None:
                    phone = row.xpath('td[6]/div')[0].text
                phone = '615-' + phone.split()[0]
                email = row.xpath('td[7]/a')[0].text 
                member_url = root_url + url_chamber_name + '/members/' + abbr + district + '.html'
                member_photo_url = root_url + url_chamber_name + '/members/images/' + abbr + district + '.jpg'

                with self.urlopen(member_url) as member_page:
                    member_page = lxml.html.fromstring(member_page)
                    name = member_page.xpath('//div[@id="membertitle"]/h2')[0].text
                    if 'Speaker' in name:
                        full_name = name[8:len(name)]
                    elif 'Lt.' in name:
                        full_name = name[13:len(name)]
                    elif abbr == 'h':
                        full_name = name[5: len(name)]
                    else:
                        full_name = name[8:len(name)]
                    
                    leg = Legislator(term, chamber, district, full_name, party=party, email=email, phone=phone, url=member_url, photo_url=member_photo_url)
                    leg.add_source(chamber_url)
                    leg.add_source(member_url)
                    self.save_legislator(leg)
