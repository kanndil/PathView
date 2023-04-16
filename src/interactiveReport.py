#
# Copyright 2023 AUC Open Source Hardware Lab
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
import xml.etree.ElementTree as ET

##########################################################################################

pathCellsDelays = []
criticalPaths = []
blackboxCells = []
pathNames = []
netDelays = []

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


def checkArgs(argv, staReportFile, skinFile, numberOfPaths, sortType):

    try:
        opts, args = getopt.getopt(
            argv, "i:s:h:n:", ["ifile=", "sfile=", "help", "npaths=", "sort="]
        )
    except getopt.GetoptError:
        print("invalid arguments!")
        print(
            """
Syntax:
    run: python3 interactiveReport.py -i <staReportFilePath> -s <skinFilePath>\n

Options:
    -n <numberOfPaths>
                        This option is used to specify the number of paths to be
                        generated. If this option is not specified, all paths are
                        generated.
                        
    --sort=<asc/desc>
                        This option is used to sort the paths in ascending 
                        or descending order based on slack. 
                        "asc" for ascending and "desc" for descending order.
                        
"""
        )
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(
                """
Syntax:
    run: python3 interactiveReport.py -i <staReportFilePath> -s <skinFilePath>\n

Options:
    -n <numberOfPaths>
                        This option is used to specify the number of paths to be
                        generated. If this option is not specified, all paths are
                        generated.
                        
    --sort=<asc/desc>
                        This option is used to sort the paths in ascending 
                        or descending order based on slack. 
                        "asc" for ascending and "desc" for descending order.
                        
"""
            )
            sys.exit()
        elif opt in ("-i", "--ifile"):
            staReportFile = arg
        elif opt in ("-s", "--sfile"):
            skinFile = arg
        elif opt in ("-n", "--npaths="):
            numberOfPaths = int(arg)
        elif opt in ("--sort="):
            sortType = arg

    return staReportFile, skinFile, numberOfPaths, sortType


#################################


def generate_dirs(designName):

    if not os.path.exists("../output"):
        os.makedirs("../output")

    if not os.path.exists("../output/" + designName):
        os.makedirs("../output/" + designName)

    if not os.path.exists("../output/" + designName + "/schematics"):
        os.makedirs("../output/" + designName + "/schematics")

    if not os.path.exists("../output/" + designName + "/json"):
        os.makedirs("../output/" + designName + "/json")

    if not os.path.exists("../output/" + designName + "/website"):
        os.makedirs("../output/" + designName + "/website")


#################################


def generateNetInteractions(path):
    filename = "../output/" + designName + "/schematics/" + path + ".svg"
    tree = ET.parse(filename)
    root = tree.getroot()

    # Find all line elements
    lines = root.findall(".//{http://www.w3.org/2000/svg}line")
    netInteractions = "\n"
    for line in lines:
        classline = line.get("class")
        if "net_" in classline:
            # Get XML code for line element
            classline = classline.split(" ")
            classline = classline[0]
            classline = classline.split("_")
            classline = classline[1]
            temp = ""
            index = int(classline)
            if index == -2:
                temp = 'onClick="net_click(this.id)" id="' + str(0) + '" class="net'
            elif index == -1:
                continue
            else:
                temp = (
                    'onClick="net_click(this.id)" id="'
                    + str(index + 1)
                    + '" class="net'
                )
            newstyle = "stroke: white; opacity: 0 ; stroke-width: 18;"
            lineheader = "line  "

            line_xml = ET.tostring(line, encoding="unicode")
            temp_string = line_xml.replace("stroke-width: 1", newstyle)
            temp_string = temp_string.replace('class="net_', temp)
            temp_string = temp_string.replace(
                'ns0:line xmlns:ns0="http://www.w3.org/2000/svg"', lineheader
            )
            netInteractions += temp_string + "\n"
    return netInteractions


