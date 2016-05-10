from django.contrib.gis.geos import Point

class Exporter:
    """
    An exporter for the OpenAir airspace
    """
    
    def convert(self,record):
        points = []
        for elt in record['elements']:
            if elt['type'] == 'point':
                points.append(Point(elt['location'][0], elt['location'][1]))
            elif elt['type'] == 'circle':
                pass
            elif elt['type'] == 'arc':
                pass
            elif elt['type'] == 'airway':
                pass
            
            print points


    def __init__(self, records):
        self.records = records

    def __iter__(self):
        return self.next()

    def next(self):
        for r in self.records:
            yield self.convert(r)
    
