import json
import pprint
import cPickle
import sys

level_file = ""
if len(sys.argv) >= 2:
    level_file = sys.argv[1]
else:
    print("Uporaba: python convert2JSON.py boxes.level")
    exit()

boxes = cPickle.load(file(level_file, 'rb'))
json_string = "level = " + json.dumps(boxes) + ";"

print json_string

#for box in boxes:
#        pprint.pprint(box)