# Author: Yunkun Liao
# Managing all solving work(stamping,solving flow control)

import numpy as np
import math
import scipy
import matplotlib.pyplot as plt

from error_define import *
from analysis import *
from devices import *

class Solver():
    '''Solver Class
    attributes:
        MNA: Modified Nodal Analysis Matrix
        RHS: Right Hand Side Vector
        ANS: Answer Vector
        invariant_list: list keeps r,e,f,g,h element
        source_list: list keeps i,v element
        cl_list: list keeps c,l element
        nonlinear_list: list keeps diode,mosfet element
    param:
        element_list: list keeps all elememts of the circuit,from parser
        MNA_dim: int -> the dimension of MNA,from parser
    '''
    def __init__(self, element_list, MNA_dim):
        self.MNA = None
        self.RHS = None
        self.ANS = None
        self.MNA_dim = MNA_dim
        self.invariant_list = [item for item in element_list if (item.device_type in ['r','e','f','g','h'])]
        self.source_list = [item for item in element_list if (item.device_type in ['i','v'])]
        self.cl_list = [item for item in element_list if (item.device_type in ['c','l'])]
        self.nonlinear_list = [item for item in element_list if(item.device_type in ['d','mos'])]      
        #For Hw4
        self.op_iteration = []
        self.diode_tangent = []
        self.mos_iteration = []
        self.iternum_list = []
        self.fail_flag = False
    def op_analysis(self,dc_sweep=False,dc_src1='',dc_src1_val=0.,dc_src2='',dc_src2_val=0.,
                    tran_uic_flag=False,h=1.,tran_init=False,tran_start=0):
        '''
        This method performs OP analysis
        param:
            dc_src1:str -> dc analysis source1 name
            dc_src1_val:double -> dc analysis source1 value
            dc_src2:str -> dc analysis source2 name
            dc_src2_val:double -> dc analysis source2 value
            tran_uic_flag: Boolean -> for OP for Tran analysis
            h: double -> time step in tran analysis
        Attention:
        The inclusion of this line in an input file directs 
        SPICE to determine the dc operating point of the circuit 
        with inductors shorted and capacitors opened. Note: 
        a DC analysis is automatically performed prior to a transient 
        analysis to determine the transient initial conditions, 
        and prior to an AC small-signal, Noise, and Pole-Zero analysis 
        to determine the linearized, small-signal models for nonlinear 
        devices (see the KEEPOPINFO variable above).-refence from:
        http://bwrcs.eecs.berkeley.edu/Classes/IcBook/SPICE/UserGuide
        '''
        self.MNA = np.zeros((self.MNA_dim,self.MNA_dim),dtype=np.double)
        self.RHS = np.zeros((self.MNA_dim,),dtype=np.double)
        self.ANS = np.zeros((self.MNA_dim-1,),dtype=np.double)
        
        for element in self.invariant_list:
            element.load(self.MNA,self.RHS)
        # Stamping C,L for OP analysis
        for element in self.cl_list:
            element.load_op(self.MNA,self.RHS,tran_uic_flag,h)
        # Stamping I,V source for OP Analysis
        for element in self.source_list:
            element.load_op(self.MNA,self.RHS,dc_sweep,src1=dc_src1,src1_val=dc_src1_val,\
                            src2=dc_src2,src2_val=dc_src2_val,tran_init=tran_init,tran_start=tran_start)

        # Start iteration process and determine the state of 
        # Non-linear element
        # In the iteration process,do not change the content of 
        # self.MNA,self.RHS,all we need is to determine the state
        # of element in self.nonlinear_list
        # For HW4
        #print(self.MNA,self.RHS)
        diode_iteration,diode_tangent,mos_iteration = self.Newton_Raphson()
        self.op_iteration = diode_iteration
        self.diode_tangent = diode_tangent
        self.mos_iteration = mos_iteration
        # Stampint non-linear elements(diode,mosfet) for OP Analysis
        # it's state has been determined through N-R iteration
        for element in self.nonlinear_list:
            element.load(self.MNA,self.RHS)
        # Solving MNA[1:,1:]*ANS=RHS[1:],eliminate equations related to
        # gnd
        
        self.ANS = np.linalg.solve(self.MNA[1:,1:],self.RHS[1:])
            
    def dc_analysis(self,dc_instance,source_stepping=True):
        '''
        This Method performs DC analysis
        DC = a series of OP analysis
        '''
        if(dc_instance.double_scan_flag):
            # Double source scan
            sweep_list1 = list(dc_instance.generator1)
            sweep_list2 = list(dc_instance.generator2)
            dc_result = np.empty([len(sweep_list1),len(sweep_list2),self.MNA_dim-1],dtype=np.double)
            sweep_list = np.empty([len(sweep_list1),len(sweep_list2)],dtype=np.double)
            sweep_list = [[0 for i in range(len(sweep_list2))] for j in range(len(sweep_list1))]
            for i in range(len(sweep_list1)):
                for j in range(len(sweep_list2)):
                    src1_val = sweep_list1[i]
                    src2_val = sweep_list2[j]
                    sweep_list[i][j] = (src1_val,src2_val)
                    self.MNA = np.zeros((self.MNA_dim,self.MNA_dim),dtype=np.double)
                    self.RHS = np.zeros((self.MNA_dim,),dtype=np.double)
                    self.op_analysis(dc_sweep=True,dc_src1=dc_instance.src1,dc_src1_val=src1_val,\
                                    dc_src2=dc_instance.src2,dc_src2_val=src2_val)
                    dc_result[i,j,:] = self.ANS.copy()
            src1_name = dc_instance.src1
            src2_name = dc_instance.src2
            return dc_result,sweep_list,(src1_name,src2_name)
        else:
            sweep_list = list(dc_instance.generator1)
            dc_result = np.empty([self.MNA_dim-1,len(sweep_list)], dtype=np.double)
            for i in range(len(sweep_list)):
                self.MNA = np.zeros((self.MNA_dim,self.MNA_dim),dtype=np.double)
                self.RHS = np.zeros((self.MNA_dim,),dtype=np.double)
                val = sweep_list[i]
                self.op_analysis(dc_sweep=True,dc_src1=dc_instance.src1,dc_src1_val=val)
                if(self.fail_flag and source_stepping):
                    if(i == 0):
                        next_val = sweep_list[1]
                        stepping_list = np.linspace(val,next_val,num=10)
                    else:
                        prev_val = sweep_list[i-1]
                        stepping_list = np.linspace(prev_val,val,num=10)
                    for step_val in stepping_list:
                        self.op_analysis(dc_sweep=True,dc_src1=dc_instance.src1,dc_src1_val=step_val)
                    self.op_analysis(dc_sweep=True,dc_src1=dc_instance.src1,dc_src1_val=val)
                    self.fail_flag = False
                else:
                    pass
                dc_result[:,i] = self.ANS.copy()
            src_name = dc_instance.src1
            return dc_result,sweep_list,(src_name)
                
        
    def ac_analysis(self,ac_instance):
        '''
        This Method performs AC analysis
        '''
        # Stamping C/L
        sweep_list = list(ac_instance.generator)
        ac_result = np.empty([self.MNA_dim-1,len(sweep_list)], dtype=np.complex)
        for i in range(len(sweep_list)):
            self.MNA = np.zeros((self.MNA_dim,self.MNA_dim),dtype=np.complex)
            self.RHS = np.zeros((self.MNA_dim,),dtype=np.complex)
            self.ANS = np.zeros((self.MNA_dim,),dtype=np.complex)
            freq = sweep_list[i]
            for element in self.invariant_list:
                element.load(self.MNA,self.RHS)
            for element in self.source_list:
                element.load_ac(self.MNA,self.RHS)
            for element in self.cl_list:
                element.load_ac(self.MNA,self.RHS,freq)
            # Stamp Nonlinear
            # How to deal with mos in AC?
            self.ANS = np.linalg.solve(self.MNA[1:,1:],self.RHS[1:])
            ac_result[:,i] = self.ANS.copy()
        return ac_result,sweep_list                                                      
        
    def tran_analysis(self,tran_instance,method='TR',h=1e-10):
        '''
        This Method performs Tran analysis
        Algorithm Description:
            while(the simulation is not over):
                formulate companion models for energy storage
                components(C,L),using current operating point
                Newton loop:
                    while(the convergence is not achieved):
                        formulate companion models for non-linear components,
                        using cuerrent operating point
                    end while
            end while
        '''
        
        time_series = list(tran_instance.generator)
        h = tran_instance.step/50.0
        if(h > tran_instance.max_step_size):
            h = tran_instance.max_step_size
        t_start = time_series[0]
        t_stop = time_series[-1]
        num = math.floor((t_stop-t_start)/h)
        time_intervals = np.linspace(t_start, t_stop, num=num, endpoint=False)
        ANS_series = np.zeros((self.MNA_dim-1,num))
        '''How to add initial condition for capacitor???
        if(tran_instance.uic_flag):
            # Stamping Initial Condition for C/L
            for item in self.cl_list:
                pass
        '''
        # Do OP analysis to get the initial condition
        self.op_analysis(tran_uic_flag=tran_instance.uic_flag,h=h,
                         tran_init=True,tran_start=t_start)
        ANS_series[:, 0] = np.copy(self.ANS)
        iter_num = 0
        for time in time_intervals[1:]:
            iter_num += 1
            self.MNA = np.zeros((self.MNA_dim,self.MNA_dim),dtype=np.double)
            self.RHS = np.zeros((self.MNA_dim,),dtype=np.double)
            for element in self.invariant_list:
                element.load(self.MNA,self.RHS)
            for element in self.source_list:
                element.load_tran(self.MNA,self.RHS,time)
            for element in self.cl_list:
                element.load_tran(self.MNA,self.RHS,ANS_series,iter_num,h,method)
            # stamping Non-linear elements
            self.Newton_Raphson()
            for element in self.nonlinear_list:
                element.load(self.MNA,self.RHS)
            iter_ANS = np.linalg.solve(self.MNA[1:,1:],self.RHS[1:])
            ANS_series[:, iter_num] = np.copy(iter_ANS)
        # Generate the plotted data according to step
        spl_list = []
        for i in range(self.MNA_dim-1):
            x = time_intervals
            y = ANS_series[i,:]
            spl_list.append(scipy.interpolate.InterpolatedUnivariateSpline(x, y))
        plotted_data = np.zeros((self.MNA_dim-1, len(time_series)))
        for i in range(self.MNA_dim-1):
            x = np.array(time_series)
            y = spl_list[i](x)
            plotted_data[i,:] = np.copy(y)
        return plotted_data,time_series
    
    def Newton_Raphson(self):
        '''Newton Raphson iteration for nonlinear element
            Before perform the iteration, you should make
            sure that all linear elements have been stamped
        '''
        #For HW4
        diode_iteration = []
        diode_tangent = []
        mos_iteration = []
        if(self.nonlinear_list):
            # For each cycle of N-R iteration
            # initialize the state of nonlinear
            # element first
            '''
            #Wrong Operation:
            for element in self.nonlinear_list:
                element.init_state()
            '''
            #For HW4 
            for element in self.nonlinear_list:
                if(element.device_type == 'd'):
                    diode_iteration.append(element.vd)
                    diode_tangent.append(element.tangent_generator())
            #define the CONVERGE_CRITERIA
            CONVERGE_CRITERIA = 1e-6
            converge_flag = False
            MAX_ITERNUM = 2000
            iter_num = 0
            
            while(not converge_flag and (iter_num <= MAX_ITERNUM)):
                iter_num += 1
                converge_flag = True
                MNA_local = np.zeros((self.MNA_dim,self.MNA_dim),dtype=np.double)
                RHS_local = np.zeros((self.MNA_dim,),dtype=np.double)
                MNA_local = self.MNA.copy()
                RHS_local = self.RHS.copy()

                for element in self.nonlinear_list:
                    element.load(MNA_local,RHS_local)
                ANS_local = np.linalg.solve(MNA_local[1:,1:],RHS_local[1:])
                # update the state of non-linear element
                # and check for convergence
                for element in self.nonlinear_list:
                    if(element.device_type == 'd'):
                        if(element.p_internal == 0):
                            v_p = 0
                        else:
                            v_p = ANS_local[element.p_internal-1]
                        if(element.n_internal == 0):
                            v_n = 0
                        else:
                            v_n = ANS_local[element.n_internal-1]
                        #For Hw4
                        diode_iteration.append(v_p-v_n)
                        diode_tangent.append(element.tangent_generator())
                        flag = element.update_state(v_p,v_n,CONVERGE_CRITERIA)
                        converge_flag = converge_flag and flag
                    elif(element.device_type == 'mos'):
                        if(element.node_d == 0):
                            v_d = 0
                        else:
                            v_d = ANS_local[element.node_d-1]
                        if(element.node_g == 0):
                            v_g = 0
                        else:
                            v_g = ANS_local[element.node_g-1]
                        if(element.node_s == 0):
                            v_s = 0
                        else:
                            v_s = ANS_local[element.node_s-1]
                        if(element.model == 'nmos'):
                            mos_iteration.append(v_d)
                        flag = element.update_state(v_d,v_g,v_s,CONVERGE_CRITERIA)
                        converge_flag = converge_flag and flag
                    else:
                        pass
            if(iter_num > MAX_ITERNUM):
                self.fail_flag = True
            self.iternum_list.append(iter_num)
        else:
            # No Non-linear element
            pass
        return (diode_iteration,diode_tangent,mos_iteration)
    def showIteration(self):
        '''
        For HW4
        '''
        y = self.op_iteration
        x = [i+1 for i in range(len(self.op_iteration))]
        fig = plt.figure()
        ax = fig.subplots()
        ax.plot(x,y,marker='.')
        ax.set_title("Visualize Iteration")
        ax.set_xlabel("iteration num")
        ax.set_ylabel("voltage across Diode")
        plt.show()
    def printMNAwithDiode(self):
        '''
        For HW4
        '''
        print('----MNA with Diode------')
        print(self.MNA)
        print('----RHS with Diode------')
        print(self.RHS)
    def showNewtonRaphson(self):
        '''
        For HW4
        '''
        vol = np.linspace(0,0.05,num=50)
        Id = 2/3*vol-5/3+np.exp(40*vol)
        Id_tan = []
        for i in range(len(self.diode_tangent)):
            Id_tan.append(vol*self.diode_tangent[i][0]+self.diode_tangent[i][1])
        fig = plt.figure()
        ax = fig.subplots()
        plt.rc('text', usetex=True)
        ax.plot(vol,Id,label=r'$f(v_2)=\frac{2}{3}v_2-\frac{5}{3}+e^{40v_2}$')
        for i in range(len(self.diode_tangent)):
            ax.plot(vol,Id_tan[i],label='iteration{}'.format(i+1))
        ax.plot(vol,[0]*len(vol),marker='.')
        ax.set_xlabel(r'$v_2$')
        ax.set_ylabel(r'$f(v_2)$')
        ax.legend()
        plt.show()

    def showMOSIteration(self,set_vg,set_vdd):
        '''
        MOS Iteration
        '''
        nmos = MOS('M1','nmos',1,2,0,0,2,2)
        pmos = MOS('M2','pmos',1,2,3,3,2,4)
        vd = np.linspace(-20,20,num=100)
        vgsn = set_vg
        vgsp = vgsn-set_vdd
        vdd = set_vdd
        f_vd = []
        for i in range(len(vd)):
            vds = vd[i]
            ids = nmos.get_Id(vgsn,vd[i])+pmos.get_Id(vgsp,vd[i]-vdd)
            f_vd.append(ids)
        mos_tangent = []
        #print(self.mos_iteration)
        
        for item in self.mos_iteration:
            m = nmos.get_gds(vgsn,item)+pmos.get_gds(vgsp,item-vdd)
            c = nmos.get_Id(vgsn,item)-nmos.get_gds(vgsn,item)*item+pmos.get_Id(vgsp,item-vdd)-pmos.get_gds(vgsp,item-vdd)*item
            mos_tangent.append((m,c))
        f_vd_tan = []
        #print(mos_tangent)
        for i in range(len(mos_tangent)):
            m,c = mos_tangent[i]
            f_vd_tan.append(vd*m+c)
        
        fig = plt.figure(figsize=(12,12))
        ax = fig.subplots()
        
        for i in range(len(mos_tangent)):
            ax.plot(vd,f_vd_tan[i],label='iteration{}'.format(i+1))
        
        ax.plot(vd,[0]*len(f_vd))
        ax.plot(vd,f_vd,label='object function',marker='.')
        ax.set_xlabel('v_d')
        ax.set_ylabel('f(v_d)')
        ax.set_title('Vg={}V'.format(vgsn))
        ax.legend()
        fig.savefig('mos_iteration_vg_{}.png'.format(vgsn))
        plt.show()



        