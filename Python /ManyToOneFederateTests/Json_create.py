#======================================== commands to run the scripts ==================================================================#
#commands to run the json & runner-creator -  python Json_create.py 10 1 1 10 30 zmq
#commands to run the helics runner - time -p helics run --path /home/kris756/HELICS_scalability_tests/JSON_scriptgenerator/log_files/config_runner.json
#=======================================================================================================================================#

import sys 
import os
import json
from json_tricks import loads
from json_tricks import dumps
from json_tricks import dump

#===============================================Input arguments and variable initializations ===========================================#
sender_number=int(sys.argv[1])     #input --  sender number
message_number=int(sys.argv[2])    #input -- number of sender message
number_bytes = int(sys.argv[3])    #input -- value
update_interval=float(sys.argv[4]) #input -- update interval
time_stop=float(sys.argv[5])       # stop time
core_type=str(sys.argv[6])

sub_name=[]
pub_name=[]
sub_name_echo=[]
pub_name_echo=[]
value_pub_echo=[]
value_sub_echo=[]
fed={}
federatedata = []
#========================================================================================================================================#
#                                       Creating JSON Scripts for the Sender federate
#========================================================================================================================================#

#====================================== Getting publication and subscription names for sender ===========================================#
for i in range (0, sender_number):
    pub_name.append("Test%stoTestR" %(i+1))
    sub_name.append("TestRtoTest%s" %(i+1))

#================================= JSON dump is done through class instance objects for sender federates=================================#
for i in range(0, sender_number):    
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
                self.subscriptions.append({"key": "%s_message%s" %(sub_name[i], j+1), "required" : True})
            
        def toJson(self):
            '''
            Serialize the object custom object
            '''
            return json.dumps(self, default=lambda o: o.__dict__, 
                    sort_keys=False, indent=4)  
    
# creating federate objects                          
    fed[i] = Federate("PythonTest%stoTestRFederate" %(i+1), 5, False, core_type, "1", update_interval, update_interval) 
    federatedata.append(json.loads(fed[i].toJson()))

## json.dumps() method turns a Python data structure into JSON:
#jsonData = dumps(federatedata, indent=4)
#print(jsonData)
#========================================================================================================================================#

# Writing JSON data into a file called JSONData_federatenumber.json for sender federates
# Use the method called json.dump()
for i in range(0, sender_number):
    with open('JSONData_Fed%s.json' %(i+1), 'w') as f:
       json.dump(federatedata[i], f, indent=4)

#========================================================================================================================================#
#                                       Creating JSON Scripts for the Echo federate
#========================================================================================================================================#
    
#=========================================== Getting publication and subscription names for echoer ======================================#
for i in range (0, sender_number):
    pub_name_echo.append("TestRtoTest%s" %(i+1))
    sub_name_echo.append("Test%stoTestR" %(i+1))
        
for l in range (0, sender_number):    
    for m in range (0, message_number):
        value_pub_echo.append("%s_message%s" %(pub_name_echo[l], m+1))
        value_sub_echo.append("%s_message%s" %(sub_name_echo[l], m+1))
        
#==================================== JSON dump is done through class instance objects for Echo federate=================================# 
class EchoFederate(object):
    
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
        for i in range (0, len(value_pub_echo)):
            self.publications.append({"key": value_pub_echo[i], "global" : True})
            self.subscriptions.append({"key": value_sub_echo[i], "required" : True})
        #print(i)    
        
    def toJson(self):
        '''
        Serialize the object custom object
        '''
        return json.dumps(self, default=lambda o: o.__dict__, 
                sort_keys=False, indent=4)  

# creating federate objects                          
echofed = EchoFederate("PythonTestRFederate", 5, False, core_type, "1", update_interval, update_interval) 
echofederatedata =json.loads(echofed.toJson())

## json.dumps() method turns a Python data structure into JSON:
#EchojsonData = dumps(echofederatedata, indent=4)
#print(EchojsonData)
#============================================================================================================================================#

# Writing JSON data into a file called JSONData_EchoFed.json for Echo federate
# Use the method called json.dump()
with open('JSONData_EchoFed.json', 'w') as f:
   json.dump(echofederatedata, f, indent=4)    
   
#============================================================================================================================================#
#                                  Creating helics runner script - Config_runner.json
#============================================================================================================================================#

cwd = os.getcwd()
dir=cwd +'/log_files/config_runner.json'
file = open(dir, "w")

#config_echoer
file.write('{\n')
file.write('    "broker": false,\n')
file.write('    "federates":[\n')
file.write('        {\n')
file.write('            "directory":"%s/",\n'%(cwd))
file.write('            "exec":"python echoer.py %s %s %s JSONData_EchoFed.json &",\n' %(sender_number, time_stop, core_type))
file.write('            "host":"localhost",\n')
file.write('            "name":"PythonTestRFederate"\n')
file.write('        },\n')

#configuring the senders
for i in range (0, sender_number):
	  file.write('        {\n')
	  file.write('            "directory":"%s/",\n'%(cwd))
	  file.write('            "exec":"python sender.py %s %s %s JSONData_Fed%s.json &",\n' %(number_bytes, update_interval, time_stop, i+1))
	  file.write('            "host":"localhost",\n')
	  file.write('            "name":"PythonTest%stoTestRFederate"\n' %(i+1))
	  if (i == (sender_number-1)):
           file.write('        }\n')
	  else: 
           file.write('        },\n') 
			
file.write('\n')
file.write('    ],\n')
file.write('    "name":"Federate_Generator"\n')
file.write('}\n')

#=========================================================================================================================================#


