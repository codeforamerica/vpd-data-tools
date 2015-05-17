import csv
import sys
from datetime import datetime, timedelta, time

from pytz import timezone
from django.contrib.gis.geos import Point

from rms.models import Incident, Incunit, GPSLog, CaseAudit, Terminal

TZ = timezone('US/Pacific')


def parse_timestring(timestring):
    if timestring:
        hours_str, minutes_str, seconds_str = timestring.split(':')        
        return time(int(hours_str), int(minutes_str), int(seconds_str))

def combine_date_time_strings(datestring, timestring, localize=True):
    if datestring and timestring:
        date_ts = datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S.%f')
        time_ts = parse_timestring(timestring)
        timestamp = datetime.combine(date_ts, time_ts)
        if localize:
            return TZ.localize(timestamp)
        return timestamp


def load_incidents(working_dir, fpath='incident.csv'):
    with open(working_dir + fpath) as f:

        for i in xrange(0, 4):
            next(f)

        for line in f:
            if line[:12].isdigit():

                try:
                    incnum, type, location, num, street, status, cname, cadrs, capt, cphone, datex, \
                    time, pu, beat, casen, rcvtime, disptime, enrttime, ostime, cleartime, cmt1 = line.strip().split('|')
                except ValueError:
                    # TODO: rarely, one of the fields contains the delimiter
                    print line
                    continue

                timestamp = combine_date_time_strings(datex, time)

                rcvtime = parse_timestring(rcvtime)
                disptime = parse_timestring(disptime)
                enrttime = parse_timestring(enrttime)
                ostime = parse_timestring(ostime)
                cleartime = parse_timestring(cleartime)

                Incident.objects.get_or_create(incnum=incnum, type=type, location=location, num=num, street=street, status=status, cname=cname, cadrs=cadrs,
                                               capt=capt, cphone=cphone, timestamp=timestamp, pu=pu, beat=beat, casen=casen, rcvtime=rcvtime, disptime=disptime,
                                               enrttime=enrttime, ostime=ostime, cleartime=cleartime, cmt1=cmt1)


            elif not line:
                break

            else:
                pass
                # TODO: append this to the previous row's comment field

def load_incunits(working_dir, fpath='incunits.csv'):
    with open(working_dir + fpath) as f:

        for i in xrange(0, 4):
            next(f)

        for line in f:
            if line[:12].isdigit():

                try:
                    incnum, unitid, ofcrnum, dispdate, disptime, enrtdate, enrttime, osdate, ostime, \
                    cleardate, cleartime, primaryunit = line.strip().split('|')
                except ValueError:
                    raise

                primaryunit = {'T': True, 'F': False}.get(primaryunit)

                dispdatetime = combine_date_time_strings(dispdate, disptime)
                enrtdatetime = combine_date_time_strings(enrtdate, enrttime)
                osdatetime = combine_date_time_strings(osdate, ostime)
                cleardatetime = combine_date_time_strings(cleardate, cleartime)

                incidents = Incident.objects.filter(incnum=int(incnum))
                if incidents:
                    incident = Incident.objects.get(incnum=int(incnum))

                    Incunit.objects.get_or_create(incident=incident, unitid=unitid, ofcrnum=ofcrnum, dispdatetime=dispdatetime, enrtdatetime=enrtdatetime,
                                                  osdatetime=osdatetime, cleardatetime=cleardatetime, primaryunit=primaryunit)


def load_incpers(working_dir, fpath='incpers.csv'):
    with open(working_dir + fpath) as f:

        for i in xrange(0, 4):
            next(f)

        for line in f:
            if line[:12].isdigit():

                try:
                    incnum, name, id, dob, address, city, st, zip, phone = line.strip().split('|')
                    # TODO: create objects

                except ValueError:
                    raise


def load_alpha(working_dir, fpath='alpha.csv'):
    with open(working_dir + fpath) as f:

        for i in xrange(0, 4):
            next(f)

        for line in f:
            if not line.strip():
                break
            try:
                last_name, first_name, id, address, apt, phone, sex, f, inches, dob, city, st, zip = line.strip().split('|')
                # TODO: create objects

            except ValueError:
                raise

def load_gpslog(working_dir, fpath='gpslog.csv'):
    with open(working_dir + fpath) as f:

        for i in xrange(0, 4):
            next(f)

        for line in f:
            if not line.strip():
                break
            try:
                unitid, xcoord, ycoord, datetimex, heading, mph, status = line.strip().split('|')
                # TODO: create objects
                location = Point(float(xcoord), float(ycoord))
                timestamp = TZ.localize(datetime.strptime(datetimex, '%Y-%m-%d %H:%M:%S.%f'))

                GPSLog.objects.get_or_create(unitid=unitid, location=location, timestamp=timestamp, heading=heading, speed=mph, status=status)

            except ValueError:
                raise

def load_caseaudit(working_dir, fpath='caseaudit.csv'):

    with open(working_dir + fpath, 'rb') as f:
        dialect = csv.Sniffer().sniff(f.read(1048576), delimiters="|")
        f.seek(0)
        reader = csv.reader(f, dialect)

        for i in xrange(4):
            next(reader)

        for row in reader:
            if len(row) == 7:
                casen, datex, timex, descx, userid, logcode, crtnum = row
            else:
                print 'Invalid line: %s' % row

            try:
                timestamp = combine_date_time_strings(datex, timex, localize=True)
                CaseAudit.objects.get_or_create(caseid=casen, timestamp=timestamp, description=descx, userid=userid, logcode=logcode, termid=crtnum)
            except:
                print row
                raise

def load_terminals(working_dir, fpath='terminal.csv'):

    with open(working_dir + fpath, 'rb') as f:
        dialect = csv.Sniffer().sniff(f.read(1048576), delimiters="|")
        f.seek(0)
        reader = csv.reader(f, dialect)

        for i in xrange(4):
            next(reader)

        for row in reader:
            if len(row) == 3:
                crtnum, descx, userid = row
            else:
                print 'Invalid line: %s' % row

            try:
                Terminal.objects.get_or_create(termid=crtnum, description=descx, userid=userid)
            except:
                print row
                raise

if __name__ == "__main__":
    import django
    django.setup()

    working_dir = sys.argv[1]

    load_incidents(working_dir)
    load_incunits(working_dir)
    load_incpers(working_dir)
    load_alpha(working_dir)
    load_gpslog(working_dir)
    load_caseaudit(working_dir)
    load_terminals(working_dir)
