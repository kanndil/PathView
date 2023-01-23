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

import os
import re
import copy
##########################################################################################


criticalPathCells = []
allPaths = []
criticalPaths=[]
blackboxCells = []

##########################################################################################


class Pin:
    def __init__(self, name, net, type):
        self.name=name
        self.net=net
        self.type=type
##############################

class StandardCell:
    def __init__(self, name, id):
        self.name=name
        self.id=id
        self.pins=[]
    def addPin(self, pin):
        self.pins.append(pin)
##########################################################################################


def get_offset(line):
    offset= re.search(r'\b(Delay)\b', line)
    return offset.start()
##############################


def add_cell_to_path(_standardCell, tempCriticalPath):
    flag= False
    for iterationCell in tempCriticalPath:
        if (_standardCell.id == iterationCell.id):
            flag == True
            # take care of deep copy
            iterationCell.pins.append(copy.deepcopy(_standardCell.pins[0]))
            return
        
    if  flag ==  False:
        tempCriticalPath.append(copy.deepcopy(_standardCell)) 
    return 
##############################
def add_pin_to_blackbox_cell(pin, cell):
    flag= False
    for iterationPin in cell.pins:
        if (pin.name == iterationPin.name):
            flag == True
            return
        
    if  flag ==  False:
        tempPin = Pin(copy.deepcopy(pin.name), "", copy.deepcopy(pin.type))
        cell.pins.append(copy.deepcopy(tempPin)) 
    return 

def add_blackbox_cell(_standardCell):
    flag= False
    for iterationCell in blackboxCells:
        if (_standardCell.name == iterationCell.name):
            flag == True
            # take care of deep copy
            for pin in _standardCell.pins:
                add_pin_to_blackbox_cell(pin, iterationCell)
            return
        
    if  flag ==  False:
        blackboxCells.append(copy.deepcopy(_standardCell)) 
    return 
##############################


def manage_net_names(tempCriticalPath):
    for i in range (0, len(tempCriticalPath)-1):
        tempCriticalPath[i].pins[1].net = "net" + str(i)
        tempCriticalPath[i+1].pins[0].net = "net" + str(i)
    return
##############################


def get_all_paths_in_report(staReportFile):
    f = open(staReportFile, "r+")
    processingPath= False
    tempPath=[]
    tempCriticalPath = []
    offset = 0
    net_index=0
    counter=0
    _pinType = "input"
    for line in f:
        counter+=1
        print(counter)
        #print(line)
        line = line[offset:]
        line = line.strip()
        if "Delay" in line: 
            offset = get_offset(line)  
        elif "Startpoint" in line:
            processingPath= True
            tempPath.clear()
            tempCriticalPath.clear()
            _pinType = "input"
        elif "Endpoint" in line:
            pass
        elif(processingPath):
            if "data arrival time" in line :
                manage_net_names(tempCriticalPath)
                allPaths.append(copy.deepcopy(tempPath))
                criticalPaths.append(copy.deepcopy(tempCriticalPath))
                processingPath = False
                offset = 0
                net_index = 0
            elif ("(net)" in line):
                pass
            elif('/' in line):
                _cell = []
                line = line.split('(')
                
                cellName = line[1]
                cellName =  cellName.split(')')
                cellName =  cellName[0]
                
                line = line[0]
                line = line.split(' ')
                line  = list(filter(None, line))
                delay = line[0] 
                time = line[1]
                
                cellNameAndPin= line.pop()
                cellInfo = cellNameAndPin.split('/')
                pinName = cellInfo[-1]
                cellInfo.pop()
                cellId = '_'.join(cellInfo)
                cellId = cellId.replace('.', '_')
                cellId = cellId.replace('[', '_')
                cellId = cellId.replace(']', '_')
                
                _cell.append(cellId)
                _cell.append(cellNameAndPin)
                _cell.append(delay)
                _cell.append(time)
                tempPath.append(_cell)
        
                _standardCell= StandardCell(cellName, cellId)
                
                _net = ""
                if net_index == 0:
                    _net = "clk "
                    net_index +=1
                    
                _pin = Pin(pinName, _net, _pinType)
                
                if (_pinType == "input"):
                    _pinType = "output"
                else:
                    _pinType = "input"

                
                _standardCell.addPin(copy.deepcopy(_pin))
    
                add_cell_to_path(_standardCell, tempCriticalPath)
                add_blackbox_cell(_standardCell)
    
    return 
##########################################################################################

