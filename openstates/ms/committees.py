from billy.scrape import NoDataForPeriod
from billy.scrape.committees import CommitteeScraper, Committee
from .utils import clean_committee_name

import lxml.etree


class MSCommitteeScraper(CommitteeScraper):
    state = 'ms'

    def scrape(self, chamber, term_name):
        self.save_errors=False
        if int(term_name[0:4]) < 2008:
            raise NoDataForPeriod(term_name)

        if chamber == 'lower':
            chamber = 'h'
        else:
            chamber = 's'

        self.scrape_comm(chamber, term_name)

    def scrape_comm(self, chamber, term_name):
        url = 'http://billstatus.ls.state.ms.us/htms/%s_cmtememb.xml' % chamber
        with self.urlopen(url) as comm_page:
            root = lxml.etree.fromstring(comm_page.bytes)
            if chamber == 'h':
                chamber = "lower"
            else:
                chamber = "upper"
            for mr in root.xpath('//committee'):
                name = mr.xpath('string(name)')
                comm = Committee(chamber, name)

                chair = mr.xpath('string(chair)')
                chair = chair.replace(", Chairman", "")
                role = "Chairman"
                if len(chair) > 0:
                    comm.add_member(chair, role=role)
                vice_chair = mr.xpath('string(vice_chair)')
                vice_chair = vice_chair.replace(", Vice-Chairman", "")
                role = "Vice-Chairman"
                if len(vice_chair) > 0:
                    comm.add_member(vice_chair, role=role)
                members = mr.xpath('string(members)').split(";")
                
                for leg in members:
                    if leg[0] == " ":
                        comm.add_member(leg[1: len(leg)])
                    else:
                        comm.add_member(leg)
                comm.add_source(url)
                self.save_committee(comm)
