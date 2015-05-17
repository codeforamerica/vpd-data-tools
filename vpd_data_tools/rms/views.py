import json
import operator
from datetime import datetime, timedelta

from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection

from rms.models import Incident, Incunit

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description

    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def routes(request):

    month = request.GET.get('month')
    day = request.GET.get('day')
    year = request.GET.get('year')
    unitid = request.GET.get('unitid')

    cursor = connection.cursor()
    cursor.execute(
    """
    set time zone 'America/Los_Angeles';
    DROP TABLE IF EXISTS hex_grid;
    CREATE TABLE IF NOT EXISTS hex_grid (gid serial not null primary key);
    SELECT addgeometrycolumn('hex_grid','the_geom', 0, 'POLYGON', 2);

    CREATE OR REPLACE FUNCTION genhexagons(width float, xmin float,ymin  float,xmax float,ymax float  )
    RETURNS float AS $total$
    declare
        b float :=width/2;
        a float :=b/2; --sin(30)=.5
        c float :=2*a;
        height float := 2*a+c;  --1.1547*width;
        ncol float :=ceil(abs(xmax-xmin)/width);
        nrow float :=ceil(abs(ymax-ymin)/height);

        polygon_string varchar := 'POLYGON((' ||
                                            0 || ' ' || 0     || ' , ' ||
                                            b || ' ' || a     || ' , ' ||
                                            b || ' ' || a+c   || ' , ' ||
                                            0 || ' ' || a+c+a || ' , ' ||
                                         -1*b || ' ' || a+c   || ' , ' ||
                                         -1*b || ' ' || a     || ' , ' ||
                                            0 || ' ' || 0     ||
                                    '))';
    BEGIN
        INSERT INTO hex_grid (the_geom) SELECT st_translate(the_geom, x_series*(2*a+c)+xmin, y_series*(2*(c+a))+ymin)
        from generate_series(0, ncol::int , 1) as x_series,
        generate_series(0, nrow::int,1 ) as y_series,
        (
           SELECT polygon_string::geometry as the_geom
           UNION
           SELECT ST_Translate(polygon_string::geometry, b , a+c)  as the_geom
        ) as two_hex;
        ALTER TABLE hex_grid
        ALTER COLUMN the_geom TYPE geometry(Polygon, 4326)
        USING ST_SetSRID(the_geom,4326);
        RETURN NULL;
    END;
    $total$ LANGUAGE plpgsql;

    SELECT genhexagons(0.003, 
                       (select min(st_x(location)) from rms_gpslog),
                       (select min(st_y(location)) from rms_gpslog where st_y(location) > 1),
                       (select max(st_x(location)) from rms_gpslog where st_x(location) < -1),
                       (select max(st_y(location)) from rms_gpslog)
                       );

    -- select h.gid, count(*), st_asgeojson(h.the_geom)::json
    select h.gid, st_asgeojson(h.the_geom), count(*)
    from hex_grid h, rms_gpslog g
    where st_contains(h.the_geom, g.location) = true
    and g.unitid = %s
    and date_part('month', g.timestamp) = %s
    and date_part('day', g.timestamp) = %s
    and date_part('year', g.timestamp) = %s
    group by h.gid
    order by count(*) desc;
    """,
    [unitid, month, day, year]
    )

    unitid = request.GET.get('unitid')
    month = request.GET.get('month')
    day = request.GET.get('day')
    year = request.GET.get('year')

    results = dictfetchall(cursor)

    max_count = None

    geojson = {'type': 'FeatureCollection', 'features': []}

    for x in results[1:]:

        if not max_count:
            max_count = float(x['count'])

        geojson['features'].append({
            "type": "Feature",
            "properties": {
                "opacity": x['count'] / max_count,
                "color": "blue"
            },
            "geometry": json.loads(x['st_asgeojson'])
        })

    results_json = json.dumps(geojson)

    return render(request, 'routes.html', {'results_json': results_json})