def write_verilog_from_path(critica_path, path):
    if not os.path.exists("../output/"+designName+"/verilog"):
        os.makedirs("../output/"+designName+"/verilog")
    with open("../output/"+designName+"/verilog/"+path+".v", "w") as f:
        f.write("""module top (input clk, output out);\n""")
        for i in range(len(critica_path)-1):
            f.write("""\nwire net"""+ str(i) +""";""")
            
        for cell in critica_path:
            f.write("""\n\n"""+cell.name +""" """+ cell.id +"""(""")
            for pin in cell.pins:
                f.write("""."""+pin.name+"""("""+ pin.net +"""), """)
                
            f.write(""");""")   
            
        f.write("""assign out = """+critica_path[-1].pins[0].net+""";\nendmodule\n\n""")

        for cell in blackboxCells:
            f.write("""\n\n(* blackbox *)\n module """+cell.name +""" (""")
            for pin in cell.pins:
                f.write(""" """+pin.type+""" """+ pin.name +""",""")
                
            f.write(""");\nendmodule""")   
             
    return
##########################################################################################

def test_print():
    for criticalPath in criticalPaths:
        for standardCell in criticalPath :
            print(standardCell.id,standardCell.name, len(standardCell.pins))
            for pin in standardCell.pins:
                print("     ", pin.name, pin.net)
        print("\n\n\n")
    return
##########################################################################################

def generate_JSON_from_verilog(path):
    if not os.path.exists("../output/"+designName+"/scripts"):
        os.makedirs("../output/"+designName+"/scripts")
        
    if not os.path.exists("../output/"+designName+"/json"):
        os.makedirs("../output/"+designName+"/json")
        
    with open("../output/"+designName+"/scripts/generateJSON.ys", "w") as f:
        f.write(
                """
read_verilog ../output/"""+designName+"""/verilog/""" + path + """.v
prep -top top
write_json ../output/"""+designName+"""/json/""" + path + """.json
                """
        )
    os.system("yosys ../output/"+designName+"/scripts/generateJSON.ys")
    return
##########################################################################################

def generate_SVG_from_JSON(path):
    if not os.path.exists("../output/"+designName+"/schematics"):
        os.makedirs("../output/"+designName+"/schematics")
    os.system("netlistsvg ../output/"+designName+"/json/"+path+".json -o ../output/"+designName+"/schematics/"+path+".svg")
    return
##########################################################################################
       
def addInteraction(path, i):
    jsScript =''' 
        
        <script type="text/javascript">
            function reply_click(id)
            {
                const cells = '''+str(allPaths[i])+''' ;
                var cellName = "cell name is " ;
                var delay = "delay = " ;
                var time = "time = " ;
                for (let i = 0; i < cells.length; i++) { 
                    if (("cell_" + cells[i][0]) == id ){
                        data = "delay = " + cells[i][2];
                        cellName = "cell name is " + cells[i][0];
                        time = "time = " + cells[i][3]  ;
                    }
                }
                var data = cellName + "\\n" + data + "\\n" + time + "\\n";
                alert(data);
            }
        </script>
    '''
    #print(jsScript)
    with open("../output/"+designName+"/schematics/"+path+".svg", "a") as f:
        f.write(jsScript)
        
    os.system("mv ../output/"+designName+"/schematics/"+path+".svg ../output/"+designName+"/schematics/"+path+".html")
    return
##########################################################################################

# Main Class
def main():
    #staReportFile = "./../sta_reports/mprj-max.rpt"
    #staReportFile = "./../sta_reports/mprj-min.rpt"
    #staReportFile = "./../sta_reports/timing_path.txt"
    staReportFile ="./../sta_reports/prv32_cpu_min_max.rpt"
    
    if not os.path.exists("../output"):
        os.makedirs("../output")
    global designName 
    designName = copy.copy(staReportFile)
    designName= designName.split("/")[-1]
    designName= designName.split(".")[0]
    get_all_paths_in_report(staReportFile)
    for i in range(len(criticalPaths)):
        if not os.path.exists("../output/"+designName):
            os.makedirs("../output/"+designName)
        write_verilog_from_path(criticalPaths[i], "path"+str(i))
        generate_JSON_from_verilog("path"+str(i))
        generate_SVG_from_JSON("path"+str(i))
        addInteraction("path"+str(i), i)
    
    print(designName)
    
    #test_print()
    #len(criticalPaths)
if __name__ == "__main__":
   main()