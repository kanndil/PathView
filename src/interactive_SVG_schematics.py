# Copyright 2023 AUC Open Source Hardware Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import getopt
import os
import re
import copy
import sys
import json
import time

##########################################################################################

criticalPathCells = []
allPaths = []
criticalPaths = []
blackboxCells = []
no_nets = 200

##########################################################################################


class Pin:
    def __init__(self, name, net, type):
        self.name = name
        self.net = net
        self.type = type


##############################


class StandardCell:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.pins = []

    def addPin(self, pin):
        self.pins.append(pin)


##########################################################################################


def get_offset(line):
    offset = re.search(r"\b(Delay)\b", line)
    return offset.start()


##############################


def add_cell_to_path(_standardCell, tempCriticalPath):
    flag = False
    for iterationCell in tempCriticalPath:
        if _standardCell.id == iterationCell.id:
            flag == True
            # take care of deep copy
            pinFlag = False
            for pin in iterationCell.pins:
                if pin.name == _standardCell.pins[0].name:
                    pinFlag = True
                    return pin.net
            if pinFlag == False:
                iterationCell.pins.append(copy.deepcopy(_standardCell.pins[0]))
            return copy.copy(_standardCell.pins[0].net)

    if flag == False:
        tempCriticalPath.append(copy.deepcopy(_standardCell))
    return copy.copy(_standardCell.pins[0].net)


##############################

def add_pin_to_blackbox_cell(pin, cell):
    flag = False
    for iterationPin in cell.pins:
        if pin.name == iterationPin.name:
            flag == True
            return

    if flag == False:
        tempPin = Pin(copy.deepcopy(pin.name), "", copy.deepcopy(pin.type))
        cell.pins.append(copy.deepcopy(tempPin))
    return


def add_blackbox_cell(_standardCell):
    flag = False
    for iterationCell in blackboxCells:
        if _standardCell.name == iterationCell.name:
            flag == True
            # take care of deep copy
            for pin in _standardCell.pins:
                add_pin_to_blackbox_cell(pin, iterationCell)
            return

    if flag == False:
        blackboxCells.append(copy.deepcopy(_standardCell))
    return

##############################


def get_all_paths_in_report(staReportFile):
    f = open(staReportFile, "r+")
    processingPath = False
    tempPath = []
    tempCriticalPath = []
    offset = 0
    net_index = -1
    counter = 0
    wire = 0
    _net = ""
    _pinType = "input"
    for line in f:
        counter += 1
        #print(counter)
        line = line[offset:]
        line = line.strip()
        if "Delay" in line:
            offset = get_offset(line)
        elif "Startpoint" in line:
            processingPath = True
            tempPath.clear()
            tempCriticalPath.clear()
            _pinType = "input"
        elif "Endpoint" in line:
            pass
        elif processingPath:
            if "data arrival time" in line:
                tempCriticalPath[-1].pins.append(Pin("out", "net_out", "output"))
                wire += 1
                net_index = -1
                _pinType = "input"
            elif "data required time" in line:
                for cell in tempCriticalPath:
                    add_blackbox_cell(cell)
                allPaths.append(copy.deepcopy(tempPath))
                criticalPaths.append(copy.deepcopy(tempCriticalPath))
                processingPath = False
                offset = 0
                wire = 0
                _pinType = "input"
                net_index = -1
                pass
            elif "(net)" in line:
                pass
            elif "/" in line:
                _cell = []
                line = line.split("(")

                cellName = line[1]
                cellName = cellName.split(")")
                cellName = cellName[0]

                line = line[0]
                line = line.split(" ")
                line = list(filter(None, line))
                delay = line[0]
                time = line[1]

                cellNameAndPin = line.pop()
                cellInfo = cellNameAndPin.split("/")
                pinName = cellInfo[-1]
                cellInfo.pop()
                cellId = "_".join(cellInfo)
                cellId = cellId.replace(".", "_")
                cellId = cellId.replace("[", "_")
                cellId = cellId.replace("]", "_")

                _cell.append(cellId)
                _cell.append(cellNameAndPin)
                _cell.append(delay)
                _cell.append(time)
                tempPath.append(_cell)

                _standardCell = StandardCell(cellName, cellId)

                if net_index == -1:
                    _net = "clk "
                    net_index += 1
                else:
                    if net_index == 0:
                        _net = "net" + str(wire)
                        net_index += 1
                    elif net_index == 1:

                        net_index = 0
                        wire += 1

                _pin = Pin(pinName, _net, _pinType)

                if _pinType == "input":
                    _pinType = "output"
                else:
                    _pinType = "input"

                _standardCell.addPin(copy.deepcopy(_pin))

                _net = add_cell_to_path(_standardCell, tempCriticalPath)

    return


##########################################################################################

def generate_SVG_from_JSON(path, skinfile):
    os.system(
        "netlistsvg ../output/"
        + designName
        + "/json/"
        + path
        + ".json -o ../output/"
        + designName
        + "/schematics/"
        + path
        + ".svg --skin "
        + skinfile
    )
    return

##########################################################################################


def addInteraction(path, i):
    jsScript = (
        """ 
        
        <script type="text/javascript">
            function reply_click(id)
            {
                const cells = """
        + str(allPaths[i])
        + """ ;
                var cellName = "cell name is " ;
                var delay = "\\n" ;
                var time = "\\n" ;
                for (let i = 0; i < cells.length; i++) { 
                    if (("cell_" + cells[i][0]) == id ){
                        delay += "Pin  " +cells[i][1]+ "\\t delay = " + cells[i][2]+"\\n";
                        cellName = "cell name is " + cells[i][0]+"\\n";
                        time += "Pin  " +cells[i][1]+  "\\t time = " + cells[i][3] +"\\n" ;
                    }
                }
                var data = cellName + "\\n" + delay + "\\n" + time + "\\n";
                alert(data);
            }
        </script>
    """
    )
    with open("../output/" + designName + "/schematics/" + path + ".svg", "a") as f:
        f.write(jsScript)

    os.system(
        "mv ../output/"
        + designName
        + "/schematics/"
        + path
        + ".svg ../output/"
        + designName
        + "/schematics/"
        + path
        + ".html"
    )
    return


