import re
from . import ParserError

RE_WHITESPACE = re.compile(r'\s+')
RE_LATITUDE = re.compile(r'^([NS])([\d]{2})([\d]{2})([\d]{2})$')
RE_LONGITUDE = re.compile(r'^([EW])([\d]{3})([\d]{2})([\d]{2})$')
RE_ICAO = re.compile(r'^[\w\d]{4}$')
RE_FIELD_NUMBER = re.compile(r'^\*FL([\d]+)$')
RE_RUNWAY_LENGTH = re.compile(r'^\s*([\d]+)\s*$')
RE_RUNWAY_DIRECTION = re.compile(r'^\s*([\d]+)\s*$')
RE_FREQUENCY = re.compile(r'^(1[\d]{2})([\d]{2})$')
RE_ELEVATION = re.compile(r'^[\s]*(-?[\d]+)')

RE_CLASSIFIERS = [
    (re.compile(r'\bA[\d]+ B?AB[\d]*[abc]?\b'), ['highway-exit']),
    (re.compile(r'\bA[\d]+XA[\d]+\b'), ['highway-interchange']),
    (re.compile(r'\bA[\d]+YA[\d]+\b'),
        ['highway-interchange', 'y-interchange']),
    (re.compile(r'\bSTR\b'), ['road']),
    (re.compile(r'\bSX\b'), ['road-interchange']),
    (re.compile(r'\bSY\b'), ['road-interchange', 'y-interchange']),
    (re.compile(r'\bEX\b'), ['railway-interchange']),
    (re.compile(r'\bEY\b'), ['railway-interchange', 'y-interchange']),
    (re.compile(r'\bTR\b'), ['gas-station']),
    (re.compile(r'\b(BF|RS|RAIL(WAY)? STATION|GARE)\b'), ['railway-station']),
    (re.compile(r'\b(BR|BRIDGE|VIADUCT|PONT)\b'), ['bridge']),
    (re.compile(r'\b(TV|TURM|TWR|TOWER|SCHORNSTEIN)\b'), ['tower']),
    (re.compile(r'\b(CHURCH|KIRCHE|KERK|KIRKE|EGLISE|TEMPLE|TEMPLOM|DOM|'
                r'KLOSTER)\b'), ['church']),
    (re.compile(r'\b(HANGAR|HALLE)\b'), ['hangar']),
    (re.compile(r'\b(CASTLE|BURG|SCHLOSS|KOSTEL|KOSTOL|FESTUNG)\b'),
        ['castle']),
    (re.compile(r'\bVILLAGE\b'), ['village']),
    (re.compile(r'\b(TOP|PEAK|BERG|GIPFEL|MOUNTAIN|SPITZE|SUMMIT)\b'),
        ['mountain-top']),
    (re.compile(r'^(MT|MOUNT|MONT|MONTE)\b'), ['mountain']),
    (re.compile(r'\b(COL|PASS)\b'), ['mountain-pass']),
    (re.compile(r'\b(KW|KKW|POWER (PLANT|ST|STA|STN|STATION))\b'),
        ['power-plant']),
    (re.compile(r'\b(DAM|(STAU)?DAMM|STAUMAUER)\b'), ['dam']),
    (re.compile(r'\b(SILO)\b'), ['silo']),
    (re.compile(r'\b(VULCAN|VULKAN|VOLCANO)\b'), ['volcano']),
    (re.compile(r'\b(LAKE|LAC|(STAU)?SEE|TEICH)\b'), ['lake']),
    (re.compile(r'\b(SENDER)\b'), ['sender']),
    (re.compile(r'\b(VOR)\b'), ['vor']),
    (re.compile(r'\b(NDB)\b'), ['ndb']),
    (re.compile(r'\b(TUNNEL)\b'), ['tunnel']),
    (re.compile(r'\b(PFLICHTMELDEPUNKT)\b'), ['reporting-point']),
]

SURFACES = {
    'A': 'asphalt',
    'C': 'concrete',
    'L': 'loam',
    'S': 'sand',
    'Y': 'clay',
    'G': 'grass',
    'V': 'gravel',
    'D': 'dirt',
    'W': 'meadow',
}


