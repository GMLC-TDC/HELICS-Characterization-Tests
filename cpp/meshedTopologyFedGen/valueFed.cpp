/*
Copyright © 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/
#include <helics/application_api/ValueFederate.hpp>
#include <helics/application_api/queryFunctions.hpp>
#include <helics/application_api/Inputs.hpp>
#include <helics/application_api/Publications.hpp>
#include <thread>
#include <iostream>
#include <functional>

int main(int argc, const char *const *argv) {
    if (argc != 3) {
        std::cerr << "Expecting two arguments. You have entered " << argc - 1 << " arguments" << std::endl;
        return 0;
    }

    // string for the name of the federate configuration file
    std::string configString = argv[1];

    // loads configuration, registers interfaces and starts the federate
    //auto vFed = new helics::ValueFederate ("temp_name", configString);
    auto vFed = new helics::ValueFederate(configString);

    /* This part is if you don't use the one line above
    // load the configuration file
    auto fedInfo = helics::loadFederateInfo("temp_name", configString);

    // register the federate with its configuration
    //auto vFed = std::make_unique<helics::ValueFederate> (fedInfo);
    auto vFed = new helics::ValueFederate (fedInfo);

    // register the publications and subscriptions
    vFed->registerInterfaces (configString);
    */

    // some user messages
    std::cout << "fed name -> " << vFed->getName() << std::endl;
    std::cout << "config name -> " << configString << std::endl;

    //std::cout << "publication count -> " << vFed->getPublicationCount() << std::endl; 
    //std::cout << "subscription count -> " << vFed->getSubscriptionCount() << std::endl; 

    std::cout << "pubs -> " << vFed->query(vFed->getName(), "publications") << std::endl;
    std::cout << "subs -> " << vFed->query(vFed->getName(), "subscriptions") << std::endl;

    // returns a list of publication keys in the configuration file
    auto pubKeys = vectorizeAndSortQueryResult(vFed->query(vFed->getName(), "publications"));

    // returns a list of subscription keys in the configuration file
    auto subKeys = vectorizeAndSortQueryResult(vFed->query(vFed->getName(), "subscriptions"));

    // print out the publications for the user
    std::cout << "publication keys:" << std::endl;
    for (auto it = pubKeys.begin(); it != pubKeys.end(); ++it) {
        std::cout << "\t " << *it << std::endl;
    }

    // print out the subscriptions for the user
    std::cout << "subscription keys:" << std::endl;
    for (auto it = subKeys.begin(); it != subKeys.end(); ++it) {
        std::cout << "\t " << *it << std::endl;
    }

    // this federate is only built to handle one publication and one subscription. Will exit if that is not the case!!
    //if (vFed->getPublicationCount() > 1 || vFed->getSubscriptionCount() > 1) {
//    if (pubKeys.size() > 1 || subKeys.size() > 1) {
//        std::cerr << "This federate only supports one subscription and publication. You specified more and only the first one will be used!!" << std::endl;
//    }

    // get the id of the publication. In the future this could support more than one!
//    auto id = vFed->getPublicationId(pubKeys[0]);
//    auto id = vFed->getPublication(pubKeys[0]);
//    // get the id of the subscription. In the future this could support more than one!
////    auto subid = vFed->getSubscriptionId(subKeys[0]);
//    auto subid = vFed->getSubscription(subKeys[0]);

    // we are done with the setup, start the initialization
    std::cout << "entering init mode" << std::endl;
    vFed->enterInitializingMode();
    std::cout << "entered init State" << std::endl;

    // now enter execution state
    vFed->enterExecutingMode();
    std::cout << "entered exec mode" << std::endl;

    double currentTime = 0;
    double currentTimeTemp = 0;
    double nextTime = 0;
    double stopTime = 200;
    double timeDelta = atof(argv[2]);;
    std::cout << "delta time -> " << timeDelta << " seconds" << std::endl;
    std::cout << "stop time -> " << stopTime << " seconds" << std::endl;
    // simple loop that count from 0 through 9 to test pub/sub
    do {
        currentTimeTemp = currentTime;
        // publish our variable
        for (int pubNum = 0; pubNum < pubKeys.size(); pubNum++) {
            auto pub = vFed->getPublication(pubKeys[pubNum]);
            pub.publish(currentTime);
        }

        // if our subscription is updated lets get the value
        for (int subNum = 0; subNum < subKeys.size(); subNum++) {
            auto sub = vFed->getSubscription(subKeys[subNum]);
            if (vFed->isUpdated(sub)) {
                // get the latest value for the subscription
                auto val = vFed->getDouble(sub);
                std::cout << "received updated value of " << val << " at " << currentTime << " from "
                          << vFed->getTarget(sub) << std::endl;
            }
        }

        nextTime = currentTime + timeDelta;
        currentTime = vFed->requestTime((helics::Time) nextTime);

        std::cout << "############## TIMING ##############" << std::endl;
        std::cout << "    processed time " << currentTimeTemp << std::endl;
        std::cout << "    requested new time " << nextTime << std::endl;
        std::cout << "    requestTime call returned " << currentTime << std::endl;
        std::cout << "####################################" << std::endl;

    } while (currentTime < stopTime);

    std::cout << "about to exit" << std::endl;
    // end the federate
    vFed->finalize ();
    return 0;
}

