import json
import sys, getopt
import re
import os
import copy
criticalPathCells = []
allPaths = []
index = 0




def generateJSON(inputGateLevel, designName):
    
    with open("./generateJSON.ys", "w") as f:

        f.write(
                """
read_liberty -lib -ignore_miss_dir -setattr blackbox sky130_fd_sc_hd.lib 
read_verilog """ + inputGateLevel + """
prep -top """ + designName + """
flatten
prep -top """ + designName + """
write_json """ + designName + """.json
                """
        )
    os.system("yosys generateJSON.ys")

#######


def generateSTAreport(inputGateLevel, designName):
    
    with open("./sta.tcl", "w") as f:

        f.write(
                """set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um
read_liberty sky130_fd_sc_hd.lib
read_verilog """+inputGateLevel+"""
link_design """+designName+"""
create_clock -name clk -period 20 sys_clk
report_checks -path_delay min_max  -format full> ./staReport.txt
# Exit OpenSTA shell
exit
                """
        )
    os.system("sta -no_splash ./sta.tcl")

#######

def get_offset(line):
    offset= re.search(r'\b(Delay)\b', line)
    return offset.start()
    
    
def get_all_paths_in_report(staReportFile):
    f = open(staReportFile, "r+")
    pathStartPoint= ""
    pathEndPoint= ""
    processingPath= False
    tempPath=[]
    offset = 0
    for line in f:
        line = line[offset:]
        line = line.strip()
        if "Delay" in line: 
            offset = get_offset(line)  
        elif "Startpoint" in line:
            pathStartPoint = line.split("_")
            pathStartPoint = pathStartPoint[1]
            processingPath= True
            tempPath.clear()
        elif "Endpoint" in line:
            pathEndPoint = line.split("_")
            pathEndPoint = pathEndPoint[1]
        elif(processingPath):
            if "data arrival time" in line :
                print("here")
                allPaths.append(copy.copy(tempPath))
                processingPath = False
                offset = 0
            elif('/' in line):
                cell = []
                line = line.split(' ')
                line  = list(filter(None, line))
                delay = line[0] 
                time = line[1]
                line.pop()
                cellNameAndPin= line.pop()
                cellName = cellNameAndPin.split('/')
                cellName = cellName[0]
                cell.append(cellName)
                cell.append(cellNameAndPin)
                cell.append(delay)
                cell.append(time)
                tempPath.append(cell)
    return 

########################################################
def is_not_a_critical_cell(cell, path):
    flag= True
    for criticalPathCell in path:
        if (criticalPathCell[0] == cell):
            flag= False
    return flag


########################################################

def generatePathsInJSON(data, path, i, topModuleName, outputJSONfile):
    
    modules = data['modules']
    topModule= modules[topModuleName]
    cells = topModule['cells']
    remove_cell_list=[]

    for cell in cells:
        if (is_not_a_critical_cell(cell,path)):
            remove_cell_list.append(cell)
        else:
            print(cell)
            
    for remove_cell in remove_cell_list:
        
        cells.pop(remove_cell, None)


    #print(modules[topModuleName]['cells'])
    json_object = json.dumps(data, indent=4)
    with open("./pathsJSON/"+outputJSONfile+"_"+str(i)+".json", "w") as outfile:
        outfile.write(json_object)

########################################################

def extractCriticalPath(inputJSONfile,outputJSONfile):
    
    staReportFile= "./staReport.txt"
    global index
    get_all_paths_in_report(staReportFile)
    if len(allPaths) >0:
        Exists = os.path.exists("./pathsJSON")
        if not Exists:
            os.mkdir("./pathsJSON")
        topModuleName = 'i2c_master'


        for path in allPaths:
            f = open(inputJSONfile)
            data = json.load(f)

            print ("hetre")
            index+=1
            generatePathsInJSON(copy.copy(data), path, index,topModuleName, outputJSONfile)
            
########################################################

def createNstlistSVGSchematics(path):
    for i in range(index):
        #os.system("netlistsvg " + wholeDesign)
        #addInteraction("wholeDesign")
        
        os.system("netlistsvg ./pathsJSON/" + path+"_"+ str(i+1)+".json")
        addInteraction( path + str(i+1), i)
        
        
def addInteraction(design, i):
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
        
        print(jsScript)
        with open("out.svg", "a") as f:
            f.write(jsScript)
            
        os.system("mv out.svg ./pathsJSON/"+design+".html")
         

#############
# Main Class
def main(argv):
    inputGateLevel = ''
    designName = ''
    
    try:
        opts, args = getopt.getopt(argv,"d:n:",["dfile=","nfile="])
    except getopt.GetoptError:
        print ('invalid arguments!')
        print ('extract_critical_path.py -r <staReportFile.txt> -i <inputFile.json> -o <outputFile.json>')
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print ('python3 genrate_interactive_schematics.py -d <gateLevelDesign.v> -n <design Name>\n')
            sys.exit()
        elif opt in ("-d", "--dfile"):
            inputGateLevel = arg
        elif opt in ("-n", "--nfile"):
            designName = arg

    print(inputGateLevel, designName)
    generateJSON(inputGateLevel, designName)
    generateSTAreport(inputGateLevel, designName)
    extractCriticalPath(designName+".json", designName+"_path")
    createNstlistSVGSchematics( designName+"_path")
 
if __name__ == "__main__":
   main(sys.argv[1:])