class Reader:
    """
    A reader for the WELT2000 waypoint file format.

    see http://www.segelflug.de/vereine/welt2000/download/WELT2000-SPEC.TXT
    """

    def __init__(self, fp=None):
        self.fp = fp

    def __iter__(self):
        return self.next()

    def next(self):
        for line in self.fp:
            wp = self.decode_waypoint(line)
            if wp:
                yield wp

    def decode_waypoint(self, line):
        line = line.strip()

        if not line or line.startswith('$'):
            return

        # Check valid line length
        if len(line) != 64:
            raise ParserError('Line length does not match 64')

        return {
            'shortform': self.decode_shortform(line),
            'is_airfield': self.decode_is_airfield(line),
            'is_unclear': self.decode_is_unclear(line),
            'is_outlanding': self.decode_is_outlanding(line),
            'shortform_zander': self.decode_shortform_zander(line),
            'text': self.decode_text(line),
            'icao': self.decode_icao(line),
            'is_ulm': self.decode_is_ulm(line),
            'field_number': self.decode_field_number(line),
            'is_glidersite': self.decode_is_glidersite(line),
            'runway_surface': self.decode_runway_surface(line),
            'runway_length': self.decode_runway_length(line),
            'runway_directions': self.decode_runway_directions(line),
            'frequency': self.decode_frequency(line),
            'elevation': self.decode_elevation(line),
            'elevation_proved': self.decode_elevation_proved(line),
            'latitude': self.decode_latitude(line),
            'longitude': self.decode_longitude(line),
            'ground_check_necessary': self.decode_ground_check_necessary(line),
            'better_coordinates': self.decode_better_coordinates(line),
            'country': self.decode_country(line),
            'year_code': self.decode_year_code(line),
            'source_code': self.decode_source_code(line),
        }

    def has_metadata(self, line):
        return line[23] == '#' or line[23] == '*' or line[23] == '?'

    def decode_shortform(self, line):
        return line[0:6]

    def decode_is_airfield(self, line):
        return line[5] == '1'

    def decode_is_unclear(self, line):
        return line[4] == '2'

    def decode_is_outlanding(self, line):
        return line[5] == '2'

    def decode_shortform_zander(self, line):
        if line[6] == ' ' or line[6] == '-':
            return line[7:19].rstrip()
        else:
            return line[7:19] + line[6]

    def decode_text(self, line):
        if not self.has_metadata(line):
            return line[7:41].rstrip('?! ')
        elif line[20:23] == 'GLD':
            return line[7:20].rstrip('?! ')
        else:
            return line[7:23].rstrip('?! ')

    def decode_icao(self, line):
        if (line[23] == '#' and line[24] != ' ' and
                line[27] != '?' and line[27] != '!'):
            return line[24:28].rstrip()

    def decode_is_ulm(self, line):
        return (
            line[23:27] == '*ULM' or
            line[23:27] == '#ULM' or
            line[23:28] == '# ULM'
        )

    def decode_field_number(self, line):
        match = RE_FIELD_NUMBER.match(line[23:28])
        if match:
            return int(match.group(1))

    def decode_is_glidersite(self, line):
        return (
            line[23:28] == '# GLD' or
            line[23:27] == '#GLD' or
            line[23:27] == '*GLD' or
            line[19:24] == 'GLD #' or
            line[20:24] == 'GLD#' or
            line[20:24] == 'GLD*'
        )

    def decode_runway_surface(self, line):
        if self.has_metadata(line):
            return SURFACES.get(line[28], None)

    def decode_runway_length(self, line):
        if self.has_metadata(line):
            match = RE_RUNWAY_LENGTH.match(line[29:32])
            if match:
                return int(match.group(1)) * 10

    def decode_runway_directions(self, line):
        if self.has_metadata(line):
            directions = []

            match = RE_RUNWAY_DIRECTION.match(line[32:34])
            if match:
                direction = int(match.group(1)) * 10
                directions.append(direction)

            match = RE_RUNWAY_DIRECTION.match(line[34:36])
            if match:
                direction = int(match.group(1)) * 10
                if direction not in directions:
                    directions.append(direction)

            return directions or None

    def decode_frequency(self, line):
        if self.has_metadata(line):
            match = RE_FREQUENCY.match(line[36:41])
            if match:
                frq = match.group(1) + '.' + match.group(2)
                frq += '5' if frq.endswith('2') or frq.endswith('7') else '0'
                return frq

    def decode_elevation(self, line):
        match = RE_ELEVATION.match(line[41:45])
        if match:
            return int(match.group(1))

    def decode_elevation_proved(self, line):
        return line[41] == '0'

    def decode_latitude(self, line):
        match = RE_LATITUDE.match(line[45:52])
        if not match:
            raise ParserError('Reading latitude failed')

        lat = (
            int(match.group(2)) +
            int(match.group(3)) / 60. +
            int(match.group(4)) / 3600.
        )

        if not (0 <= lat <= 90):
            raise ParserError('Latitude out of bounds')

        if match.group(1) == 'S':
            lat = -lat

        return lat

    def decode_longitude(self, line):
        match = RE_LONGITUDE.match(line[52:60])
        if not match:
            raise ParserError('Reading longitude failed')

        lon = (
            int(match.group(2)) +
            int(match.group(3)) / 60. +
            int(match.group(4)) / 3600.
        )

        if not (0 <= lon <= 180):
            raise ParserError('Longitude out of bounds')

        if match.group(1) == 'W':
            lon = -lon

        return lon

    def decode_ground_check_necessary(self, line):
        return '?' in line

    def decode_better_coordinates(self, line):
        return line[6] == '-'

    def decode_country(self, line):
        return line[60:62].strip()

    def decode_year_code(self, line):
        return line[62].strip()

    def decode_source_code(self, line):
        return line[63].strip()


