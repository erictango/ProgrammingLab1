############################################################################
## Tool Name:  Export Feature Class to GeoJSON
## Source Name: GeoJSONExporter.py
## Version: ArcGIS 9.2
## Author: Dejung Gewissler (NJOGIS) 4/11/08
##
## This script will iterate through all features in a feature layer and
## export them with attributes to a geojson file
############################################################################


def go_print(msg): # - printing message
    gp.addmessage(msg) ; print msg ; ## logfile.write(msg + "\n")

def go_warn(msg): # - printing message
    gp.addwarning(msg) ; print msg ; ## logfile.write(msg + "\n")

def go_error(msg): # - printing message
    gp.adderror(msg) ; print msg ; ## logfile.write(msg + "\n")


import sys, os
sys.path.append('C:\\DEV\\python\\GeoJSON')
import json, time, arcgisscripting

startTime = time.clock()
nodeCounter = 0

gp = arcgisscripting.create()
go_print (" ")
go_print ("started.")
#get input parameters
lyrName = sys.argv[1] #FC to be exported
outputFile = sys.argv[2] #output JSON file
if (sys.argv[3] != "#"):
    fieldList = sys.argv[3].split(";") #fields to return
else:
    fieldList = "#"

##set the outFile
outFile = open(outputFile, "w")

## get the shape field's name
desc = gp.Describe(lyrName)
lyrType = desc.ShapeType

SHPfieldname = desc.ShapeFieldName

# Get a list of fields to return since the user didn't specify any (removes the geometry field)
if (fieldList == "#"):
    fieldList = []
    fields = gp.ListFields(lyrName)
    field = fields.Next()
    while field:
        if (field.name != SHPfieldname):
            fieldList.append(field.Name)
        field = fields.Next()
FeatureCollection = {"type": "FeatureCollection"}
FeatureCollection["features"] = []

# Create search cursor by opening featureclass
rows = gp.SearchCursor(lyrName)
row = rows.Next()

# Enter while loop for each feature/row
while row:
    tmpFeature = {"type": "Feature"}  
    tmpFeature["properties"] = {}
    for i, v in enumerate(fieldList):
        if (v != "SHAPE"):
            tmpFeature["properties"][v] = row.GetValue(v)

    tmpFeature["geometry"] = {}
     
    # Create the geometry object 'feature'
    feature = row.GetValue(SHPfieldname)
    
    if (lyrType == "Point"):
        tmpFeature["geometry"]["type"] = "Point"
        pnt = feature.GetPart()
        tmpFeature["geometry"]["coordinates"]  = [int(pnt.X), int(pnt.Y)]
        nodeCounter += 1
        
    elif (lyrType == "Multipoint"):
        tmpFeature["geometry"]["bbox"] = feature.Extent.split(" ")
        tmpFeature["geometry"]["type"] = "MultiPoint"
        tmpFeature["geometry"]["coordinates"] = []
        partnum = 0
        while partnum < feature.PartCount:
            pnt = feature.GetPart(partnum)
            tmpFeature["geometry"]["coordinates"].append([int(pnt.X), int(pnt.Y)])
            partnum += 1
            nodeCounter += 1
        
    elif (lyrType == "Polyline"):
        tmpFeature["geometry"]["bbox"] = feature.Extent.split(" ")
        tmpFeature["geometry"]["coordinates"] = []

        if (feature.IsMultipart == "FALSE"):
            tmpFeature["geometry"]["type"] = "LineString"
            partnum = 0
            
            # Enter while loop for each part in the feature (if a singlepart feature this will occur only once)
            while partnum < feature.PartCount:
                part = feature.GetPart(partnum)
                pnt = part.Next()
                # Enter while loop for each vertex
                while pnt:
                    tmpFeature["geometry"]["coordinates"].append([int(pnt.X), int(pnt.Y)])
                    pnt = part.Next()
                    nodeCounter += 1
                partnum += 1

        else:
            tmpFeature["geometry"]["type"] = "MultiLineString"
            partnum = 0
            
            # Count the number of points in the current multipart feature
            partcount = feature.PartCount

            # Enter while loop for each part in the feature (if a singlepart feature this will occur only once)
            while partnum < partcount:
                # Print the part number
                part = feature.GetPart(partnum)
                pnt = part.Next()
                pntcount = 0
                tmpFeature["geometry"]["coordinates"].append([])
                # Enter while loop for each vertex
                while pnt:
                    # Print x, y coordinates of current point
                    tmpFeature["geometry"]["coordinates"][partnum].append([int(pnt.X), int(pnt.Y)])
                    pnt = part.Next()
                    pntcount += 1
                    nodeCounter += 1
                partnum += 1

    elif (lyrType == "Polygon"):
        tmpFeature["geometry"]["bbox"] = feature.Extent.split(" ")
        
        fCollection = []
        partnum = 0        
        # Enter while loop for each part in the feature (if a singlepart feature this will occur only once)
        while partnum < feature.PartCount:
            part = feature.GetPart(partnum)
            pnt = part.Next()
            intRing = False
            aPoly = []
            outPoly = []
            inPolyColl = []
            inPolyTemp = []
            # Enter while loop for each vertex
            while pnt:
                # Print x, y coordinates of current point
                if intRing:
                    inPolyTemp.append([int(pnt.X), int(pnt.Y)])
                else:
                    outPoly.append([int(pnt.X), int(pnt.Y)])
                pnt = part.Next()
                nodeCounter += 1

                # If pnt is null, either the part is finished or there is an interior ring
                if not pnt:
                    if (len(inPolyTemp) != 0):
                        aPoly.append(inPolyTemp)
                    pnt = part.Next()
                    if pnt:
                        inPolyTemp = []
                        intRing = True
            aPoly.insert(0,outPoly)

            partnum += 1
            fCollection.append(aPoly)
          
        if (feature.IsMultipart == "TRUE"):
            tmpFeature["geometry"]["coordinates"] = fCollection
            tmpFeature["geometry"]["type"] = "MultiPolygon"
        else:
            tmpFeature["geometry"]["coordinates"] = fCollection[0]
            tmpFeature["geometry"]["type"] = "Polygon"
    else:
        go_error("Bad Geometry. Please check the type of layer!!!")

    FeatureCollection["features"].append(tmpFeature)
    row = rows.Next()
del rows

with open(outputFile, 'w') as outfile:
    json.dump(FeatureCollection, outfile)

stopTime = time.clock()
elapsedTime = stopTime - startTime

if (nodeCounter > 5000):
    go_warn("**************WARNING**************")
    go_warn("I've counted " + str(nodeCounter) + " vertices!")
    go_warn("If you are intending to send this file to a web-browser, please consider simplifying the data first.")
    go_warn("***********************************")
    go_warn(" ")

go_print("Your output GeoJSON file can be found at:")
go_print("  " + outputFile)
go_print("done in " + str(round(elapsedTime, 1)) + " seconds.")
go_print(" ")

del gp
