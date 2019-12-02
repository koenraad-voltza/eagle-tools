#must be run with python3
import argparse
import xml.etree.ElementTree as ET

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Align components in Eagle schematic sheet to grid')
    parser.add_argument('file', action="store", help='Eagle Schematic file (.sch)')
    parser.add_argument('--grid', '-g', action="store", default="100", help='grid size (mil)')
    args = parser.parse_args()

    tree = ET.parse(args.file)
    root = tree.getroot()
    for component in root.iter('instance'):
        #print(instance.attrib['part'])
        #print(instance.attrib['x'])
        #print(instance.attrib['y'])

        oldcoordinates = (component.attrib['x'], component.attrib['y'])
        if not(((float(component.attrib['x'])*1000) % int(args.grid))==0):
            changed = True
            component.attrib['x'] = str(int((float(component.attrib['x'])*1000) / int(args.grid))*float(args.grid)/1000.0)
            #print(int(component.fields[0]['posx']))
        if not(((float(component.attrib['y'])*1000) % int(args.grid))==0):
            changed = True
            component.attrib['y'] = str(int((float(component.attrib['x'])*1000) / int(args.grid))*float(args.grid)/1000.0)
        if changed == True:
            newcoordinates = (component.attrib['x'], component.attrib['y'])
            print("Changed component " + component.attrib['part'] + "from " + str(oldcoordinates) + " to " + str(newcoordinates))
    tree.write(args.file)
