# TCX Creator
This project is intend to enbale getting the most out of your [Polar RCX 5](http://www.polar.fi/en/products/maximize_performance/running_multisport/RCX5) when using [Strava](http://strava.com).
The Polar RCX 5 export creates a GPX and an [HRM](http://www.polar.fi/files/Polar_HRM_file%20format.pdf) file. The GPX file contains the location data while the HRM file contains HR, speed cadence etc...

This python script searches for all gpx files in the folder that do not have a likely named tcx file. All the files found will be converted to tcx if an hrm file is found.
The assumption is that for file 123.gpx there is an 123.hrm file (That is how polar exports it) and it will create an 123.tcx file