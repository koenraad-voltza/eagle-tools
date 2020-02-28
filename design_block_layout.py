#must be run with python3
import argparse
import xml.etree.ElementTree as ET
import re

r = re.compile("([a-zA-Z]+)([0-9]+)")

def moveelement(element,x, y, rot, dx, dy, drot, addrotation=True):
    if drot == 0:
        element.attrib["x"]=str(x + dx)
        element.attrib["y"]=str(y + dy)
    if drot == 90:
        element.attrib["x"]=str(y + dx)
        element.attrib["y"]=str(-x + dy)
    if drot == 180:
        element.attrib["x"]=str(-x + dx)
        element.attrib["y"]=str(-y + dy)
    if drot == 270:
        element.attrib["x"]=str(-y + dx)
        element.attrib["y"]=str(x + dy)
    if addrotation:
        split=r.match(rot).groups()
        element.attrib["rot"]=split[0]+ str((int(split[1])+drot)%360)
        if element.attrib["rot"]=="R0":
            element.attrib.pop("rot")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add design block layout')
    parser.add_argument('file', action="store", help='Eagle Schematic/Layout file (.sch/.brd)')
    parser.add_argument('sheet', action="store", help='Eagle Schematic sheet name')
    parser.add_argument('block', action="store", help='Eagle Design Block file (.dbl)')
    parser.add_argument('--coordinates', '-c', action="store", default="0,0", help='origin coordinates on PCB: "x,y"')
    parser.add_argument('--rotate', '-r', action="store", default="0", help='rotate the block x degrees clockwise')
    args = parser.parse_args()
    coordinates = (float(args.coordinates.split(',')[0]), float(args.coordinates.split(',')[1]))

    #find corresponding sheet
    schematictree = ET.parse(args.file + ".sch")
    schematicroot = schematictree.getroot()
    instanceroot = schematicroot
    for hierarchmoduleinst in args.sheet.split(':'):
        for moduleinst in instanceroot.iter('moduleinst'):
            if moduleinst.attrib["name"]==hierarchmoduleinst:
                break
        else:
            print("module not found in schematic file")
            break
        for module in schematicroot.iter('module'):
            if module.attrib["name"]==moduleinst.attrib["module"]:
                schematicmodule = module
                instanceroot = module
                break
        else:
            print("module not found in schematic file")
            break

    layouttree = ET.parse(args.file + ".brd")
    layoutroot = layouttree.getroot()
    for board in layoutroot.iter('board'):
        layoutboard = board

    blocktree = ET.parse(args.block + ".dbl")
    blockroot = blocktree.getroot()
    for schematic in blockroot.iter('schematic'):
        blockschematic = schematic
    for board in blockroot.iter('board'):
        blockboard = board

    #check if schematic sheet corresponds with design block schematic and create dictionary
    dsntosch_refs = {}
    #eagle > designblock > drawings > drawing > schematic > sheets > sheet > instances
    for schinstance in schematicmodule.iter("instance"):
        for blkinstance in blockschematic.iter("instance"):
            if (schinstance.attrib["x"],schinstance.attrib["y"]) == (blkinstance.attrib["x"], blkinstance.attrib["y"]):
                print("Matched " + schinstance.attrib["part"] + " with " +blkinstance.attrib["part"])
                dsntosch_refs[blkinstance.attrib["part"]]=schinstance.attrib["part"]
                break
        else:
            print("No equivalent found for " + schinstance.attrib["part"])
            #return

    #place/move all components
    #eagle > designblock > drawings > drawing > board > elements
    for blkelement in blockboard.iter("element"):
        #print blkelement.attrib["name"]
        #print("Move " + dsntosch_refs[blkelement.attrib["name"]] + " to " + str(x) + "," + str(y))
        for layelement in layoutboard.iter("element"):
            if layelement.attrib["name"].split(':')[:-1] == args.sheet.split(':'):
                if layelement.attrib["name"].split(':')[-1] == dsntosch_refs[blkelement.attrib["name"]]:
                    print("Moving " + layelement.attrib["name"])
                    #if "rot" in blkelement.attrib:
                    #    moveelement(layelement, float(blkelement.attrib["x"]), float(blkelement.attrib["y"]), blkelement.attrib["rot"], 0, coordinates[0], coordinates[1], int(args.rotate))
                    #else:
                    #    moveelement(layelement, float(blkelement.attrib["x"]), float(blkelement.attrib["y"]), "R0", coordinates[0], coordinates[1], int(args.rotate))
                    layelement.attrib["x"]=str(float(blkelement.attrib["x"]) + coordinates[0])
                    layelement.attrib["y"]=str(float(blkelement.attrib["y"]) + coordinates[1])
                    if "rot" in blkelement.attrib:
                        layelement.attrib["rot"]= blkelement.attrib["rot"]
                    for layattribute in layelement.iter("attribute"):
                        for blkattribute in blkelement.iter("attribute"):
                            if blkattribute.attrib["name"] == layattribute.attrib["name"]:
                                # if "rot" in blkattribute.attrib:
                                #     moveelement(layattribute, float(blkattribute.attrib["x"]), float(blkattribute.attrib["y"]), blkattribute.attrib["rot"], 0, coordinates[0], coordinates[1], int(args.rotate))
                                # else:
                                #     moveelement(layattribute, float(blkattribute.attrib["x"]), float(blkattribute.attrib["y"]), "R0", coordinates[0], coordinates[1], int(args.rotate))
                                x = float(blkattribute.attrib["x"]) + coordinates[0]
                                y = float(blkattribute.attrib["y"]) + coordinates[1]
                                layattribute.attrib["x"]=str(x)
                                layattribute.attrib["y"]=str(y)
                                if "rot" in blkattribute.attrib:
                                    layattribute.attrib["rot"]= blkattribute.attrib["rot"]
                                break
                        else:
                            #moveelement(layattribute, float(blkattribute.attrib["x"]), float(blkattribute.attrib["y"]), "R0", coordinates[0], coordinates[1], int(args.rotate))
                            layattribute.attrib["x"]=str(float(blkelement.attrib["x"]) + coordinates[0])
                            layattribute.attrib["y"]=str(float(blkelement.attrib["y"]) + coordinates[1])

    #eagle > designblock > drawings > drawing > schematic > sheets > sheet > nets
    dsntosch_nets = {}

    #place all other layout elements
    #eagle > designblock > drawings > drawing > board > signals
    for blksignal in blockboard.iter("signal"):
        for laysignal in layoutboard.iter("signal"):
            #Match nets based on the connected elements
            for blkcontactref in blksignal.iter("contactref"):
                for laycontactref in laysignal.iter("contactref"):
                    if laycontactref.attrib["element"].split(':')[:-1] == args.sheet.split(':'):
                        if laycontactref.attrib["element"].split(':')[-1] == blkcontactref.attrib["element"]:
                            if laycontactref.attrib["pad"] == blkcontactref.attrib["pad"]:
                                #print laycontactref.attrib["element"].split(':')[:-1], args.sheet.split(':')
                                #print laycontactref.attrib["element"].split(':')[-1],blkcontactref.attrib["element"]
                                print "Matched Net " + blksignal.attrib["name"] + " to Net " + laysignal.attrib["name"]
                                for wire in blksignal.findall("wire"):
                                    if int(args.rotate) == 0:
                                        wire.attrib["x1"]=str(float(wire.attrib["x1"])+coordinates[0])
                                        wire.attrib["x2"]=str(float(wire.attrib["x2"])+coordinates[0])
                                        wire.attrib["y1"]=str(float(wire.attrib["y1"])+coordinates[1])
                                        wire.attrib["y2"]=str(float(wire.attrib["y2"])+coordinates[1])
                                    if int(args.rotate) == 90:
                                        wire.attrib["x1"]=str(float(wire.attrib["y1"])+coordinates[0])
                                        wire.attrib["x2"]=str(float(wire.attrib["y2"])+coordinates[0])
                                        wire.attrib["y1"]=str(-float(wire.attrib["x1"])+coordinates[1])
                                        wire.attrib["y2"]=str(-float(wire.attrib["x2"])+coordinates[1])
                                    if int(args.rotate) == 180:
                                        wire.attrib["x1"]=str(-float(wire.attrib["x1"])+coordinates[0])
                                        wire.attrib["x2"]=str(-float(wire.attrib["x2"])+coordinates[0])
                                        wire.attrib["y1"]=str(-float(wire.attrib["y1"])+coordinates[1])
                                        wire.attrib["y2"]=str(-float(wire.attrib["y2"])+coordinates[1])
                                    if int(args.rotate) == 270:
                                        wire.attrib["x1"]=str(-float(wire.attrib["y1"])+coordinates[0])
                                        wire.attrib["x2"]=str(-float(wire.attrib["y2"])+coordinates[0])
                                        wire.attrib["y1"]=str(float(wire.attrib["x1"])+coordinates[1])
                                        wire.attrib["y2"]=str(float(wire.attrib["x2"])+coordinates[1])
                                    # wire.attrib["x1"]=str(float(wire.attrib["x1"])+coordinates[0])
                                    # wire.attrib["x2"]=str(float(wire.attrib["x2"])+coordinates[0])
                                    # wire.attrib["y1"]=str(float(wire.attrib["y1"])+coordinates[1])
                                    # wire.attrib["y2"]=str(float(wire.attrib["y2"])+coordinates[1])
                                    laysignal.append(wire)
                                for via in blksignal.findall("via"):
                                    #via.attrib["x"]=str(float(via.attrib["x"])+coordinates[0])
                                    #via.attrib["y"]=str(float(via.attrib["y"])+coordinates[1])
                                    moveelement(via, float(via.attrib["x"]), float(via.attrib["y"]), "R0", coordinates[0], coordinates[1], int(args.rotate),False)
                                    laysignal.append(via)
                                for polygon in blksignal.findall("polygon"):
                                    for vertex in polygon.findall("vertex"):
                                        moveelement(vertex, float(vertex.attrib["x"]), float(vertex.attrib["y"]), "R0", coordinates[0], coordinates[1], int(args.rotate),False)
                                        #vertex.attrib["x"]=str(float(vertex.attrib["x"])+coordinates[0])
                                        #vertex.attrib["y"]=str(float(vertex.attrib["y"])+coordinates[1])
                                    laysignal.append(polygon)
                                break
                else:
                    continue
                break
            else:
                continue
            break
        else:
            print("Net not found " + blksignal.attrib["name"])

    layouttree.write(args.file + ".brd")
print "Turn airwires off and on with:"
print "\t ratsnest ! *"
print "\t ratsnest *"
