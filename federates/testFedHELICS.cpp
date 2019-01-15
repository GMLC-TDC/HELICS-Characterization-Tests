/*
==========================================================================================
Copyright (C) 2019, Battelle Memorial Institute
Written by Jacob Hansen, Pacific Northwest National Laboratory
==========================================================================================
*/
#include <iostream>
#include <fstream>
#include <vector>
#include <iomanip>
#include <algorithm>
#include <stdio.h>
#include <string.h> 

#include "helics/helics.hpp"
#include "helics/application_api/queryFunctions.hpp"
#include "logging.hpp"

using namespace std;

// set the definition for the logger
loglevel_e loglevel;

/* ==================================================================================================================
====================== MAIN PART ====================================================================================
===================================================================================================================*/

string generate_random_string(int max_length){
    string possible_characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    random_device rd;
    mt19937 engine(rd());
    uniform_int_distribution<> dist(0, possible_characters.size()-1);
    string ret = "";
    for(int i = 0; i < max_length; i++){
        int random_index = dist(engine); //get index between 0 and possible_characters.size()-1
        ret += possible_characters[random_index];
    }
    return ret;
}


int main(int argc, const char *argv[]) {
	// variable to keep track of the total time used
	clock_t tStart = clock();
	clock_t tStop;

	time_t tStartWall = time(NULL);
	time_t tStopWall;
	
	double initTime;
	double initTimeWall;
	double executionTime;
	double executionTimeWall;
	double closeTime;
	double closeTimeWall;

	// Setting up the logger based on user input
	char *log_level_export = NULL;
	log_level_export = getenv("LOG_LEVEL");
	
	if (!log_level_export) {
		loglevel = logWARNING; 
	} else if (strcmp(log_level_export,"ERROR") == 0) {
		loglevel = logERROR;
	} else if (strcmp(log_level_export,"WARNING") == 0) {
		loglevel = logWARNING;
	} else if (strcmp(log_level_export,"INFO") == 0) {
		loglevel = logINFO;
	} else if (strcmp(log_level_export,"DEBUG") == 0) {
		loglevel = logDEBUG;
	} else if (strcmp(log_level_export,"DEBUG1") == 0) {
		loglevel = logDEBUG1;
	} else if (strcmp(log_level_export,"DEBUG2") == 0) {
		loglevel = logDEBUG2;
	} else if (strcmp(log_level_export,"DEBUG3") == 0) {
		loglevel = logDEBUG3;
	} else if (strcmp(log_level_export,"DEBUG4") == 0) {
		loglevel = logDEBUG4;
	}
	
	LINFO << "Running process -> " << argv[0] ;
		
	// portion to initialize HELICS
	LINFO << "Initializing HELICS federate";
	// configuration file for federate
	std::string configString = argv[1];
	auto fed = std::make_unique<helics::ValueFederate> (configString);   	

	// determine simulator name
	string simName = fed->getName();
	LINFO << "Name of simulator is -> " << simName;	

	try {	
		int logTime; // federate type -> 0=false, 1=true
		sscanf(argv[2], "%d%*s", &logTime);
		LINFO << "Federate log time [0=false, 1=true]: " << logTime;

		int simType; // federate type -> 0=echoer, 1=publisher
		sscanf(argv[3], "%d%*s", &simType);
		LINFO << "Federate type [0=echoer, 1=publisher]: " << simType;

		double simStopTime; // simulation stop time
		sscanf(argv[4], "%lf%*s", &simStopTime);
		LINFO << "Simulation stop time [seconds]: " << simStopTime;
		
		double deltaTime; // simulation delta time
		sscanf(argv[5], "%lf%*s", &deltaTime);
		LINFO << "Delta time [seconds]: " << deltaTime;

		int messageSize; // individual message size
		sscanf(argv[6], "%d%*s", &messageSize);
		LINFO << "Message size: " << messageSize;
				
		double currentTime = 0; //current time in seconds
		double nextTime = 0; // next time in seconds
			
		// Let's get a list of the subscriptions we have 
		vector<string> subscription_keys;
		subscription_keys = vectorizeAndSortQueryResult(fed->query(fed->getName(), "subscriptions"));

		vector<helics::Input> subscription_ids;
		
		// loop through subscriptions and get the id for them
		for(vector<string>::size_type i = 0; i != subscription_keys.size(); i++) {
			auto idTemp = fed->getSubscription(subscription_keys[i]);
			idTemp.setDefault<string>("");
			subscription_ids.push_back(idTemp);
		}

		// vectors of equal size for the actual values
		vector<string> subscription_values (subscription_keys.size());
		
		if (loglevel >= logDEBUG) {
			LDEBUG << "Subscriptions:";
			for(auto it = subscription_keys.begin(); it != subscription_keys.end(); ++it) {
				LDEBUG << "    " << *it ;
			}
		}

		// Let's get a list of the publications we have 
		vector<string> publication_keys;
		publication_keys = vectorizeAndSortQueryResult(fed->query(fed->getName(), "publications"));
		
		vector<helics::Publication> publication_ids;
		vector<string> publication_values;
		
		
	    for(vector<string>::size_type i = 0; i != publication_keys.size(); i++) {
	        auto idTemp = fed->getPublication(publication_keys[i]);
	        publication_ids.push_back(idTemp);
	        if (simType == 1) { // if we are a publisher we need to create random strings to publish
	        	publication_values.push_back(generate_random_string(messageSize));
	        } else {
	        	publication_values.push_back("");
	        }
   		}

		if (loglevel >= logDEBUG) {
			LDEBUG << "Publications:";
			for(vector<string>::size_type i = 0; i != publication_keys.size(); i++) {
				LDEBUG << "    " << publication_keys[i] << " -> " << publication_values[i];
			}
		}		
		
		// we are done with the setup, start the initialization
	    LINFO << "federate entering init mode";
	    fed->enterInitializingMode ();

	    // now enter execution state
	    fed->enterExecutingMode ();
	    LINFO << "federate entering exec mode";

	   	// capture the time it took to initialize
	    tStop = clock();
	    tStopWall = time(NULL);
		initTime = double(tStop - tStart) / CLOCKS_PER_SEC;
		initTimeWall = difftime(tStopWall, tStartWall);
		tStart = clock();
		tStartWall = time(NULL);

		
    	do {
			// update time
			LINFO << "Current time = " << currentTime;
	
			if (currentTime == nextTime) {
				// update subscriptions
				LDEBUG << "Updated subscriptions:";
				for(vector<double>::size_type i = 0; i != subscription_keys.size(); i++) {
					subscription_values[i] = subscription_ids[i].getValue<string>();
					LDEBUG1 << "    " << subscription_keys[i] << " -> " << subscription_values[i];			
				}

				// update publications
				LDEBUG << "Updated publications";
				for(vector<double>::size_type i = 0; i != publication_ids.size(); i++) {
					if (simType == 1) {
						publication_ids[i].publish(publication_values[i]);	
						LDEBUG1 << "    " << publication_keys[i] << " -> " << publication_values[i];
					} else {
						publication_ids[i].publish(subscription_values[i]);	
						LDEBUG1 << "    " << publication_keys[i] << " -> " << subscription_values[i];	
					}	
				}

				nextTime = min(currentTime + deltaTime, simStopTime);
			}

			currentTime = fed->requestTime ((helics::Time) nextTime);
		}
		while(currentTime < simStopTime);

		// capture the time it took to execute main loop
		tStop = clock();
	    tStopWall = time(NULL);
		executionTime = double(tStop - tStart) / CLOCKS_PER_SEC;
		executionTimeWall = difftime(tStopWall, tStartWall);
		tStart = clock();
		tStartWall = time(NULL);

		LINFO << "Terminating HELICS federate";
		fed->finalize();
		helics::cleanupHelicsLibrary();

			// capture the time it took to close out
		tStop = clock();
	    tStopWall = time(NULL);
		closeTime = double(tStop - tStart) / CLOCKS_PER_SEC;
		closeTimeWall = difftime(tStopWall, tStartWall);


		LDEBUG << "Initialization time [seconds]: " << initTime;
		LDEBUG << "Execution time [seconds]: " << executionTime;
		LDEBUG << "Closing time [seconds]: " << closeTime;
		
		if (logTime) {
			// adding in a file that collects data time execution
			ofstream timeDataLogging("timeDataLogging.csv", ios::out);
			// creating the beginning of the header for the file
			timeDataLogging << "Initialization time,Execution time,Closing time" << endl;
			timeDataLogging << std::fixed << std::setprecision(4) << initTime << "," << executionTime << "," << closeTime << endl;
			timeDataLogging << std::fixed << std::setprecision(4) << initTimeWall << "," << executionTimeWall << "," << closeTimeWall << endl;
		}

	}	
	catch (const exception& e) {
		LERROR << "Caught a standard exception, see below for details";
		cerr << e.what() << endl;
		cerr << "Terminating program..." << endl;
        fed->error(-2, e.what());
        fed->finalize();
		helics::cleanupHelicsLibrary();
        return -2;
  	}
    catch (...) {
        LERROR << "Unknown and unexpected error thrown";
		cerr << "Terminating program..." << endl;
        fed->error(-3, "Unknown and unexpected error thrown");
        fed->finalize();
		helics::cleanupHelicsLibrary();
        return -3;
	}	

	return 0;
}
