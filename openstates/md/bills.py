#!/usr/bin/env python
import datetime
import itertools
import re

import lxml.html
from scrapelib import HTTPError

from billy.scrape import NoDataForPeriod
from billy.scrape.bills import BillScraper, Bill
from billy.scrape.votes import Vote

CHAMBERS = {
    'upper': ('SB','SJ'),
    'lower': ('HB','HJ'),
}

classifiers = {
    r'Committee Amendment .+? Adopted': 'amendment:passed',
    r'Favorable': 'committee:passed:favorable',
    r'First Reading': 'committee:referred',
    r'Floor (Committee )?Amendment\s?\(.+?\)$': 'amendment:introduced',
    r'Floor Amendment .+? Rejected': 'amendment:failed',
    r'Floor (Committee )?Amendment.+?Adopted': 'amendment:passed',
    r'Floor Amendment.+? Withdrawn': 'amendment:withdrawn',
    r'Pre\-filed': 'bill:introduced',
    r'Re\-(referred|assigned)': 'committee:referred',
    r'Recommit to Committee': 'committee:referred',
    r'Referred': 'committee:referred',
    r'Third Reading Passed': 'bill:passed',
    r'Third Reading Failed': 'bill:failed',
    r'Unfavorable': 'committee:passed:unfavorable',
    r'Vetoed': 'governor:vetoed',
    r'Approved by the Governor': 'governor:signed',
    r'Conference Committee|Passed Enrolled|Special Order|Senate Concur|Motion|Laid Over|Hearing|Committee Amendment|Assigned a chapter|Second Reading|Returned Passed|House Concur|Chair ruled|Senate Refuses to Concur|Senate Requests': 'other',
}

vote_classifiers = {
    r'third': 'passage',
    r'fla|amend|amd': 'amendment',
}

def _classify_action(action):
    if not action:
        return None

    ctty = None

    for regex, type in classifiers.iteritems():
        if re.match(regex, action):
            if 'committee:referred' in type:
                ctty = re.sub(regex, "", action).strip()
            return ( type, ctty )
    return ( None, ctty )

def _clean_sponsor(name):
    if name.startswith('Delegate') or name.startswith('Senator'):
        name = name.split(' ', 1)[1]
    if ', District' in name:
        name = name.rsplit(',', 1)[0]
    return name.strip()

BASE_URL = "http://mlis.state.md.us"
BILL_URL = BASE_URL + "/%s/billfile/%s%04d.htm" # year, session, bill_type, number

