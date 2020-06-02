'''
documentation:
this file has the idea to check if a design block has been used and to adapt board layouts IF the schematic has been changed, yet the board layout is not updated accordingly.

We specify a conversion:
[name of block in sheet, name of design block, center component to choose]

all coordinates of components and others are placed based on the center component, thus keeping the relative coordinates

step 1: check coordinate of "center component" in design block
step 2: check coordinate of "center component" on board layout
step 3: place components with that coordinate difference

'''
import xml.etree.ElementTree as ET
import os
import argparse
import design_block_layout
import moduleplacement as mod

db_center_x, db_center_y, brd_center_x, brd_center_y = 0, 0, 0, 0


designblocklist = [['FILTER', 'filter_mezzanine_carpatchiot'], ['SUB_EQ', 'MEMS-eq'], ['5V_GEN', 'powerblock_P_5V_4A'],
                   ['ENVELOPE', 'envelope_detection']]  # [['AD8334', 'ad8334_LNAVGAVGA'], ['ENVELOPE', 'envelope_detection'], [
# 'LEVEL_SHIFTER', 'level_shifter_adj_15V'], ['DRIVER', 'sthv1600'],['STHV1600','sthv1600']]
# command = "python3 ./design_block_layout.py "#~/repositories/imec-github/SilenSE/hardware/silense_v2"
# "~/repositories/imec-github/eagle/design\ blocks/design\ blocks/"
design_block_dir = "/Users/wdevries/GIT/eagle/design blocks/"

modList = []
dList = list(zip(*designblocklist))


def design_block_retrieval(moduleName):
    try:
        return (designblocklist[dList[0].index(str(moduleName))][1])
    except:
        return 0


def locate_in_design_block(component, design_block):
    # "open a design block and find the (x,y) coordinates of the specified IC"
    db_file = design_block_dir+str(design_block)
    # find corresponding sheet
    blocktree = ET.parse(db_file + ".dbl")
    blockroot = blocktree.getroot()
    for element in blockroot.iter("element"):
        # print(element.attrib["name"])
        if(element.attrib["name"] == str(component)):
            # print(element.attrib["name"], element.attrib["value"],
            #       element.attrib["x"], element.attrib["y"])
            x = element.attrib["x"]
            y = element.attrib["y"]
            if "rot" in element.attrib:
                rot = element.attrib["rot"]
            else:
                rot = "R0"
    return x, y, rot


def remove_wires_and_vias_in_board(layouttree, name, board):
    # "open a design block and find the (x,y) start and end-coordinates of wires corresponding to a certain design block"

    # find corresponding sheet
    layoutroot = layouttree.getroot()
    for signals in layoutroot.iter("signals"):
        for signal in signals:
            # print(element.attrib["name"])
            if(signal.attrib["name"].find(name) >= 0):
                # print(element.attrib["name"], element.attrib["value"],
                #       element.attrib["x"], element.attrib["y"])
                # print(signal.attrib["name"])
                # we remove old wires and vias
                for child in signal:
                    if(child.tag == "wire" or child.tag == "via"):
                        # print("remove:", child.tag)
                        signal.remove(child)
                    else:
                        continue
    return layouttree

# contact element z


def place_new_wires_and_vias(dbl, layouttree, contact_element, coordinates, center_rot, center_origin):
    dblocktree = ET.parse(design_block_dir+dbl + ".dbl")
    dblockroot = dblocktree.getroot()
    dblockroot = dblocktree.getroot()
    layoutroot = layouttree.getroot()
    for blksignal in dblockroot.iter("signal"):
        for laysignal in layoutroot.iter("signal"):
            # Match nets based on the connected elements
            for blkcontactref in blksignal.iter("contactref"):
                for laycontactref in laysignal.iter("contactref"):
                    if laycontactref.attrib["element"].split(':')[:-1] == contact_element.split(":")[:-1]:
                        if laycontactref.attrib["element"].split(':')[-1] == blkcontactref.attrib["element"]:
                            if laycontactref.attrib["pad"] == blkcontactref.attrib["pad"]:
                                # print(laycontactref.attrib["element"].split(':')[:-1], contact_element)
                                # print laycontactref.attrib["element"].split(':')[-1],blkcontactref.attrib["element"]
                                # print(
                                #     "Matched Net " + blksignal.attrib["name"] + " to Net " + laysignal.attrib["name"])
                                # print("-->", laysignal.attrib["name"])
                                for wire in blksignal.findall("wire"):
                                    # print("--->", blksignal.attrib["name"], center_rot, coordinates,
                                    #       wire.attrib["x1"], wire.attrib["x2"], wire.attrib["width"])
                                    wire_up = update_wire(
                                        wire, coordinates, center_rot, center_origin)
                                    # print(
                                    #     "--->", wire_up.attrib["x1"], wire_up.attrib["y1"], wire_up.attrib["x2"], wire_up.attrib["y2"], )
                                    laysignal.append(wire_up)
                                for via in blksignal.findall("via"):
                                    via = update_via_vertex(
                                        via, coordinates, center_rot, center_origin)
                                    laysignal.append(via)
                                for polygon in blksignal.findall("polygon"):
                                    for vertex in polygon.findall("vertex"):
                                        update_via_vertex(
                                            vertex, coordinates, center_rot, center_origin)
                                    laysignal.append(polygon)
                                break
                    # else:
                        # print(laycontactref.attrib["element"].split(':')[:-1],contact_element.split(":"))
                else:
                    continue
                break
            else:
                continue
            break
        # else:
            # print("Net not found " + blksignal.attrib["name"])
            # we place the new wires and vias
    return layouttree


