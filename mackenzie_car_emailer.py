import sys
import os
import csv
import argparse
from datetime import timedelta,date,datetime
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


from py_db import db

db = db('craigslist')


key_file = os.getcwd()+"/un_pw.csv"
key_list = {}
with open(key_file, 'rU') as f:
    mycsv = csv.reader(f)
    for row in mycsv:
        un, pw = row
        key_list[un]=pw


def generate_body(type):
    mesg = ''
    sub = "New Listings (Matt's Truck Preferences) [%s]" % (str(date.today()))

    i = 1
    ids = []
    for search_type in ('mhop',):
        if search_type == 'mhop':
            search_title = '4WD - <30000 miles - <$30k'
            mesg += '\n\n-------------------------------------------\n'
            mesg += 'Category #' + str(i) + ' %s\n\n' % (search_title)

            i += 1
            mesg = query_listings(search_type, mesg, ids)

    # raw_input(sub)
    if ids != []:
        email(sub, mesg)
        log_ids(ids)
    else:
        print "no new mackenzie car posts"

def query_listings(search_type, mesg, ids):


    qry = """SELECT cl_id, title, url, sub_site, has_image, has_map, list_price FROM cars_current 
WHERE 1
AND cl_id NOT IN (SELECT cl_id FROM _email_ids)
AND mackenzie_search = '%s'
ORDER BY has_image+has_map DESC, list_price ASC"""

    query = qry % (search_type)

    # raw_input(query)

    res = db.query(query)

    j = 0

    for row in res:
        cl_id, title, url, sub_site, has_image, has_map, list_price = row

        ids.append(cl_id)

        mesg += str(j+1) + '. ' + title 
        # mesg += '\n' + str(cl_id) + ' : ' + str(bool(has_image)) + ' image : ' + str(bool(has_map)) + ' map'
        mesg += '\n$' + str(list_price) + ' : ' + str(sub_site) + '\n'
        mesg += '\t' + url + '\n\n'
        j += 1

    return mesg


def log_ids(ids):
    cur_time = datetime.now()

    entries = []
    for _id in ids:
        id_entry = {'cl_id':_id, 'email_time':cur_time}
        entries.append(id_entry)

    if entries not in ([], None): 
        db.insertRowDict(entries, '_email_ids', replace=True, insertMany=True, rid=0)
    db.conn.commit()

    return None

def email(sub, mesg):
    email_address = "connor.reed.92@gmail.com"
    fromaddr = email_address
    toaddr = "Matthoppy92@gmail.com"
    bcc_addr = email_address
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['BCC'] = bcc_addr
    msg['Subject'] = sub
    body = mesg
    msg.attach(MIMEText(mesg,'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, key_list.get(email_address))
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', default='cars')
    args = parser.parse_args()

    generate_body(args.type)