class Converter:
    """
    A reader for the WELT2000 waypoint file forrmat.

    see http://www.segelflug.de/vereine/welt2000/download/WELT2000-SPEC.TXT
    """

    def __init__(self, fp):
        self.fp = fp

    def __iter__(self):
        return self.next()

    def next(self):
        for old in Reader(self.fp):
            new = self.convert_waypoint(old)
            if new:
                yield new

    def convert_waypoint(self, old):
        waypoint = {}

        waypoint['name'] = old['text']
        waypoint['shortname'] = old['shortform']
        waypoint['country'] = old['country']
        waypoint['description'] = None

        waypoint['latitude'] = old['latitude']
        waypoint['longitude'] = old['longitude']

        waypoint['elevation'] = old['elevation']

        waypoint['classifiers'] = set()

        if old['is_glidersite']:
            waypoint['classifiers'].add('glidersite')

        if old['is_ulm']:
            waypoint['classifiers'].add('ulm')

        if old['is_airfield']:
            waypoint['classifiers'].add('landable')
            waypoint['classifiers'].add('airfield')

        if old['is_outlanding']:
            waypoint['classifiers'].add('landable')

        if 'landable' in waypoint['classifiers']:
            waypoint['icao'] = self.convert_icao(old['icao'])
            waypoint['runways'] = self.convert_runways(
                old['runway_surface'],
                old['runway_directions'],
                old['runway_length']
            )
            waypoint['frequencies'] = self.convert_frequencies(
                old['frequency']
            )

            if old['field_number'] is not None:
                waypoint['classifiers'].add('catalogued')
                waypoint['field_number'] = old['field_number']

        for regex, values in RE_CLASSIFIERS:
            if regex.search(old['text']):
                waypoint['classifiers'].update(values)

        return waypoint

    def convert_icao(self, icao):
        if icao and RE_ICAO.match(icao):
            return icao

    def convert_runways(self, surface, directions, length):
        runways = []
        if surface or length or directions:
            runway = {}
            if surface:
                runway['surface'] = surface
            if length:
                runway['length'] = length
            if directions:
                if len(directions) == 1:
                    runway['directions'] = [directions[0] % 360]
                else:
                    runway['directions'] = \
                        [directions[0] % 360, (directions[0] + 180) % 360]

            runways.append(runway)

        if (directions and len(directions) == 2 and
                (directions[0] + 180) % 360 != directions[1]):
            runways.append({
                'directions': [
                    directions[1] % 360,
                    (directions[1] + 180) % 360
                ],
            })

        return runways

    def convert_frequencies(self, frq):
        if not frq:
            return []

        return [{
            'frequency': frq,
        }]