def unique_board_block_center(dir, file, center_component, value, dbl):
    # Open the board layout and find the (x,y) coordinates of a certain submodule
    search_file = str(dir)+str(file)
    tree = ET.parse(search_file+".sch")
    root = tree.getroot()
    # find corresponding sheet
    boardtree = ET.parse(search_file + ".brd")
    boardroot = boardtree.getroot()

    brd_db_naming_list = create_mod_list(boardroot, value)
    for element in boardroot.iter("element"):
        # el_level_name = element.attrib["name"].split(
        #     ":")[0] + ":" + element.attrib["name"].split(":")[1] + ":"
        for i in brd_db_naming_list:
            x_orig = float(brd_db_naming_list.get(i).get("x"))
            y_orig = float(brd_db_naming_list.get(i).get("y"))
            rot_el = str(brd_db_naming_list.get(i).get("rot"))
            if(element.attrib["name"].find(i) >= 0):
                new_x, new_y, local_rot = rel_x_y_in_dbl(center_component,
                                                         element.attrib["name"].split(":")[2], dbl)

                # we use the rotation of the center element to calculate the x, y movement. new_rot is then used for local element rotation

                place_x, place_y, place_rot = calc_new_loc_element(
                    x_orig, y_orig, new_x, new_y, rot_el, local_rot)

                element.attrib["x"] = str(place_x)
                element.attrib["y"] = str(place_y)
                element.attrib["rot"] = str(place_rot)

            remove_wires_and_vias_in_board(boardtree, i, search_file)
    for i in brd_db_naming_list:
        x_orig = float(brd_db_naming_list.get(i).get("x"))
        y_orig = float(brd_db_naming_list.get(i).get("y"))
        rot_el = str(brd_db_naming_list.get(i).get("rot"))
        # print("wiring ", i, "at", x_orig, y_orig)
        center_origin = locate_in_design_block(center_component, dbl)
        boardtree = place_new_wires_and_vias(dbl,
                                             boardtree, i, {"x": x_orig, "y": y_orig}, rot_el, center_origin)

    return boardtree

# center should be center component in desi


def rel_x_y_in_dbl(center_component, component, dbl):
    comp_x, comp_y, rot = locate_in_design_block(component, dbl)
    center_x, center_y, rot_center = locate_in_design_block(
        center_component, dbl)
    x = round(float(comp_x) - float(center_x),2)
    y = round(float(comp_y) - float(center_y),2)
    return x, y, rot


def calc_new_loc_element(x_orig, y_orig, new_x, new_y, rot_el, local_rot):
    if(rot_el == 'R0'):
        place_x = x_orig+new_x
        place_y = y_orig+new_y
        place_rot = local_rot
    else:
        if(rot_el == 'R90'):
            print("need to verify coordinates!")
            place_x = x_orig-new_y
            place_y = y_orig+new_x
        else:
            if(rot_el == 'R180'):
                place_x = x_orig-new_x
                place_y = y_orig-new_y
                if(local_rot == 'R0'):
                    place_rot = 'R180'
                if(local_rot == 'R90'):
                    place_rot = 'R270'
                if(local_rot == 'R180'):
                    place_rot = 'R0'
                if(local_rot == 'R270'):
                    place_rot = 'R90'
            else:
                if(rot_el == 'R270'):
                    print("need to verify coordinates!")
                    place_x = x_orig+new_y
                    place_y = y_orig-new_x
                else:
                    print("different")
    return place_x, place_y, place_rot



