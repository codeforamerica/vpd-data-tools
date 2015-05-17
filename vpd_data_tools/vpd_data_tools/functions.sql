CREATE OR REPLACE FUNCTION address_to_coords(IN address text, IN key text) RETURNS text ARRAY[2] AS
$$

import json
import urllib
import urllib2

lat, lon = None, None
data = {'address': address, 'key': key}
url = 'https://maps.googleapis.com/maps/api/geocode/json?%s' % urllib.urlencode(data)

response = json.loads(urllib2.urlopen(url).read())
status = response.get('status')
if status == 'OK':
    results = response.get('results')
    if results:
        point = results[0]['geometry']['location']
        lat = point['lat']
        lon = point['lng']


return lon, lat

$$
LANGUAGE 'plpythonu' VOLATILE;


CREATE OR REPLACE FUNCTION address_to_geom(IN address text, IN key text) RETURNS geometry AS
$$
SELECT
ST_SetSRID(ST_GeomFromText('POINT(' || r.ll[1] || ' ' || r.ll[2] || ')'), 4326)
FROM (
SELECT
address_to_coords($1, $2) AS ll ) r
$$
LANGUAGE sql VOLATILE;
