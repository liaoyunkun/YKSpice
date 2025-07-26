# Author:Yunkun Liao
# This module defines some utility function
import re
from error_define import*

def scale_factor_convert(value):
    '''This function convert val_postfix in netlist
        eg: 1k -> 1e03
        param:
            unit_value:str,value represent in SPICE Netlist fashion
        return:
            float,value in scientific representation
    '''
    if(value[-1] == 'k'):
        return float(value[:-1])*1e03
    elif(value.endswith('meg')):
        return float(value[:-3])*1e06
    elif(value[-1] == 'g'):
        return float(value[:-1])*1e09
    elif(value[-1] == 'm'):
        return float(value[:-1])*1e-03
    elif(value[-1] == 'u'):
        return float(value[:-1])*1e-06
    elif(value[-1] == 'n'):
        return float(value[:-1])*1e-09
    elif(value[-1] == 'p'):
        return float(value[:-1])*1e-12
    elif(value[-1] == 'f'):
        return float(value[:-1])*1e-15
    else:
        # Automately convert (str '1e3') to (float 1000.)
        return float(value)

def value_extract(line_number,line,raw_value):
    '''This function extract valuable information
    from raw value string
    eg. when we define a sin source:
        sin(0voff 1vpeak  2khz)
        extraction process:
        0voff -> 0
        1vpeak -> 1
        2khz -> 1k
        1ns -> 1n
    param:
        raw_value: str->'0voff'
    return:
        value: str->'0'
    '''
    value_pattern = re.compile(r'-?[0-9]+\.?[0-9]*(meg)?[fpnumkg]?')
    match = re.search(value_pattern,raw_value)
    if(match):
        value = raw_value[match.span()[0]:match.span()[1]]
        return value
    else:
        raise  NetlistSyntaxError(line_number,line,'Unable to extract the meaningful value')
        
def adjust(time):
    if(1e-15 <= abs(time) < 1e-12):
        return (1e12,'p')
    elif(1e-12 <= abs(time) < 1e-9):
        return (1e9,'n')
    elif(1e-9 <= abs(time) < 1e-6):
        return (1e6,'u')
    elif(1e-6 <= abs(time) < 1e-3):
        return (1e3,'m')
    else:
        return (1,'')

#Generator are much more memory efficient 
#when dealing with large datasets. 
#here I design three generators to get the Scanning 
#point set
def lin_generator(start,stop,step):
    '''A python generator for linear variation
    '''
    temp = start
    if(step > 0):
        while(temp <= stop):
            yield temp
            temp += step
    else:
        while(temp >= stop):
            yield temp
            temp += step
            
def dec_generator(start,stop,step):
    '''A python generator for decade variation
    '''
    temp = start
    factor = pow(10, 1./step)
    while(temp <= stop):
        yield temp
        temp *= factor

def oct_generator(start,stop,step):
    '''A python generator for octave variation
    '''
    temp = start
    factor = pow(8,1./step)
    while(temp <= stop):
        yield temp
        temp *= factor

