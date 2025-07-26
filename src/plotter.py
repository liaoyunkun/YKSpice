# Author: Yunkun Liao
# Managing all plotting work

import pandas as pd
import matplotlib.pyplot as plt
import math

from myparser import *
from solver import *
from error_define import *
from utilites import *

class Plotter:
    '''Plotter class
    Attributes:
        print_dict:dict
            key:str->'dc','ac','tran'
            value:dict->dict: {type: ,variables:list 
                        of PrintCmd instance}
        result_dict:dict
            key:str->'dc','ac','tran'
            value:for 'ac' and 'tran',value is a dataframe keeps the
                result of analysis
                for 'dc',value is a dict:(key,val):'src':the source name been
                    sweeped,'data':pandas datafram keeps the result of analysis
        index:list,['v(1)','v(2)',...i(k)]
        figure_num:recorder the number of figures
        figure_list:recorder the figures
    Param:
        print_dict:from parser
        result_dict:from solver
        index:from myspice
    '''
    def __init__(self,print_dict,result_dict,index):
        self.print_dict = print_dict
        self.result_dict = result_dict
        self.index = index
        self.figure_num = 0
        self.figure_list = []
        self.axdc_v = None
        self.axdc_i = None
        self.axac_v = None
        self.axac_i = None
        self.axtran_v = None
        self.axtran_i = None      
    def plot(self):
        for key,value in self.print_dict.items():
            if(len(value) == 0):
                pass
            else:
                '''
                value format:
                    dict: {type: ,variables:list of PrintCmd instance}
                '''
                if(key == 'dc'):
                    for printItem in value:
                        self.plot_dc(printItem)
                elif(key == 'ac'):
                    for printItem in value:
                        self.plot_ac(printItem)
                elif(key == 'tran'):
                    for printItem in value:
                        self.plot_tran(printItem)
                else:
                    pass
    def plot_v2(self):
        for key,value in self.print_dict.items():
            if(len(value) == 0):
                pass
            else:
                '''
                value format:
                    dict: {type: ,variables:list of PrintCmd instance}
                '''
                if(key == 'dc'):
                    for printItem in value:
                        if(printItem.var_type == 'v'):
                            if(not self.axdc_v):
                                self.axdc_v =  plt.figure(1,figsize=(10,10)).subplots()
                            self.plot_dc_v(printItem)
                            self.axdc_v.legend()
                            self.axdc_v.set_title('DC-Voltage')
                        else:
                            if(not self.axdc_i):
                                self.axdc_i = plt.figure(2,figsize=(10,10)).subplots()
                            self.plot_dc_i(printItem)
                            self.axdc_i.legend()
                            self.axdc_i.set_title('DC-Current')
                elif(key == 'ac'):
                    for printItem in value:
                        if(printItem.var_type == 'v'):
                            if(not self.axac_v):
                                self.axac_v = plt.figure(3,figsize=(10,10)).subplots()
                            self.plot_ac_v(printItem)
                            self.axac_v.legend()
                            self.axac_v.set_title('AC-Voltage')
                        else:
                            if(not self.axac_i):
                                self.axac_i = plt.figure(4,figsize=(10,10)).subplots()
                            self.plot_ac_i(printItem)
                            self.axac_i.legend()
                            self.axac_i.set_title('AC-Current')
                elif(key == 'tran'):
                    for printItem in value:
                        if(printItem.var_type == 'v'):
                            if(not self.axtran_v):
                                self.axtran_v = plt.figure(5,figsize=(10,10)).subplots()
                            self.plot_tran_v(printItem)
                            self.axtran_v.legend()
                            self.axtran_v.set_title('Tran-Voltage')
                        else:
                            if(not self.axtran_i):
                                self.axtran_i = plt.figure(6,figsize=(10,10)).subplots()
                            self.plot_tran_i(printItem)
                            self.axtran_i.legend()
                            self.axtran_i.set_title('Tran-Current')
                else:
                    pass
        plt.show()
    def plot_dc(self,item):
        dc_result = self.result_dict['dc']
        self.figure_num = self.figure_num + 1
        if(not dc_result['double']):
            # For single source dc analysis
            if(item.difference_flag):
                # v(1,2)
                target1 = '{}({})'.format(item.var_type,item.node_list[0])
                target2 = '{}({})'.format(item.var_type,item.node_list[1])
                if(target1 not in self.index or target2 not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    fig = plt.figure(self.figure_num)
                    self.figure_list.append(fig)
                    ax = fig.subplots()
                    plot_data = dc_result['data'].loc[target1,:]-dc_result['data'].loc[target2,:]
                    title = 'DC Result:{}-{}'.format(target1,target2)
                    unit_x = 'V' if(dc_result['src'][0] == 'v') else "A"
                    unit_y = "V" if(target1[0] == 'v') else 'A'
                    xlabel = '{}/{}'.format(dc_result['src'],unit_x)
                    ylabel = '({}-{})/V'.format(target1,target2)
                    ax.plot(dc_result['data'].columns,plot_data,label=xlabel)
                    ax.set_title(title)
                    #ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
                    plt.show()
            else:
                # v(1)
                target = '{}({})'.format(item.var_type,item.node_list[0])
                if(target not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    fig = plt.figure(self.figure_num)
                    self.figure_list.append(fig)
                    ax = fig.subplots()
                    plot_data = dc_result['data'].loc[target,:]
                    scale_unit = ''
                    scale_factor = 1
                    scale_factor,scale_unit = self.adjust(plot_data.iloc[-1])
                    plot_data = plot_data*scale_factor
                    title = 'DC Result:{}'.format(target)
                    unit_x = 'V' if(dc_result['src'][0] == 'v') else 'A'
                    unit_y = "{}V".format(scale_unit) if (target[0] == 'v') else "{}A".format(scale_unit)
                    xlabel = '{}/{}'.format(dc_result['src'],unit_x)
                    ylabel = '{}/{}'.format(target,unit_y)
                    ax.plot(dc_result['data'].columns,plot_data,label=xlabel)
                    ax.set_title(title)
                    #ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
                    fig.savefig('../figures/DC_graph{}.png'.format(self.figure_num))
                    plt.show()
        else:
            # For double source dc analysis
            src1 = dc_result['src']
            data = dc_result['data']
            sweep_list = dc_result['sweep_list']
            src2 = dc_result['src2']  
            if(item.difference_flag):
                target1 = '{}({})'.format(item.var_type,item.node_list[0])
                target2 = '{}({})'.format(item.var_type,item.node_list[1])
                if(target1 not in self.index or target2 not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    target1_index = dc_result['index'].index(target1)
                    target2_index = dc_result['index'].index(target2)
                    dimension = data.shape
                    # set the default x-axis is src1
                    # extract src1 sweep list
                    src1_sweep_list = [item[0][0] for item in sweep_list]
                    src2_sweep_list = [item[1] for item in sweep_list[0]]
                    fig = plt.figure(self.figure_num,figsize=(12,12))
                    self.figure_list.append(fig)
                    ax = fig.subplots()
                    scale_unit = ''
                    scale_factor = 1 
                    scale_factor,scale_unit = self.adjust(data[-1,-1,target_index])
                    for i in range(dimension[1]):
                        # extract the data under
                        # different src2 value
                        plot_data = data[:,i,target1_index]-data[:,i,target2_index]
                        plot_data = plot_data * scale_factor
                        label = '{}={:.2f}'.format(src2,src2_sweep_list[i])
                        ax.plot(src1_sweep_list,plot_data,label=label)
                        title = 'DC Result:{}-{}'.format(target1,target2)
                        unit_x = 'V' if(src1[0] == 'v') else 'A'
                        unit_y = "{}V".format(scale_unit) if (target1[0] == 'v') else "{}A".format(scale_unit)
                        xlabel = '{}/{}'.format(src1,unit_x)
                        ylabel = '({}-{})/{}'.format(target1,target2,unit_y)
                        ax.set_title(title)
                        ax.set_xlabel(xlabel)
                        ax.set_ylabel(ylabel)
                    ax.legend()
                    fig.savefig('../figures/DC_graph{}.png'.format(self.figure_num))
                    plt.show()
            else:
                target = '{}({})'.format(item.var_type,item.node_list[0])
                if(target not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    # self.index=[v(1),v(2),...,i(n)]
                    target_index = dc_result['index'].index(target)
                    # find the data
                    dimension = data.shape
                    # set the default x-axis is src1
                    # extract src1 sweep list
                    src1_sweep_list = [item[0][0] for item in sweep_list]
                    src2_sweep_list = [item[1] for item in sweep_list[0]]
                    fig = plt.figure(self.figure_num,figsize=(12,12))
                    self.figure_list.append(fig)
                    ax = fig.subplots()
                    scale_unit = ''
                    scale_factor = 1 
                    scale_factor,scale_unit = self.adjust(data[-1,-1,target_index])
                    for i in range(dimension[1]):
                        # extract the data under
                        # different src2 value
                        plot_data = data[:,i,target_index]
                        plot_data = plot_data * scale_factor
                        label = '{}={:.2f}'.format(src2,src2_sweep_list[i])
                        ax.plot(src1_sweep_list,plot_data,label=label)
                        title = 'DC Result:{}'.format(target)
                        unit_x = 'V' if(src1[0] == 'v') else 'A'
                        unit_y = "{}V".format(scale_unit) if (target[0] == 'v') else "{}A".format(scale_unit)
                        xlabel = '{}/{}'.format(src1,unit_x)
                        ylabel = '{}/{}'.format(target,unit_y)
                        ax.set_title(title)
                        ax.set_xlabel(xlabel)
                        ax.set_ylabel(ylabel)
                    ax.legend()
                    fig.savefig('../figures/DC_graph{}.png'.format(self.figure_num))
                    plt.show()  
    def plot_ac(self,item):
        ac_result = self.result_dict['ac']
        self.figure_num = self.figure_num + 1
        # prepare origin data,title,y_label
        if(item.difference_flag):
            target1 = '{}({})'.format(item.var_type,item.node_list[0])
            target2 = '{}({})'.format(item.var_type,item.node_list[1])
            origin_data = ac_result.loc[target1,:] - ac_result.loc[target2,:]
            title = "AC Result:{}-{}".format(target1,target2)
            y_label = "({}-{})".format(target1,target2)
        else:
            target = '{}({})'.format(item.var_type,item.node_list[0])
            origin_data = ac_result.loc[target,:]
            title = "AC Result:{}".format(target)
            y_label = "{}".format(target)
        # Plot for different figure type
        if(item.ac_unit == 'm'):
            # Print magnitude
            plot_data = np.abs(origin_data)
            fig = plt.figure(self.figure_num)
            self.figure_list.append(fig)
            ax = fig.subplots()
            ax.semilogx(ac_result.columns,plot_data,color="red")
            ax.set_title(title)
            ax.set_xlabel("Frequency/Hz")
            ax.set_ylabel("Magnitude of {}".format(y_label))
            fig.savefig('../figures/AC_graph{}.png'.format(self.figure_num))
            plt.show()
        elif(item.ac_unit == 'p'):
            # Print phase
            plot_data = np.angle(origin_data,deg=True)
            fig = plt.figure(self.figure_num)
            self.figure_list.append(fig)
            ax = fig.subplots()
            ax.semilogx(ac_result.columns,plot_data,color="red")
            ax.set_title(title)
            ax.set_xlabel("Frequency/Hz")
            ax.set_ylabel("Phase of {}/deg".format(y_label))
            fig.savefig('../figures/AC_graph{}.png'.format(self.figure_num))
            plt.show()                           
        elif(item.ac_unit == 'db'):
            # Print 20 *log10(magnitude)
            plot_data = 20*np.log10(origin_data)
            plot_data = np.abs(origin_data)
            fig = plt.figure(self.figure_num)
            self.figure_list.append(fig)
            ax = fig.subplots()
            ax.semilogx(ac_result.columns,plot_data,color="red")
            ax.set_title(title)
            ax.set_xlabel("Frequency/Hz")
            ax.set_ylabel("Magnitude of {}/dB".format(y_label))
            fig.savefig('../figures/AC_graph{}.png'.format(self.figure_num))
            plt.show()
        elif(item.ac_unit == 'r'):
            # Print real part
            plot_data = np.real(origin_data)
            plot_data = np.abs(origin_data)
            fig = plt.figure(self.figure_num)
            self.figure_list.append(fig)
            ax = fig.subplots()
            ax.semilogx(ac_result.columns,plot_data,color="red")
            ax.set_title(title)
            ax.set_xlabel("Frequency/Hz")
            ax.set_ylabel("Real Part of {}".format(y_label))
            fig.savefig('../figures/AC_graph{}.png'.format(self.figure_num))
            plt.show()
        elif(item.ac_unit == 'i'):
            # Print imaginary part
            plot_data = np.imag(origin_data)
            plot_data = np.abs(origin_data)
            fig = plt.figure(self.figure_num)
            self.figure_list.append(fig)
            ax = fig.subplots()
            ax.semilogx(ac_result.columns,plot_data,color="red")
            ax.set_title(title)
            ax.set_xlabel("Frequency/Hz")
            ax.set_ylabel("Imaginary Part of {}/j".format(y_label))
            fig.savefig('../figures/AC_graph{}.png'.format(self.figure_num))
            plt.show()                            
        else:
            PlotError('Unsupported Plot Command')
    def plot_tran(self,item):
        tran_result = self.result_dict['tran']
        self.figure_num = self.figure_num + 1
        if(item.difference_flag):
            target1 = '{}({})'.format(item.var_type,item.node_list[0])
            target2 = '{}({})'.format(item.var_type,item.node_list[1])
            if(target1 not in self.index or target2 not in self.index):
                raise PlotError('Unsupported Plot')
            else:
                origin_data = tran_result.loc[target1,:] - tran_result.loc[target2,:]
                title = "Tran Result:{}-{}".format(target1,target2)
                unit = "V" if (target1[0] == 'v') else "A"
                y_label = "({}-{})/{}".format(target1,target2,unit)
        else:
            target = '{}({})'.format(item.var_type,item.node_list[0])
            if(target not in self.index):
                raise PlotError('Unsupported Plot:{}'.format(target))
            else:
                origin_data = tran_result.loc[target, :]
                title = "Tran Result:{}".format(target)
                unit = "V" if (target[0] == 'v') else "A"
                y_label = "{}/{}".format(target, unit)
        #Plot
        scale_factor,scale_unit = adjust(tran_result.columns[-1])
        time = tran_result.columns * scale_factor
        fig = plt.figure(self.figure_num)
        self.figure_list.append(fig)
        ax = fig.subplots()
        ax.plot(time,origin_data)
        ax.autoscale(enable=True, axis='both', tight=None)
        ax.set_title(title)
        ax.set_xlabel("Time/{}s".format(scale_unit))
        ax.set_ylabel(y_label)
        fig.savefig('../figures/TRAN_graph{}.png'.format(self.figure_num))
        plt.show()
    def adjust(self,value):
        if(1e-15 <= abs(value) < 1e-12):
            return (1e12,'p')
        elif(1e-12 <= abs(value) < 1e-9):
            return (1e9,'n')
        elif(1e-9 <= abs(value) < 1e-6):
            return (1e6,'u')
        elif(1e-6 <= abs(value) < 1e-3):
            return (1e3,'m')
        elif(1e-3 <= abs(value) < 1):
            return (1,'')
        elif(1 <= abs(value) < 1e3):
            return (1,'')
        elif(1e3 <= abs(value) < 1e6):
            return (1e-6,'meg')
        elif(1e6 <= abs(value) < 1e9):
            return (1e-9,'g')
        else:
            return (1,'')

    '''
    Below functions are for TA
    '''
    def plot_dc_v(self,item):
        dc_result = self.result_dict['dc']
        if(not dc_result['double']):
            # For single source dc analysis
            if(item.difference_flag):
                # v(1,2)
                target1 = '{}({})'.format(item.var_type,item.node_list[0])
                target2 = '{}({})'.format(item.var_type,item.node_list[1])
                if(target1 not in self.index or target2 not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    plot_data = dc_result['data'].loc[target1,:]-dc_result['data'].loc[target2,:]
                    unit_x = 'V' 
                    unit_y = 'V'
                    xlabel = '{}/{}'.format(dc_result['src'],unit_x)
                    ylabel = '({}-{})/V'.format(target1,target2)
                    self.axdc_v.plot(dc_result['data'].columns,plot_data,label=ylabel)
                    self.axdc_v.set_xlabel(xlabel)
            else:
                # v(1)
                target = '{}({})'.format(item.var_type,item.node_list[0])
                if(target not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    plot_data = dc_result['data'].loc[target,:]
                    scale_unit = ''
                    scale_factor = 1
                    scale_factor,scale_unit = self.adjust(plot_data.iloc[-1])
                    plot_data = plot_data*scale_factor
                    unit_x = 'V'
                    unit_y = "{}V".format(scale_unit)
                    xlabel = '{}/{}'.format(dc_result['src'],unit_x)
                    ylabel = '{}/{}'.format(target,unit_y)
                    self.axdc_v.plot(dc_result['data'].columns,plot_data,label=ylabel)
                    self.axdc_v.set_xlabel(xlabel)
        else:
            # For double source dc analysis
            src1 = dc_result['src']
            data = dc_result['data']
            sweep_list = dc_result['sweep_list']
            src2 = dc_result['src2']  
            if(item.difference_flag):
                target1 = '{}({})'.format(item.var_type,item.node_list[0])
                target2 = '{}({})'.format(item.var_type,item.node_list[1])
                if(target1 not in self.index or target2 not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    target1_index = dc_result['index'].index(target1)
                    target2_index = dc_result['index'].index(target2)
                    dimension = data.shape
                    # set the default x-axis is src1
                    # extract src1 sweep list
                    src1_sweep_list = [item[0][0] for item in sweep_list]
                    src2_sweep_list = [item[1] for item in sweep_list[0]]
                    scale_unit = ''
                    scale_factor = 1 
                    scale_factor,scale_unit = self.adjust(data[-1,-1,target_index])
                    for i in range(dimension[1]):
                        # extract the data under
                        # different src2 value
                        plot_data = data[:,i,target1_index]-data[:,i,target2_index]
                        plot_data = plot_data * scale_factor
                        label = '{}={:.2f}'.format(src2,src2_sweep_list[i])
                        title = 'DC Result:{}-{}'.format(target1,target2)
                        unit_x = 'V'
                        unit_y = "{}V".format(scale_unit)
                        xlabel = '{}/{}'.format(src1,unit_x)
                        ylabel = '{},({}-{})/{}'.format(label,target1,target2,unit_y)
                        self.axdc_v.plot(src1_sweep_list,plot_data,label=ylabel)
                        self.axdc_v.set_xlabel(xlabel)
                        self.axdc_v.set_ylabel(ylabel)
    def plot_dc_i(self,item):
        dc_result = self.result_dict['dc']
        if(not dc_result['double']):
            # For single source dc analysis
            if(item.difference_flag):
                # v(1,2)
                target1 = '{}({})'.format(item.var_type,item.node_list[0])
                target2 = '{}({})'.format(item.var_type,item.node_list[1])
                if(target1 not in self.index or target2 not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    plot_data = dc_result['data'].loc[target1,:]-dc_result['data'].loc[target2,:]
                    title = 'DC Result:{}-{}'.format(target1,target2)
                    unit_x = 'A'
                    unit_y = 'A'
                    xlabel = '{}/{}'.format(dc_result['src'],unit_x)
                    ylabel = '({}-{})/A'.format(target1,target2)
                    self.axdc_i.plot(dc_result['data'].columns,plot_data,label=ylabel)
                    self.axdc_i.set_xlabel(xlabel)
            else:
                # v(1)
                target = '{}({})'.format(item.var_type,item.node_list[0])
                if(target not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    plot_data = dc_result['data'].loc[target,:]
                    scale_unit = ''
                    scale_factor = 1
                    scale_factor,scale_unit = self.adjust(plot_data.iloc[-1])
                    plot_data = plot_data*scale_factor
                    unit_x = 'A'
                    unit_y = "{}A".format(scale_unit)
                    xlabel = '{}/{}'.format(dc_result['src'],unit_x)
                    ylabel = '{}/{}'.format(target,unit_y)
                    self.axdc_i.plot(dc_result['data'].columns,plot_data,label=ylabel)
                    self.axdc_i.set_xlabel(xlabel)
        else:
            # For double source dc analysis
            src1 = dc_result['src']
            data = dc_result['data']
            sweep_list = dc_result['sweep_list']
            src2 = dc_result['src2']  
            if(item.difference_flag):
                target1 = '{}({})'.format(item.var_type,item.node_list[0])
                target2 = '{}({})'.format(item.var_type,item.node_list[1])
                if(target1 not in self.index or target2 not in self.index):
                    raise PlotError('Unsupported Plot Command')
                else:
                    target1_index = dc_result['index'].index(target1)
                    target2_index = dc_result['index'].index(target2)
                    dimension = data.shape
                    # set the default x-axis is src1
                    # extract src1 sweep list
                    src1_sweep_list = [item[0][0] for item in sweep_list]
                    src2_sweep_list = [item[1] for item in sweep_list[0]]
                    scale_unit = ''
                    scale_factor = 1 
                    scale_factor,scale_unit = self.adjust(data[-1,-1,target_index])
                    for i in range(dimension[1]):
                        # extract the data under
                        # different src2 value
                        plot_data = data[:,i,target1_index]-data[:,i,target2_index]
                        plot_data = plot_data * scale_factor
                        label = '{}={:.2f}'.format(src2,src2_sweep_list[i])
                        title = 'DC Result:{}-{}'.format(target1,target2)
                        unit_x = 'A'
                        unit_y = "{}A".format(scale_unit)
                        xlabel = '{}/{}'.format(src1,unit_x)
                        ylabel = '{},({}-{})/{}'.format(label,target1,target2,unit_y)
                        self.axdc_i.plot(src1_sweep_list,plot_data,label=ylabel)
                        self.axdc_i.set_xlabel(xlabel)
                        self.axdc_i.set_ylabel(xlabel)


    def plot_ac_v(self,item):
        ac_result = self.result_dict['ac']
        # prepare origin data,title,y_label
        if(item.difference_flag):
            target1 = '{}({})'.format(item.var_type,item.node_list[0])
            target2 = '{}({})'.format(item.var_type,item.node_list[1])
            origin_data = ac_result.loc[target1,:] - ac_result.loc[target2,:]
            title = "AC Result:{}-{}".format(target1,target2)
            y_label = "({}-{})".format(target1,target2)
        else:
            target = '{}({})'.format(item.var_type,item.node_list[0])
            origin_data = ac_result.loc[target,:]
            title = "AC Result:{}".format(target)
            y_label = "{}".format(target)
        # Plot for different figure type
        if(item.ac_unit == 'm'):
            # Print magnitude
            plot_data = np.abs(origin_data)
            self.axac_v.semilogx(ac_result.columns,plot_data,color="red",label = "Magnitude of {}".format(y_label))
            self.axac_v.set_xlabel("Frequency/Hz")
        elif(item.ac_unit == 'p'):
            # Print phase
            plot_data = np.angle(origin_data,deg=True)
            self.axac_v.semilogx(ac_result.columns,plot_data,color="red",label = "Phase of {}".format(y_label))
            self.axac_v.set_xlabel("Frequency/Hz")                       
        elif(item.ac_unit == 'db'):
            # Print 20 *log10(magnitude)
            plot_data = 20*np.log10(origin_data)
            plot_data = np.abs(origin_data)
            self.axac_v.semilogx(ac_result.columns,plot_data,color="red")
            self.axac_v.semilogx(ac_result.columns,plot_data,color="red",label = "Magnitude of {}/dB".format(y_label))
            self.axac_v.set_xlabel("Frequency/Hz")
        elif(item.ac_unit == 'r'):
            # Print real part
            plot_data = np.real(origin_data)
            self.axac_v.semilogx(ac_result.columns,plot_data,color="red",label = "Real of {}".format(y_label))
            self.axac_v.set_xlabel("Frequency/Hz")
        elif(item.ac_unit == 'i'):
            # Print imaginary part
            plot_data = np.imag(origin_data)
            self.axac_v.semilogx(ac_result.columns,plot_data,color="red",label = "Imag of {}".format(y_label))
            self.axac_v.set_xlabel("Frequency/Hz")                            
        else:
            PlotError('Unsupported Plot Command')

    def plot_ac_i(self,item):
        ac_result = self.result_dict['ac']
        # prepare origin data,title,y_label
        if(item.difference_flag):
            target1 = '{}({})'.format(item.var_type,item.node_list[0])
            target2 = '{}({})'.format(item.var_type,item.node_list[1])
            origin_data = ac_result.loc[target1,:] - ac_result.loc[target2,:]
            title = "AC Result:{}-{}".format(target1,target2)
            y_label = "({}-{})".format(target1,target2)
        else:
            target = '{}({})'.format(item.var_type,item.node_list[0])
            origin_data = ac_result.loc[target,:]
            title = "AC Result:{}".format(target)
            y_label = "{}".format(target)
        # Plot for different figure type
        if(item.ac_unit == 'm'):
            # Print magnitude
            plot_data = np.abs(origin_data)
            self.axac_i.semilogx(ac_result.columns,plot_data,color="red",label = "Magnitude of {}".format(y_label))
            self.axac_i.set_xlabel("Frequency/Hz")
        elif(item.ac_unit == 'p'):
            # Print phase
            plot_data = np.angle(origin_data,deg=True)
            self.axac_i.semilogx(ac_result.columns,plot_data,color="red",label = "Phase of {}".format(y_label))
            self.axac_i.set_xlabel("Frequency/Hz")                        
        elif(item.ac_unit == 'db'):
            # Print 20 *log10(magnitude)
            plot_data = 20*np.log10(origin_data)
            plot_data = np.abs(origin_data)
            self.axac_i.semilogx(ac_result.columns,plot_data,color="red")
            self.axac_i.semilogx(ac_result.columns,plot_data,color="red",label = "Magnitude of {}/dB".format(y_label))
            self.axac_i.set_xlabel("Frequency/Hz")
        elif(item.ac_unit == 'r'):
            # Print real part
            plot_data = np.real(origin_data)
            self.axac_i.semilogx(ac_result.columns,plot_data,color="red",label = "Real of {}".format(y_label))
            self.axac_i.set_xlabel("Frequency/Hz")
        elif(item.ac_unit == 'i'):
            # Print imaginary part
            plot_data = np.imag(origin_data)
            self.axac_i.semilogx(ac_result.columns,plot_data,color="red",label = "Imag of {}".format(y_label))
            self.axac_i.set_xlabel("Frequency/Hz")                          
        else:
            PlotError('Unsupported Plot Command')

    def plot_tran_v(self,item):
        tran_result = self.result_dict['tran']
        if(item.difference_flag):
            target1 = '{}({})'.format(item.var_type,item.node_list[0])
            target2 = '{}({})'.format(item.var_type,item.node_list[1])
            if(target1 not in self.index or target2 not in self.index):
                raise PlotError('Unsupported Plot')
            else:
                origin_data = tran_result.loc[target1,:] - tran_result.loc[target2,:]
                unit = "V"
                y_label = "({}-{})/{}".format(target1,target2,unit)
        else:
            target = '{}({})'.format(item.var_type,item.node_list[0])
            if(target not in self.index):
                raise PlotError('Unsupported Plot:{}'.format(target))
            else:
                origin_data = tran_result.loc[target, :]
                unit = "V"
                y_label = "{}/{}".format(target, unit)
        #Plot
        scale_factor,scale_unit = adjust(tran_result.columns[-1])
        time = tran_result.columns * scale_factor
        self.axtran_v.plot(time,origin_data,label=y_label)
        self.axtran_v.autoscale(enable=True, axis='both', tight=None)
        self.axtran_v.set_xlabel("Time/{}s".format(scale_unit))

    def plot_tran_i(self,item):
        tran_result = self.result_dict['tran']
        if(item.difference_flag):
            target1 = '{}({})'.format(item.var_type,item.node_list[0])
            target2 = '{}({})'.format(item.var_type,item.node_list[1])
            if(target1 not in self.index or target2 not in self.index):
                raise PlotError('Unsupported Plot')
            else:
                origin_data = tran_result.loc[target1,:] - tran_result.loc[target2,:]
                title = "Tran Result:{}-{}".format(target1,target2)
                unit = "V" if (target1[0] == 'v') else "A"
                y_label = "({}-{})/{}".format(target1,target2,unit)
        else:
            target = '{}({})'.format(item.var_type,item.node_list[0])
            if(target not in self.index):
                raise PlotError('Unsupported Plot:{}'.format(target))
            else:
                origin_data = tran_result.loc[target, :]
                title = "Tran Result:{}".format(target)
                unit = "V" if (target[0] == 'v') else "A"
                y_label = "{}/{}".format(target, unit)
        #Plot
        scale_factor,scale_unit = adjust(tran_result.columns[-1])
        time = tran_result.columns * scale_factor
        self.axtran_i.plot(time,origin_data,label=y_label)
        self.axtran_i.autoscale(enable=True, axis='both', tight=None)
        self.axtran_i.set_xlabel("Time/{}s".format(scale_unit))