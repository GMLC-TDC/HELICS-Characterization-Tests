"""
Test suite script to exercise co-simulation platforms and quantify their performance. Currently this suite is
able to test both FNCS and HELICS

"""

##################################################################################################################
# Created December 20, 2018 by Jacob Hansen (jacob.hansen@pnnl.gov)

# Copyright (c) 2018 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
# worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
# Government, including the right to distribute to other Government contractors.
##################################################################################################################

import os, json, yaml, shutil, subprocess, time, random
from yaml import CDumper as Dumper
from pathlib import Path
import pandas as pd
from termcolor import colored
import numpy as np
import matplotlib.pyplot as plt


def log_level_int(log_level):
    """
    This function returns the integer log level from a string. Used for compatibility across HELICS and FNCS
    
    Inputs
        log_level - Log level string

    Outputs
        log level integer
    """ 

    logLevels = {'ERROR': 0,'WARNING': 1,'INFO': 2,'DEBUG': 3,'DEBUG1': 4,
                 'DEBUG2': 5,'DEBUG3': 6,'DEBUG4': 7}

    if log_level in logLevels:
        return logLevels[log_level]
    else:
        print("WARNING: unknown log level specified")
        return 2


def write_launch_script(outFolder, logLevel, federateNumber, simTime, updateInterval, bytesNumber, coreTick, coreTimeout, coreType, coSim, typeSim):
    """
    This function writes a launch script for the experiment to disk
    
    Inputs
        outFolder - Folder that the experiment was created in
        logLevel - log level for the federates
        federateNumber - number of federates in the federation
        simTime - total simulation time
        updateInterval - interval between sending messages
        bytesNumber - number of bytes in each message 
        coreTick - HELICS setting for federates
        coreTimeout - HELICS setting for federates
        coreType - HELICS setting for federates
        coSim - either FNCS or HELICS
        typeSim - either ManyToOne or Meshed

    Outputs
        None
    """ 

        # create launch script
    file = open(outFolder / 'run.sh', "w")
    file.write('#!/bin/bash\n\n')

    file.write('set -m\n\n')

    file.write('catchFailures() {\n')
    file.write('    rv=`jobs -n | grep -v \'Running \\| Done\'`\n')
    file.write('    if [ ! -z "$rv" ]\n')
    file.write('    then\n')
    file.write('        echo "found an error"\n')
    file.write('        echo "$rv"\n')
    file.write('        kill $( jobs -p ) > /dev/null 2>&1\n')
    file.write('        exit 1\n')
    file.write('    fi\n')
    file.write('}\n\n')

    file.write('trap "catchFailures" SIGCHLD\n\n')

    file.write('export LOG_LEVEL=%s\n\n' %(logLevel))

    if coSim == 'FNCS':
        if typeSim == 'ManyToOne':
            file.write('fncs_broker %s' %(federateNumber+1))
        else:
            file.write('fncs_broker %s' %(federateNumber))
    else:
        if typeSim == 'ManyToOne':
            file.write('helics_broker --federates=%s --tick=%s --timeout=%s --log_level=%s --coretype=%s' %(federateNumber+1, coreTick, coreTimeout, log_level_int(logLevel), coreType))  
        else:
            file.write('helics_broker --federates=%s --tick=%s --timeout=%s --log_level=%s --coretype=%s' %(federateNumber, coreTick, coreTimeout, log_level_int(logLevel), coreType))  
    if logFiles:
        file.write(' &> broker.out &\n')
    else:
        file.write(' > /dev/null 2>&1 &\n')
    
    if typeSim == 'ManyToOne':
        if coSim == 'FNCS':
            file.write('testFedFNCS echo.yaml %s %s %s %s %s' %(1, 0, simTime, updateInterval, bytesNumber))
        else:
            file.write('testFedHELICS echo.json %s %s %s %s %s' %(1, 0, simTime, updateInterval, bytesNumber))
        if logFiles:
            file.write(' &> echo.out &\n')
        else:
            file.write(' > /dev/null 2>&1 &\n')
        for i in range (0, federateNumber):
            if coSim == 'FNCS':
                file.write('testFedFNCS send%s.yaml %s %s %s %s %s' %(i, 0, 1, simTime, updateInterval, bytesNumber))
            else:
                file.write('testFedHELICS send%s.json %s %s %s %s %s' %(i, 0, 1, simTime, updateInterval, bytesNumber))      
            if logFiles:
                file.write(' &> send%s.out &\n' %(i))
            else:
                file.write(' > /dev/null 2>&1 &\n')
    else:
        for i in range (0, federateNumber):
            if coSim == 'FNCS':
                if i == 0:
                    file.write('testFedFNCS fed%s.yaml %s %s %s %s %s' %(i, 1, 1, simTime, updateInterval, bytesNumber))
                else:
                    file.write('testFedFNCS fed%s.yaml %s %s %s %s %s' %(i, 0, 1, simTime, updateInterval, bytesNumber))
            else:
                if i == 0:
                    file.write('testFedHELICS fed%s.json %s %s %s %s %s' %(i, 1, 1, simTime, updateInterval, bytesNumber))
                else:
                    file.write('testFedHELICS fed%s.json %s %s %s %s %s' %(i, 0, 1, simTime, updateInterval, bytesNumber))          
            if logFiles:
                file.write(' &> fed%s.out &\n' %(i))
            else:
                file.write(' > /dev/null 2>&1 &\n')

    file.write('\necho "Waiting for it to finish"\n') 
    file.write('wait\n')   
    file.close()
 
    termProcess = subprocess.Popen(['chmod', '+x', 'run.sh'], cwd=outFolder, stdout=subprocess.PIPE)
    if termProcess.wait() != 0:
        raise Exception('something went wrong when doing "chmod" on run.sh')


