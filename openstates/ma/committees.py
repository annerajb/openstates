from billy.scrape.committees import CommitteeScraper, Committee

import lxml.html


class MACommitteeScraper(CommitteeScraper):
    state = 'ma'

    def scrape(self, term, chambers):
        page_types = []
        if 'upper' in chambers:
            page_types += ['Senate', 'Joint']
        if 'lower' in chambers:
            page_types += ['House']
        chamber_mapping = {'Senate': 'upper',
                           'House': 'lower',
                           'Joint': 'joint'}

        foundComms = []

        for page_type in page_types:
            url = 'http://www.malegislature.gov/Committees/' + page_type

            with self.urlopen(url) as html:
                doc = lxml.html.fromstring(html)
                doc.make_links_absolute('http://www.malegislature.gov')

                for com_url in doc.xpath('//ul[@class="committeeList"]/li/a/@href'):
                    chamber = chamber_mapping[page_type]
                    self.scrape_committee(chamber, com_url)

    def scrape_committee(self, chamber, url):
        with self.urlopen(url) as html:
            doc = lxml.html.fromstring(html)

            name = doc.xpath('//span[@class="committeeShortName"]/text()')
            if len(name) == 0:
                self.warning("Had to skip this malformed page.")
                return
            # Because of http://www.malegislature.gov/Committees/Senate/S29 this
            # XXX: hack had to be pushed in. Remove me ASAP. This just skips
            #      malformed pages.

            name = name[0]
            com = Committee(chamber, name)
            com.add_source(url)

            # get both titles and names, order is consistent
            titles = doc.xpath('//p[@class="rankingMemberTitle"]/text()')
            names = doc.xpath('//p[@class="rankingMemberName"]/a/text()')

            for title, name in zip(titles, names):
                com.add_member(name, title)

            for member in doc.xpath('//div[@class="committeeRegularMembers"]//a/text()'):
                com.add_member(member)

            self.save_committee(com)