def get_all_paths_in_report(staReportFile, no_nets):
    f = open(staReportFile, "r+")
    processingPath = False
    tempPathDelays = []
    tempNetDelays = []
    tempCriticalPath = []
    offset = 0
    counter = -1
    wire = 0
    net_index = -1
    _net = ""
    startPoint = "None"
    endPoint = "None"
    slack = "None"
    _pinType = "input"

    for line in f:
        line = line[offset:]
        line = line.strip()

        if "Delay" in line:
            offset = get_offset(line)

        elif "Startpoint" in line:
            counter += 1
            no_nets.append(2)
            startPoint = "None"
            endPoint = "None"
            slack = "None"
            startPoint = copy.copy(line)

            processingPath = True
            tempPathDelays.clear()
            tempNetDelays.clear()
            tempCriticalPath.clear()
            _pinType = "input"

        elif "Endpoint" in line:
            endPoint = copy.copy(line)

        elif "slack" in line:
            if startPoint != "None":
                slack = copy.copy(line)
                slack = slack.split(" ")
                slack = slack[0]
                pathNames.append([startPoint, endPoint, slack, counter])

        elif processingPath:
            if "data arrival time" in line:
                tempCriticalPath[-1].pins.append(Pin("out", "net_out", "output"))
                wire += 1
                net_index = -1
                _pinType = "input"

            elif "data required time" in line:
                for cell in tempCriticalPath:
                    add_blackbox_cell(cell)
                pathCellsDelays.append(copy.deepcopy(tempPathDelays))
                netDelays.append(copy.deepcopy(tempNetDelays))
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

                _standardCell = StandardCell(cellName, cellId)
                
                wirecopy = copy.copy(wire)

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
                
                _cell = []
                _cell.append(cellId)
                _cell.append(_pinType)
                _cell.append(delay)
                _cell.append(time)
                _cell.append(pinName)
                tempPathDelays.append(_cell)
                _standardCell.addPin(copy.deepcopy(_pin))
                
                if _pinType == "input":
                    no_nets[counter] += 1
                    _net_report = []
                    _net_report.append(delay)
                    _net_report.append(time)
                    tempNetDelays.append(_net_report)
                    _pinType = "output"
                else:
                    _pinType = "input"
                    


                _net = add_cell_to_path(_standardCell, tempCriticalPath)
                
                if _pinType == "input":
                    repeatednet= copy.copy(_net)
                    repeatednet =_net.split("net")
                    repeatednet = repeatednet[1]
                    repeatednetid = int(repeatednet)
                    if repeatednetid != wirecopy:
                        tempNetDelays[repeatednetid].append(delay)
                        tempNetDelays[repeatednetid].append(time)         
               

    return no_nets


##########################################################################################


def generate_SVG_from_JSON(path, skinfile):
    print(path)
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


def compareConsecutivePaths(index):

    if index < 1:
        return False

    if len(criticalPaths[index]) != len(criticalPaths[index - 1]):
        return False

    for i in range(len(criticalPaths[index])):

        if criticalPaths[index][i].name != criticalPaths[index - 1][i].name:
            return False

        if len(criticalPaths[index][i].pins) != len(criticalPaths[index - 1][i].pins):
            return False

        for j in range(len(criticalPaths[index][i].pins)):
            if (
                criticalPaths[index][i].pins[j].name
                != criticalPaths[index - 1][i].pins[j].name
            ):
                return False

    return True