def write_config(configString, type):
    """
    This function writes the Co-Simulation configuration file to disk
    
    Inputs
        configString - Python dictionary that hold the JSON config information to write to disk
        type - either JSON or YAML

    Outputs
        None
    """ 

    # the config dictionary contains the output folder. This will read it and the delete as it should not be part of the config
    outFolder = configString['outputFolder']
    del configString['outputFolder']

    if type == 'JSON':
        # write the JSON config to disk
        with open(outFolder, 'w') as outfile:
            json.dump(configString, outfile, ensure_ascii=False, indent = 4)
    elif type == 'YAML':
        with open(outFolder, 'w') as outfile:
            yaml.dump(configString, outfile, default_flow_style=False, indent=4, Dumper=Dumper)
    else:
        print("WARNING: unknown configuration file format")


def create_meshed_experiment_helics(outFolder, federateNumber, exchangeNumber, messageNumber, bytesNumber, updateInterval, simTime, logLevel, logFiles, uninterruptible, coreType, coreTick, coreTimeout):
    """
    This function creates the HELICS configuration file and shell scripts for the Meshed use case
    
    Inputs
        outFolder - Folder that the experiment will be created in
        federateNumber - number of federates in the federation
        exchangeNumber - number of other federates to talk to (ring talk topology)
        messageNumber - number of messages per sender
        bytesNumber - number of bytes in each message 
        updateInterval - interval between sending messages
        simTime - total simulation time
        logLevel - log level for the federates
        logFiles - flag to determine if log files are created
        uninterruptible - HELICS setting for federates
        coreType - HELICS setting for federates
        coreTick - HELICS setting for federates
        coreTimeout - HELICS setting for federates

    Outputs
        None
    """

    if exchangeNumber >= federateNumber or exchangeNumber == 0:
        raise Exception("Unable to create case as you are have specified either no or to many exchanges")

    # We need to create the experiment folder. If it already exists we delete it and then create it
    if os.path.isdir(outFolder):
        print("experiment folder already exists, deleting and moving on...")
        shutil.rmtree(outFolder)
    os.makedirs(outFolder)

    # create the senders
    for fed in range (0, federateNumber):
        name = 'fed' + str(fed)

        configData = dict()
        configData['outputFolder'] = outFolder / str(name + '.json')
        configData['name'] = name
        configData['log_level'] = log_level_int(logLevel)
        configData['uninterruptible'] = uninterruptible
        configData['coreType'] = coreType
        configData['coreName'] = ''
        configData['coreInit'] = '--federates=1 --tick=' + coreTick + ' --timeout=' + coreTimeout
        configData['maxIterations'] = 1
        configData['period'] =  updateInterval
        configData['timeDelta'] = updateInterval

        configData['publications'] = []
        configData['subscriptions'] = []

        # loop through all subscriptions
        for exchange in range (1, exchangeNumber+1):
            if fed+exchange > federateNumber-1:
                tempName = 'fed' + str(fed+exchange-federateNumber)
            else:
                tempName = 'fed' + str(fed+exchange)   

            #print('current fed ->', name, 'subs ->',tempName)
            for subs in range (0, messageNumber):
                temp = {'key': tempName + '/m' + str(subs),
                        'type': 'string',
                        'unit': '#',
                        'required': True}
                configData['subscriptions'].append(temp)

        # loop through all publications
        for pubs in range (0, messageNumber):
            temp = {'key':  'm' + str(pubs),
                    'type': 'string',
                    'unit': '#',
                    'global': False}
            configData['publications'].append(temp) 

        # writen the config to disk
        write_config(configData, 'JSON')

    # create launch script
    write_launch_script(outFolder, logLevel, federateNumber, simTime, updateInterval, bytesNumber, coreTick, coreTimeout, coreType, 'HELICS', 'Meshed')


