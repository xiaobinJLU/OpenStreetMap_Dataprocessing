import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "quanzhou.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
maohao =  re.compile(r'^(.*?):(.*?)$')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


#我写的从这开始

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    # YOUR CODE HERE
    if element.tag == 'node':
        #node_attribs
        for i in NODE_FIELDS:
            s = element.attrib[i]
            if i == 'version':
                node_attribs['version'] = element.attrib[i]
            elif is_int(s):
                node_attribs[i] = int(s)
            elif is_float(s):
                node_attribs[i] = float(s)
            else:
                node_attribs[i] = s
           
        #node_tags
        for child in element:
            a = {} 
            a["id"] = node_attribs['id']
            if not PROBLEMCHARS.search(child.attrib['k']):
                if child.attrib['k'].find(':') == -1:
                    a['key'] = child.attrib['k']
                    a['type'] = 'regular'
                else:
                    k = maohao.search(child.attrib['k'])
                    a['key']=k.group(2)
                    a['type'] = k.group(1)
                if child.attrib['v']:
                    a['value']=child.attrib['v']
            
                tags.append(a)    
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        #way_attribs
        for way in WAY_FIELDS:
            s = element.attrib[way]
            if way == 'version':
                way_attribs['version'] = element.attrib[way]
            elif is_int(s):
                way_attribs[way] = int(s)
            else:
                way_attribs[way] = s
        
        position=0
        # way_nodes and way_tags
        for j in element:
            try:
                w_nod={}
                w_nod['id'] = way_attribs['id']
                w_nod['node_id'] = j.attrib['ref']
                w_nod['position'] = position
                position += 1
                way_nodes.append(w_nod)
            except KeyError:
                b = {}
                if not PROBLEMCHARS.search(j.attrib['k']):
                    if j.attrib['k'].find(':') == -1:
                        b['key'] = j.attrib['k']
                        b['type'] = 'regular'
                    else:
                        k1 = maohao.search(j.attrib['k'])
                        b['key']=k1.group(2)
                        b['type'] = k1.group(1)
                    if j.attrib['v']:
                        b['value']=j.attrib['v']
                    b['id'] = way_attribs['id']
                    tags.append(b)
    
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
#从这结束

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
#         raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
        codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