def addInteraction(path, i, index, hrefs):

    html = (
        """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
  font-family: "Lato", sans-serif;
}

.sidenav {
  height: 100%;
  width: 160px;
  position: fixed;
  z-index: 1;
  top: 0;
  left: 0;
  background-color: #111;
  overflow-x: hidden;
  padding-top: 20px;
}

.sidenav a {
  padding: 6px 8px 6px 16px;
  text-decoration: none;
  font-size: 18px;
  color: #818181;
  display: block;
}

.sidenav a:hover {
  color: #f1f1f1;
}

.main {
  margin-left: 160px; /* Same as the width of the sidenav */
  font-size: 28px; /* Increased text to enable scrolling */
  padding: 0px 10px;
}

@media screen and (max-height: 450px) {
  .sidenav {padding-top: 15px;}
  .sidenav a {font-size: 18px;}
}
</style>
</head>
<body>

<div class="main">

<h2>Interactive SVG Schematics</h2>

<h4> Path: """
        + str(i + 1)
        + """</h4>

<h5>"""
        + pathNames[i][0]
        + """</h5>
        
<h5>"""
        + pathNames[i][1]
        + """</h5>

<h5>Slack: """
        + pathNames[i][2]
        + """</h5>
    """
    )
    jsScript = (
        """ 
    
</div>
   
</body>
</html> 


        <script type="text/javascript">
            function reply_click(id)
            {
                const cells = """
        + str(pathCellsDelays[index])
        + """ ;
        
                var cellName = "";
                var logicpath= "";
                var clkpath= "";
                var count=0;
                var data = "";
                var flag = 0;
                var parent = document.getElementById(id);
                var child = parent.querySelector("#flipflop");
                if (child !== null) {
                    flag =1;
                    for (let i = 0; i < cells.length; i++) { 
                        if (("cell_" + cells[i][0]) == id ){
                            cellName = "Cell name: " + cells[i][0]+"\\n\\n";
                            if (cells[i][1] == "input"){
                                data += "\\tPin (" + cells[i][4] + ") arrival time = " + cells[i][3]+"\\n\\n";
                            } else {
                                data += "\\tDelay = " + cells[i][2] + "\\n";
                                data += "\\tPin (" + cells[i][4] +  ") time = " + cells[i][3] + "\\n";
                            }
                            count = count+1;
                        }
                    }
                  } else {
                    for (let i = 0; i < cells.length; i++) { 
                        if (("cell_" + cells[i][0]) == id ){
                            flag = 1
                            cellName = "Cell name: " + cells[i][0]+"\\n";
                            if (count < 2){
                                if (cells[i][1] == "input"){
                                    logicpath += "\\tPin (" + cells[i][4] + ") arrival time = " + cells[i][3]+"\\n\\n";
                                } else {
                                    logicpath += "\\tDelay = " + cells[i][2] + "\\n";
                                    logicpath += "\\tPin (" + cells[i][4] +  ") time = " + cells[i][3] + "\\n";
                                }
                            } else {
                                if (count == 3 ){
                                    logicpath = "\\nLogic Path: \\n" + logicpath ;
                                    clkpath = "\\nClock Path: \\n";
                                }
                                if (cells[i][1] == "input"){
                                    clkpath += "\\tPin (" + cells[i][4] + ") arrival time = " + cells[i][3]+"\\n\\n";
                                } else {
                                    clkpath += "\\tDelay = " + cells[i][2] + "\\n";
                                    clkpath += "\\tPin (" + cells[i][4] +  ") time = " + cells[i][3] + "\\n";
                                }
                                
                            }
                            data = logicpath + clkpath;
                            count = count+1;
                        }
                    }
                  }

                if (flag){
                    alert(cellName + data);
                }
            }
            
            function net_click(id)
            {
                const nets = """
        + str(netDelays[index])
        + """ ;
                var data = "net_" + id;
                var i = parseInt(id);
                if (nets[i].length == 2){
                    data += "\\n\\tdelay = " + nets[i][0];
                    data += "\\n\\ttime = " + nets[i][1] + "\\n";
                } else if (nets[i].length == 4){
                    data+= "\\n\\nLogic Path:"
                    data+= "\\n\\tdelay = " + nets[i][0];
                    data+= "\\n\\ttime = " + nets[i][1];
                    data+= "\\n\\nClock Path:"
                    data+= "\\n\\tdelay = " + nets[i][2];
                    data+= "\\n\\ttime = " + nets[i][3];
                }
                alert(data);
            }
            
        </script>
    """
    )

    netInteractions = generateNetInteractions(path)

    body = ""
    with open("../output/" + designName + "/schematics/" + path + ".svg", "r") as f:
        body = f.read()

    body = body.replace("</svg>", " ")
    with open("../output/" + designName + "/schematics/" + path + ".svg", "w") as f:
        f.write(html + hrefs + body + netInteractions + "</svg>" + jsScript)

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