def create_many_to_one_experiment_helics(outFolder, federateNumber, messageNumber, bytesNumber, updateInterval, simTime, logLevel, logFiles, uninterruptible, coreType, coreTick, coreTimeout):
    """
    This function creates the HELICS configuration file and shell scripts for the Many to One use case
    
    Inputs
        outFolder - Folder that the experiment will be created in
        federateNumber - number of senders in the federation
        messageNumber - number of messages per sender
        bytesNumber - number of bytes in each message 
        updateInterval - interval between sending messages
        simTime - total simulation time
        logLevel - log level for the federates
        logFiles - flag to determine if log files are created
        uninterruptible - HELICS setting for federates
        coreType - HELICS setting for federates
        coreTick - HELICS setting for federates
        coreTimeout - HELICS setting for federates

    Outputs
        None
    """

    # We need to create the experiment folder. If it already exists we delete it and then create it
    if os.path.isdir(outFolder):
        print("experiment folder already exists, deleting and moving on...")
        shutil.rmtree(outFolder)
    os.makedirs(outFolder)
    
    topicList = [[],[]] 

    # create the senders
    for fed in range (0, federateNumber):
        name = 'send' + str(fed)

        configData = dict()
        configData['outputFolder'] = outFolder / str(name + '.json')
        configData['name'] = name
        configData['log_level'] = log_level_int(logLevel)
        configData['uninterruptible'] = uninterruptible
        configData['coreType'] = coreType
        configData['coreName'] = ''
        configData['coreInit'] = '--federates=1 --tick=' + coreTick + ' --timeout=' + coreTimeout
        configData['maxIterations'] = 1
        configData['period'] =  updateInterval
        configData['timeDelta'] = updateInterval

        configData['publications'] = []
        configData['subscriptions'] = []

        # loop through all subscriptions
        for subs in range (0, messageNumber):
            temp = {'key': 'echo/' + name + '_m' + str(subs),
                    'type': 'string',
                    'unit': '#',
                    'required': True}
            configData['subscriptions'].append(temp)

        # loop through all publications
        for pubs in range (0, messageNumber):
            topicList[0].append(name + '/' + name + '_m' + str(pubs))
            topicList[1].append(name + '_m' + str(pubs))
            temp = {'key':  name + '_m' + str(pubs),
                    'type': 'string',
                    'unit': '#',
                    'global': False}
            configData['publications'].append(temp) 

        # writen the config to disk
        write_config(configData, 'JSON')       
     
    # create the echoer
    name = 'echo'

    configData = dict()
    configData['outputFolder'] = outFolder / str(name + '.json')
    configData['name'] = name
    configData['log_level'] = log_level_int(logLevel)
    configData['uninterruptible'] = uninterruptible
    configData['coreType'] = coreType
    configData['coreName'] = ''
    configData['coreInit'] = '--federates=1 --tick=' + coreTick + ' --timeout=' + coreTimeout
    configData['maxIterations'] = 1
    configData['period'] =  updateInterval
    configData['timeDelta'] = updateInterval

    configData['publications'] = []
    configData['subscriptions'] = []

    # loop through all subscriptions
    for top in topicList[0]:
        temp = {'key': top,
                'type': 'string',
                'unit': '#',
                'required': True}
        configData['subscriptions'].append(temp)

    # loop through all publications
    for top in topicList[1]:
        temp = {'key': top,
                'type': 'string',
                'unit': '#',
                'global': False}
        configData['publications'].append(temp) 

    # writen the config to disk
    write_config(configData, 'JSON')

    # create launch script
    write_launch_script(outFolder, logLevel, federateNumber, simTime, updateInterval, bytesNumber, coreTick, coreTimeout, coreType, 'HELICS', 'ManyToOne')