##########################################################################################

def generate_website(numberOfPaths):
    path = "../schematics/"+ "path"
    html= '''
    <html>
  <head>
    <title>interactive_SVG_schematics</title>
  </head>
  <body>

    <h1 id="interactive_svg_schematics">interactive_SVG_schematics</h1>
    <h2 id="examples">Examples</h2>
    <ul>
'''

    path_format = '''    <li><a href="link">name</a></li>'''
    for i in range(numberOfPaths):
        path_html = copy.copy(path_format)
        html +=  path_html.replace("link", path +str(i)+".html").replace("name", "Path_"+str(i)) + "\n"

    html += ''''
    
    </ul>
    
  </body>
</html>'''

    with open("../output/" + designName + "/website/website"+".html", "w") as f:
        f.write(html)

def get_json_blackbox_cells():
    json_blackbox_modules = {}
    for i in range(len(blackboxCells)):
        sub_module={}
        ports= {}
        
        sub_module['attributes']= {
                                    "blackbox": "00000000000000000000000000000001",
                                    }
        
        for pin in blackboxCells[i].pins:
            ports[pin.name] = {
                                "direction": pin.type,
                                "bits": [0]
                                }
        sub_module['ports']= ports
        json_blackbox_modules[blackboxCells[i].name] = sub_module
    
    return json_blackbox_modules
        

def json_from_report(critica_path, path, json_blackbox_modules):
        
    modules = {"modules": {}}
    modules["modules"].update(json_blackbox_modules)
    
    top_module ={
                "top": {
                    "attributes": {
                        "top": "00000000000000000000000000000001"
                    },
                    "cells": {},
                    "netnames": {},      
                    "ports": {}
                    }
                }
    
    ports = {
                "clk": {
                    "direction": "input",
                    "bits": [ -2 ]
                    },
                "out": {
                    "direction": "output",
                    "bits": [ -1 ]
                    }
                }
    
    top_module["top"]["ports"].update(ports)
    
    for i in range(len(critica_path)):
        cell = {}
        cell[critica_path[i].id] = {
                                    "type": critica_path[i].name,
                                    "attributes": {
                                        "module_not_derived": "00000000000000000000000000000001",
                                    },
                                    "port_directions": {},
                                    "connections": {}
                                    }
        for pin in critica_path[i].pins:
            connection_number = copy.copy(pin.net)
            #print(connection_number)
            if ("clk" in connection_number  ):
                connection_number = -2
            elif ("out" in connection_number):
                connection_number = -1
            else:
                connection_number = int(connection_number.replace("net",""))
                
            cell[critica_path[i].id]["connections"][pin.name] = [connection_number]
            cell[critica_path[i].id]["port_directions"][pin.name] = pin.type
        top_module["top"]["cells"].update(cell)
        
    for i in range(no_nets):
        net ={
                "net"+str(i): {
                    "bits": [ i ],
                    "hide_name": 0,
                } 
            }
        top_module["top"]["netnames"].update(net)
        
    modules["modules"].update(top_module)
    
    with open("../output/" + designName + "/json/" + path + ".json", "w") as jsonfile:
        json.dump(modules, jsonfile,indent=4)


def generate_dirs(designName):
    if not os.path.exists("../output/" + designName):
        os.makedirs("../output/" + designName)
        
    if not os.path.exists("../output/" + designName + "/schematics"):
        os.makedirs("../output/" + designName + "/schematics")

    if not os.path.exists("../output/" + designName + "/json"):
        os.makedirs("../output/" + designName + "/json")
        
    if not os.path.exists("../output/" + designName + "/website"):
        os.makedirs("../output/" + designName + "/website")
    




# Main Class
def main(argv):

    staReportFile = ""
    skinFile = ""
    numberOfPaths = 0

    try:
        opts, args = getopt.getopt(argv, "i:s:h:n:", ["ifile=", "sfile=", "help", "npaths"])
    except getopt.GetoptError:
        print("invalid arguments!")
        print("run: python3 interactive_SVG_schematics.py -i <staReportFilePath> -s <skinFilePath>\n")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("run: python3 interactive_SVG_schematics.py -i <staReportFilePath> -s <skinFilePath>\n")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            staReportFile = arg
        elif opt in ("-s", "--sfile"):
            skinFile = arg
        elif opt in ("-n", "--npaths"):
            numberOfPaths = int(arg)


    start = time.time()

    if not os.path.exists("../output"):
        os.makedirs("../output")
    global designName
    designName = copy.copy(staReportFile)
    designName = designName.split("/")[-1]
    designName = designName.split(".")[0]
    
    generate_dirs(designName)
    
    get_all_paths_in_report(staReportFile)
    
    if numberOfPaths==0:
        numberOfPaths = len(criticalPaths)
    
    json_blackbox_modules = get_json_blackbox_cells()
    
    for i in range(numberOfPaths):
        json_from_report(criticalPaths[i], "path" + str(i), json_blackbox_modules)
        generate_SVG_from_JSON("path" + str(i), skinFile)
        addInteraction("path" + str(i), i)
        
        #print(i)
        
    generate_website(numberOfPaths)

    end = time.time()
    print("time taken: ", end - start)
    
if __name__ == "__main__":
    main(sys.argv[1:])
