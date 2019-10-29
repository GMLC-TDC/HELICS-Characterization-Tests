# HELICS Characterization Test Suite

This repository contains the co-simulation test suite used to evaluate the performance of HELICS. The test suite is set up to perform two types of experiments on that deploys many to one communication and one that uses meshed communication topology.

## Installation

To run the scripts python 3.6+ is needed. You can install this in many way but if you are new, the easiest I know of is [Anaconda](https://www.anaconda.com/download/)

After python is installed it is time to install the C++ federates needed for the test suite. These are located in the federates folder. To install do the following:

``` bash
# navigate to the federates folder
cd <path to repository>/federates

# create a build folder
mkdir -p build
cd build

# run the cmake process
cmake ../ -DCMAKE_INSTALL_PREFIX=$HOME/software/helicsTestSuite/1.0 -DZeroMQ_ROOT_DIR=$HOME/software/zeromq/4.1.6 -DBOOST_ROOT=$HOME/software/boost/1.6.1 -DFNCS_SOURCE_PATH=$HOME/software/fncs/launcher2 -DCZMQ_SOURCE_PATH=$HOME/software/czmq/3.0.2

# build
make
make install
```

## Running Tests

To run the test suite simply run `python helicsTestSuite.py` in the root of this repository. This will run the tests pre-specified in the files. Those experiments can be modified by editing the following portion of the python file:

``` bash
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
```

## Release
HELICS-Characterization-Tests are distributed under the terms of the BSD-3 clause license. All new
contributions must be made under this license. [LICENSE](LICENSE)

SPDX-License-Identifier: BSD-3-Clause
