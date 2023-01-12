import json
import sys, getopt
import re
import os
import copy
criticalPathCells = []
allPaths = []

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

def generatePathsInJSON(data, path, index, topModuleName, outputJSONfile):
    
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
    with open("./pathsJSON/"+outputJSONfile+"_"+str(index)+".json", "w") as outfile:
        outfile.write(json_object)

    








#################################################################
###########################################################################
# Main Class
def main(argv):
    staReportFile = "/Users/youssef/Documents/Work/AUC_Open_Hardware_Lab/netlistsvgForSky130/report.txt"
    inputJSONfile = ''
    outputJSONfile = ''
    
    try:
        opts, args = getopt.getopt(argv,"hr:i:o:",["rfile=","ifile=","ofile="])
    except getopt.GetoptError:
        print ('invalid arguments!')
        print ('extract_critical_path.py -r <staReportFile.txt> -i <inputFile.json> -o <outputFile.json>')
        sys.exit(2)
        
        
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print ('To use this tool you need to: \n')
            print ('1- Run STA report using OpenSTA: \n')
            print ('    * Get the report for the critical path like this \n')
            print ('    * report_checks -path_delay max > ./report.txt \n')
            print ('2- Extract the JSON file for you design using Yosys \n')
            print ('3- Input the above files + the output file paths in the arguments \n')
            print ('Follow the command description: \n')
            print ('python3 extract_critical_path.py -r <staReportFile.txt> -i <inputFile.json> -o <outputFile.json>\n')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputJSONfile = arg
        elif opt in ("-o", "--ofile"):
            outputJSONfile = arg
        elif opt in ("-r", "--rfile"):
            staReportFile = arg
            
  
    get_all_paths_in_report(staReportFile)
    if len(allPaths) >0:
        Exists = os.path.exists("./pathsJSON")
        if not Exists:
            os.mkdir("./pathsJSON")
        topModuleName = 'i2c_master'


        for path in allPaths:
            f = open(inputJSONfile)
            data = json.load(f)
            index = 0
            print ("hetre")
            index+=1
            generatePathsInJSON(copy.copy(data), path, index,topModuleName, outputJSONfile)


if __name__ == "__main__":
   main(sys.argv[1:])