class MDBillScraper(BillScraper):
    state = 'md'

    def parse_bill_sponsors(self, doc, bill):
        sponsor_list = doc.cssselect('a[name=Sponlst]')
        if sponsor_list:
            # more than one bill sponsor exists
            elems = sponsor_list[0].getparent().getparent().getparent().cssselect('dd a')
            for elem in elems:
                bill.add_sponsor('cosponsor',
                                 _clean_sponsor(elem.text.strip()))
        else:
            # single bill sponsor
            sponsor = doc.xpath('//a[@name="Sponsors"]/../../dd')[0].text_content()
            bill.add_sponsor('primary', _clean_sponsor(sponsor))

    def parse_bill_actions(self, doc, bill):
        for h5 in doc.xpath('//h5'):
            if h5.text == 'House Action':
                chamber = 'lower'
            elif h5.text == 'Senate Action':
                chamber = 'upper'
            elif h5.text.startswith('Action after passage'):
                chamber = 'governor'
            else:
                break
            dts = h5.getnext().xpath('dl/dt')
            for dt in dts:
                action_date = dt.text.strip()
                if action_date and action_date != 'No Action':
                    year = int(bill['session'][:4])
                    action_date += ('/%s' % year)
                    action_date = datetime.datetime.strptime(action_date,
                                                             '%m/%d/%Y')

                    # no actions after June?, decrement the year on these
                    if action_date.month > 6:
                        year -= 1
                        action_date = action_date.replace(year)

                    # iterate over all dds following the dt
                    dcursor = dt
                    while (dcursor.getnext() is not None and
                           dcursor.getnext().tag == 'dd'):
                        dcursor = dcursor.getnext()
                        actions = dcursor.text_content().split('\r\n')
                        for act in actions:
                            act = act.strip()
                            if not act:
                                continue
                            atype, committee = _classify_action(act)
                            kwargs = {
                                "type": atype
                            }
                            if committee is not None:
                                kwargs['committee'] = committee

                            if atype:
                                bill.add_action(chamber, act, action_date,
                                                **kwargs)
                            else:
                                self.log('unknown action: %s' % act)



    def parse_bill_documents(self, doc, bill):
        bill_text_b = doc.xpath('//b[contains(text(), "Bill Text")]')[0]
        for sib in bill_text_b.itersiblings():
            if sib.tag == 'a':
                bill.add_version(sib.text.strip(','), BASE_URL + sib.get('href'))

        note_b = doc.xpath('//b[contains(text(), "Fiscal and Policy")]')[0]
        for sib in note_b.itersiblings():
            if sib.tag == 'a' and sib.text == 'Available':
                bill.add_document('Fiscal and Policy Note',
                                  BASE_URL + sib.get('href'))

    def parse_bill_votes(self, doc, bill):
        params = {
            'chamber': None,
            'date': None,
            'motion': None,
            'passed': None,
            'yes_count': None,
            'no_count': None,
            'other_count': None,
        }
        elems = doc.cssselect('a')

        # MD has a habit of listing votes twice
        seen_votes = set()

        for elem in elems:
            href = elem.get('href')
            if (href and "votes" in href and href.endswith('htm') and 
                href not in seen_votes):
                seen_votes.add(href)
                vote_url = BASE_URL + href

                if bill['session'] in ('2007', '2007s1', '2008', '2009',
                                       '2010', '2011'):
                    vote = self.parse_old_vote_page(vote_url)
                else:
                    vote = self.parse_vote_page(vote_url)
                vote.add_source(vote_url)
                bill.add_vote(vote)

    def parse_old_vote_page(self, vote_url):
        params = {
            'chamber': None,
            'date': None,
            'motion': None,
            'passed': None,
            'yes_count': None,
            'no_count': None,
            'other_count': None,
        }

        with self.urlopen(vote_url) as vote_html:
            vote_doc = lxml.html.fromstring(vote_html)

            # motion
            box = vote_doc.xpath('//td[@colspan=3]/font[@size=-1]/text()')
            params['motion'] = box[-1]
            params['type'] = 'other'
            if 'senate' in vote_url:
                params['chamber'] = 'upper'
            else:
                params['chamber'] = 'lower'
            for regex, vtype in vote_classifiers.iteritems():
                if re.findall(regex, params['motion'], re.IGNORECASE):
                    params['type'] = vtype

            # counts
            bs = vote_doc.xpath('//td[@width="20%"]/font/b/text()')
            yeas = int(bs[0].split()[0])
            nays = int(bs[1].split()[0])
            excused = int(bs[2].split()[0])
            not_voting = int(bs[3].split()[0])
            absent = int(bs[4].split()[0])
            params['yes_count'] = yeas
            params['no_count'] = nays
            params['other_count'] = excused + not_voting + absent
            params['passed'] = yeas > nays

            # date
            # parse the following format: March 23, 2009
            date_elem = vote_doc.xpath('//font[starts-with(text(), "Legislative Date")]')[0]
            params['date'] = datetime.datetime.strptime(date_elem.text[18:], '%B %d, %Y')

            vote = Vote(**params)

            status = None
            for row in vote_doc.cssselect('table')[3].cssselect('tr'):
                text = row.text_content()
                if text.startswith('Voting Yea'):
                    status = 'yes'
                elif text.startswith('Voting Nay'):
                    status = 'no'
                elif text.startswith('Not Voting') or text.startswith('Excused'):
                    status = 'other'
                else:
                    for cell in row.cssselect('a'):
                        getattr(vote, status)(cell.text.strip())
        return vote

    def parse_vote_page(self, vote_url):
        vote_html = self.urlopen(vote_url)
        doc = lxml.html.fromstring(vote_html)

        # chamber
        if 'senate' in vote_url:
            chamber = 'upper'
        else:
            chamber = 'lower'

        # date in the following format: Mar 23, 2009
        date = doc.xpath('//td[starts-with(text(), "Legislative")]')[0].text
        date = date.replace(u'\xa0', ' ')
        date = datetime.datetime.strptime(date[18:], '%b %d, %Y')

        # motion
        motion = ''.join(x.text_content() for x in \
                         doc.xpath('//td[@colspan="23"]'))
        if motion == '':
            motion = "No motion given"  # XXX: Double check this. See SJ 3.
        motion = motion.replace(u'\xa0', ' ')

        # totals
        tot_class = doc.xpath('//td[contains(text(), "Yeas")]')[0].get('class')
        totals = doc.xpath('//td[@class="%s"]/text()' % tot_class)[1:]
        yes_count = int(totals[0].split()[-1])
        no_count = int(totals[1].split()[-1])
        other_count = int(totals[2].split()[-1])
        other_count += int(totals[3].split()[-1])
        other_count += int(totals[4].split()[-1])
        passed = yes_count > no_count

        vote = Vote(chamber=chamber, date=date, motion=motion,
                    yes_count=yes_count, no_count=no_count,
                    other_count=other_count, passed=passed)

        # go through, find Voting Yea/Voting Nay/etc. and next tds are voters
        func = None
        for td in doc.xpath('//td/text()'):
            td = td.replace(u'\xa0', ' ')
            if td.startswith('Voting Yea'):
                func = vote.yes
            elif td.startswith('Voting Nay'):
                func = vote.no
            elif td.startswith('Not Voting'):
                func = vote.other
            elif td.startswith('Excused'):
                func = vote.other
            elif func:
                func(td)

        return vote

    def scrape_bill(self, chamber, session, bill_type, number):
        """ Creates a bill object """
        if len(session) == 4:
            session_url = session+'rs'
        else:
            session_url = session
        url = BILL_URL % (session_url, bill_type, number)
        with self.urlopen(url) as html:
            doc = lxml.html.fromstring(html)
            # find <a name="Title">, get parent dt, get parent dl, then dd n dl
            title = doc.xpath('//a[@name="Title"][1]/../../dd[1]/text()')[0].strip()

            synopsis = doc.xpath('//font[@size="3"]/p/text()')[0].strip()

            #print "%s %d %s" % (bill_type, number, title)

            if 'B' in bill_type:
                _type = ['bill']
            elif 'J' in bill_type:
                _type = ['joint resolution']

            bill = Bill(session, chamber, "%s %d" % (bill_type, number), title,
                        type=_type, synopsis=synopsis)
            bill.add_source(url)

            self.parse_bill_sponsors(doc, bill)     # sponsors
            self.parse_bill_actions(doc, bill)      # actions
            self.parse_bill_documents(doc, bill)    # documents and versions
            self.parse_bill_votes(doc, bill)        # votes

            # subjects
            subjects = []
            for subj in doc.xpath('//a[contains(@href, "/subjects/")]'):
                subjects.append(subj.text.split('-see also-')[0])
            bill['subjects'] = subjects

            # add bill to collection
            self.save_bill(bill)


    def scrape(self, chamber, session):

        self.validate_session(session)

        for bill_type in CHAMBERS[chamber]:
            for i in itertools.count(1):
                try:
                    self.scrape_bill(chamber, session, bill_type, i)
                except HTTPError as he:
                    if he.response.status_code != 404:
                        raise he
                    break
