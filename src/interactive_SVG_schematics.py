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

##########################################################################################


criticalPathCells = []
allPaths = []
criticalPaths = []
blackboxCells = []

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


def manage_net_names(tempCriticalPath):
    for i in range(0, len(tempCriticalPath) - 1):
        if tempCriticalPath[i].isEndSectionOne == True:
            tempCriticalPath[i].pins.append(Pin("out", "net" + str(i), "output"))
        else:
            tempCriticalPath[i].pins[1].net = "net" + str(i)
            tempCriticalPath[i + 1].pins[0].net = "net" + str(i)

    for cell in tempCriticalPath:
        add_blackbox_cell(cell)

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
        print(counter)
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
            elif "data required time" in line:
                for cell in tempCriticalPath:
                    add_blackbox_cell(cell)
                allPaths.append(copy.deepcopy(tempPath))
                criticalPaths.append(copy.deepcopy(tempCriticalPath))
                processingPath = False
                offset = 0
                wire = 0
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


def write_verilog_from_path(critica_path, path):
    if not os.path.exists("../output/" + designName + "/verilog"):
        os.makedirs("../output/" + designName + "/verilog")
    with open("../output/" + designName + "/verilog/" + path + ".v", "w") as f:
        f.write("""module top (input clk, output out);\n""")
        # for i in range(len(critica_path) ):
        #    f.write("""\nwire net""" + str(i) + """;""")

        for i in range(len(critica_path)):
            f.write(
                """\n\n"""
                + critica_path[i].name
                + """ """
                + critica_path[i].id
                + """("""
            )
            for pin in critica_path[i].pins:
                f.write(""".""" + pin.name + """(""" + pin.net + """), """)

            f.write(""");""")

        ## writing output pin
        f.write("""\nassign out = net_out ;\nendmodule\n\n""")

        for cell in blackboxCells:
            f.write("""\n\n(* blackbox *)\n module """ + cell.name + """ (""")
            for pin in cell.pins:
                f.write(""" """ + pin.type + """ """ + pin.name + """,""")

            f.write(""");\nendmodule""")

    return


##########################################################################################


def test_print():
    for criticalPath in criticalPaths:
        for standardCell in criticalPath:
            print(standardCell.id, standardCell.name, len(standardCell.pins))
            for pin in standardCell.pins:
                print("     ", pin.name, pin.net)
        print("\n\n\n")
    return


##########################################################################################


def generate_JSON_from_verilog(path):
    if not os.path.exists("../output/" + designName + "/scripts"):
        os.makedirs("../output/" + designName + "/scripts")

    if not os.path.exists("../output/" + designName + "/json"):
        os.makedirs("../output/" + designName + "/json")

    with open("../output/" + designName + "/scripts/generateJSON.ys", "w") as f:
        f.write(
            """
read_verilog ../output/"""
            + designName
            + """/verilog/"""
            + path
            + """.v
hierarchy -check -top top
proc 
write_json ../output/"""
            + designName
            + """/json/"""
            + path
            + """.json
                """
        )
    os.system("yosys ../output/" + designName + "/scripts/generateJSON.ys")
    return


##########################################################################################


def generate_SVG_from_JSON(path, skinfile):
    if not os.path.exists("../output/" + designName + "/schematics"):
        os.makedirs("../output/" + designName + "/schematics")
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

# Main Class
def main(argv):

    staReportFile = ""
    skinFile = ""

    try:
        opts, args = getopt.getopt(argv, "i:s:", ["ifile=", "sfile="])
    except getopt.GetoptError:
        print("invalid arguments!")
        print("run: python3 interactive_SVG_schematics.py -i <staReportFilePath>\n")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("run: python3 interactive_SVG_schematics.py -i <staReportFilePath>\n")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            staReportFile = arg
        elif opt in ("-s", "--sfile"):
            skinFile = arg

    if not os.path.exists("../output"):
        os.makedirs("../output")
    global designName
    designName = copy.copy(staReportFile)
    designName = designName.split("/")[-1]
    designName = designName.split(".")[0]
    get_all_paths_in_report(staReportFile)
    for i in range(5):
        if not os.path.exists("../output/" + designName):
            os.makedirs("../output/" + designName)
        write_verilog_from_path(criticalPaths[i], "path" + str(i))
        generate_JSON_from_verilog("path" + str(i))
        generate_SVG_from_JSON("path" + str(i), skinFile)
        addInteraction("path" + str(i), i)
        print(i)

    print(designName)
    #


if __name__ == "__main__":
    main(sys.argv[1:])
