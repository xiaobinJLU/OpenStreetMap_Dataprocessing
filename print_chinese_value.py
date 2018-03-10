# -*- coding: utf-8 -*-  
"""
寻找中文的值
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "fujian.osm"
chinese_end = re.compile(u"[\u4e00-\u9fa5]$")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
#                 if tag.attrib['k'] == 'addr:postcode':
#                     print tag.attrib['v']
                if chinese_end.search(tag.attrib['v']) != None:
                    print tag.attrib['v']



def test():
    st_types = audit(OSMFILE)

if __name__ == '__main__':
    test()
