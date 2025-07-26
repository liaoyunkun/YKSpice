#Author:Yunkun Liao
#This module defines some error that may happen
class Error(Exception):
    '''Base class for exceptions in this module.'''
    pass

class ParseError(Error):
    '''Exception raised for errors during the parsing process.
    Attributes:
        position -- position in which the error occurred
        expression -- input expression in which the error occurred
        message -- explanation of the error
    '''
    def __init__(self, position,expression,message):
        self.position = 'Error position: line '+str(position)
        self.expression = expression
        self.message = message

class UnsupportError(ParseError):
    '''Exception raised for errors if the command is unsupported currently
        during parsing process
    Attributes:
        same as ParseError
    '''
    pass

class NetlistSyntaxError(ParseError):
    '''Exception raised for errors if the syntax is wrong currently
        during parsing process
    Attributes:
        same as ParseError
    '''
    pass

class NoGndError(Error):
    '''Exception raised if there is no '0'(gnd) node
        in the netlist
    '''
    def __init__(self,message):
        self.message = message

class StampError(Error):
    '''Exception raised for errors during the stamping process
    Attributes:
        message: Error message
    '''
    def __init__(self,message):
        self.message = message

class PlotError(Error):
    '''Exception raised for error during the plotting process
    Attributes:
        message: Error message
    '''
    def __init__(self,message):
        self.message = message

class UnsupportedMethod(Error):
    '''
    Methods except for FE,BE,TR are unsupported! 
    '''
    def __init__(self,message):
        self.message = message

class FileError(Error):
    '''
    No file loaded
    '''
    def __init__(self,message):
        self.message = message
