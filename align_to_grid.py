#must be run with python3
import argparse
import xml.etree.ElementTree as ET
from decimal import Decimal

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Align components in Eagle schematic sheet to grid')
    parser.add_argument('file', action="store", help='Eagle Schematic file (.sch)')
    parser.add_argument('--grid', '-g', action="store", default="100", help='grid size (mil)')
    args = parser.parse_args()

    tree = ET.parse(args.file)
    root = tree.getroot()
    for component in root.iter('instance'):
        changed = False
        grid_nm = int(int(args.grid) * 25.4 * 1000)
        #print(instance.attrib['part'])
        #print(instance.attrib['x'])
        #print(instance.attrib['y'])
        x_nm = Decimal(component.attrib['x'])*1000*1000
        y_nm = Decimal(component.attrib['y'])*1000*1000
        oldcoordinates = (component.attrib['x'], component.attrib['y'])
        if not((x_nm % grid_nm)==0):
            #print(x_nm)
            #print(grid_nm)
            #print(x_nm % grid_nm)
            changed = True
            component.attrib['x'] = str(round(Decimal(0.001*0.001)*(x_nm/grid_nm).quantize(1)*grid_nm,2))
            #print(int(component.fields[0]['posx']))
        if not((y_nm % grid_nm)==0):
            #print(x_nm)
            #print(grid_nm)
            #print(x_nm % grid_nm)
            changed = True
            component.attrib['y'] = str(round(Decimal(0.001*0.001)*(y_nm/grid_nm).quantize(1)*grid_nm,2))
        #if not((Decimal(component.attrib['y']) % grid_mm)==0):
        #    changed = True
        #    component.attrib['y'] = str(round(float(component.attrib['y'])/grid_mm)*grid_mm)
        if changed == True:
            newcoordinates = (component.attrib['x'], component.attrib['y'])
            print("Changed component " + component.attrib['part'] + " from " + str(oldcoordinates) + " to " + str(newcoordinates))
    tree.write(args.file)