def get_json_blackbox_cells():
    json_blackbox_modules = {}
    for i in range(len(blackboxCells)):
        sub_module = {}
        ports = {}

        sub_module["attributes"] = {
            "blackbox": "00000000000000000000000000000001",
        }

        for pin in blackboxCells[i].pins:
            ports[pin.name] = {"direction": pin.type, "bits": [0]}
        sub_module["ports"] = ports
        json_blackbox_modules[blackboxCells[i].name] = sub_module

    return json_blackbox_modules


def json_from_report(critica_path, path, json_blackbox_modules, index):

    modules = {"modules": {}}
    modules["modules"].update(json_blackbox_modules)

    top_module = {
        "top": {
            "attributes": {"top": "00000000000000000000000000000001"},
            "cells": {},
            "netnames": {},
            "ports": {},
        }
    }

    ports = {
        "clk": {"direction": "input", "bits": [-2]},
        "out": {"direction": "output", "bits": [-1]},
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
            "connections": {},
        }
        for pin in critica_path[i].pins:
            connection_number = copy.copy(pin.net)
            if "clk" in connection_number:
                connection_number = -2
            elif "out" in connection_number:
                connection_number = -1
            else:
                connection_number = int(connection_number.replace("net", ""))

            cell[critica_path[i].id]["connections"][pin.name] = [connection_number]
            cell[critica_path[i].id]["port_directions"][pin.name] = pin.type
        top_module["top"]["cells"].update(cell)

    for i in range(no_nets[index]):
        net = {
            "net"
            + str(i): {
                "bits": [i],
                "hide_name": 0,
            }
        }
        top_module["top"]["netnames"].update(net)

    modules["modules"].update(top_module)

    with open("../output/" + designName + "/json/" + path + ".json", "w") as jsonfile:
        json.dump(modules, jsonfile, indent=4)


def generate_href(numberOfPaths):
    hrefs = """<div class="sidenav">"""
    for j in range(numberOfPaths):
        hrefs += (
            """<a href="path"""
            + str(j)
            + """.html">Slack: """
            + pathNames[j][2]
            + """</a></li> """
        )
    hrefs += """</div>"""
    return hrefs


def sortPaths(sortType):

    if sortType == "desc":
        pathNames.sort(key=lambda x: float(x[2]), reverse=True)
    elif sortType == "asc":
        pathNames.sort(key=lambda x: float(x[2]))
    elif sortType == "none":
        pass


# Main Class
def main(argv):
    start = time.time()

    staReportFile, skinFile, numberOfPaths, sortType = checkArgs(
        argv, "", "", -1, "none"
    )
    global no_nets
    global designName
    no_nets = []

    designName = copy.copy(staReportFile)
    designName = designName.split("/")[-1]
    designName = designName.split(".")[0]

    generate_dirs(designName)

    no_nets = get_all_paths_in_report(staReportFile, no_nets)

    if (numberOfPaths < 0) or (numberOfPaths > len(criticalPaths)):
        numberOfPaths = len(criticalPaths)

    json_blackbox_modules = get_json_blackbox_cells()

    sortPaths(sortType)

    hrefs = generate_href(numberOfPaths)
    for i in range(numberOfPaths):
        json_from_report(
            criticalPaths[pathNames[i][3]],
            "path" + str(i),
            json_blackbox_modules,
            pathNames[i][3],
        )
        generate_SVG_from_JSON("path" + str(i), skinFile)
        addInteraction("path" + str(i), i, pathNames[i][3], hrefs)


    end = time.time()
    print("Time taken: ", (end - start) / 60.0)


if __name__ == "__main__":
    main(sys.argv[1:])
