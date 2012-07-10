import re
import datetime
import urlparse
from collections import defaultdict
import lxml.html

from billy.scrape import NoDataForPeriod
from billy.scrape.bills import BillScraper, Bill

# Base URL for the details of a given bill.
BILL_DETAIL_URL_BASE = 'https://www.revisor.mn.gov/revisor/pages/search_status/'

# The versions of a bill use a different base URL.
VERSION_URL_BASE = "https://www.revisor.mn.gov"

class MNBillScraper(BillScraper):
    state = 'mn'

    _categorizers = (
        ('Introduced', 'bill:introduced'),
        ('Introduction and first reading, referred to',
         ['bill:introduced', 'committee:referred']),
        ('Introduction and first reading', 'bill:introduced'),
        ('Referred (by Chair )?to', 'committee:referred'),
        ('Second reading', 'bill:reading:2'),
        ('Comm(ittee)? report: (T|t)o pass( as amended)? and re-refer(red)? to',
         ['committee:passed', 'committee:referred']),
        ('Comm(ittee)? report: (T|t)o pass( as amended)?', 'committee:passed'),
        ('Third reading Passed', 'bill:passed'),
        ('Bill was passed', 'bill:passed'),
        ('Third reading', 'bill:reading:3'),
        ("Governor('s action )?Approval", 'governor:signed'),
        (".+? (V|v)eto", 'governor:vetoed'),
        ("Presented to Governor", 'governor:received'),
        ("Amended", 'amendment:passed'),
        ("Amendments offered", 'amendment:introduced'),
        (" repassed ", 'bill:passed'),
        (" re-referred ", 'committee:referred'),
        ("Received from", "bill:introduced"),
    )

    def get_bill_topics(self, chamber, session):
        search_chamber = {'lower':'House', 'upper':'Senate'}[chamber]
        search_session = self.metadata['session_details'][session]['site_id']
        self._subject_mapping = defaultdict(list)

        url = '%sstatus_search.php?body=%s&search=topic&session=%s' % (
            BILL_DETAIL_URL_BASE, search_chamber, search_session)
        with self.urlopen(url) as html:
            doc = lxml.html.fromstring(html)
            # skip first one ('--- All ---')
            for option in doc.xpath('//select[@name="topic[]"]/option')[1:]:
                # Subjects look like "Name of Subject (##)" -- split off the #
                subject = option.text.rsplit(' (')[0]
                value = option.get('value')
                opt_url = '%sstatus_results.php?body=%s&search=topic&session=%s&topic[]=%s' % (
                    BILL_DETAIL_URL_BASE, search_chamber, search_session, value)
                with self.urlopen(opt_url) as opt_html:
                    opt_doc = lxml.html.fromstring(opt_html)
                    for bill in opt_doc.xpath('//table[@width="80%"]/tr/td[2]/a/font/text()'):
                        self._subject_mapping[bill].append(subject)

    def extract_bill_actions(self, doc, current_chamber):
        """Extract the actions taken on a bill.
        A bill can have actions taken from either chamber.  The current
        chamber's actions will be the first table of actions. The other
        chamber's actions will be in the second table.

        Returns a list of bill actions. Each bill action is a dict with keys:
            action_chamber = 'upper|lower'
            action = string
            date = MM/DD/YYYY
        """

        bill_actions = list()
        action_tables = doc.xpath('//table[@summary="Actions"]')

        for cur_table in action_tables:
            for row in cur_table.xpath('tr')[1:]:
                bill_action = dict()

                # split up columns
                (date_col, action_col, desc_col, text_col,
                 page_col, rc_col) = row.xpath('td')

                action_date = date_col.text_content().strip()
                action_text = action_col.text_content().strip()
                description = desc_col.text_content().strip()

                # skip non-actions (don't have date)
                if action_text in ('Chapter number', 'See also', 'See',
                                   'Effective date', 'Secretary of State'):
                    continue

                # dates are really inconsistent here
                try:
                    action_date = datetime.datetime.strptime(action_date,
                                                             '%m/%d/%Y')
                except ValueError:
                    try:
                        action_date = datetime.datetime.strptime(description,
                                                                 '%m/%d/%y')
                    except ValueError:
                        try:
                            action_date = datetime.datetime.strptime(
                                description, '%m/%d/%Y')
                        except ValueError:
                            self.warning('ACTION without date: %s' %
                                         action_text)
                            continue
                # categorize actions
                action_type = 'other'
                for pattern, atype in self._categorizers:
                    if re.match(pattern, action_text):
                        action_type = atype
                        if 'committee:referred' in action_type:
                            bill_action['committee'] = description
                        break

                if description:
                    action_text += ' ' + description
                bill_action['action_text'] = action_text
                if isinstance(action_type, list):
                    for atype in action_type:
                        if atype.startswith('governor'):
                            bill_action['action_chamber'] = 'executive'
                            break
                    else:
                        bill_action['action_chamber'] = current_chamber
                else:
                    if action_type.startswith('governor'):
                        bill_action['action_chamber'] = 'executive'
                    else:
                        bill_action['action_chamber'] = current_chamber
                bill_action['action_date'] = action_date
                bill_action['action_type'] = action_type
                bill_actions.append(bill_action)

            # if there's a second table, toggle the current chamber
            if current_chamber == 'upper':
                current_chamber = 'lower'
            else:
                current_chamber = 'upper'

        return bill_actions

    def get_bill_info(self, chamber, session, bill_detail_url, version_list_url):
        """Extracts all the requested info for a given bill.

        Calls the parent's methods to enter the results into JSON files.
        """
        if chamber == "House":
            chamber = 'lower'
        else:
            chamber = 'upper'

        with self.urlopen(bill_detail_url) as bill_html:
            doc = lxml.html.fromstring(bill_html)

            bill_id = doc.xpath('//title/text()')[0].split()[0]
            bill_title = doc.xpath('//font[@size=-1]/text()')[0]
            bill_type = {'F': 'bill', 'R':'resolution',
                         'C': 'concurrent resolution'}[bill_id[1]]
            bill = Bill(session, chamber, bill_id, bill_title, type=bill_type)
            bill['subjects'] = self._subject_mapping[bill_id]
            bill.add_source(bill_detail_url)

            # grab sponsors
            sponsors = doc.xpath('//table[@summary="Show Authors"]/descendant::a/text()')
            if sponsors:
                primary_sponsor = sponsors[0].strip()
                bill.add_sponsor('primary', primary_sponsor, chamber=chamber)
                cosponsors = sponsors[1:]
                for leg in cosponsors:
                    bill.add_sponsor('cosponsor', leg.strip(), chamber=chamber)

            # Add Actions performed on the bill.
            bill_actions = self.extract_bill_actions(doc, chamber)
            for action in bill_actions:
                kwargs = {}
                if 'committee' in action:
                    kwargs['committee'] = action['committee']

                bill.add_action(action['action_chamber'],
                                action['action_text'],
                                action['action_date'],
                                type=action['action_type'],
                                **kwargs)

        # Get all versions of the bill.
        # Versions of a bill are on a separate page, linked to from the column
        # labeled, "Bill Text", on the search results page.
        with self.urlopen(version_list_url) as version_html:
            if 'resolution' in version_html.response.url:
                bill.add_version('resolution text', version_html.response.url)
            else:
                version_doc = lxml.html.fromstring(version_html)
                for v in version_doc.xpath('//a[starts-with(@href, "/bin/getbill.php")]'):
                    version_url = urlparse.urljoin(VERSION_URL_BASE,
                                                   v.get('href'))
                    bill.add_version(v.text.strip(), version_url)

        self.save_bill(bill)

    def scrape(self, chamber, session):
        """Scrape all bills for a given chamber and a given session.

        This method uses the legislature's search page to collect all the bills
        for a given chamber and session.
        """
        search_chamber = {'lower':'House', 'upper':'Senate'}[chamber]
        search_session = self.metadata['session_details'][session]['site_id']

        self.get_bill_topics(chamber, session)

        # MN bill search page returns a maximum of 999 search results
        total_rows = list() # used to concatenate search results
        stride = 900
        start = 0

        # get total list of rows
        search_url = ('https://www.revisor.mn.gov/revisor/pages/search_status/'
                      'status_results.php?body=%s&session=%s&bill=%s-%s'
                      '&bill_type=%s&submit_bill=GO')
        for bill_type in ('bill', 'concurrent', 'resolution'):
            for start in xrange(0, 10000, stride):
                # body: "House" or "Senate"
                # session: legislative session id
                # bill: Range start-end (e.g. 1-10)
                url = search_url % (search_chamber, search_session, start,
                                    start+stride, bill_type)

                with self.urlopen(url) as html:
                    doc = lxml.html.fromstring(html)

                    # get table containing bills
                    rows = doc.xpath('//table[@width="80%"]/tr')[1:]
                    total_rows.extend(rows)

                    # out of rows
                    if len(rows) == 0:
                        self.debug("Total Bills Found: %d" % len(total_rows))
                        break

        # process each row
        for row in total_rows:
            # second column: status link
            bill_details_link = row.xpath('td[2]/a')[0]
            bill_details_url = urlparse.urljoin(BILL_DETAIL_URL_BASE,
                                                bill_details_link.get('href'))

            # version link sometimes goes to wrong place, forge it
            session_year = search_session[-4:]
            session_number = search_session[0]
            bill_id = bill_details_link.text_content()
            bill_version_url = 'https://www.revisor.mn.gov/bin/getbill.php' \
            '?session_year=%s&session_number=%s&number=%s&version=list' % (
                session_year, session_number, bill_id)

            self.get_bill_info(search_chamber, session, bill_details_url,
                               bill_version_url)
