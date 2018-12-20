#Created on Mon Nov 20, 2018
#@author: Gayathri krishnamoorthy

import time
import helics as h
import math
import sys
import scipy

number_bytes = int(sys.argv[1])    # input -- value
update_interval=float(sys.argv[2]) # input -- update interval
time_stop=float(sys.argv[3])       # input -- stop time
config_string=sys.argv[4]          # input -- configuration string

helicsversion = h.helicsGetVersion()
#print("SENDER: Helics version = {}".format(helicsversion))

#.............................................Create Federate ..................................#

vfed = h.helicsCreateValueFederateFromConfig(config_string)
status = h.helicsFederateRegisterInterfaces(vfed, config_string)
federate_name = h.helicsFederateGetName(vfed)
print("Federate {} has been registered".format(federate_name))
pubkeys_count = h.helicsFederateGetPublicationCount(vfed)
subkeys_count = h.helicsFederateGetInputCount(vfed)

pubid = {}
subid = {}
for i in range(0,pubkeys_count):
    pubid["m{}".format(i)] = h.helicsFederateGetPublicationByIndex(vfed, i)
for i in range(0,subkeys_count):
    subid["m{}".format(i)] = h.helicsFederateGetInputByIndex(vfed, i)


# Enter execution mode #
status = h.helicsFederateEnterExecutingMode(vfed)
print("SENDER: Entering execution mode")


#............................................. Main script ..................................#

this_time = 0.0
t=0.0
currenttime=0.0
time_step_latency = []

value=str()
for i in range (0, number_bytes):
	value=value+'1'
 

while (t < time_stop):

    start = time.time()
    
    t = t + update_interval
    currenttime = h.helicsFederateRequestTime(vfed, t)
    print("Request time is = {}".format(t))
    print("Granted time is {}".format(currenttime)) 

    for i in range (0, subkeys_count):
        sub = subid["m{}".format(i)]
        isupdated = h.helicsInputIsUpdated(sub)
        if (isupdated == 1):
            last_update_time = h.helicsInputLastUpdateTime(sub)
            value = h.helicsInputGetString(sub)
            info_sub = h.helicsSubscriptionGetKey(sub)
            #print("SENDER: Last updated at time {}".format(last_update_time))
            #print("Sender: Received value = {} with key = {} at time {}".format(value, info_sub, currenttime))
            
    if (currenttime == time_stop) and (currenttime == t):
        print("Sender: Received last value")
    elif (currenttime == t):
        val = str(value)
        for i in range (0, pubkeys_count):
            pub = pubid["m{}".format(i)]
            status = h.helicsPublicationPublishString(pub, val)
            info_pub = h.helicsPublicationGetKey(pub)
            #print("Sender: Published value = {} with key = {} at time {}".format(val, info_pub, currenttime))

    end = time.time()
    time_step_latency.append(end - start)

status = h.helicsFederateFinalize(vfed)

h.helicsFederateFree(vfed)
h.helicsCloseLibrary()
h.helicsCleanupLibrary()

print("SENDER: Federate finalized")
print('TimeStepLatency = {} '.format(time_step_latency))
#print('Number of Time steps should be {}'.format(math.floor(time_stop/update_interval)))
