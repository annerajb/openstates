import lxml.html
from billy.fulltext import oyster_text

metadata = dict(
    name='Mississippi',
    abbreviation='ms',
    legislature_name='Mississippi Legislature',
    upper_chamber_name='Senate',
    lower_chamber_name='House',
    upper_chamber_title='Senator',
    lower_chamber_title='Representative',
    upper_chamber_term=4,
    lower_chamber_term=4,
    terms=[
        {'name': '2008-2011', 'sessions': ['2008', '2009', '20091E', '20092E',
                                           '20093E', '20101E', '20102E',
                                           '2010', '2011', '20111E'],
         'start_year': 2008, 'end_year': 2011},
        {'name': '2012-2015', 'sessions': ['2012'],
         'start_year': 2012, 'end_year': 2015},
    ],
    session_details={
        '2008': {'display_name': '2008 Regular Session',
                 '_scraped_name': '2008 Regular Session',
                },
        '2009': {'display_name': '2009 Regular Session',
                 '_scraped_name': '2009 Regular Session',
                },
        '20091E': {'display_name': '2009, 1st Extraordinary Session',
                   '_scraped_name': '2009 First Extraordinary Session',
                  },
        '20092E': {'display_name': '2009, 2nd Extraordinary Session',
                   '_scraped_name': '2009 Second Extraordinary Session',
                  },
        '20093E': {'display_name': '2009, 3rd Extraordinary Session',
                   '_scraped_name': '2009 Third Extraordinary Session',
                  },
        '20101E': {'display_name': '2010, 1st Extraordinary Session',
                   '_scraped_name': '2010 First Extraordinary Session',
                  },
        '20102E': {'display_name': '2010, 2nd Extraordinary Session',
                   '_scraped_name': '2010 Second Extraordinary Session',
                  },
        '2010': {'display_name': '2010 Regular Session',
                 '_scraped_name': '2010 Regular Session',
                },
        '2011': {'display_name': '2011 Regular Session',
                 '_scraped_name': '2011 Regular Session',
                },
        '20111E': {'display_name': '2011, 1st Extraordinary Session',
                   '_scraped_name': '2011 First Extraordinary Session',
                  },
        '2012': {'display_name': '2012 Regular Session',
                 '_scraped_name': '2012 Regular Session',
                },
    },
    feature_flags=['subjects'],
    _ignored_scraped_sessions=['2008 First Extraordinary Session',
                               '2007 Regular Session',
                               '2007 First Extraordinary Session',
                               '2006 Regular Session',
                               '2006 First Extraordinary Session',
                               '2006 Second Extraordinary Session',
                               '2005 Regular Session',
                               '2005 First Extraordinary Session',
                               '2005 Second Extraordinary Session',
                               '2005 Third Extraordinary Session',
                               '2005 Fourth Extraordinary Session',
                               '2005 Fifth Extraordinary Session',
                               '2004 Regular Session',
                               '2004 First Extraordinary Session',
                               '2004 Second Extraordinary Session',
                               '2004 Third Extraordinary Session',
                               '2003 Regular Session',
                               '2002 Regular Session',
                               '2002 First Extraordinary Session',
                               '2002 Second Extraordinary Session',
                               '2002 Third Extraordinary Session',
                               '2001 Regular Session',
                               '2001 First Extraordinary Session',
                               '2001 Second Extraordinary Session',
                               '2000 Regular Session',
                               '2000 First Extraordinary Session',
                               '2000 Second Extraordinary Session',
                               '2000 Third Extraordinary Session',
                               '1999 Regular Session',
                               '1998 Regular Session',
                               '1997 Regular Session']
)

def session_list():
    from billy.scrape.utils import url_xpath
    return url_xpath('http://billstatus.ls.state.ms.us/sessions.htm',
                     '//a/text()')

@oyster_text
def extract_text(oyster_doc, data):
    doc = lxml.html.fromstring(data)
    text = ' '.join(p.text_content() for p in
                    doc.xpath('//h2/following-sibling::p'))
    return text

document_class = dict(
    AWS_PREFIX = 'documents/ms/',
    update_mins = 30*24*60,
    extract_text = extract_text,
    onchanged = ['oyster.ext.elasticsearch.ElasticSearchPush']
)
