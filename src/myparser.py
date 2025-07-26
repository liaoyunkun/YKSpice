# Author:Yunkun liao
# Managing the netlist parser

import re
import math
from collections import defaultdict

from utilites import*
from error_define import*
from devices import *
from analysis import *

class MyParser():
    '''Parser Class
    The class defines a parser for spice netlist
    initialization param:
        filename: str -> name of the spice netlist
    attribute:
        element_list: list -> keep the device instances in the netlist
        analysis_list: list -> keep the analysis instances in the netlist
        print_dict: dict -> key: analysis type('dc','ac','tran'),
                            value: list -> keep the PrintCmd instance
        model_list: list -> list -> keep the information of models defined
                            in the netlist(To do!!!)
        ctrl_list: list -> list -> keep the information of control command(To do!!!)
        node_dict: dict -> key: external node(str)
                            value: internal node(int) number
        node_num: int -> the number of nodes in the netlist
        branch_dcit: dict -> key: the name of devices whose branch flag = True,
                            value: internal branch number
        branch_num: int -> the number of branches in the netlist
        num2label: dict -> key: label of the node or branch
                        value: num of the node or branch in MNA
        MNA_dim: int -> the dimension of MNA
    return:
        No return
    '''
    def __init__(self):
        self.element_list = None
        self.analysis_list = None
        self.print_dict = None
        self.model_list = None
        self.ctrl_list = None
        self.node_dict = None
        self.branch_dict = None
        self.node_num = None
        self.branch_num = None
        self.MNA_dim = None
        self.num2label = None
    
    def parse(self,filename):
        with open(filename, "r") as netlist:
            self.element_list = []
            self.analysis_list = []
            self.print_dict = {'dc':[],'ac':[],'tran':[]}
            self.model_list = []
            self.ctrl_list = []
            self.node_set = set()  # record the node
            self.node_dict = defaultdict(self.default_factory_node)
            self.node_dict['0'] = 0  # default gnd node 
            self.node_num = 1  # by default we have gnd node
            self.branch_dict = defaultdict(self.default_factory_branch)
            self.branch_num = 0
            self.MNA_dim = 0 
            line_number = 0
            while(True):
                try:
                    line = netlist.readline()
                    line_number += 1
                    line = line.strip().lower()
                    if(line == '.end'):
                        break
                    else:
                        # Comment line,empty line
                        if(line == '' or line == '\n' or line == '\r\n' or line_number == 1 or line[0] == '*'):
                            continue
                        
                        # Device
                        elif(line[0] == 'r'):
                            res = self.parse_resistor(line_number,line)
                            self.node_set.add(res['pnode'])
                            self.node_set.add(res['nnode'])
                            pnode_inter = self.node_dict[res['pnode']]
                            nnode_inter = self.node_dict[res['nnode']]
                            _res = Resistor(res['name'],res['value'],pnode_inter,nnode_inter)
                            self.element_list.append(_res)
                        elif(line[0] == 'c'):
                            cap = self.parse_capacitor(line_number,line)
                            self.node_set.add(cap['pnode'])
                            self.node_set.add(cap['nnode'])
                            pnode_inter = self.node_dict[cap['pnode']]
                            nnode_inter = self.node_dict[cap['nnode']]
                            branch = self.branch_dict[cap['name']]
                            _cap = Capacitor(cap['name'],cap['value'],pnode_inter,nnode_inter,cap['ic'],branch)
                            self.element_list.append(_cap)
                        elif(line[0] == 'l'):
                            ind = self.parse_inductor(line_number,line)
                            self.node_set.add(ind['pnode'])
                            self.node_set.add(ind['nnode'])
                            pnode_inter = self.node_dict[ind['pnode']]
                            nnode_inter = self.node_dict[ind['nnode']]
                            branch = self.branch_dict[ind['name']]
                            _ind = Inductor(ind['name'],ind['value'],pnode_inter,nnode_inter,ind['ic'],branch)
                            self.element_list.append(_ind)
                        elif(line[0] == 'd'):
                            dio = self.parse_diode(line_number,line)
                            if(dio['model'] not in ['diode']):
                                raise UnsupportError(line_number,line,'Unsupported diode model!')
                            else:
                                pass
                            self.node_set.add(dio['pnode'])
                            self.node_set.add(dio['nnode'])
                            pnode_inter = self.node_dict[dio['pnode']]
                            nnode_inter = self.node_dict[dio['nnode']]
                            _dio = Diode(dio['name'],pnode_inter,nnode_inter,dio['model'],dio['ic'])
                            self.element_list.append(_dio)
                        elif(line[0] == 'm'):
                            mos = self.parse_mos(line_number,line)
                            if(mos['model'] not in ['nmos','pmos']):
                                raise UnsupportError(line_number,line,'Unsupported mosfet model!')
                            else:
                                pass
                            self.node_set.add(mos['node_d'])
                            self.node_set.add(mos['node_g'])
                            self.node_set.add(mos['node_s'])
                            self.node_set.add(mos['node_b'])
                            node_d_inter = self.node_dict[mos['node_d']]
                            node_g_inter = self.node_dict[mos['node_g']]
                            node_s_inter = self.node_dict[mos['node_s']]
                            node_b_inter = self.node_dict[mos['node_b']]
                            _mos = MOS(mos['name'],mos['model'],node_d_inter,
                                    node_g_inter,node_s_inter,node_b_inter,
                                    mos['length'],mos['width'])
                            self.element_list.append(_mos)
                        elif(line[0] == 'v'):
                            vol = self.parse_vsource(line_number,line)
                            self.node_set.add(vol['pnode'])
                            self.node_set.add(vol['nnode'])
                            pnode_inter = self.node_dict[vol['pnode']]
                            nnode_inter = self.node_dict[vol['nnode']]
                            branch = self.branch_dict[vol['name']]
                            dc = vol['dc_value']
                            ac = vol['ac_complex']
                            tran = vol['tran']
                            name = vol['name']
                            _vol = VSource(name,dc,pnode_inter,nnode_inter,ac,tran,branch)
                            self.element_list.append(_vol)
                        elif(line[0] == 'i'):
                            cur = self.parse_isource(line_number,line)
                            self.node_set.add(cur['pnode'])
                            self.node_set.add(cur['nnode'])
                            pnode_inter = self.node_dict[cur['pnode']]
                            nnode_inter = self.node_dict[cur['nnode']]
                            dc = cur['dc_value']
                            ac = cur['ac_complex']
                            tran = cur['tran']
                            name = cur['name']
                            _cur = ISource(name,dc,pnode_inter,nnode_inter,ac,tran)
                            self.element_list.append(_cur)
                        elif(line[0] == 'e'):
                            vcvs = self.parse_vcvs(line_number,line)
                            self.node_set.add(vcvs['pnode'])
                            self.node_set.add(vcvs['nnode'])
                            self.node_set.add(vcvs['pnode_ctrl'])
                            self.node_set.add(vcvs['nnode_ctrl'])
                            pnode_inter = self.node_dict[vcvs['pnode']]
                            nnode_inter = self.node_dict[vcvs['nnode']]
                            pnode_ctrl_inter = self.node_dict[vcvs['pnode_ctrl']]
                            nnode_ctrl_inter = self.node_dict[vcvs['nnode_ctrl']]
                            branch = self.branch_dict[vcvs['name']]
                            _vcvs = VCVS(vcvs['name'],vcvs['vol_gain'],pnode_inter,
                                    nnode_inter,branch,pnode_ctrl_inter,nnode_ctrl_inter)
                            self.element_list.append(_vcvs)
                        elif(line[0] == 'f'):
                            cccs = self.parse_cccs(line_number,line)
                            self.node_set.add(cccs['pnode'])
                            self.node_set.add(cccs['nnode'])
                            pnode_inter = self.node_dict[cccs['pnode']]
                            nnode_inter = self.node_dict[cccs['nnode']]
                            branch_ctrl = self.branch_dict[cccs['vnam']]
                            _cccs = CCCS(cccs['name'],cccs['cur_gain'],pnode_inter,nnode_inter,branch_ctrl)
                            self.element_list.append(_cccs)
                        elif(line[0] == 'g'):
                            vccs = self.parse_vccs(line_number,line)
                            self.node_set.add(vccs['pnode'])
                            self.node_set.add(vccs['nnode'])
                            self.node_set.add(vccs['pnode_ctrl'])
                            self.node_set.add(vccs['nnode_ctrl'])
                            pnode_inter = self.node_dict[vccs['pnode']]
                            nnode_inter = self.node_dict[vccs['nnode']]
                            pnode_ctrl_inter = self.node_dict[vccs['pnode_ctrl']]
                            nnode_ctrl_inter = self.node_dict[vccs['nnode_ctrl']]
                            _vccs = VCCS(vccs['name'],vccs['transconductance'],pnode_inter,
                                        nnode_inter,pnode_ctrl_inter,nnode_ctrl_inter)
                            self.element_list.append(_vccs)
                        elif(line[0] == 'h'):
                            ccvs = self.parse_ccvs(line_number,line)
                            self.node_set.add(ccvs['pnode'])
                            self.node_set.add(ccvs['nnode'])
                            pnode_inter = self.node_dict[ccvs['pnode']]
                            nnode_inter = self.node_dict[ccvs['nnode']]
                            branch = self.branch_dict[ccvs['name']]
                            branch_ctrl = self.branch_dict[ccvs['vnam']]
                            _ccvs = CCVS(ccvs['name'],ccvs['transresistance'],pnode_inter,nnode_inter,branch,branch_ctrl)
                            self.element_list.append(_ccvs) 

                        # Model definition
                        elif(line.startswith('.model')):
                            # Without Class
                            model = self.parse_model(line_number,line)
                            self.model_list.append(model)
                            
                        # Control Command
                        elif(line.startswith('.print') or line.startswith('.plot')):
                            print_command = self.parse_print(line_number,line)
                            self.print_dict[print_command['type']].extend(print_command['variables'])
                        elif(line.startswith('.option')):
                            ctrl = self.parse_ctrl(line_number,line)
                            self.ctrl_list.append(ctrl)
                        
                        # Analysis
                        elif(line.startswith('.dc')):
                            dc = self.parse_dc(line_number,line)
                            self.analysis_list.append(dc)
                        elif(line.startswith('.ac')):
                            ac = self.parse_ac(line_number,line)
                            self.analysis_list.append(ac)
                        elif(line.startswith('.op')):
                            op = self.parse_op(line)
                            self.analysis_list.append(op)
                        elif(line.startswith('.tran')):
                            tran = self.parse_tran(line_number,line)
                            self.analysis_list.append(tran)
                        else:
                            raise UnsupportError(line_number,line,'Unsupported command now')
                except NetlistSyntaxError:
                    print('parse error:occured in line {:d},Wrong Syntax'.format(line_number))
                    raise NetlistSyntaxError(line_number,line,'Wrong Synatax')
                except UnsupportError:
                    print('parse error:occured in line {:d},Unsupport Error'.format(line_number))
                    raise UnsupportError(line_number,line,'Unsupported command now')
                finally:
                    pass
            if('0' not in self.node_set):
                print("Can't find 0(gnd) Node")
                raise NoGndError("Can't find 0(gnd) Node")
            self.merge_node_branch()
            self.MNA_dim = self.node_num + self.branch_num


    # Method for parsing devices
    def parse_resistor(self,line_number,line):
        '''Parse resistor
        general syntax:
            Rname <node> <node> <val>
        param:
            line_number: int -> for error info
            line: str -> command
        return:
            a dict descrinbing resistor
        '''
        component = line.split()
        if(len(component) != 4):
            raise NetlistSyntaxError(line_number, line, 'lack of argument')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            value = scale_factor_convert(value_extract(line_number,line,component[3]))
            res = {'type':'r','name':name,'pnode':pnode,'nnode':nnode,'value':value}
            return res
    
    def parse_capacitor(self,line_number,line):
        '''Parse capacitor
        general syntax:
            CXXXXXXX N+ N- VALUE < IC=INCOND >
            default IC=0v
        param:
            line_number: int -> for error info
            line: str -> command
        return:
            a dict descrinbing capacitor
        '''
        component = line.split()
        if(len(component) < 4):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            value = scale_factor_convert(value_extract(line_number,line,component[3]))
            if(len(component) >= 5):
                # ic=3v or ic =3v or ic= 3v or ic = 3v 
                ic_value = line[re.search(r'ic( )*=',line).span()[1]:].strip()
                ic = scale_factor_convert(value_extract(line_number,line,ic_value))
            else:
                # default value for ic = 0v
                ic = 0.
            cap = {'type':'c','name':name,'pnode':pnode,'nnode':nnode,'value':value,'ic':ic}
            return cap
    
    def parse_inductor(self,line_number,line):
        '''Parse inductor
        general syntax:
            LYYYYYYY N+ N- VALUE < IC=INCOND >
            default IC=0a
        param:
            line_number: int -> for error info
            line: str -> command
        return:
            a dict descrinbing inductor
        '''
        component = line.split()
        if(len(component) < 4):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            value = scale_factor_convert(value_extract(line_number,line,component[3]))
            if(len(component) >= 5):
                # ic=3a or ic =3a or ic= 3a or ic = 3a 
                ic_value = line[re.search(r'ic( )*=',line).span()[1]:].strip()
                ic = scale_factor_convert(value_extract(line_number,line,ic_value))
            else:
                # default value for ic = 0
                ic = 0.
            ind = {'type':'l','name':name,'pnode':pnode,'nnode':nnode,'value':value,'ic':ic}
            return ind
    def parse_diode(self,line_number,line):
        '''Parse diode
        general syntax:
            DXXXXXXX N+ N- MNAME <AREA> <OFF> <IC=VD> <TEMP=T>
            default ic=0,area=1.0
            <TEMP>,<OFF> is unsupported,no error info now
        param:
            line_number: int -> for error info
            line: str -> command
        return:
            a dict descrinbing diode
        '''
        component = line.split()
        if(len(component) < 4):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else: 
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            model = component[3]
            area = 0.  # Default area
            ic = 0.  #Default ic
            if(re.search(r'ic( )*=',line)):
                pre_line = line[:re.search(r'ic( )*=',line).span()[0]]
                ic_str = line[re.search(r'ic( )*=',line).span()[0]:]
                if(len(pre_line.split()) == 5):
                    area = scale_factor_convert(pre_line.split()[-1])
                ic_value = ic_str[re.search(r'ic( )*=',ic_str).span()[1]:].strip()
                ic = scale_factor_convert(value_extract(line_number,line,ic_value))
            else:
                if(len(component) == 5):
                    area = scale_factor_convert(value_extract(line_number,line,component[-1]))
            dio = {'type':'d','name':name,'pnode':pnode,'nnode':nnode,'model':model,'area':area,'ic':ic}
            return dio
                   
    def parse_mos(self,line_number,line):
        '''Parse mos transistor
        general syntax:
            MXXXXXXX ND NG NS NB MNAME <L=VAL> <W=VAL>
            default l=16nm,w=32nm
            Other option is unsupported,no error info now
        param:
            line_number: int -> for error info
            line: str -> command
        return:
            a dict descrinbing mos transistor
        '''
        component = line.split()
        if(len(component) < 6):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else:     
            name = component[0]
            node_d = component[1]
            node_g = component[2]
            node_s = component[3]
            node_b = component[4]
            model = component[5]
            length = 16e-09  #default lenght
            width = 32e-09  #default width
            if(re.search(r'l( )*=( )*[0-9]+\.?[0-9]*(meg)?[numkg]?',line)):
                span_l = re.search(r'l( )*=( )*[0-9]+\.?[0-9]*(meg)?[numkg]?',line).span()
                length_str = line[span_l[0]:span_l[1]]
                lenght_val = length_str[re.search(r'l( )*=( )*[^\w]*',length_str).span()[1]:]
                length = scale_factor_convert(lenght_val)
            if(re.search(r'w( )*=( )*[0-9]+\.?[0-9]*(meg)?[numkg]?',line)):
                span_w = re.search(r'w( )*=( )*[0-9]+\.?[0-9]*(meg)?[numkg]?',line).span()
                width_str = line[span_w[0]:span_w[1]]
                width_val = width_str[re.search(r'w( )*=( )*[^\w]*',width_str).span()[1]:]
                width = scale_factor_convert(width_val)
            mos = {'type':'m','name':name,'node_d':node_d,'node_g':node_g,'node_s':node_s,'node_b':node_b,
                   'model':model,'length':length,'width':width}
            return mos

    def parse_vsource(self,line_number,line):
        '''Parse independent voltage source
        general syntax:
            VXXXXXXX N+ N- << DC > DC/TRAN VALUE> < AC < ACMAG <ACPHASE >>>>
            For transient analysis an independent source can be a
            time-dependent function
            Other option is unsupported,no error info now
        param:
            line_number: int -> for error info
            line: str -> command
        return:
            a dict descrinbing independent voltage source
        '''
        component = line.split()
        if(len(component) < 3):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            dc_value = -1  # default dc value,
            #dc_value=-1 means that if DC source is missing
            #If a source is a time-dependent function, the 0-time
            #value is used for DC analysis ().
            ac_complex = 0  # default ac info
            time_func = None  # default time function is None
            if(len(component) > 3):
                # DC Infomation
                if(line[3] == 'dc'):
                    dc_value = scale_factor_convert(component[4])
                else:
                    if(re.match(r'-?[0-9]+\.?[0-9]*(meg)?[numkg]?',component[3])):
                        dc_value = scale_factor_convert(value_extract(line_number,line,component[3]))
                # AC Information
                ac_match = re.search(r'ac\s+-?[0-9]+\.?[0-9]*(meg)?[numkg]?\s*[0-9]*\.?[0-9]*',line)
                if(ac_match):
                    ac_info = ac_match.group().split()
                    ac_mag = scale_factor_convert(ac_info[1])
                    ac_phase = 0
                    if(len(ac_info) == 3):
                        ac_phase = eval(ac_info[2])
                    # Convert (mag,phase) to complex form
                    real = ac_mag * math.cos(math.pi * ac_phase/180)
                    imag = ac_mag * math.sin(math.pi * ac_phase/180)
                    ac_complex = complex(real,imag)
                # Time function Information for Tran
                if(re.search(r'pulse|sin|pwl|const',line)):
                    time_func_str = line[re.search(r'pulse|sin|pwl|const',line).span()[0]:]
                    time_func = self.parse_timefunc(line_number,time_func_str)
            vsource = {'type':'v','name':name,'pnode':pnode,'nnode':nnode,
                       'dc_value':dc_value,'ac_complex':ac_complex,'tran':time_func}
            return vsource
            
    def parse_isource(self,line_number,line):
        '''Parse independent current source
        general syntax:
            VXXXXXXX N+ N- << DC > DC/TRAN VALUE> < AC < ACMAG <ACPHASE >>>>
            For transient analysis an independent source can be a
            time-dependent function
            Other option is unsupported,no error info now
        param:
            line_number: int -> for error info
            line: str -> command
        return:
            a dict descrinbing independent current source
        '''
        component = line.split()
        if(len(component) < 3):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            dc_value = 0  # default dc value
            ac_complex = 0  # default ac info
            time_func = None  # default time functoin
            if(len(component) > 3):
                # DC Infomation
                if(line[3] == 'dc'):
                    dc_value = scale_factor_convert(value_extract(line_number,line,component[4]))
                else:
                    if(re.match(r'-?[0-9]*\.?[0-9]*(meg)?[numkg]?',component[3])):
                        dc_value = scale_factor_convert(value_extract(line_number,line,component[3]))
                # AC Information
                ac_match = re.search(r'ac\s+[0-9]+\.?[0-9]*(meg)?[numkg]?\s*[0-9]*\.?[0-9]*',line)
                if(ac_match):
                    ac_info = ac_match.group().split()
                    ac_mag = scale_factor_convert(ac_info[1])
                    ac_phase = 0
                    if(len(ac_info) == 3):
                        ac_phase = eval(ac_info[2])
                    # Convert (mag,phase) to complex form
                    real = ac_mag * math.cos(math.pi * ac_phase/180)
                    imag = ac_mag * math.sin(math.pi * ac_phase/180)
                    ac_complex = complex(real,imag)
                # Time function Information
                if(re.search(r'pulse|sin|pwl|const',line)):
                    time_func_str = line[re.search(r'pulse|sin|pwl|const',line).span()[0]:]
                    time_func = self.parse_timefunc(line_number,time_func_str)
            isource = {'type':'i','name':name,'pnode':pnode,'nnode':nnode,
                       'dc_value':dc_value,'ac_complex':ac_complex,'tran':time_func}
            return isource

    # Linear Dependent Source
    def parse_vcvs(self,line_number,line):
        '''Parse Voltage Controlled Voltage Source
        general syntax:
            EXXX N+ N- NC+ NC- VALUE
        '''
        component = line.split()
        if(len(component) != 6):
            raise NetlistSyntaxError(line_number,line,'Wrong definition!')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            pnode_ctrl = component[3]
            nnode_ctrl = component[4]
            vol_gain = scale_factor_convert(value_extract(line_number,line,component[5]))
            vcvs = {'name':name,'pnode':pnode,'nnode':nnode,'pnode_ctrl':pnode_ctrl,'nnode_ctrl':nnode_ctrl,'vol_gain':vol_gain}
            return vcvs

    def parse_cccs(self,line_number,line):
        '''Parse Current Controlled Current Source
        general syntax:
            FXXX N+ N- VNAM VALUE
        '''
        component = line.split()
        if(len(component) != 5):
            raise NetlistSyntaxError(line_number,line,'Wrong definition!')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            vnam = component[3]
            cur_gain = scale_factor_convert(value_extract(line_number,line,component[4]))
            cccs = {'name':name,'pnode':pnode,'nnode':nnode,'vnam':vnam,'cur_gain':cur_gain}
            return cccs

    def parse_vccs(self,line_number,line):
        '''Parse Voltage Controlled Current Source
        general syntax:
            GXXX N+ N- NC+ NC- VALUE
        '''
        component = line.split()
        if(len(component) != 6):
            raise NetlistSyntaxError(line_number,line,'Wrong definition!')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            pnode_ctrl = component[3]
            nnode_ctrl = component[4]
            transconductance = scale_factor_convert(value_extract(line_number,line,component[5]))
            vccs = {'name':name,'pnode':pnode,'nnode':nnode,'pnode_ctrl':pnode_ctrl,'nnode_ctrl':nnode_ctrl,'transconductance':transconductance}
            return vccs

    def parse_ccvs(self,line_number,line):
        '''Parse Current Controlled Voltage Source
        general syntax;
            HXXX N+ N- VNAM VALUE
        '''
        component = line.split()
        if(len(component) != 5):
            raise NetlistSyntaxError(line_number,line,'Wrong definition!')
        else:
            name = component[0]
            pnode = component[1]
            nnode = component[2]
            vnam = component[3]
            transresistance = scale_factor_convert(value_extract(line_number,line,component[4]))
            ccvs = {'name':name,'pnode':pnode,'nnode':nnode,'vnam':vnam,'transresistance':transresistance}
            return ccvs


    def parse_model(self,line_number,line):
        '''Parse model definition
        general syntax:
            .MODEL MNAME MTYPE (PNAME1=PVAL1 PNAME2=PVAL2 ... )
            only support MTYPE = R/C/D/PMOS/NMOS now
        param:
        return:
            a dict describing the model definition
        '''
        #To do!!!
        component = line.split()
        if(len(component) < 4):
            raise NetlistSyntaxError(line_number,line,'Unable to  define a model')
        else:
            model = {'model_name':component[1],'model_type':component[2],'define':component[2:]}
            return model

    # Method for parsing time-varient source
    def parse_timefunc(self,line_number,time_func):
        '''Parse time function independent source
        current support source: ref from hspice
            PULSE(V1 V2 TD TR TF PW PER)
            SIN (Vo Va Freq Td Df Phase)
            PWL (T1 V1 T2 V2 T3 V3 ... Tn Vn ... )
        param:
            time_func:str,pulse(-1 1 2ns 2ns 2ns 50ns 100ns)
        return:
            a SinSource instance or a PulseSource instance or a PWL list
        '''
        if(time_func.startswith('pulse')):
            val_str = time_func[5:]
            start = val_str.find('(')
            if(start != -1):
                val_str = val_str[start+1:]
                end = val_str.find(')')
                val_str = val_str[:end]
            component = val_str.split()
            if(len(component) != 7):
                raise NetlistSyntaxError(line_number,time_func,'unable to define a pulse')
            else:
                v1 = scale_factor_convert(value_extract(line_number,time_func,component[0]))
                v2 = scale_factor_convert(value_extract(line_number,time_func,component[1]))
                td = scale_factor_convert(value_extract(line_number,time_func,component[2]))
                tr = scale_factor_convert(value_extract(line_number,time_func,component[3]))
                tf = scale_factor_convert(value_extract(line_number,time_func,component[4]))
                pw = scale_factor_convert(value_extract(line_number,time_func,component[5]))
                per = scale_factor_convert(value_extract(line_number,time_func,component[6]))
                pulse = PulseSource(v1,v2,td,tr,tf,pw,per)
                return pulse
        elif(time_func.startswith('sin')):
            val_str = time_func[3:]
            start = val_str.find('(')
            if(start != -1):
                val_str = val_str[start+1:]
                end = val_str.find(')')
                val_str = val_str[:end]
            component = val_str.split()
            if(len(component) >= 3):
                vo = scale_factor_convert(value_extract(line_number,time_func,component[0]))
                va = scale_factor_convert(value_extract(line_number,time_func,component[1]))
                freq = scale_factor_convert(value_extract(line_number,time_func,component[2]))
                if(len(component) == 4):
                    td = scale_factor_convert(value_extract(line_number,time_func,component[3]))
                    df = 0  #default damping factor = 0
                    theta = 0  #default phase advance = 0
                elif(len(component) == 5):
                    td = scale_factor_convert(value_extract(line_number,time_func,component[3]))
                    df = scale_factor_convert(value_extract(line_number,time_func,component[4]))
                    theta = 0  #default phase advance = 0
                elif(len(component) == 6):
                    td = scale_factor_convert(value_extract(line_number,time_func,component[3]))
                    df = scale_factor_convert(value_extract(line_number,time_func,component[4]))
                    theta = scale_factor_convert(value_extract(line_number,time_func,component[5]))
                else:
                    td = 0  #deafult delay time
                    df = 0  #default damping factor
                    theta = 0  #default phase advance
            else:
                raise NetlistSyntaxError(line_number,time_func,'lack of information to define a sin')
            sin = SinSource(vo,va,freq,td,df,theta)
            return sin
        elif(time_func.startswith('pwl')):
            val_str = time_func[3:]
            start = val_str.find('(')
            if(start != -1):
                val_str = val_str[start+1:]
                end = val_str.find(')')
                val_str = val_str[:end]
            component = val_str.split()
            if(len(component) % 2 != 0):
                raise NetlistSyntaxError(line_number,time_func,'Unable to define a pwl')
            else:
                time = []
                vol = []
                for i in range(len(component)):
                    if(i%2 == 0):
                        time.append(scale_factor_convert(value_extract(line_number,time_func,component[i])))
                    else:
                        vol.append(scale_factor_convert(value_extract(line_number,time_func,component[i])))
                # Haven't been reconstructed
                pwl = PWLSource(time,vol)
                return pwl
        elif(time_func.startswith('const')):
            '''
            CONST(value)
            '''
            val_str = time_func[5:]
            start = val_str.find('(')
            if(start != -1):
                val_str = val_str[start+1:]
                end = val_str.find(')')
                val_str = val_str[:end]
            component = val_str.split()
            if(len(component) != 1):
                raise NetlistSyntaxError(line_number,time_func,'Unable to define a const source')
            else:
                value = eval(val_str)
                const = CONSTSource(value)
                return const
        else: 
            raise UnsupportError(line_number,time_func,'Unsupported Time Function')

    # Method for parsing analysis
    def parse_ac(self,line_number,line):
        '''Parse AC analysis command
        Genaral syntax:
            .AC DEC ND FSTART FSTOP
            .AC OCT NO FSTART FSTOP
            .AC LIN NP FSTART FSTOP
        param:
            line: str
        return:
            a AnalysisAC instance
        '''
        component = line.split()
        if(len(component) < 5):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else: 
            variation_type = component[1]
            num_points_per_decade = scale_factor_convert(component[2])
            start_f = scale_factor_convert(component[3])
            stop_f = scale_factor_convert(component[4])
            step = (stop_f-start_f)/num_points_per_decade
            if(variation_type == 'lin'):
                generator = lin_generator(start_f,stop_f,step)
            elif(variation_type == 'oct'):
                generator = oct_generator(start_f,stop_f,num_points_per_decade)
            elif(variation_type == 'dec'):
                generator = dec_generator(start_f,stop_f,num_points_per_decade)
            else:
                raise NetlistSyntaxError(line_number,line,"Wrong variation type")
            ac = AnalysisAC(generator)
            return ac

    def parse_dc(self,line_number,line):
        '''Parse DC analysis command
        General syntax:
            .DC SRC1 START1 STOP1 INCR1 [SRC2 START2 STOP2 INCR2]
        param:
            line: str
        return:
            a AnalysisDC instance
        '''
        component = line.split()
        if(len(component) < 5):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else:
            source1 = component[1]
            start1 = scale_factor_convert(component[2])
            stop1 = scale_factor_convert(component[3])
            increment1 = scale_factor_convert(component[4])
            generator1 = lin_generator(start1,stop1,increment1)
            double_source_flag = False
            if(len(component) > 5):
                double_source_flag = True
                source2 = component[5]
                start2 = scale_factor_convert(component[6])
                stop2 = scale_factor_convert(component[7])
                increment2 = scale_factor_convert(component[8])
                generator2 = lin_generator(start2,stop2,increment2)
                dc = AnalysisDC(source1,generator1,True,source2,generator2)
                return dc
            else:
                dc = AnalysisDC(source1,generator1)
                return dc

    def parse_op(self,line):
        '''Parse OP analysis command
        param:
            line: str
        return:
            a AnalysisOP instance
        '''
        op = AnalysisOP()
        return op
    
    def parse_tran(self,line_number,line):
        '''Parse tran analysis command
        genearal syntax:
            .TRAN TSTEP TSTOP < TSTART < TMAX >> <UIC>
        param:
            line:str
        return:
            a dict describe tran analysis
        '''
        component = line.split()
        if(len(component) < 3):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else:
            start = 0  #default start time
            uic_flag = False  #default use initial condition flag
            step = scale_factor_convert(value_extract(line_number,line,component[1]))
            stop = scale_factor_convert(value_extract(line_number,line,component[2]))
            max_step_size = (stop-start)/50.0#default max_step_size
            if(re.search(r'uic',line)):
                uic_flag = True
            if(len(component) > 3):
                if(component[3] != 'uic'):
                    start = scale_factor_convert(value_extract(line_number,line,component[3]))
                    max_step_size = (stop-start)/50.0
                    if(len(component) > 4 and component[4] != 'uic'):
                        max_step_size = scale_factor_convert(value_extract(line_number,line,component[4]))
            generator = lin_generator(start,stop,step)
            tran = AnalysisTran(generator,step,max_step_size,uic_flag)
            return tran

    # Method for parsing control command
    def parse_print(self,line_number,line):
        '''Parse .PRINT/.PLOT commmand
        general syntax:
            .PRINT/.PLOT PRTYPE OV1 <OV2 ... OV8>
        param:
            line:str
        return:
            a dict describe total print/plot command,
            key: 'type','variable':list of PrintCmd instance
        '''
        # Haven't been reconstructed
        component = line.split()
        if(len(component) < 3):
            raise NetlistSyntaxError(line_number,line,'lack of argument')
        else:
            print_command = {'type':component[1],'variables':[]}
            ac_flag = print_command['type'] == 'ac'
            for item in component[2:]:
                var_type = item[0]
                ac_unit = 'm'  #default is magnitude
                difference_flag = False
                node_list = []
                start = item.find('(')
                end = item.find(')')
                #node_list = item[start+1:end].split(sep=',')
                if(item[0] == 'v'):
                    if(component[1] == 'ac'):
                        if(start != 1):
                            ac_unit = item[1:start]
                    node_info = item[start+1:end]
                    if(node_info.find(',') != -1):
                        node_list.append(node_info.split(sep=',')[0].strip())
                        node_list.append(node_info.split(sep=',')[1].strip())
                        difference_flag = True
                    else:
                        node_list.append(node_info.strip())
                elif(item[0] == 'i'):
                    if(component[1] == 'ac'):
                        if(start != 1):
                            ac_unit = item[1:start]
                    node_info = item[start+1:end]
                    if(node_info[0] not in ['v','c','l','d','m']):
                        raise UnsupportError(line_number,line,'Unsupported')
                    else:
                        node_list.append(node_info.strip())
                _var = PrintCmd(var_type,ac_unit,difference_flag,node_list)
                print_command['variables'].append(_var)
            return print_command
    def parse_ctrl(self,line_number,line):
        '''Parse control command
        general syntax:
            .OPTION POST
            only support post option,nomod option
        param:
            line_number: int -> for error info
            line: str -> command
        return:
            a dict descrinbing the control info
        '''
        if(line.startswith('.option')):
            ctrl = dict()
            ctrl['type'] = 'option'
            match = re.search(r'post\s*=\s*',line)
            if(match):
                ctrl['post'] = int(value_extract(line_number,line,line[match.span()[1]:].strip()))
            else:
                ctrl['post'] = 1  #default according to hspice
            if(re.search(r'nomod',line)):
                ctrl['nomod'] = True
            else:
                ctrl['nomod'] = False
            return ctrl
        else:
            raise UnsupportError(line_number,line,'Unsupported control command now')
    def print_result(self):
        print('-----devices in the netlist-----\n')
        print(self.element_list)
        print('--------------------------------\n')
        print('-----analysis in the netlist----\n')
        print(self.analysis_list)
        print('--------------------------------\n')
        print('--models defined in the netlist--\n')
        print(self.model_list)
        print('--------------------------------\n')
        print('---------print commands---------\n')
        print(self.print_list)
        print('--------------------------------\n')
        print('---------control commands--------\n')
        print(self.ctrl_list)
    
    # Functions to help construct MNA
    
    def default_factory_node(self):
        '''Factory method for node_dict(defaultdict)
        i_th node -> i-1(for convenience of later MNA construction)
        '''
        self.node_num += 1
        return self.node_num-1
    
    def default_factory_branch(self):
        '''Factory method for branch_dict(defaultdict)
        i_th branch -> i
        '''
        self.branch_num += 1
        return self.branch_num-1

    def merge_node_branch(self):
        '''Method to merge node and branch information for
            later construction of MNA
        The form of MNA:
            ( Y  |  E )(V)
                            =  RHS
            ( F  |  0 )(I)          refer: Pro.Guoyong Shi
        '''
        for item in self.element_list:
            if(item.branch_flag):
                item.branch_num += self.node_num
                if(item.device_type == 'h'):
                    item.branch_num_ctrl += self.node_num
        self.branch_dict = {key:(value+self.node_num) for (key,value) in self.branch_dict.items()}
        temp1 = {value:key for (key,value) in self.node_dict.items()}
        temp2 = {value:key for (key,value) in self.branch_dict.items()}
        self.num2label = {**temp1,**temp2}                  
                    







    
        
            
                    
                        
                    








    
    
    