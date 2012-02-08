# -*- coding: utf-8 -*-
import lxml.html
from billy.scrape import NoDataForPeriod
from billy.scrape.committees import CommitteeScraper, Committee
import re

def clean_spaces(s):
    """ remove \xa0, collapse spaces, strip ends """
    if s is not None:
    	return re.sub('\s+', ' ', s.replace(u'\xa0', ' ')).strip()

class PRCommitteeScraper(CommitteeScraper):
    state = 'pr'

    def scrape(self, chamber, term):
        self.validate_term(term, latest_only=True)

        if chamber == "upper":
            self.scrape_upper()
        elif chamber == "lower":
            self.scrape_lower()
            
    def scrape_upper(self):
        url = 'http://senadopr.us/Lists/Listado%20de%20Comisiones/Comisiones%20del%20Senado.aspx'
        with self.urlopen(url) as html:
            doc = lxml.html.fromstring(html)
            doc.make_links_absolute(url)
            table = doc.xpath('//table[@id="{C05AFE0D-D977-4033-8D7B-C43ABF948A4A}-{3E52C91B-AFC8-4493-967A-C8A47AC4E7B6}"]')
            
            for link in table[0].iterchildren('tr'):
                td_column = list(link)
                name = td_column[0].find('a')
                if name is not None:
                    com_source = name.get('href')
                    #if committee does not have a url use the default.
                    if com_source == 'http://senadopr.us/':
                        com_source = url

                    com_name = name.text
                    #check the committee name to see if it's a join one.
                    if td_column[1].text == 'Comisi\xf3n Conjunta':
                        chamber = 'joint'
                    else:
                        chamber = 'upper'
                    com = Committee(chamber, com_name)
                    com.add_source(com_source)
		    member_name = clean_spaces(td_column[2].find('a').text.replace('HON.','',1));
		    if member_name == "LUZ Z. ARCE FERRER":
			member_name = "Luz Z. Arce Ferrer"
			
                    com.add_member(member_name, 'chairman')
                    self.save_committee(com)
                    
    def scrape_lower(self):
        url = 'http://www.camaraderepresentantes.org/comisiones.asp'
        with self.urlopen(url) as html:
            doc = lxml.html.fromstring(html)
            doc.make_links_absolute(url)
            for link in doc.xpath('//a[contains(@href, "comisiones2")]'):
                self.scrape_lower_committee(link.text, link.get('href'))
    
    def scrape_lower_committee(self, name, url):
        com = Committee('lower', name)
        com.add_source(url)

        with self.urlopen(url) as html:
            doc = lxml.html.fromstring(html)

            contact, directiva, reps = doc.xpath('//div[@class="sbox"]/div[2]')

            # all members are tails of images (they use img tags for bullets)

            # first three members are in the directiva div
            chair = directiva.xpath('b[text()="Presidente:"]/following-sibling::img[1]')
            vchair = directiva.xpath('b[text()="Vice Presidente:"]/following-sibling::img[1]')
            sec = directiva.xpath('b[text()="Secretario(a):"]/following-sibling::img[1]')
            member = 0;
            if chair and chair[0].tail is not None:
                chair = chair[0].tail
                com.add_member(clean_spaces(chair), 'chairman')
                member += 1
            if vchair and vchair[0].tail is not None:
                vchair = vchair[0].tail
                com.add_member(clean_spaces(vchair), 'vice chairman')
                member += 1
            if sec and sec is not None:
                sec = sec[0].tail
                com.add_member(clean_spaces(sec), 'secretary')
                member += 1

            for img in reps.xpath('.//img'):
                member_name = clean_spaces(img.tail)
		if member_name is not None:
                    com.add_member(member_name)
                    member += 1
            if member > 0:
                self.save_committee(com)