def create_meshed_experiment_fncs(outFolder, federateNumber, exchangeNumber, messageNumber, bytesNumber, updateInterval, simTime, logLevel, logFiles):
    """
    This function creates the HELICS configuration file and shell scripts for the Meshed use case
    
    Inputs
        outFolder - Folder that the experiment will be created in
        federateNumber - number of federates in the federation
        exchangeNumber - number of other federates to talk to (ring talk topology)
        messageNumber - number of messages per sender
        bytesNumber - number of bytes in each message 
        updateInterval - interval between sending messages
        simTime - total simulation time
        logLevel - log level for the federates
        logFiles - flag to determine if log files are created

    Outputs
        None
    """
    if exchangeNumber >= federateNumber or exchangeNumber == 0:
        raise Exception("Unable to create case as you are have specified either no or to many exchanges")

    # We need to create the experiment folder. If it already exists we delete it and then create it
    if os.path.isdir(outFolder):
        print("experiment folder already exists, deleting and moving on...")
        shutil.rmtree(outFolder)
    os.makedirs(outFolder)

    # create the senders
    for fed in range (0, federateNumber):
        name = 'fed' + str(fed)

        configData = dict()
        configData['outputFolder'] = outFolder / str(name + '.yaml')
        configData['name'] = name
        configData['time_delta'] = str(int(updateInterval)) + 's'
        configData['broker'] = 'tcp://localhost:5570'
        configData['values'] = {}

        # loop through and add subscriptions
        for exchange in range (1, exchangeNumber+1):
            if fed+exchange > federateNumber-1:
                tempName = 'fed' + str(fed+exchange-federateNumber)
            else:
                tempName = 'fed' + str(fed+exchange)   

            #print('current fed ->', name, 'subs ->',tempName)
            for subs in range (0, messageNumber):
                # <message name>::<from federate>
                configData['values']['m' + str(subs) + '::' + tempName] = {'topic': tempName + '/m' + str(subs),
                                               'default': '',
                                               'type': 'string',
                                               'list': False}

        # writen the config to disk
        write_config(configData, 'YAML')

    # create launch script
    write_launch_script(outFolder, logLevel, federateNumber, simTime, updateInterval, bytesNumber, coreTick, coreTimeout, coreType, 'FNCS', 'Meshed')


