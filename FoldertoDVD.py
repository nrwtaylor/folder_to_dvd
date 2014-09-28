# Calculate best packing of multiple folders onto multiple DVDs
# and display a list of folders.  User can then manually move
# the folders into the suggested folders prior to burning onto DVD.
# Only parent folders in the root folder are calculated.  Child
# folders move in entirety with the parent folder.

# This facilites implementation of the backup system described in
# 'The DAM Book' where image files from a photoshoot are saved
# in sequential files in a dated shoot folder (ie 2012-10-25 Wedding photos)
# Those files are saved in sequential folders DRV001, DRV002 ... DRVnnn
# with a new DVD burnt as each folder reaches capacity.

import math
import sys
from time import time, clock
import ConfigParser
import os

config = ConfigParser.RawConfigParser()
config.read('foldertodvd.ini')

print "\n\n"
names = []
items = []


class Bin:
    """Bin for holding items"""
    def __init__(self, capacity, contents=[], names = []):
            self.capacity = capacity
            self.contents = contents
            self.names = names
            
            
    def add(self, item, name):
            # item
            self.contents.append(item)
            # name
            self.names.append(name)
            
    def __repr__(self):
            return "n:" + str(self.names) + " c:" +str(self.contents) + " %" + str(sum(self.contents)/self.capacity*100)

    def printf(self,indent):
            for name, item in zip(self.names,self.contents):
                    printl(name,item)
# see: http://goo.gl/kTQMs
SYMBOLS = {
    'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
}

def GetHumanReadable(n, format='%(value).2f %(symbol)s', symbols='customary'):
    """
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs

      >>> bytes2human(9856, symbols="customary")
      '9.6 K'
      >>> bytes2human(9856, symbols="customary_ext")
      '9.6 kilo'
      >>> bytes2human(9856, symbols="iec")
      '9.6 Ki'
      >>> bytes2human(9856, symbols="iec_ext")
      '9.6 kibi'

      >>> bytes2human(10000, "%(value).1f %(symbol)s/sec")
      '9.8 K/sec'

      >>> # precision can be adjusted by playing with %f operator
      >>> bytes2human(10000, format="%(value).5f %(symbol)s")
      '9.76562 K'
    """
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = SYMBOLS[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)

def getFolder(msg = 'Enter folder name:', default_folder='.', allow_new_folders = False):

    while True:
        try:
            path = raw_input(msg)

            
            if path == "":
                path = default_folder
            print "path",path
            path = path.strip()
            if allow_new_folders == True:
                if not os.path.exists(path):
                    os.makedirs(path)
            if not os.path.isdir(path): raise WindowsError("Folder not found")
            
            break

        except ValueError:
            print "You didn't enter input correctly!"
        except WindowsError:
            
            print "Invalid folder name!"
        except UserWarning:
            print "Folder has previous SplitFolder in it."


    path.strip('\\')
    path = path + "\\"
        
    return path

def getCap(msg,default_cap = '4700000000'):
    #http://www.osta.org/technology/dvdqa/dvdqa6.htm
    #DVD+R	1.2	        4,700,372,992
    #DVD+RW	1.2	        4.700.372.992
    #DVD-R	1	        3,950,000,000
    #DVD-R	Authoring 2.1	4,700,000,000
    #DVD-R	General 2.1	4,700,000,000
    #DVD-RW	1.1	        4,700,000,000
    #DVD-RAM	1	        2,496,430,080
    #DVD-RAM	2	        4,700,307,456

    while True:
        try:
            cap_input = (raw_input(msg).strip())
            
            if not cap_input:
                cap_input=default_cap
            cap = float(cap_input)
            break
        except ValueError:
            print "You didn't enter input correctly!"

        
    return int(cap)

def exit_routine():
    raw_input('Press enter to continue')
    
    

def printl(name,item):
    print "  ",
    print name.ljust(30),           
    print str(GetHumanReadable(item)).rjust(10)

def isskip(item,skip_folders):   
    for skip in skip_folders:    
        if skip in item:
            return True
    return False
            



from progressbar import *               # just a simple progress bar

# pbar http://stackoverflow.com/questions/3160699/python-progress-bar


def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size



run_type = config.get('defaults', 'run')

default_cap = config.get('defaults', 'capacity')
default_source_folder = config.get('defaults', 'source_folder')
skip_folders = config.get('defaults', 'skip').split(',')
for s in skip_folders:
    s.strip(' ')
if skip_folders == '*':skip_folders=None

    
if run_type == "interactive":

    cap = getCap("Default media size (default = " + default_cap + " bytes/" + GetHumanReadable(int(default_cap)) + "):", default_cap)
    folder = getFolder('Enter the folder to process (Enter to default to '+str(default_source_folder)+'): ',default_source_folder)

elif run_type == "auto":

    cap = float(default_cap)
    folder = default_source_folder

else:
    raise Exception("Invalid config file - run not valid")

print "Parameters:"
print "  Media size:",cap,type(cap)
print "  Source folder:", folder

root = folder
max_folders = float(len(os.listdir(root)))

pbar = ProgressBar(widgets=['Calculating folder sizes:',Percentage(), Bar()], maxval=max_folders)
pbar.start()

unprocessed_folders = []
skipped_folders = []
t1 = time.time()

for i,item in enumerate(os.listdir(root)):
    if os.path.isdir(os.path.join(root, item)):
        # Test with RAW folders allowed, this should identify when to put
        # folders into existing RAW folders
		
        size = get_size(os.path.join(root,item))
        if isskip(item,skip_folders):
            #Folder contains string to be skipped, do not process.
            skipped_folders.append((item,size))
            
        elif size > cap:
            #Folder is larger than DVD, so do not process.
            unprocessed_folders.append((item,size))
        else:
            #Create list of size and folder name for next step.
            items.append(size)
            names.append(item)


    pbar.update(i) #this adds a little symbol at each iteration

pbar.finish()
print

maxBins = len(items)
minBins = int(math.ceil(sum(items)/cap))
bins = []

bins.append(Bin(cap, [], [])) # we need at least one bin to begin

if maxBins == 0:
    #print "No folders in source folder.  Exiting."
    raise Exception("No folders in source folder")
    #exit_routine()

pbar = ProgressBar(widgets=['Computing folders for DVDs:',Percentage(), Bar()], maxval=len(items))
pbar.start()

for i, (name, item) in enumerate(zip(names, items)):

        #print name
        # Add the item to the first bin that can hold it
        # If no bin can hold it, make a new bin

        for xBin in bins:
                if xBin.capacity - sum(xBin.contents) >= item:
                        xBin.add(item,name)
                        break
                if bins.index(xBin) == len(bins) - 1:
                        bins.append(Bin(cap, [], []))
        pbar.update(i) #this adds a little symbol at each iteration

pbar.finish()
print

# Print results
for i, bin in enumerate(bins):
        print "DVD", i+1,
        print ': %s (%.1f%%)' % (GetHumanReadable(sum(bin.contents)), (round(float(sum(bin.contents))/bin.capacity*100,1)))
        bin.printf(2)
        
if len(unprocessed_folders) != 0:
    print "Unprocessed folders"
    for u in unprocessed_folders:
        printl(u[0],u[1])

if len(skipped_folders) != 0:
    print "Skipped folders"
    for u in skipped_folders:
        printl(u[0],u[1])

t2 = time.time()
print "Completed in %ss" % int(t2 - t1)


raw_input('Press enter to continue')
