import xml.etree.ElementTree as ET
import os
import argparse
import design_block_layout

designblocklist = [['AD8334', 'ad8334_LNAVGAVGA'], ['ENVELOPE', 'envelope_detection'], [
    'LEVEL_SHIFTER', 'level_shifter_adj_15V'], ['DRIVER', 'sthv1600']]
command = "python3 ./design_block_layout.py "#~/repositories/imec-github/SilenSE/hardware/silense_v2"
design_block_dir = "/Users/wdevries/GIT/eagle/design blocks/design blocks/"#"~/repositories/imec-github/eagle/design\ blocks/design\ blocks/"



modList = []

# todo get offsets from design block max layout size
x = 40
y = 40
x_offset = 50
y_offset = 50
dList = list(zip(*designblocklist))


def design_block_placement(moduleName):
    try:
        return (designblocklist[dList[0].index(str(moduleName))][1])
    except:
        return 0


def findModule(moduleName):
    # retrieve design block module names
    for module in root.iter('module'):
        if(module.attrib.get('name') == moduleName):
            print("found", module)
            design_block_module = design_block_placement(moduleName)
            if(design_block_module != 0):
                design_block_name = design_block_placement(moduleName)
            else:
                design_block_name = []
                for moduleinst in module.iter('moduleinst'):
                    print("*--> ", moduleinst.attrib.get('name'),
                        moduleinst.attrib.get('module'))
                    modInst = design_block_placement(
                        moduleinst.attrib.get('module'))
                    if(modInst != 0):
                        design_block_name.append([moduleinst.attrib.get('name')+":" +
                                                  moduleinst.attrib.get('module'), modInst])
            return design_block_name


def listModuleInst(file, root,x,y):
    for sheet in root.iter('sheet'):
        # we look for the sheets, they contain design blocks
        if(sheet.find('description') != None):
            print("sheet: ", sheet.find('description').text)
            # we list the amount of moduleinstances we encounter, with their respective module names
            for moduleinst in sheet.iter('moduleinst'):
                modInst = moduleinst.attrib.get('name')
                modClass = moduleinst.attrib.get('module')
                print("-->", modInst, modClass)
                design_block_name = findModule(modClass)
                if(design_block_name != []):
                    # print(modInst+":"+str(design_block_name[0][0]))
                    print(modInst, design_block_name)
                    if(type(design_block_name) != list):
                        placeblock(file,
                            modInst, command, design_block_dir+str(design_block_name), x, y)
                        x += x_offset
                        y += y_offset

# call the placement function for the specific designblock and components, place them at (x,y)


def placeblock(file, module, command, design_block, x, y):
    # os.system(command + " " + module + " " + design_block +
    #           " --coordinates " + str(x) + "," + str(y))
    design_block_layout.placeBlock(file, module, design_block, (x,y))
# todo parser for link to design block directory


if __name__ == "__main__":
    # todo parser for schematic relative link
    parser = argparse.ArgumentParser()
    parser.add_argument("directory",help="directory where schematic is")
    parser.add_argument(
        "schematic", help="link the schematic with design blocks")
    args = parser.parse_args()
    sch = args.directory + "/" + args.schematic
    command = command + sch
    tree = ET.parse(sch+".sch")
    root = tree.getroot()
    listModuleInst(sch, root,x,y)
