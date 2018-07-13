# HELICS-Characterization-Tests

This repository contains the co-simulations used to evaluate the performance of HELICS and uncover limitations and bugs in the process.

Each folder provides a specific test case that contains:

* Source code for any custom federates used to execute the test
* Any scripts necessary to create the structure and/or support files for the co-simulation federation.
* The helics-runner script necessary to run one test case (that is, one instance of the test case with specific input parameters)
* Results files defining the specific details for each use case including the hardware on which it was performed, input parameters, and results

