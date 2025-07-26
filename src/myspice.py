# Author: Yunkun Liao
# Define MySpice class

import pandas as pd
import matplotlib.pyplot as plt
import math

from myparser import *
from solver import *
from plotter import *
from error_define import *
from utilites import *

class MySpice():
    '''MySpice Class
    attributes:
        filename: path of netlist
        pareser: instance of MyParser
        solver: instance of Solver
    methods:
        change_netlist: update the netlist
        parse: instantiate a MyParser object and parse the netlist
        stamp: instantiate a Solver object and solve the netlist      
    '''
    def __init__(self,filename):
        self.filename = filename
        self.parser = None
        self.solver = None
        self.plotter = None
        self.index = []
        self.result_dict = {}
        self.name_ele_dict = {}
    def change_netlist(self,filename):
        self.filename = filename
        self.index = []
        self.result_dict = {}
    def solve(self,method='BE',h=1e-10):
        self.parser = None
        self.solver = None
        self.index = []
        self.result_dict = {}
        self.parse()
        self.analysis(method,h)
        self.plot_result()
        return self.result_dict
    def parse(self):
        self.parser = MyParser()
        self.parser.parse(self.filename)
        self.name_ele_dict = {item.name:item for item in self.parser.element_list}
    def analysis(self,method='BE',h=1e-12):
        self.solver = Solver(self.parser.element_list,self.parser.MNA_dim)
        self.index = []
        for i in range(1,self.parser.MNA_dim):
            if(i < self.parser.node_num):
                self.index.append("v({})".format(self.parser.num2label[i]))
            else:
                self.index.append("i({})".format(self.parser.num2label[i]))
                    
        if(len(self.parser.analysis_list) > 0):
            for analysis in self.parser.analysis_list:
                if(analysis.analysis_type == 'dc'):
                    if(not analysis.double_scan_flag):
                        '''Structure of single source dc_result:dict
                        key: 'src','data','double':False,'src2':None
                        value: 
                            dc_result['src']:str,the sweep source name
                            dc_result['data']:pandas data frame
                                  dc_0  dc_1 ... dc_n
                            v(0)  double
                            v(1)
                            ...
                            i(n)
                        '''
                        dc_result,sweep_list,src_name = self.solver.dc_analysis(analysis)
                        dc_data = pd.DataFrame(dc_result,index=self.index,columns=sweep_list)
                        dc_result = {'src':src_name[0],'data':dc_data,'double':False,'src2':None}
                    else:
                        '''Structure of double source dc_result:dict
                        key:'src','data','double','src2','sweep_list','index'
                        value:
                            dc_result['src']:str,the first sweep source name
                            dc_result['data']:3-D numpy array
                            dc_result['double']:bool:True
                            dc_result['src2']:str,the second sweep source name
                            dc_result['sweep_list']:2-d list,tuplt as element
                        '''
                        dc_result,sweep_list,src_name = self.solver.dc_analysis(analysis)
                        dc_result = {'src':src_name[0],'data':dc_result,'double':True,\
                                    'src2':src_name[1],'sweep_list':sweep_list,'index':self.index}
                    self.result_dict['dc'] = dc_result
                elif(analysis.analysis_type == 'ac'):
                    '''Structure of ac_result:pandas data frame
                            freq0  freq1  ...  freqn
                    v(0)   complex
                    v(1)
                    ...
                    i(n)
                    '''
                    ac_result,sweep_list = self.solver.ac_analysis(analysis)
                    ac_result = pd.DataFrame(ac_result,index=self.index,columns=sweep_list)
                    self.result_dict['ac'] = ac_result
                elif(analysis.analysis_type == 'tran'):
                    tran_data,time_series = self.solver.tran_analysis(analysis,method,h)
                    tran_result = pd.DataFrame(tran_data,index=self.index,columns=time_series)
                    self.result_dict['tran'] = tran_result
                else:
                    self.solver.op_analysis()
                    op_result = pd.DataFrame(self.solver.ANS,index=self.index)
                    self.result_dict['op'] = op_result
        else:
            self.solver.op_analysis()
            op_result = pd.DataFrame(self.solver.ANS,index=self.index)
            self.result_dict['op'] = op_result
        self.nonlinear_data_gen()
    def plot(self):
        self.plotter = Plotter(self.parser.print_dict,self.result_dict,self.index)
        self.plotter.plot_v2()
    def print_MNA_RHS(self):
        '''
        This funcion print MNA and RHS to the console,
        only for debug and assignment use.
        '''
        if(self.solver):
            print('-------------MNA---------------\n')
            print(self.solver.MNA)
            print('-------------RHS---------------\n')
            print(self.solver.RHS)
    def print_ANS(self):
        '''
        This functoin print ANS to the console,
        only for debug and assignment use
        '''
        print('--------------ANS-----------------\n')
        if(len(self.solver.ANS)):
            for i in range(1,self.parser.MNA_dim):
                if(i < self.parser.node_num):
                    # Voltage
                    print("v({})={} V".format(self.parser.num2label[i],self.solver.ANS[i-1]))
                else:
                    # Current
                    print("i({})={} A".format(self.parser.num2label[i],self.solver.ANS[i-1]))
    def print_result(self):
        for key,value in self.result_dict.items():
            if(key == 'op'):
                print(key +' analysis\n')
                print(value)
    def N_R_Convergence(self):
        converge_num = 0
        non_converge_num = 0
        MAX_ITERNUM = 2000
        converge = [i for i in self.solver.iternum_list if i <= MAX_ITERNUM]
        non_converge = [i for i in self.solver.iternum_list if i > MAX_ITERNUM]
        converge_num = len(converge)
        converge_aver = 'inf' if (len(converge) == 0) else sum(converge) / len(converge)
        non_converge_num = len(non_converge)
        print('converge_num:{}'.format(converge_num))
        print('converge_aver:{}'.format(converge_aver))
        print('non_converge_num:{}'.format(non_converge_num))

    def nonlinear_data_gen(self):
        '''
        Generate data for i(diode) and i(mos)
        '''
        if(self.solver.nonlinear_list):
            for element in self.solver.nonlinear_list:
                self.index.append('i({})'.format(element.name))
                if(element.device_type == 'd'):
                    for key,value in self.result_dict.items():
                        if(key == 'dc' and value['double']==True):
                            '''Because the data structure for double-scan
                            dc analysis result is different from others,it
                            need special handler to generate data for non-linear
                            elements
                            '''
                            data = value['data']      
                            dimension = data.shape
                            z = np.zeros((dimension[0],dimension[1],1))
                            value['data'] = np.concatenate((data,z),axis=2)
                            for i in range(dimension[0]):
                                for j in range(dimension[1]):
                                    if(element.p_internal == 0):
                                        p_vol = 0
                                    else:
                                        p_vol = value['data'][i,j,element.p_internal-1]
                                    if(element.n_internal == 0):
                                        n_vol = 0
                                    else:
                                        n_vol = value['data'][i,j,element.n_internal-1]
                                    vd = (p_vol-n_vol)
                                    i_dio = element.get_Id(vd)
                                    value['data'][i,j,dimension[2]] = i_dio
                            value['index'].append('i({})'.format(element.name))
                        else:
                            if(key == 'dc'):
                                value = value['data']
                            result_dim = len(value.columns)
                            gnd = np.zeros((1,result_dim))
                            if(element.p_internal == 0):
                                p_vol = gnd
                            else:
                                p_vol = value.iloc[element.p_internal-1,:].values
                            if(element.n_internal == 0):
                                n_vol = gnd
                            else:
                                n_vol = value.iloc[element.n_internal-1,:].values
                            vd = (p_vol - n_vol).reshape((1,result_dim))
                            i_dio = np.zeros((1,result_dim))
                            for i in range(result_dim):
                                i_dio[0,i] = element.get_Id(vd[0,i])
                            i_dio = pd.DataFrame(i_dio,index=['i({})'.format(element.name)],columns=value.columns)
                            if(key == 'dc'):
                                self.result_dict[key]['data'] = value.append(i_dio)
                            else:
                                self.result_dict[key] = value.append(i_dio)
                elif(element.device_type == 'mos'):
                    for key,value in self.result_dict.items():
                        if(key == 'dc' and value['double']==True):
                            '''Because the data structure for double-scan
                            dc analysis result is different from others,it
                            need special handler to generate data for non-linear
                            elements
                            '''
                            data = value['data']      
                            dimension = data.shape
                            z = np.zeros((dimension[0],dimension[1],1))
                            value['data'] = np.concatenate((data,z),axis=2)
                            for i in range(dimension[0]):
                                for j in range(dimension[1]):
                                    if(element.node_d == 0):
                                        d_vol = 0
                                    else:
                                        d_vol = value['data'][i,j,element.node_d-1]
                                    if(element.node_g == 0):
                                        g_vol = 0
                                    else:
                                        g_vol = value['data'][i,j,element.node_g-1]
                                    if(element.node_s == 0):
                                        s_vol = 0
                                    else:
                                        s_vol = value['data'][i,j,element.node_s-1]
                                    vgs = g_vol - s_vol
                                    vds = d_vol - s_vol
                                    i_mos = element.get_Id(vgs,vds)
                                    value['data'][i,j,dimension[2]] = i_mos
                            value['index'].append('i({})'.format(element.name))
                        else:
                            if(key == 'dc'):
                                value = value['data']
                            else:
                                pass
                            result_dim = len(value.columns)
                            gnd = np.zeros((1,result_dim))
                            if(element.node_d == 0):
                                d_vol = gnd
                            else:
                                d_vol = value.iloc[element.node_d-1,:].values
                            if(element.node_g == 0):
                                g_vol = gnd
                            else:
                                g_vol = value.iloc[element.node_g-1,:].values
                            if(element.node_s == 0):
                                s_vol = gnd
                            else:
                                s_vol = value.iloc[element.node_s-1,:].values
                            vgs = (g_vol - s_vol).reshape((1,result_dim))
                            vds = (d_vol - s_vol).reshape(1,result_dim)
                            if(key == 'op'):
                                i_mos = element.get_Id(vgs[0],vds[0])
                                i_mos = pd.DataFrame([i_mos],index=['i({})'.format(element.name)])
                                self.result_dict[key] = value.append(i_mos)
                            else:  
                                i_mos = np.zeros((1,result_dim))
                                for i in range(result_dim):
                                    i_mos[0,i] = element.get_Id(vgs[0,i],vds[0,i])
                                i_mos = pd.DataFrame(i_mos,index=['i({})'.format(element.name)],columns=value.columns)
                                if(key == 'dc'):
                                    self.result_dict[key]['data'] = value.append(i_mos)
                                else:
                                    self.result_dict[key] = value.append(i_mos)
                else:
                    pass
        else:
            pass
    