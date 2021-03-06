#must be run with python3
import argparse
import xml.etree.ElementTree as ET

def placeBlock(file, sheet, block, coordinates):
    
    #find corresponding sheet
    schematictree = ET.parse(file + ".sch")
    schematicroot = schematictree.getroot()
    instanceroot = schematicroot
    #find matches in schematic as in RECEIVER1:S1:AD8334 => find RECEIVER1 instance
    print("sheet split",sheet,sheet.split(":"))
    for hierarchmoduleinst in sheet.split(':'):
        for moduleinst in instanceroot.iter('moduleinst'):
            if moduleinst.attrib["name"]==hierarchmoduleinst:
                break
        else:
            print("moduleinst not found in schematic file")
            break
        for module in schematicroot.iter('module'):
            if module.attrib["name"]==moduleinst.attrib["module"]:
                schematicmodule = module
                instanceroot = module
                break
        else:
            print("module not found in schematic file")
            break

    layouttree = ET.parse(file + ".brd")
    layoutroot = layouttree.getroot()
    for board in layoutroot.iter('board'):
        layoutboard = board
    blocktree = ET.parse(block + ".dbl")
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
        x = float(blkelement.attrib["x"]) + coordinates[0]
        y = float(blkelement.attrib["y"]) + coordinates[1]
        #print blkelement.attrib["name"]
        print("Move " + dsntosch_refs[blkelement.attrib["name"]] + " to " + str(x) + "," + str(y))
        for layelement in layoutboard.iter("element"):
            if layelement.attrib["name"].split(':')[:-1] == sheet.split(':'):
                if layelement.attrib["name"].split(':')[-1] == dsntosch_refs[blkelement.attrib["name"]]:
                    print("Moving " + layelement.attrib["name"])
                    layelement.attrib["x"]=str(x)
                    layelement.attrib["y"]=str(y)
                    if "rot" in blkelement.attrib:
                        layelement.attrib["rot"]= blkelement.attrib["rot"]
                    for layattribute in layelement.iter("attribute"):
                        for blkattribute in blkelement.iter("attribute"):
                            if blkattribute.attrib["name"] == layattribute.attrib["name"]:
                                x = float(blkattribute.attrib["x"]) + coordinates[0]
                                y = float(blkattribute.attrib["y"]) + coordinates[1]
                                layattribute.attrib["x"]=str(x)
                                layattribute.attrib["y"]=str(y)
                                if "rot" in blkattribute.attrib:
                                    layattribute.attrib["rot"]= blkattribute.attrib["rot"]
                                break
                        else:
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
                    if laycontactref.attrib["element"].split(':')[:-1] == sheet.split(':'):
                        if laycontactref.attrib["element"].split(':')[-1] == blkcontactref.attrib["element"]:
                            if laycontactref.attrib["pad"] == blkcontactref.attrib["pad"]:
                                #print laycontactref.attrib["element"].split(':')[:-1], args.sheet.split(':')
                                #print laycontactref.attrib["element"].split(':')[-1],blkcontactref.attrib["element"]
                                print("Matched Net " + blksignal.attrib["name"] + " to Net " + laysignal.attrib["name"])
                                for wire in blksignal.findall("wire"):
                                    wire.attrib["x1"]=str(float(wire.attrib["x1"])+coordinates[0])
                                    wire.attrib["x2"]=str(float(wire.attrib["x2"])+coordinates[0])
                                    wire.attrib["y1"]=str(float(wire.attrib["y1"])+coordinates[1])
                                    wire.attrib["y2"]=str(float(wire.attrib["y2"])+coordinates[1])
                                    laysignal.append(wire)
                                for via in blksignal.findall("via"):
                                    via.attrib["x"]=str(float(via.attrib["x"])+coordinates[0])
                                    via.attrib["y"]=str(float(via.attrib["y"])+coordinates[1])
                                    laysignal.append(via)
                                for polygon in blksignal.findall("polygon"):
                                    for vertex in polygon.findall("vertex"):
                                        vertex.attrib["x"]=str(float(vertex.attrib["x"])+coordinates[0])
                                        vertex.attrib["y"]=str(float(vertex.attrib["y"])+coordinates[1])
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

    layouttree.write(file + ".brd")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add design block layout')
    parser.add_argument('file', action="store", help='Eagle Schematic/Layout file (.sch/.brd)')
    parser.add_argument('sheet', action="store", help='Eagle Schematic sheet name')
    parser.add_argument('block', action="store", help='Eagle Design Block file (.dbl)')
    parser.add_argument('--coordinates', '-c', action="store", default="0,0", help='origin coordinates on PCB: "x,y"')
    args = parser.parse_args()
    coordinates = (float(args.coordinates.split(',')[0]), float(args.coordinates.split(',')[1]))
    placeBlock(args.file, args.sheet, args.block, coordinates)
print("Turn airwires off and on with:")
print("\t ratsnest ! *")
print("\t ratsnest *")