def update_wire(wire, coordinates, center_rot, center_origin):
    wire_up = wire
    if(center_rot == 'R0'):
        wire_up.attrib["x1"] = str(
            round(float(wire.attrib["x1"])+coordinates.get("x"), 2))
        wire_up.attrib["x2"] = str(
            round(float(wire.attrib["x2"])+coordinates.get("x"), 2))
        wire_up.attrib["y1"] = str(
            round(float(wire.attrib["y1"])+coordinates.get("y"), 2))
        wire_up.attrib["y2"] = str(
            round(float(wire.attrib["y2"])+coordinates.get("y"), 2))
    else:
        if(center_rot == 'R90'):
            print("need to verify coordinates!")
            place_x = x_orig-new_y
            place_y = y_orig+new_x
            place_rot = 'R0'  # not correct
        else:
            if(center_rot == 'R180'):
                wire_up.attrib["x1"] = str(
                    round(float(center_origin[0])-float(wire.attrib["x1"])+coordinates.get("x"), 2))
                wire_up.attrib["x2"] = str(
                    round(float(center_origin[0])-float(wire.attrib["x2"])+coordinates.get("x"), 2))
                wire_up.attrib["y1"] = str(
                    round(float(center_origin[1])-float(wire.attrib["y1"])+coordinates.get("y"), 2))
                wire_up.attrib["y2"] = str(
                    round(float(center_origin[1])-float(wire.attrib["y2"])+coordinates.get("y"), 2))
            else:
                if(center_rot == 'R270'):
                    print("need to verify coordinates!")
                    place_x = x_orig+new_y
                    place_y = y_orig-new_x
                else:
                    print("different")
    return wire_up


def update_via_vertex(via, coordinates, center_rot, center_origin):
    if(center_rot == 'R0'):
        via.attrib["x"] = str(round(float(via.attrib["x"])+coordinates.get("x"),2))
        via.attrib["y"] = str(round(float(via.attrib["y"])+coordinates.get("y"),2))
    else:
        if(center_rot == 'R90'):
            print("need to verify coordinates!")
            place_x = x_orig-new_y
            place_y = y_orig+new_x
            place_rot = 'R0'  # not correct
        else:
            if(center_rot == 'R180'):
                via.attrib["x"] = str(
                    round(float(center_origin[0])-float(via.attrib["x"])+coordinates.get("x"),2))
                via.attrib["y"] = str(
                    round(float(center_origin[1])-float(via.attrib["y"])+coordinates.get("y"),2))
            else:
                if(center_rot == 'R270'):
                    print("need to verify coordinates!")
                    place_x = x_orig+new_y
                    place_y = y_orig-new_x
                else:
                    print("different")
    return via


def create_mod_list(blockroot, value):
    brd_db_naming = {}
    for element in blockroot.iter("element"):
        # print(element.attrib["name"])
        # print(str(name)+":"+str(component))
        if(element.attrib["value"] == str(value)):
            print(element.attrib["name"], element.attrib["value"],
                  element.attrib["x"], element.attrib["y"])
            brd_center_x = element.attrib["x"]
            brd_center_y = element.attrib["y"]
            x = round(float(brd_center_x) - float(db_center_x),2)
            y = round(float(brd_center_y) - float(db_center_y),2)
            if "rot" in element.attrib:
                rot_el = element.attrib.get("rot")
            else:
                rot_el = "R0"
            name = element.attrib["name"].split(
                ":")[0] + ":" + element.attrib["name"].split(":")[1]+":"
            if name not in brd_db_naming.keys():
                brd_db_naming[name] = {"x": brd_center_x,
                                       "y": brd_center_y, "rot": rot_el}
    print(brd_db_naming)
    return brd_db_naming

'''
In order to use this:
This is only useful if most parts of the designblock remains the same.
remove all vias close to design blocks
open a second eagle application (both board and schematic layout open), copy the updated designblock over the old one (schematic). 
Now some components should be added on your board layout.
Run the script
'''
if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("directory",help="directory where schematic is")
    # parser.add_argument(
    #     "schematic", help="link the schematic with design blocks")
    # args = parser.parse_args()
    # sch = args.directory + "/" + args.schematic
    # # command = command + sch
    # tree = ET.parse(sch+".sch")
    # root = tree.getroot()

    address = "/Users/wdevries/GIT/SilenSE/hardware/v3_0/"
    file = "silense_v3"
    
    # db_center_x, db_center_y, center_rot = locate_in_design_block(
    #     "IC1", "ad8334_LNAVGAVGA")
    
    # tree = unique_board_block_center(
    #     address, file, "IC1", "AD8334ACPZ", "ad8334_LNAVGAVGA")

    db_center_x, db_center_y, center_rot = locate_in_design_block(
        "IC1", "envelope_detection_2nd_order_LP")
    
    tree = unique_board_block_center(
        address, file, "IC1", "LT6238HGN#PBF", "envelope_detection_2nd_order_LP")

    tree.write(address + file+".brd")