def create_many_to_one_experiment_fncs(outFolder, federateNumber, messageNumber, bytesNumber, updateInterval, simTime, logLevel, logFiles):
    """
    This function creates the FNCS configuration file and shell scripts for the Many to One use case
    
    Inputs
        outFolder - Folder that the experiment will be created in
        federateNumber - number of senders in the federation
        messageNumber - number of messages per sender
        bytesNumber - number of bytes in each message 
        updateInterval - interval between sending messages
        simTime - total simulation time
        logLevel - log level for the federates
        logFiles - flag to determine if log files are created

    Outputs
        None
    """

    # We need to create the experiment folder. If it already exists we delete it and then create it
    if os.path.isdir(outFolder):
        print("experiment folder already exists, deleting and moving on...")
        shutil.rmtree(outFolder)
    os.makedirs(outFolder)

    topicList = [[],[]] 

    # create the senders
    for fed in range (0, federateNumber):
        name = 'send' + str(fed)

        configData = dict()
        configData['outputFolder'] = outFolder / str(name + '.yaml')
        configData['name'] = name
        configData['time_delta'] = str(int(updateInterval)) + 's'
        configData['broker'] = 'tcp://localhost:5570'
        configData['values'] = {}

        # loop through all feeders and add subscriptions for feeder load
        for subs in range (0, messageNumber):
            topicList[0].append(name + '/' + name + '_m' + str(subs))
            topicList[1].append(name + '_m' + str(subs))
            configData['values'][name + '_m' + str(subs)] = {'topic': 'echo/' + name + '_m' + str(subs),
                                               'default': '',
                                               'type': 'string',
                                               'list': False}

        # writen the config to disk
        write_config(configData, 'YAML')      
     
    # create the echoer
    name = 'echo'

    configData = dict()
    configData['outputFolder'] = outFolder / str(name + '.yaml')
    configData['name'] = name
    configData['time_delta'] = str(int(updateInterval)) + 's'
    configData['broker'] = 'tcp://localhost:5570'
    configData['values'] = {}

    # loop through all feeders and add subscriptions for feeder load
    for idx, _ in enumerate(topicList[0]):
        configData['values'][topicList[1][idx]] = {'topic': topicList[0][idx],
                                               'default': '',
                                               'type': 'string',
                                               'list': False}

    # writen the config to disk
    write_config(configData, 'YAML')

    # create launch script
    write_launch_script(outFolder, logLevel, federateNumber, simTime, updateInterval, bytesNumber, coreTick, coreTimeout, coreType, 'FNCS', 'ManyToOne')


def run_experiment(experimentFolder, simulationTimeout):
    """
    This function executes an experiment and collects the results
    
    Inputs
        experimentFolder - Folder that the experiment exist in
        simulationTimeout - Timeout value before we consider the experiment failed

    Outputs
        Status - 0 if successfull, 1 if failed, and 2 if timed out
        Initialization time (cpu)
        Execution time (cpu)
        Closing time (cpu)
        Initialization time (wall)
        Execution time (wall)
        Closing time (wall)
    """
    
    currentPath = os.getcwd()
    os.chdir(experimentFolder)
    time.sleep( 1 )
    logFile = open("sim.out", "w")
    try:
        processReturn = subprocess.run(['./run.sh'], stdout=logFile, timeout=simulationTimeout)
    except subprocess.TimeoutExpired:
        os.chdir(currentPath)
        processReturn = subprocess.run(['pkill','-9','_broker'], stdout=logFile) # this will kill any HELICS or FNCS broker
        processReturn = subprocess.run(['pkill','-9','testFed'], stdout=logFile) # this will kill any HELICS of FNCS federate
        logFile.close
        return 2, 0., 0., 0., 0., 0., 0.
        
    logFile.close
    if processReturn.returncode == 0:
        data = pd.read_csv('timeDataLogging.csv')
        os.chdir(currentPath)
        return 0, data.iloc[0]['Initialization time'], data.iloc[0]['Execution time'], data.iloc[0]['Closing time'], data.iloc[1]['Initialization time'], data.iloc[1]['Execution time'], data.iloc[1]['Closing time']
    else:
        os.chdir(currentPath)
        return 1, 0., 0., 0., 0., 0., 0.


