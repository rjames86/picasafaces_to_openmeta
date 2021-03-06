# ! /bin/python
# Based on https://github.com/dasmaeh/pyFaceExtract

# System environment
import sys
import os
import ConfigParser
import fnmatch
import re
import time
import datetime
# from lib.openmeta import openmeta
from lib import tag

"""

   Function to read id tags and names stored in Picasa contacts.xml file.

"""

HOME = os.path.expanduser('~')
contactsfile = HOME +\
    "/Library/Application Support/Google/Picasa3/contacts/contacts.xml"


now = datetime.datetime.now().strftime('%Y_%m_%d %H.%M.%S')

def timer(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        log('%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res
    return wrapper


def log(msg):
    print msg
    with open('output_%s.txt' % now, 'a') as f:
        f.write(msg + '\n')


def createNameList(contactsfile):
    namelist = {}
    readfile = [line.strip()
                for line in open(contactsfile, 'r').readlines() if line]

    for line in readfile:
        name_search = re.search("name=\"([A-Za-z ]+)\"", line)
        contactid_search = re.search("contact id=\"([A-Za-z0-9]+)\"", line)
        if name_search and contactid_search:
            namelist[contactid_search.group(1)] = name_search.group(1)

    return namelist


def check_existing_tags(current_tags, new_tags):
    return all(tag in current_tags for tag in new_tags)


def writeNamesToFiles(imgs, path):
    directory = os.path.dirname(path)
    for filename, names in imgs.iteritems():
        filepath = os.path.join(directory, filename)
        tags = list(tag.get_tags(filepath))
        if 'photos' not in tags:
            names.append('photos')
        log("filepath %s" % filepath)
        if not check_existing_tags(tags, names):
            new_tags = list(set(tags + names))
            log("current tags: %s" % tags)
            log("new names: %s" % names)
            log("tags will be: %s" % new_tags)
            # if not testing:
            tag.add_tags(filepath, new_tags)
        else:
            log("tags match. skipping...")
        log("-" * 10)
    return


@timer
def main():
    matches = []
    for src in srcs:
        for root, dirnames, filenames in os.walk(src):
            for filename in fnmatch.filter(filenames, '.picasa.ini'):
                matches.append(os.path.join(root, filename))

    for path in matches:

        # maybe we should check if the last part of path is 'picasa.ini'...
        if os.path.isfile(path):
            contactmap = createNameList(contactsfile)
            config = ConfigParser.ConfigParser()
            config.read(path)
            # we will write all information in dictionary first:
            imgs = {}

            # loop over all images found in the .picasa.ini
            for item in config.sections():
                if item == 'Contacts2':
                    continue
                # create list entry for this image
                imgs[item] = []

                try:
                    # take all faces detected in this image
                    faces = config.get(item, 'faces').split(';')
                    for f in faces:
                        face = f.split(',')[1]
                        try:
                            # and look for a name:
                            name = contactmap[face]
                            if face != "ffffffffffffffff":
                                # we found a (proper) name, so add it to the dictionary
                                log("Adding name '"+name+"' to file '"+item+"'")
                                imgs[item].append(name)
                            else:
                                # No name attached to the face (aka unkown face in picasa)
                                "Face not identified"
                        except:
                            # no name found for the face (not saved in the contacts.xml)
                            log("No name found for this id")

                    # log(imgs  # lets see what we found)
                    # here we should write the names to the images
                except:
                    log("No faces saved in this file ('"+item+"')")
            try:
                writeNamesToFiles(imgs, path)
            except Exception as err:
                log("Error while saving! %s" % err)
        else:
            log("Please enter path to 'picasa.ini' as first argument")
            sys.exit(0)


if __name__ == '__main__':
    testing = True

    srcs = [
        HOME + "/Dropbox/Pictures/My Photos",
        HOME + "/Dropbox/Pictures/Scans of Negatives/Low Res JPGs",
    ]

    main()
