import time
import pprint

def log(who, s):
    pp = pprint.PrettyPrinter(indent=4)
    
    if type(s).__name__ != 'str' and type(s).__name__ != 'unicode':
        print time.ctime() + ' [' + who + ']: '
        pp.pprint(s)
    else:
        print time.ctime() + ' [' + who + ']: ' + s
    
