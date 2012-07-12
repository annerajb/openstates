import datetime
from billy.fulltext import (pdfdata_to_text, oyster_text,
                            text_after_line_numbers)

metadata = dict(
    name='Idaho',
    abbreviation='id',
    legislature_name='Idaho State Legislature',
    upper_chamber_name='Senate',
    lower_chamber_name='House',
    upper_chamber_title='Senator',
    lower_chamber_title='Representative',
    upper_chamber_term=2,
    lower_chamber_term=2,
    terms = [
        #{'name': '1997-1998',
        #    'sessions': [
        #        '1998',
        #    ],
        #    'start_year': 1997, 'end_year': 1998
        #},
        #{'name': '1999-2000',
        #    'sessions': [
        #        '1999',
        #        '2000',
        #        '2000spcl'
        #    ],
        #    'start_year': 1999, 'end_year': 2000
        #},
        #{'name': '2001-2002',
        #    'sessions': [
        #        '2001',
        #        '2002'
        #    ],
        #    'start_year': 2001, 'end_year': 2002
        #},
        #{'name': '2003-2004',
        #    'sessions': [
        #        '2003',
        #        '2004'
        #    ],
        #    'start_year': 2003, 'end_year': 2004
        #},
        #{'name': '2005-2006',
        #    'sessions': [
        #        '2005',
        #        '2006',
        #        '2006spcl'
        #    ],
        #    'start_year': 2005, 'end_year': 2006
        #},
        #{'name': '2007-2008',
        #    'sessions': [
        #        '2007',
        #        '2008'
        #    ],
        #    'start_year': 2007, 'end_year': 2008
        #},
        #{'name': '2009-2010',
        #    'sessions': [
        #        '2009',
        #        '2010'
        #    ],
        #    'start_year': 2009, 'end_year': 2010
        #},
        {'name': '2011-2012',
            'sessions': [
                '2011', '2012',
            ],
            'start_year': 2011, 'end_year': 2012
        },
    ],
    session_details = {
        #'1998':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-fourth Legislature - Second Regular Session',
        #    'start_date': datetime.date(1998, 1, 12),
        #    'end_date': datetime.date(1998, 3, 23)},
        #'1999':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-fifth Legislature - First Regular Session',
        #    'start_date': datetime.date(1999, 1, 11),
        #    'end_date': datetime.date(1999, 3, 19)},
        #'2000':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-fifth Legislature - Second Regular Session',
        #    'start_date': datetime.date(2000, 1, 10),
        #    'end_date': datetime.date(2000, 4, 5)},
        #'2000spcl':
        #    {'type': 'special',
        #    'verbose_name': 'Fifty-fifth Legislature - First Extraordinary Session',
        #    'start_date': datetime.date(2000, 12, 8), # 10:00 am
        #    'end_date': datetime.date(2000, 12, 8)}, # 1:47 pm
        #'2001':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-sixth Legislature - First Regular Session',
        #    'start_date': datetime.date(2001, 1, 8),
        #    'end_date': datetime.date(2001, 3, 30)},
        #'2002':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-sixth Legislature - Second Regular Session',
        #    'start_date': datetime.date(2002, 1, 7),
        #    'end_date': datetime.date(2002, 3, 15)},
        #'2003':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-seventh Legislature - First Regular Session',
        #    'start_date': datetime.date(2003, 1, 6),
        #    'end_date': datetime.date(2003, 3, 3)},
        #'2004':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-seventh Legislature - Second Regular Session',
        #    'start_date': datetime.date(2004, 1, 12),
        #    'end_date': datetime.date(2004, 3, 20)},
        #'2005':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-eighth Legislature - First Regular Session',
        #    'start_date': datetime.date(2005, 1, 10),
        #    'end_date': datetime.date(2005, 4, 6)},
        #'2006':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-eighth Legislature - Second Regular Session',
        #    'start_date': datetime.date(2006, 1, 9),
        #    'end_date': datetime.date(2006, 4, 11)},
        #'2006spcl':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-eighth Legislature - First Extraordinary Session',
        #    'start_date': datetime.date(2006, 8, 25), # 8:00 am
        #    'end_date': datetime.date(2006, 8, 25)}, # 11:16 pm
        #'2007':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-ninth Legislature - First Regular Session',
        #    'start_date': datetime.date(2007, 1, 8),
        #    'end_date': datetime.date(2007, 3, 30)},
        #'2008':
        #    {'type': 'primary',
        #    'verbose_name': 'Fifty-ninth Legislature - Second Regular Session',
        #    'start_date': datetime.date(2008, 1, 7),
        #    'end_date': datetime.date(2008, 4, 2)},
        #'2009':
        #    {'type': 'primary',
        #    'verbose_name': 'Sixtieth Legislature - First Regular Session',
        #    'start_date': datetime.date(2009, 1, 12),
        #    'end_date': datetime.date(2009, 3, 8)},
        #'2010':
        #    {'type': 'primary',
        #    'verbose_name': 'Sixtieth Legislature - Second Regular Session',
        #    'start_date': datetime.date(2010, 1, 11),
        #    'end_date': datetime.date(2010, 3, 29)},
        '2011':
            {'type': 'primary',
            'display_name': '61st Legislature, 1st Regular Session',
            'start_date': datetime.date(2011, 1, 10),
            'end_date': datetime.date(2011, 4, 7),
            '_scraped_name': '2011 Session Information',
            },
        '2012':
            {'type': 'primary',
            'display_name': '61st Legislature, 2nd Regular Session',
            '_scraped_name': '2012 Session Information',
            },
    },
    feature_flags=[],
    _ignored_scraped_sessions=['2010 Session Information',
                               '2009 Session Information',
                               '2008 Session Information',
                               '2007 Session Information',
                               '2006 Extraordinary Session Information',
                               '2006 Session Information',
                               '2005 Session Information',
                               '2004 Session Information',
                               '2003 Session Information ',
                               '2002 Session Information ',
                               '2001 Session Information ',
                               '2000 - 1998 Session Information '],
    )

def session_list():
    from billy.scrape.utils import url_xpath
    return url_xpath('http://legislature.idaho.gov/priorsessions.htm',
                     '//td[@width="95%"]/ul/li/a/text()')[:-1]


@oyster_text
def extract_text(oyster_doc, data):
    return text_after_line_numbers(pdfdata_to_text(data))

document_class = dict(
    AWS_PREFIX = 'documents/id/',
    update_mins = 7*24*60,
    extract_text = extract_text,
    onchanged = ['oyster.ext.elasticsearch.ElasticSearchPush']
)
