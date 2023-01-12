import os
import re
import copy
##########################################################################################


criticalPathCells = []
allPaths = []
criticalPaths=[]
##########################################################################################


class Pin:
    def __init__(self, name, net):
        self.name=name
        self.net=net
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
    for line in f:
        line = line[offset:]
        line = line.strip()
        if "Delay" in line: 
            offset = get_offset(line)  
        elif "Startpoint" in line:
            processingPath= True
            tempPath.clear()
            tempCriticalPath.clear()
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
                cellId = cellInfo[0]
                pinName = cellInfo[1]
                
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

                    
                _pin = Pin(pinName, _net)

                
                _standardCell.addPin(copy.deepcopy(_pin))
    
                add_cell_to_path(_standardCell, tempCriticalPath)
    
    return 
##########################################################################################

def write_verilog_from_path(critica_path, path):
    if not os.path.exists("./../verilog"):
        os.makedirs("./../verilog")
    with open("./../verilog/"+path+".v", "w") as f:
        f.write("""module top (input clk, output out);\n""")
        for i in range(len(critica_path)-1):
            f.write("""\nwire net"""+ str(i) +""";""")
            
        for cell in critica_path:
            f.write("""\n\n"""+cell.name +""" """+ cell.id +"""(""")
            for pin in cell.pins:
                f.write("""."""+pin.name+"""("""+ pin.net +"""), """)
                
            f.write(""");""")   
            
        f.write("""assign out = """+critica_path[-1].pins[0].net+""";\nendmodule""")
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
    if not os.path.exists("./../scripts"):
        os.makedirs("./../scripts")
        
    if not os.path.exists("./../json"):
        os.makedirs("./../json")
        
    with open("./../scripts/generateJSON.ys", "w") as f:
        f.write(
                """
read_liberty -lib -ignore_miss_dir -setattr blackbox ./../../lib/sky130_fd_sc_hd.lib 
read_verilog ./../verilog/""" + path + """.v
prep -top top
flatten
prep -top top
write_json ./../json/""" + path + """.json
                """
        )
    os.system("yosys ./../scripts/generateJSON.ys")
    return
##########################################################################################

def generate_SVG_from_JSON(path):
    if not os.path.exists("./../schematics"):
        os.makedirs("./../schematics")
    os.system("netlistsvg ./../json/"+path+".json -o ./../schematics/"+path+".svg")
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
    with open("./../schematics/"+path+".svg", "a") as f:
        f.write(jsScript)
        
    os.system("mv ./../schematics/"+path+".svg ./../schematics/"+path+".html")
    return
##########################################################################################

# Main Class
def main():
    staReportFile = "./../../sta_reports/timing_path.txt"
    get_all_paths_in_report(staReportFile)
    for i in range(len(criticalPaths)):
        write_verilog_from_path(criticalPaths[i], "path"+str(i))
        generate_JSON_from_verilog("path"+str(i))
        generate_SVG_from_JSON("path"+str(i))
        addInteraction("path"+str(i), i)
    
    #test_print()
if __name__ == "__main__":
   main()