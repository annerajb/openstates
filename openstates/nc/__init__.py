import datetime
import lxml.html
from billy.fulltext import oyster_text, text_after_line_numbers

metadata = dict(
    name='North Carolina',
    abbreviation='nc',
    legislature_name='North Carolina General Assembly',
    lower_chamber_name='House of Representatives',
    upper_chamber_name='Senate',
    lower_chamber_title='Representative',
    upper_chamber_title='Senator',
    lower_chamber_term=2,
    upper_chamber_term=2,
    terms=[
        #{'name': '1985-1986',
        # 'sessions': ['1985', '1985E1'],
        # 'start_year': 1985, 'end_year': 1986},
        #{'name': '1987-1988',
        # 'sessions': ['1987'],
        # 'start_year': 1987, 'end_year': 1988},
        #{'name': '1989-1990',
        # 'sessions': ['1989', '1989E1', '1989E2'],
        # 'start_year': 1989, 'end_year': 1990},
        #{'name': '1991-1992',
        # 'sessions': ['1991', '1991E1'],
        # 'start_year': 1991, 'end_year': 1992},
        #{'name': '1993-1994',
        # 'sessions': ['1993', '1993E1'],
        # 'start_year': 1993, 'end_year': 1994},
        #{'name': '1995-1996',
        # 'sessions': ['1995', '1995E1', '1995E2'],
        # 'start_year': 1995, 'end_year': 1996},
        #{'name': '1997-1998',
        # 'sessions': ['1997', '1997E1'],
        # 'start_year': 1997, 'end_year': 1998},
        #{'name': '1999-2000',
        # 'sessions': ['1999', '1999E1', '1999E2'],
        # 'start_year': 1999, 'end_year': 2000},
        #{'name': '2001-2002',
        # 'sessions': ['2001', '2001E1'],
        # 'start_year': 2001, 'end_year': 2002},
        #{'name': '2003-2004',
        # 'sessions': ['2003', '2003E1', '2003E2', '2003E3'],
        # 'start_year': 2003, 'end_year': 2004},
        #{'name': '2005-2006',
        # 'sessions': ['2005'],
        # 'start_year': 2005, 'end_year': 2006},
        #{'name': '2007-2008',
        # 'sessions': ['2007', '2007E1', '2007E3'],
        # 'start_year': 2007, 'end_year': 2008},
        {'name': '2009-2010',
         'sessions': ['2009'],
         'start_year': 2009, 'end_year': 2010},
        {'name': '2011-2012',
         'sessions': ['2011'],
         'start_year': 2011, 'end_year': 2012},
        ],
    session_details={
        '2009': {'start_date': datetime.date(2009,1,28), 'type': 'primary',
                 'display_name': '2009 Regular Session',
                 '_scraped_name': '2009-2010 Session',
                },
        '2011': {'start_date': datetime.date(2011,1,26), 'type': 'primary',
                 'display_name': '2011 Regular Session',
                 '_scraped_name': '2011-2012 Session',
                },
    },
    _ignored_scraped_sessions=['2008 Extra Session', '2007-2008 Session',
                             '2007 Extra Session', '2005-2006 Session',
                             '2004 Extra Session', '2003-2004 Session',
                             '2003 Extra Session 1', '2003 Extra Session 2',
                             '2002 Extra Session', '2001-2002 Session',
                             '2000 Special Session', '1999-2000 Session',
                             '1999 Special Session', '1998 Special Session',
                             '1997-1998 Session', '1996 2nd Special Session',
                             '1996 1st Special Session', '1995-1996 Session',
                             '1994 Special Session', '1993-1994 Session',
                             '1991-1992 Session', '1991 Special Session',
                             '1990 Special Session', '1989-1990 Session',
                             '1989 Special Session', '1987-1988 Session',
                             '1986 Special Session', '1985-1986 Session'],
    feature_flags=['subjects'],
)


def session_list():
    from billy.scrape.utils import url_xpath
    return url_xpath('http://www.ncleg.net',
                     '//select[@name="sessionToSearch"]/option/text()')


@oyster_text
def extract_text(oyster_doc, data):
    doc = lxml.html.fromstring(data)
    text = ' '.join([x.text_content() for x in
                     doc.xpath('//p[starts-with(@class, "a")]')])
    return text

document_class = dict(
    AWS_PREFIX = 'documents/nc/',
    update_mins = None,
    extract_text = extract_text,
    onchanged = ['oyster.ext.elasticsearch.ElasticSearchPush']
)
