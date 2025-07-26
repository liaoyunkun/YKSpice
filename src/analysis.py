# Author: Yunkun Liao
# Managing all analysis objects
# Analysis Command

class AnalysisDC():
    '''DC analysis
    attributes:
        device_type = 'dc'
        src1: the value of the sweep points are put into 
            generator1   
        generator1:
        double_scan_flag: indicate whether needs double scan(
            two source)
        src2: the value of the sweep points are put into 
            generator2
        generator2:
    '''
    def __init__(self,src1,generator1,double_scan_flag=False,src2='',generator2=0):
        self.analysis_type = 'dc'
        self.src1 = src1
        self.generator1 = generator1
        self.double_scan_flag = double_scan_flag
        self.src2 = src2
        self.generator2 = generator2

class AnalysisAC():
    '''AC analysis
    attributes:
        analysis_type = 'ac'
    '''
    def __init__(self,generator):
        self.analysis_type = 'ac'
        self.generator = generator

class AnalysisTran():
    '''Tran Analysis
    attributes:
        analysis_type = 'tran'
        uic_flag: indicate whether use initiali condition
    '''
    def __init__(self,generator,step,max_step_size,uic_flag=0):
        self.analysis_type = 'tran'
        self.generator = generator
        self.step = step
        self.uic_flag = uic_flag
        self.max_step_size = max_step_size

class AnalysisOP():
    '''Operating Point Analysis
        When an .OP statement is included in an input file, 
        the DC operating point of the circuit is calculated. 
        You can also use the .OP statement to produce an operating
        point during a transient analysis. Only one .OP statement 
        can appear in a StarHspice simulation
        attributes:
        device_type = 'op'
    '''
    def __init__(self):
        self.analysis_type = 'op'
# Control Command Class

class PrintCmd():
    '''Print Command
    attributes: 
        var: the type of value to be printed,i or v
        ac_unit:
            r - real part
            i - imaginary part
            m - magnitude (by default)
            p - phase
            db - 20 *log10(magnitude)
        difference_flag: whether we need a differnetial value
        node_list: the node
    '''
    def __init__(self,var_type,ac_unit,difference_flag,node_list):
        self.var_type = var_type
        self.ac_unit = ac_unit
        self.difference_flag = difference_flag
        self.node_list = node_list
    def __repr__(self):
        return "var_type:{},ac_unit:{},difference_flag:{},node_list:{}".format(self.var_type,
                         self.ac_unit,self.difference_flag,self.node_list)