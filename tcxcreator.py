import sys
import os
import xml.etree.ElementTree as ElementTree
from datetime import datetime

# Global settings
SPORT = 'Biking'
TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
VERSION = 0.2


# Polar sets the time as of it was in GMT, but its not,
# use this to offset the time so that it is actually GMT
def getTimeOffset():
    u = datetime.utcnow()
    l = datetime.now()
    return l - u


# Converts time to seconds
def calcDuration(t):
    # Removing the new line
    t = t[:-1]
    l = t.split(':')
    return str(int(l[0]) * 3600 + int(l[1]) * 60 + int(round(float(l[2]))))


# Parent is the parent element
# Data is a dictionary with the key as the tag name and the value as the text in it
def createElementSeries(parent, data):
    for k, v in data.items():
        elem = ElementTree.SubElement(parent, k)
        elem.text = v


def createTcx(basename):
    distance = 0.0 # Distance counter
    # Creates a single tracking point
    def createTcxEntry(gpx, hrm_data, distance):
        data = list(gpx)
        # Creating a trackpoint
        tp = ElementTree.SubElement(track, 'Trackpoint')
        # Time
        e = ElementTree.SubElement(tp, 'Time')
        # Converting string to dattime object, changing to actual utc time
        # and converting back
        e.text = datetime.strftime(datetime.strptime(data[0].text, TIME_FORMAT) - time_offset, TIME_FORMAT)
        # Position
        e = ElementTree.SubElement(tp, 'Position')
        l = ElementTree.SubElement(e, 'LatitudeDegrees')
        l.text = str(gpx.items()[0][1])
        l = ElementTree.SubElement(e, 'LongitudeDegrees')
        l.text = str(gpx.items()[1][1])
        # Distance Meter
        # 1/10 km/h to m/s and then for the amount of sec de inteal is.
        distance += float(hrm_data[1]) * 100 / 60 / 60 * interval
        e = ElementTree.SubElement(tp, 'DistanceMeters')
        e.text = str(distance)
        # Heart Rate
        e = ElementTree.SubElement(tp, 'HeartRateBpm', {'xsi:type': 'HeartRateInBeatsPerMinute_t'})
        v = ElementTree.SubElement(e, 'Value')
        v.text = str(hrm_data[0])
        if CADENSE:
            e = ElementTree.SubElement(tp, 'Cadence')
            e.text = str(hrm_data[2])
        return distance

    # CreatTcx Function
    print "Creating TCX file for " + basename + ".gpx"
    # Opening the HRM file
    hrmfile = open(basename + '.hrm', 'r')

    # Creating elementTree for the gpx file
    try:
        root = ElementTree.parse(basename + '.gpx').getroot()
    except:
        print "Failed to parse gpx file"
        print sys.exc_info()[1]
        sys.exit()
    print 'Files loaded'
    # Creating an iterator to iterate over all the tracking point
    gpx_points = list(list(root)[1])[1].iter('{http://www.topografix.com/GPX/1/0}trkpt')
    # Getting the HR file to the right place
    hrmiter = iter(hrmfile)
    line = hrmiter.next()
    while line.find('[HRData]') == -1:
        line = line.strip()  # Remving new line
        if line.find('Date') > -1:
            line = line[5:]  # Removing the Date=
            adate = line[0:4] + '-' + line[4:6] + '-' + line[6:8]
        elif line.find('StartTime') > -1:
            astart_time = line[10:-2]  # Removing the .X part
        elif line.find('Length') > -1:
            duration = calcDuration(line[8:-1])
        elif line.find('SMode') > -1 :
            # This is the info over the different data in the hrm chain
            # For now working only with cadence
            if line[7:8] == '1':
                CADENSE = True
            else:
                CADENSE = False
        elif line.find('Interval') > -1:
            interval = int(line[9:])
        line = hrmiter.next()
    # Finding the time offset of the zone
    time_offset = getTimeOffset()
    # Start timestamp
    start_time = datetime.strftime(datetime.strptime(adate + 'T' + astart_time + 'Z', TIME_FORMAT) - time_offset, TIME_FORMAT)
    print 'Start time: ' + str(start_time)
    # Creating a tcx
    tcx = ElementTree.Element("TrainingCenterDatabase",
    {"xmlns": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xsi:schemaLocation": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"})
    activities = ElementTree.SubElement(tcx, "Activities")
    activity = ElementTree.SubElement(activities, "Activity", {'Sport': SPORT})
    d = ElementTree.SubElement(activity, 'Id')
    d.text = start_time
    lap = ElementTree.SubElement(activity, 'Lap', {'StartTime': start_time})

    # @TODO add total distance calculation
    lap_data = {'TotalTimeSeconds': duration, 'Calories': '0',
                 'Intensity': 'Active', 'TriggerMethod': 'Manual'}
    createElementSeries(lap, lap_data)
    total_distance = ElementTree.SubElement(lap, 'DistanceMeters')
    track = ElementTree.SubElement(lap, 'Track')
    # Ready to create the points
    line = True
    while line:
        try:
            line = hrmiter.next()
            gpx = gpx_points.next()
        except:
            print sys.exc_info()[1]
            print 'Iterator issue, data finished?'
            line = False
            continue
        line = line.strip()  # Removing white spaces
        hrm_data = line.split()  # HR Speed [Cadance]
        distance = createTcxEntry(gpx, hrm_data, distance)
    # Updating total distance
    total_distance.text = str(distance)
    # Finishing the tree
    author = ElementTree.SubElement(tcx, 'Author')
    author.set('xsi:type', "Application_t")
    elem = ElementTree.SubElement(author, 'Name')
    elem.text = 'HRM-GPX to TCX'
    build = ElementTree.SubElement(author, 'Build')
    version = ElementTree.SubElement(build, 'Version')
    version_data = {'VersionMajor': '0', 'VersionMinor': '1',
                    'BuildMajor': '0', 'BuildMinor': '1'}
    createElementSeries(version, version_data)
    # @TODO Build timestamp or something
    build_data = {'Type': 'Internal', 'Time': start_time,
                    'Builder': 'Kfir Breger'}
    createElementSeries(build, build_data)
    elem = ElementTree.SubElement(author, 'LangID')
    elem.text = 'EN'
    # @TODO check spec for what this is
    elem = ElementTree.SubElement(author, 'PartNumber')
    elem.text = '123'
    # Saving the xml
    try:
        tcx_root = ElementTree.ElementTree(tcx)
        tcx_root.write(basename + '.tcx', encoding='UTF-8',
                        xml_declaration=True)
    except:
        print 'Error writing to the tcx file'
        print sys.exc_info()[1]


def main(path):
    # Getting all files in the folder
    files = os.listdir(path)
    work_files = []
    exclude_files = []
    for filename in files:
        # Skipping directories and hidden files
        if os.path.isdir(filename) or filename[0] == '.':
            continue
        basename, extension = filename.split('.')
        # If extension is tcx, add to exclude
        # If it is gpx add it to work files
        if extension == 'tcx':
            exclude_files.append(basename)
        elif extension == 'gpx':
            work_files.append(basename)
        elif extension != 'hrm':  # Not a tcx, gpx or hrm
            print "Ignoring " + filename
    # Removing files that already have a tcx
    for basename in exclude_files:
        if basename in work_files:
            work_files.remove(basename)
    # Creating tcx for each of the gpx/hrm files
    for basename in work_files:
        createTcx(basename)

if __name__ == '__main__':
    path = './'  # Default path if no is given
    if len(sys.argv) == 2:
        path = sys.argv[1]
    main(path)