def run_search(outFolder, federateNumber, messageNumber, bytesNumber, updateInterval, simTime, logLevel, logFiles, uninterruptible, coreType, coreTick, coreTimeout, simulationTimeout, coSimPlatform, experimentType):
    """
    This function runs all combinations of the specified senders, messages, bytes, and core types and returns the results in a dataframe
    
    Inputs
        outFolder - Folder that the experiment will be created in
        federateNumber - number of senders in the federation
        messageNumber - number of messages per sender
        bytesNumber - number of bytes in each message 
        updateInterval - interval between sending messages
        simTime - total simulation time
        logLevel - log level for the federates
        logFiles - flag to determine if log files are created
        uninterruptible - HELICS setting for federates
        coreType - HELICS setting for federates
        coreTick - HELICS setting for federates
        coreTimeout - HELICS setting for federates
        simulationTimeout - Timeout value before we consider the experiment failed
        coSimPlatform - Co-Simulation platform used. FNCS and HELICS supported
        experimentType - Type of experiment Meshed or ManyToOne

    Outputs
        results - pandas dataframe with results

    """

    df = pd.DataFrame(columns=['experiment type','co-simulation platform','core type','status','federates','messages','bytes','initialization time (cpu)','execution time (cpu)','closing time (cpu)','initialization time (wall)','execution time (wall)','closing time (wall)'])
    
    if coSimPlatform == 'FNCS':
        coSimType = 0
    elif coSimPlatform == 'HELICS':
        coSimType = 1
    else:
        print("ERROR: unknown Co-Simulation platform specified")
        return df

    if experimentType == 'ManyToOne':
        expType = 0
    elif experimentType == 'Meshed':
        expType = 1
    else:
        print("ERROR: unknown Co-Simulation experiment type specified")
        return df

    count = 1
    totalTestNum = len(federateNumber) * len(messageNumber) * len(bytesNumber) * len(coreType)
    for fedNum in federateNumber:
        for messNum in messageNumber:
            for bytesNum in bytesNumber:
                for coreNum in coreType:    
                    tempFolder = outFolder / coreNum / str('test_f_' + str(fedNum) + '_m_' + str(messNum) + '_b_' + str(bytesNum))
                    if coSimType == 0:
                        if expType == 0:
                            create_many_to_one_experiment_fncs(tempFolder, fedNum, messNum, bytesNum, updateInterval, simTime, logLevel, logFiles)
                        else:
                            create_meshed_experiment_fncs(tempFolder, fedNum, fedNum-1, messNum, bytesNum, updateInterval, simTime, logLevel, logFiles)
                    else:
                        if expType == 0:
                            create_many_to_one_experiment_helics(tempFolder, fedNum, messNum, bytesNum, updateInterval, simTime, logLevel, logFiles, uninterruptible, coreNum, coreTick, coreTimeout)
                        else:
                            create_meshed_experiment_helics(tempFolder, fedNum, fedNum-1, messNum, bytesNum, updateInterval, simTime, logLevel, logFiles, uninterruptible, coreNum, coreTick, coreTimeout) 
                    print("running", coSimPlatform, "test", count, "of", totalTestNum, "with federates=" + str(fedNum), "messages=" + str(messNum), "bytes=" + str(bytesNum), "core=" + str(coreNum), "status=", end='', flush=True)
                    result, initTime, execTime, closeTime , initTimeWall, execTimeWall, closeTimeWall = run_experiment(tempFolder, simulationTimeout) 
                    if result == 0:
                        simStatus = 'success'
                        print(colored(simStatus, 'green'), flush=True)
                    elif result == 1:
                        simStatus = 'failure'
                        print(colored(simStatus, 'red'), flush=True)
                    else:
                        simStatus = 'timeout'
                        print(colored(simStatus, 'yellow'), flush=True)

                    df = df.append(pd.DataFrame([[experimentType, coSimPlatform, coreNum, simStatus, fedNum, messNum, bytesNum, initTime, execTime, closeTime, initTimeWall, execTimeWall, closeTimeWall]], columns=['experiment type','co-simulation platform','core type','status','federates','messages','bytes','initialization time (cpu)','execution time (cpu)','closing time (cpu)','initialization time (wall)','execution time (wall)','closing time (wall)']), ignore_index=True)
                    count += 1

    # save the data from the runs
    df.to_csv(outFolder / 'data.csv', index_label='experiment')

    return df


