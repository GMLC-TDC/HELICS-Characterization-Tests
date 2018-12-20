#======================================== commands to run the scripts ==================================================================#
#commands to run the json & runner-creator -  python Json_create.py 10 1 1 4 10 30 zmq
#commands to run the helics runner - time -p helics run --path /to/config_runner.json
#=======================================================================================================================================#
import helics as h
import sys 
import os
import json
import random
import shutil
from json_tricks import loads
from json_tricks import dumps
from json_tricks import dump

cwd = os.getcwd()
test = os.listdir(cwd)

for item in test:
    if item.endswith(".json"):
        os.remove(os.path.join(cwd, item))
        
shutil.rmtree("log_files", ignore_errors=True)
#===============================================Input arguments and variable initializations ===========================================#
federate_number=int(sys.argv[1])   #input -- Federate number
message_number=int(sys.argv[2])    #input -- number of federate messages
number_bytes = int(sys.argv[3])    #input -- number of bytes of the message
comb_number = int(sys.argv[4])     #input -- number of connections
update_interval=float(sys.argv[5]) #input -- update interval
time_stop=float(sys.argv[6])       #stop time
core_type=str(sys.argv[7])         #input -- core type 

sub_name=[]
pub_name=[]
fed={}
federatedata = []
temp = 0

#========================================================================================================================================#
#                                       Creating JSON Scripts for the Sender federate
#========================================================================================================================================#

#====================================== Getting publication and subscription names for the federates ===========================================#
for i in range (0, federate_number):
    pub_name.append("Fed%s" %(i+1))
    for j in range (0, comb_number):
        if (i+1+(j+1) <= federate_number):
            sub_name.append("Fed%s" %(i+1+(j+1)))
        elif (i+1+(j+1) > federate_number):
            sub_name.append("Fed%s" %((i+1+(j+1)-federate_number)))
            
#print(pub_name)
#print(sub_name)            


#================================= JSON dump is done through class instance objects for federates =================================#
for i in range(0, federate_number):    
    class Federate(object):
        
        def __init__(self, name, log_level, uninterruptible, coreType, coreInit, timeDelta, period):
        
            self.name = name
            self.log_level = log_level
            self.uninterruptible = uninterruptible
            self.coreType = coreType
            self.coreInit = coreInit
            self.timeDelta = timeDelta
            self.period = period
            self.publications =[]
            self.subscriptions =[]
            for j in range (0, message_number):
                self.publications.append({"key": "%s_message%s" %(pub_name[i], j+1), "global" : True})
                for k in range (temp, temp+comb_number):       
                    self.subscriptions.append({"key": "%s_message%s" %(sub_name[k], j+1), "required" : True})
            
        def toJson(self):
            '''
            Serialize the object custom object
            '''
            return json.dumps(self, default=lambda o: o.__dict__, 
                    sort_keys=False, indent=4)  
    
# creating federate objects                          
    fed[i] = Federate("Test%sFed" %(i+1), 5, False, core_type, "1", update_interval, update_interval) 
    federatedata.append(json.loads(fed[i].toJson()))

    temp=temp+comb_number
    
## json.dumps() method turns a Python data structure into JSON:
#jsonData = dumps(federatedata, indent=4)
#print(jsonData)
#========================================================================================================================================#

# Writing JSON data into a file called JSONData_federatenumber.json for sender federates
# Use the method called json.dump()
for i in range(0, federate_number):
    with open('fed_%s.json' %(i+1), 'w') as f:
       json.dump(federatedata[i], f, indent=4)
   
#============================================================================================================================================#
#                                  Creating helics runner script - Config_runner.json
#============================================================================================================================================#

filepath = os.path.join(cwd +'/log_files', 'config_runner.json')
if not os.path.exists(cwd +'/log_files'):
    os.makedirs(cwd +'/log_files')
file = open(filepath, "w")

## config_runner.json writing
file.write('{\n')
file.write('    "broker": false,\n')
file.write('    "federates":[\n')
#configuring the federates
for i in range (0, federate_number):
	  file.write('        {\n')
	  file.write('            "directory":"%s/",\n'%(cwd))
	  file.write('            "exec":"python federate.py %s %s %s fed_%s.json &",\n' %(number_bytes, update_interval, time_stop, i+1))
	  file.write('            "host":"localhost",\n')
	  file.write('            "name":"PythonTest%sFederate"\n' %(i+1))
	  if (i == (federate_number-1)):
           file.write('        }\n')
	  else: 
           file.write('        },\n') 
			
file.write('\n')
file.write('    ],\n')
file.write('    "name":"Federate_Generator"\n')
file.write('}\n')
   
    
#=========================================================================================================================================#

