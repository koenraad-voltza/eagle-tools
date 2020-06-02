import xml.etree.ElementTree as ET
import os
import argparse
import design_block_layout

designblocklist = [['5V_GEN','powerblock_P_5V_4A'],['LEVEL_SHIFTER', 'level_shifter_adj_15V']]#[['AD8334', 'ad8334_LNAVGAVGA'], ['ENVELOPE', 'envelope_detection'], ['FILTER','filter_mezzanine_carpatchiot'],['SUB_EQ','MEMS-eq'],['5V_GEN','powerblock_P_5V_4A'],['ENVELOPE', 'envelope_detection']
    # ['DRIVER', 'sthv1600'],['STHV1600','sthv1600']]
# command = "python3 ./design_block_layout.py "#~/repositories/imec-github/SilenSE/hardware/silense_v2"
design_block_dir = "/Users/wdevries/GIT/eagle/design blocks/"#"~/repositories/imec-github/eagle/design\ blocks/design\ blocks/"

modList = []

# todo get offsets from design block max layout size
x = -100
y = -100
x_offset = 100
y_offset = 100
x_max = 1500
y_max = 1500
dList = list(zip(*designblocklist))


def design_block_retrieval(moduleName):
    try:
        return (designblocklist[dList[0].index(str(moduleName))][1])
    except:
        return 0


def findModule(root, moduleName):
    # retrieve design block module names
    for module in root.iter('module'):
        print(module)
        if(module.attrib.get('name') == moduleName):
            design_block_module = design_block_retrieval(moduleName)
            if(design_block_module != 0):
                design_block_name = design_block_retrieval(moduleName)
            else:
                design_block_name = []
                for moduleinst in module.iter('moduleinst'):
                    print("*--> ", moduleinst.attrib.get('name'),
                        moduleinst.attrib.get('module'))
                    modInst = design_block_retrieval(
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
                design_block_name = findModule(root, modClass)
                if(design_block_name != []):
                    print(modInst+":"+str(design_block_name[0][0]))
                    print(modInst, design_block_name)
                    if(type(design_block_name) != list):
                        placeblock(file,
                            modInst, design_block_dir+str(design_block_name), x, y)                      
                        if(x < x_max):
                            x += x_offset
                        else:
                            x = 0
                            y += y_offset
        else:
            print("give a description at your main sheet in order to be retrievable")

# call the placement function for the specific designblock and components, place them at (x,y)


def placeblock(file, module, design_block, x, y):
    # os.system(command + " " + module + " " + design_block +
    #           " --coordinates " + str(x) + "," + str(y))
    design_block_layout.placeBlock(file, module, design_block, (x,y))
# todo parser for link to design block directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory",help="directory where schematic is")
    parser.add_argument(
        "schematic", help="link the schematic with design blocks")
    args = parser.parse_args()
    sch = args.directory + "/" + args.schematic
    # command = command + sch
    tree = ET.parse(sch+".sch")
    root = tree.getroot()
    listModuleInst(sch, root,x,y)
