import sys
import argparse
from craigslist import CraigslistHousing, CraigslistJobs, CraigslistForSale
import MySQLdb


from py_db import db

db = db('craigslist')

def scrape_cl(site, site_abbs, search_type):
    
    for site_abb in site_abbs:
        for search in search_type:
            for category, filt in search.items():
                # print category, filt
                if category == 'apa':
                    scrape_apartments(site, category, site_abb, filt)
                elif category == 'roo':
                    scrape_apartments(site, category, site_abb, filt)

                elif category == 'cta':
                    scrape_vehicles(site, category, site_abb, filt)

                elif category == 'jjj':
                    scrape_jobs(site, category, site_abb, filt)

def scrape_jobs(site, category, site_abb, filt):
    pass

def scrape_vehicles(site, category, site_abb, filt):
    def check_car_dupes(result, current):
        _id = result['cl_id']
        _name = result['title']
        _price = result['list_price']
        check_ID = db.query("SELECT cl_id FROM cars_%s WHERE cl_id = %s" % (current,_id))
        if check_ID != ():
            return True
        check_namePrice = db.query("SELECT cl_id FROM cars_%s WHERE title = '%s' AND list_price = %s" % (current, _name, _price))
        if check_namePrice != ():
            return True
        return False

    try:
        mac_search = filt.pop('mackenzie_search')
    except KeyError:
        mac_search = None

    cl = CraigslistForSale(site=site, area=site_abb, category=category, filters=filt)

    results = cl.get_results(sort_by='newest', geotagged=True)

    # print len(results)

    for result in results:
        result['mackenzie_search'] = mac_search
        result['site_abb'] = site_abb
        result['cl_id'] = result.pop('id')
        result['list_price'] = int(result.pop('price').replace('$',''))
        result['title'] = result.pop('name').replace("'","")
        result['sub_site'] = result.pop('where')


        if result['geotag'] is not None:
            result['geotag_lat'] = result['geotag'][0]
            result['geotag_lon'] = result['geotag'][1]
        else:
            result['geotag_lat'] = None
            result['geotag_lon'] = None

        for k,v in result.items():
            if is_ascii(v) is False:
                result[k] = result['cl_id']

        del result['geotag']

        # print result['cl_id'], result['title']
        curr_dupe = check_car_dupes(result, 'current')
        if curr_dupe is False:
            db.insertRowDict(result, 'cars_current', replace=True, insertMany=False)
            db.conn.commit()

            prev_dupe = check_car_dupes(result, 'all')
            if prev_dupe is False:
                db.insertRowDict(result, 'cars_all', replace=True, insertMany=False)
                db.conn.commit()

def scrape_apartments(site, category, site_abb, filt):
    def check_apt_dupes(result, current):
        _id = result['cl_id']
        _name = result['title']
        _price = result['list_price']
        check_ID = db.query("SELECT cl_id FROM apartments_%s WHERE cl_id = %s" % (current,_id))
        if check_ID != ():
            return True
        check_namePrice = db.query("SELECT cl_id FROM apartments_%s WHERE title = '%s' AND list_price = %s" % (current, _name, _price))
        if check_namePrice != ():
            return True
        return False

    cl = CraigslistHousing(site=site, area=site_abb, category=category, filters=filt)

    results = cl.get_results(sort_by='newest', geotagged=True, limit=25)

    cats_ok = filt.get('cats_ok')

    if category == 'roo':
        room_type = 'room'
    elif category == 'apa':
        room_type = 'apartment'

    for result in results:
        result['site_abb'] = site_abb
        result['cats_ok'] = cats_ok
        result['room_type'] = room_type
        result['cl_id'] = result.pop('id')
        result['list_price'] = int(result.pop('price').replace('$',''))
        result['title'] = result.pop('name').replace("'","")
        result['sub_site'] = result.pop('where')
        try:
            result['area_SqFt'] = int(result.pop('area').replace('ft2',''))
        except AttributeError:
            result['area_SqFt'] = None

        if result['geotag'] is not None:
            result['geotag_lat'] = result['geotag'][0]
            result['geotag_lon'] = result['geotag'][1]
        else:
            result['geotag_lat'] = None
            result['geotag_lon'] = None

        del result['geotag']

        for k,v in result.items():
            if is_ascii(v) is False:
                result[k] = 'Unicode Error - Visit URL'

        area_zone = result['url'].split('craigslist.org/')[1].split('/')[0]
        if area_zone == site_abb:
            curr_dupe = check_apt_dupes(result, 'current')
            if curr_dupe is False:
                db.insertRowDict(result, 'apartments_current', replace=True, insertMany=False)
                db.conn.commit()

                prev_dupe = check_apt_dupes(result, 'all')
                if prev_dupe is False:
                    db.insertRowDict(result, 'apartments_all', replace=True, insertMany=False)
                    db.conn.commit()


# https://stackoverflow.com/questions/196345/how-to-check-if-a-string-in-python-is-in-ascii
def is_ascii(s):
    if (s is None or type(s) not in (unicode, str)):
        return True
    else:
        return all(ord(c) < 128 for c in s)


if __name__ == "__main__":  

    db.query('TRUNCATE TABLE apartments_current')
    db.query('TRUNCATE TABLE cars_current')

    parser = argparse.ArgumentParser()
    parser.add_argument('--site',       default='sfbay')
    parser.add_argument('--site_abbs',  default=['scz',])
    parser.add_argument('--search_type',    default=[
        {'roo':{'max_price':1300, 'min_price':500, 'max_bedrooms':1, 'private_room':True, 'cats_ok':True}},
        {'roo':{'max_price':1300, 'min_price':500, 'max_bedrooms':1, 'private_room':True, 'cats_ok':False}},
        {'apa':{'max_price':1300, 'min_price':500, 'max_bedrooms':1, 'private_room':True, 'cats_ok':True}},
        {'apa':{'max_price':1300, 'min_price':500, 'max_bedrooms':1, 'private_room':True, 'cats_ok':False}},
        {'apa':{'max_price':2400, 'min_price':500, 'max_bedrooms':2, 'private_room':True, 'min_bedrooms':2, 'cats_ok':True}},
        {'apa':{'max_price':2400, 'min_price':500, 'max_bedrooms':2, 'private_room':True, 'min_bedrooms':2, 'cats_ok':False}},
        # {'cta':{'max_price':15000, 'min_price':1000, 'max_miles':150000, 'model':['Toyota Tacoma'], 'auto_cylinders':'6 cylinders', 'auto_title_status':'clean', 'search_distance':200, 'zip_code':95060, 'mackenzie_search':'m1'}},
        # {'cta':{'has_image':True, 'max_price':15000, 'min_price':1000, 'max_miles':150000, 'auto_title_status':'clean', 'auto_bodytype':['pickup', 'truck'], 'model':['nissan', 'toyota', 'honda'], 'search_distance':200, 'zip_code':95060}},
        ])

    args = parser.parse_args()
    
    scrape_cl(args.site, args.site_abbs, args.search_type)