def plot_data(df):
    """
    This function plots the wall clock time results from the experiment
    
    Inputs
        df - Pandas data frame with experiment data 

    Outputs
        results - pandas dataframe with results

    """ 

    # get a list of unique core types
    coreUnique = df['core type'].unique()

    # create a list of experiments in the data
    plotLabels = []
    for index, row in df[df['core type'].isin([coreUnique[0]])].iterrows():
        plotLabels.append('f-' + str(row['federates']) + '-m-' + str(row['messages']) + '-b-' + str(row['bytes']))

    # create plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
    index = np.arange(len(plotLabels))
    bar_width = 0.1
    opacity = 0.8

    initTime = pd.DataFrame();
    executionTime = pd.DataFrame();
    closeTime = pd.DataFrame();
    for idx, core in enumerate(coreUnique):
        temp = df.loc[df['core type'].isin([core]),['initialization time (wall)']]
        temp.reset_index(drop=True, inplace=True)
        temp.columns = [core]
        temp.index = [plotLabels] 
        initTime = pd.concat([initTime, temp], axis=1)
                
        ax1.bar(index + idx*bar_width, temp[core], bar_width,
                        alpha=opacity)

        temp = df.loc[df['core type'].isin([core]),['execution time (wall)']]
        temp.reset_index(drop=True, inplace=True)
        temp.columns = [core]
        temp.index = [plotLabels] 
        executionTime = pd.concat([executionTime, temp], axis=1)
                
        ax2.bar(index + idx*bar_width, temp[core], bar_width,
                        alpha=opacity)

        temp = df.loc[df['core type'].isin([core]),['closing time (wall)']]
        temp.reset_index(drop=True, inplace=True)
        temp.columns = [core]
        temp.index = [plotLabels] 
        closeTime = pd.concat([closeTime, temp], axis=1)
                
        ax3.bar(index + idx*bar_width, temp[core], bar_width,
                        alpha=opacity)
    
    ax1.set_title('Test Suite Experiment Results (wall time)')
    ax2.set_ylabel('time (s)')
    plt.xticks(index + bar_width, (plotLabels))
    fig.legend(coreUnique)
    plt.savefig('fig.png')
    plt.show()


if __name__ == '__main__':
    experimentName = 'test_HELICS'  # name of the experiment folder that will be created 
    federateNumber = [100, 200]     # list of number of federates you want to test with               
    messageNumber = [1, 10]         # number of messages per federate        
    bytesNumber = [1, 10]           # size of each message in bytes
    coreType = ['zmq','tcp']        # core types to test. FNCS will ignore the input
    updateInterval = 10.            # interval between time updates
    simTime = 100.                  # total simulation time
    logLevel = 'INFO'               # ERROR, WARNING, INFO, DEBUG DEBUG1-4
    logFiles = True                 # flag to determine if log files are created per federate
    uninterruptible = False         # HELICS specific flag
    coreTick = '30s'                # HELICS specific flag
    coreTimeout = '30s'             # HELICS specific flag
    simulationTimeout = 120         # global timeout for any simulation
    coSimPlatform = 'HELICS'        # Co-Simulation platform to use (either HELICS or FNCS)
    experimentType = 'ManyToOne'    # experiment type to use (either ManyToOne or Meshed)

    df = run_search(Path(os.getcwd()) / experimentName, federateNumber, messageNumber, bytesNumber, updateInterval, simTime, logLevel, logFiles, uninterruptible, coreType, coreTick, coreTimeout, simulationTimeout, coSimPlatform, experimentType)

    # create_many_to_one_experiment_helics(Path(os.getcwd()) / experimentName, federateNumber[0], messageNumber[0], bytesNumber[0], updateInterval, simTime, logLevel, logFiles, uninterruptible, coreType[0], coreTick, coreTimeout)    
    # create_meshed_experiment_helics(Path(os.getcwd()) / experimentName, federateNumber[0], federateNumber[0]-1, messageNumber[0], bytesNumber[0], updateInterval, simTime, logLevel, logFiles, uninterruptible, coreType[0], coreTick, coreTimeout)
    # create_many_to_one_experiment_fncs(Path(os.getcwd()) / experimentName, federateNumber[0], messageNumber[0], bytesNumber[0], updateInterval, simTime, logLevel, logFiles)    
    # create_meshed_experiment_fncs(Path(os.getcwd()) / experimentName, federateNumber[0], federateNumber[0]-1, messageNumber[0], bytesNumber[0], updateInterval, simTime, logLevel, logFiles)
    # result = run_experiment(Path(os.getcwd()) / experimentName)
    # print(result)  

    # plot results
    # df = pd.read_csv('/Users/hans464/Desktop/test_HELICS/data.csv')
    # plot_data(df)