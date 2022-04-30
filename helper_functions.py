from shapely.geometry import Point, Polygon
from datetime import datetime
import json

def readable_date(x):
    '''
    Takes in a datetime.datetime object
    Returns the date of the object
    '''
    day = x.strftime('%d')
    month = x.strftime('%m')
    year = x.strftime('%Y')
    return f'{day}/{month}/{year}'


def readable_time(x):
    '''
    Takes in a datetime.datetime object
    Returns the time of the object
    '''
    hour = x.strftime('%I')
    hour = hour[1] if hour[0] == '0' else hour
    minute = x.strftime('%M')
    am_pm = x.strftime('%p')
    return f'{hour}:{minute}{am_pm}'


def assigned_to_tc(latitude, longitude):
    '''
    Takes in the latitude and longitude of the reported location
    Returns the name of the town council assigned to that location
    '''
    report_point = Point(longitude, latitude)

    with open('electoral_boundaries.json') as f:
        data = json.load(f)
        for k, v in data.items():
            for sub_area in v:
                poly = Polygon(sub_area)
                if report_point.within(poly):
                    with open('tc_consituency_mapping.json') as fmap:
                        tc_mapping = json.load(fmap)
                        print(tc_mapping[k])
                        return tc_mapping[k]


def assigned_to_constituency(latitude, longitude):
    '''
    Takes in the latitude and longitude of the reported location
    Returns the name of the constituency assigned to that location
    '''
    report_point = Point(longitude, latitude)

    with open('electoral_boundaries.json') as f:
        data = json.load(f)
        for k, v in data.items():
            for sub_area in v:
                poly = Polygon(sub_area)
                if report_point.within(poly):
                    print(k)
                    return k