def timing(request):

    unitid = request.GET.get('unitid')
    month = request.GET.get('month')
    day = request.GET.get('day')
    year = request.GET.get('year')

    cursor = connection.cursor()
    cursor.execute(
        """
        -- set time zone 'America/Los_Angeles';
        select array_agg(date_part('epoch', i.timestamp)) as rcv_timestamps,
        array_agg(date_part('epoch', iu.osdatetime)) as ostimestamps,
        array_agg(date_part('epoch', iu.cleardatetime)) as cleartimestamps,
        array_agg(i.type) as call_types,
        (select date_part('epoch', timestamp) as x
            from rms_incident i
            left join rms_incunit iu
                on i.incnum = iu.incident_id
            where date_part('month', i.timestamp) = %s
            and date_part('day', i.timestamp) = %s
            and date_part('year', i.timestamp) = %s
            and unitid = %s
            order by x limit 1) as min_rcvtimestamp,
        (select date_part('epoch', cleardatetime) as x
            from rms_incunit
            where date_part('month', cleardatetime) = %s
            and date_part('day', cleardatetime) = %s
            and date_part('year', cleardatetime) = %s
            and unitid = %s
            order by x desc limit 1) as max_cleartimestamp
        from rms_incunit iu
        left join rms_incident i
            on i.incnum = iu.incident_id
        where date_part('month', iu.osdatetime) = %s
        and date_part('day', iu.osdatetime) = %s
        and date_part('year', iu.osdatetime) = %s
        and iu.unitid = %s
        ;
        """,
        [month, day, year, unitid, month, day, year, unitid, month, day, year, unitid]
    )

    results = dictfetchall(cursor)

    results_converted = []
    y = zip(results[0]['rcv_timestamps'], results[0]['ostimestamps'], results[0]['cleartimestamps'], results[0]['call_types'])
    for x in sorted(y, key=operator.itemgetter(1)):
        results_converted.append({'x0': (x[0] - results[0]['min_rcvtimestamp']) / (results[0]['max_cleartimestamp'] - results[0]['min_rcvtimestamp']),
                                  'x1': (x[1] - results[0]['min_rcvtimestamp']) / (results[0]['max_cleartimestamp'] - results[0]['min_rcvtimestamp']),
                                  'x2': (x[2] - results[0]['min_rcvtimestamp']) / (results[0]['max_cleartimestamp'] - results[0]['min_rcvtimestamp']),
                                  'label': x[3]
                                 })

    return render(request, 'timing.html', {'results': json.dumps(results_converted),
                                           'min_ts': results[0]['min_rcvtimestamp'],
                                           'max_ts': results[0]['max_cleartimestamp'],
                                           'unitid': unitid,
                                           'month': month,
                                           'day': day,
                                           'year': year
                                          })


def arrival_time(request):

    day_of_week = {
        'sun': '{0}',
        'mon': '{1}',
        'tues': '{2}',
        'wed': '{3}',
        'thu': '{4}',
        'fri': '{5}',
        'sat': '{6}'
    }.get(request.GET.get('dow'), '{0, 1, 2, 3, 4, 5, 6}')

    cursor = connection.cursor()
    cursor.execute(
        """
        set time zone 'America/Los_Angeles';
        select
            round(
                (
                    date_part(
                        'hour', osdatetime
                    ) * 3600.0 +
                    date_part(
                        'minute', osdatetime
                    ) * 60.0
                ) / 300.0
            )::integer * 300 as a_sod,
            count(*)::integer as a_count
        from rms_incunit
        where osdatetime is not null
        and extract(dow from osdatetime)::integer = ANY(%s)
        and unitid ~ '\\d(D|P|A)\\d'
        group by a_sod;
        """,
        [day_of_week]
    )

    results = dictfetchall(cursor)

    cursor = connection.cursor()
    cursor.execute(
        """
        set time zone 'America/Los_Angeles';
        select
            round(
                (
                    date_part(
                        'hour',
                        rcvtime
                    ) * 3600.0 +
                    date_part(
                        'minute',
                        rcvtime
                    ) * 60.0
                ) / 300.0
            )::integer * 300 as b_sod,
            count(*)::integer as b_count
        from rms_incident
        where timestamp is not null
        and extract(dow from timestamp)::integer = ANY(%s)
        and pu ~ '\\d(D|P|A)\\d'
        group by b_sod;
        """,
        [day_of_week]
    )

    results += dictfetchall(cursor)

    results_json = json.dumps(results)

    return render(request, 'arrival_time.html', {'results': results, 'results_json': results_json, 'dow': request.GET.get('dow', 'all')})


