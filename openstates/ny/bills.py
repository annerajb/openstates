import re
import datetime

from billy.scrape.bills import BillScraper, Bill
from billy.scrape.votes import Vote

import scrapelib
import lxml.html
import lxml.etree


class NYBillScraper(BillScraper):

    state = 'ny'

    def scrape(self, chamber, session):

        errors = 0
        index = 0
        previous_nonamendment_bill = None
        self.scraped_amendments = scraped_amendments = set()

        while errors < 10:
            index += 1

            try:
                url = ("http://open.nysenate.gov/legislation/search/"
                       "?search=otype:bill&searchType=&format=xml"
                       "&pageIdx=%d" % index)

                with self.urlopen(url) as page:
                    page = lxml.etree.fromstring(page.bytes)
                    if not page.getchildren():
                        # If the result response is empty, we've hit the end of
                        # the data. Quit.
                        break

                    for result in page.xpath("//result[@type = 'bill']"):

                        bill_id = result.attrib['id'].split('-')[0]

                        # Parse the bill_id into beginning letter, number
                        # and any trailing letters indicating its an amendment.
                        bill_id_rgx = r'(^[A-Z])(\d{,6})([A-Z]{,3})'
                        bill_id_base = re.search(bill_id_rgx, bill_id)
                        letter, number, is_amendment = bill_id_base.groups()
                        if is_amendment:

                            # If this bill is an amendment, use the last
                            # nonamendment bill to add votes, documents,
                            # etc.
                            if previous_nonamendment_bill is not None:
                                self.add_amendment_data(previous_nonamendment_bill, result)

                            if bill_id in scraped_amendments:
                                continue

                        else:
                            if previous_nonamendment_bill is not None:
                                self.save_bill(previous_nonamendment_bill)
                                previous_nonamendment_bill = None

                        title = result.attrib['title'].strip()
                        if title == '(no title)':
                            continue

                        if "sponsor" not in result.attrib:
                            continue

                        primary_sponsor = result.attrib['sponsor']
                        primary_sponsor = re.sub(
                            r'\s+\(MS\)\s*$', '', primary_sponsor).strip()

                        bill_chamber, bill_type = {
                            'S': ('upper', 'bill'),
                            'R': ('upper', 'resolution'),
                            'J': ('upper', 'legislative resolution'),
                            'B': ('upper', 'concurrent resolution'),
                            'A': ('lower', 'bill'),
                            'E': ('lower', 'resolution'),
                            'K': ('lower', 'legislative resolution'),
                            'L': ('lower', 'joint resolution')}[bill_id[0]]

                        if chamber != bill_chamber:
                            continue

                        bill = Bill(session, chamber, bill_id, title,
                                    type=bill_type)

                        bill.add_source(url)

                        # Adding sponsors below.
                        #bill.add_sponsor('primary', primary_sponsor)

                        bill_url = ("http://open.nysenate.gov/legislation/"
                                    "bill/%s" % result.attrib['id'])
                        self.scrape_bill(bill, bill_url)
                        bill.add_source(bill_url)

                        if not is_amendment:
                            previous_nonamendment_bill = bill

                        index += 1

            except scrapelib.HTTPError as e:
                if e.response.code == 404:
                    errors += 1
                else:
                    raise

    def scrape_bill(self, bill, url):
        with self.urlopen(url) as page:
            page = page.replace('\x00', '')
            page = lxml.html.fromstring(page)
            page.make_links_absolute(url)

            # Scrape sponsors.
            sponsor_type = 'primary'
            xpath = '//b[starts-with(text(), "Sponsor:")]'
            siblings = page.xpath(xpath)[0].itersiblings()
            while True:
                sib = next(siblings)
                try:
                    is_sponsor = '/legislation/sponsor' in sib.attrib['href']
                except KeyError:
                    is_sponsor = False

                # Modify the sponsor type.
                is_cosponsor_heading = sib.text_content().strip()\
                    .startswith('Co-sponsor(s):')
                is_multisponsor_heading = sib.text_content().strip()\
                    .startswith('Multi-sponsor(s):')
                if not is_sponsor or is_cosponsor_heading:
                    if is_cosponsor_heading:
                        sponsor_type = 'cosponsor'
                        continue
                    elif is_multisponsor_heading:
                        sponsor_type = 'multisponsor'
                        continue
                    else:
                        break

                # Add the sponsor.
                name = sib.text_content().replace('(MS)', '').strip()
                bill.add_sponsor(sponsor_type, name)

            actions = []
            for li in page.xpath("//div[@id = 'content']/ul[1]/li"):
                text = li.xpath("string()").strip()

                match = re.match(r"([A-Z][a-z][a-z]\s+\d{1,2},\s+\d{4,4}):"
                                 r"\s+(.*)$", text)
                date = datetime.datetime.strptime(match.group(1),
                                                  "%b %d, %Y").date()
                action = match.group(2)

                actions.append((date, action))

            first = True
            act_chamber = bill['chamber']
            for date, action in reversed(actions):
                atype = []
                if first:
                    atype.append('bill:introduced')
                    first = False

                if 'REFERRED TO' in action:
                    atype.append('committee:referred')
                elif action == 'ADOPTED':
                    atype.append('bill:passed')
                elif action in ('PASSED SENATE', 'PASSED ASSEMBLY'):
                    atype.append('bill:passed')
                elif action in ('DELIVERED TO SENATE',
                                'DELIVERED TO ASSEMBLY'):
                    first = True
                    act_chamber = {'upper': 'lower',
                                   'lower': 'upper'}[act_chamber]
                elif (action.startswith('AMENDED') or
                      action.startswith('AMEND (T) AND') or
                      action.startswith('AMEND AND')):
                    atype.append('amendment:passed')
                elif action.startswith('RECOMMIT,'):
                    atype.append('committee:referred')

                if 'RECOMMIT TO' in action:
                    atype.append('committee:referred')

                if not atype:
                    atype = ['other']

                bill.add_action(bill['chamber'], action, date,
                                type=atype)

            self.scrape_versions(bill, page, url)

            self.scrape_votes(bill, page)

            subjects = []
            for link in page.xpath("//a[contains(@href, 'lawsection')]"):
                subjects.append(link.text.strip())

            bill['subjects'] = subjects

    def scrape_votes(self, bill, page):
        for b in page.xpath("//div/b[starts-with(., 'VOTE: FLOOR VOTE:')]"):
            date = b.text.split('-')[1].strip()
            date = datetime.datetime.strptime(date, "%b %d, %Y").date()

            yes_votes, no_votes, other_votes = [], [], []
            yes_count, no_count, other_count = 0, 0, 0

            vtype = None
            for tag in b.xpath("following-sibling::blockquote/*"):
                if tag.tag == 'b':
                    text = tag.text
                    if text.startswith('Ayes'):
                        vtype = 'yes'
                        yes_count = int(re.search(
                            r'\((\d+)\):', text).group(1))
                    elif text.startswith('Nays'):
                        vtype = 'no'
                        no_count = int(re.search(
                            r'\((\d+)\):', text).group(1))
                    elif (text.startswith('Excused') or
                          text.startswith('Abstain') or
                          text.startswith('Absent')
                         ):
                        vtype = 'other'
                        other_count += int(re.search(
                            r'\((\d+)\):', text).group(1))
                    else:
                        raise ValueError('bad vote type: %s' % tag.text)
                elif tag.tag == 'a':
                    name = tag.text.strip()
                    if vtype == 'yes':
                        yes_votes.append(name)
                    elif vtype == 'no':
                        no_votes.append(name)
                    elif vtype == 'other':
                        other_votes.append(name)

            passed = yes_count > (no_count + other_count)

            vote = Vote('upper', date, 'Floor Vote', passed, yes_count,
                        no_count, other_count)

            for name in yes_votes:
                vote.yes(name)
            for name in no_votes:
                vote.no(name)
            for name in other_votes:
                vote.other(name)

            bill.add_vote(vote)

    def scrape_versions(self, bill, page, url):
        '''Note--this function also scrapes the companion bill_id, or
        'same-as' id.'''

        text = page.xpath('//*[contains(., "Versions:")]')[-1].text_content()
        id_rgx = r'[A-Z]\S+'
        if 'Same as:' in text:
            same_as_text, version_text = text.split('Versions:')
            _, same_as_text = same_as_text.split('Same as:')
            same_as_numbers = re.findall(id_rgx, same_as_text)

            bill['companion_bill_ids'] = []
            for same_as_number in same_as_numbers:
                same_as_number_noyear, _ = same_as_number.rsplit('-')
                bill['companion_bill_ids'].append(same_as_number_noyear)

        else:
            version_text = text
            _, version_text = text.split('Versions:')

        url_tmpl = 'http://open.nysenate.gov/legislation/bill/'
        for version_bill_id in re.findall('\S+', version_text):
            version_bill_id_noyear, _ = version_bill_id.rsplit('-')
            version_url = url_tmpl + version_bill_id
            bill.add_version(version_bill_id_noyear, version_url)
            self.scraped_amendments.add(version_bill_id_noyear)

    def add_amendment_data(self, bill, result):
        url = ("http://open.nysenate.gov/legislation/"
                    "bill/%s" % result.attrib['id'])
        with self.urlopen(url) as page:
            page = page.replace('\x00', '')
            page = lxml.html.fromstring(page)
            page.make_links_absolute(url)
            self.scrape_votes(bill, page)
