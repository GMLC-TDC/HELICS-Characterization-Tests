/*
==========================================================================================
Copyright (C) 2019, Battelle Memorial Institute
Written by Jacob Hansen, Pacific Northwest National Laboratory
==========================================================================================
*/
#ifndef _LOG_HPP_
#define _LOG_HPP_

#include <iostream>
#include <sstream>
#include <iomanip>

enum loglevel_e
    {logERROR, logWARNING, logINFO, logDEBUG, logDEBUG1, logDEBUG2, logDEBUG3, logDEBUG4};

class logIt
{
public:
    logIt(loglevel_e _loglevel = logERROR, const char* _level_string = "LERROR") {
        _buffer << _level_string << " :" 
            << std::string(
                _loglevel > logDEBUG 
                ? (_loglevel - logDEBUG) * 4 
                : 1
                , ' ');
        _storedlevel = _loglevel;     
    }

    template <typename T>
    logIt & operator<<(T const & value)
    {
        _buffer << std::fixed << std::setprecision(4) <<  value;
        return *this;
    }

    ~logIt()
    {
        _buffer << std::endl;
        if (_storedlevel != logERROR) {
            std::cout << _buffer.str();           
        } else {
            std::cerr << _buffer.str(); 
        }
    }

private:
    std::ostringstream _buffer;
    loglevel_e _storedlevel;
};

extern loglevel_e loglevel;

#define log(level,level_string) \
if (level > loglevel) ; \
else logIt(level,level_string)

#define LERROR log(logERROR,"LERROR")
#define LWARNING log(logWARNING,"LWARNING")
#define LINFO log(logINFO,"LINFO")
#define LDEBUG log(logDEBUG,"LDEBUG")
#define LDEBUG1 log(logDEBUG1,"LDEBUG1")
#define LDEBUG2 log(logDEBUG2,"LDEBUG2")
#define LDEBUG3 log(logDEBUG3,"LDEBUG3")
#define LDEBUG4 log(logDEBUG4,"LDEBUG4")

#endif