def dashboard(request):

    month = request.GET.get('month')
    day = request.GET.get('day')
    year = request.GET.get('year')

    cursor = connection.cursor()
    cursor.execute(
        """
        set time zone 'America/Los_Angeles';
        SELECT
            n.date,
            n.unitid,
            n.count,
            n.avg,
            n.max,
            n.min,
            n2.count as fi,
            n.pct_onscene,
            n.call_types,
            n.call_times,
            n.call_locations,
            n.resp_times
        FROM (
            SELECT
                iu.cleardatetime::date as date,
                iu.unitid,
                COUNT(*) as count,
                AVG(iu.osdatetime-i.timestamp) as avg,
                MAX(iu.osdatetime-i.timestamp) as max,
                MIN(iu.osdatetime-i.timestamp) as min,
                sum(iu.cleardatetime-i.timestamp) as pct_onscene,
                ARRAY_AGG(i.type) as call_types,
                array_agg(i.location) as call_locations,
                array_agg(i.rcvtime) as call_times,
                array_agg(iu.osdatetime-i.timestamp) as resp_times
            FROM rms_incunit iu
            JOIN rms_incident i
                ON iu.incident_id = i.incnum
            WHERE iu.unitid ~ '\\d(D|P|A)\\d'
            AND date_part('month', iu.cleardatetime) = %s
            AND date_part('day', iu.cleardatetime) = %s
            AND date_part('year', iu.cleardatetime) = %s
            AND iu.cleardatetime < '2015-03-17'
            GROUP BY date, iu.unitid
        ) n
        LEFT JOIN (
            select
                iu.cleardatetime::date as date,
                iu.unitid,
                COUNT(*) as count
            from rms_incunit iu
            join rms_incident i
                on iu.incident_id = i.incnum
            where i.type = 'FI' or i.type = 'TSTOP' or i.type = 'TS'
            group by date, iu.unitid
        ) n2
        ON (n.unitid = n2.unitid and n.date = n2.date)
        ORDER BY n.date, n.unitid;
    """,
    [month, day, year]
    )

    results = dictfetchall(cursor)

    results_converted = []
    for result in results:
        call_details_converted = []
        call_details = zip(result['call_types'], [x.strftime('%H:%M:%S') for x in result['call_times']], result['call_locations'], result['resp_times'])
        for i in sorted(call_details, key=operator.itemgetter(1)):
            call_details_converted.append({'call_type': i[0], 'call_time': i[1], 'call_location': i[2], 'resp_time': i[3] and str(i[3]) or ''})

        results_converted.append({
            'avg': result['avg'] and str(timedelta(days=result['avg'].days, seconds=result['avg'].seconds)) or '',
            'min': result['min'] and str(result['min']) or '',
            'max': result['max'] and str(result['max']) or '',
            'date': result['date'].strftime('%Y-%m-%d'),
            'count': str(result['count']),
            'fi': result['fi'] and str(result['fi']) or '',
            'unitid': str(result['unitid']),
            'pct_onscene': result['pct_onscene'] and str(result['pct_onscene']) or '',
            'call_details': call_details_converted
    })

    results_json = json.dumps(results_converted, cls=DjangoJSONEncoder)

    return render(request, 'index.html', {'results': results_converted, 'results_json': results_json, 'month': month, 'day': day, 'year': year})


def lobby_creates(request):

    cursor = connection.cursor()
    cursor.execute(
        """
        set time zone 'America/Los_Angeles';
        select extract(dow from timestamp::DATE) as dow, date_part('hour', timestamp) as hour, count(*)
        from (select * from rms_caseaudit ca join rms_terminal t on t.termid = ca.termid
        where (t.description ilike '%records%' and t.description not ilike '%supervisor%')
        and logcode = 'Created') x group by 1, 2 order by 1, 2;
        """
    )
    
    results = dictfetchall(cursor)

    return render(request, 'lobby_creates.html', {'results': json.dumps(results)})
