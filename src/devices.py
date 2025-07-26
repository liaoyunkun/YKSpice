# Author: Yunkun Liao
# Managing all device objects

import math
from scipy.interpolate import InterpolatedUnivariateSpline
from numpy.linalg import lstsq
import numpy as np

from error_define import *

class DualPortDevice():
    '''Base class for most dual-port circuit elements
    attributes:
        device_type: the type of the devices
        name: the name of the devices in netlist
        value: the value of the devices
        p_internal: int -> Positive port in internal representation
        n_internal: int -> Negative port in internal representation
        + branch_flag: whether this element need a variable to represent 
            the current throught it.(default is False)
    '''
    def __init__(self,device_type,name,value,p_internal,n_internal,branch_flag):
        self.device_type = device_type
        self.name = name
        self.value = value
        self.p_internal = p_internal
        self.n_internal = n_internal
        self.branch_flag = branch_flag

class Resistor(DualPortDevice):
    '''Resistor,inherit from DualPortDevice
    attributes:
        device_type = 'r'
        branch_flag = False
    '''
    def __init__(self,name,value,p_internal,n_internal):
        super().__init__('r',name,value,p_internal,n_internal,False)
    def load(self,MNA,RHS):
        '''  N+      N-
        N+ 1/R_k    -1/R_k
        N- -1/R_k   1/R_k
        '''
        MNA[self.p_internal,self.p_internal] += 1./self.value
        MNA[self.p_internal,self.n_internal] += -1./self.value
        MNA[self.n_internal,self.p_internal] += -1./self.value
        MNA[self.n_internal,self.n_internal] += 1./self.value

class Capacitor(DualPortDevice):
    '''Capacitor,inherit from DualPortDevice
    attributes:
        device_type = 'c'
        branch_flag = False
        ic: initial condition for tran analysis
    '''
    def __init__(self,name,value,p_internal,n_internal,ic,branch_num):
        super().__init__('c',name,value,p_internal,n_internal,True)
        self.ic = ic
        self.branch_num = branch_num
    def load_op(self,MNA,RHS,uic_flag=False,h=1.):
        if(not uic_flag):
            '''MNA DC-stamp for C
                N+   N-   i   RHS
            N+            +1
            N-            -1
            i             1
            '''
            MNA[self.p_internal,self.branch_num] += 1
            MNA[self.n_internal,self.branch_num] += -1
            MNA[self.branch_num,self.branch_num] += 1
        else:
            ''' Use initial condition for C
                 N+    N-    i   RHS
            N+              +1
            N-              -1 
            i   C/h   -C/h  -1  C/h*V0
            BUG may occur!!!
            '''
            #Todo
            MNA[self.p_internal,self.branch_num] += 1
            MNA[self.n_internal,self.branch_num] += -1
            MNA[self.branch_num,self.p_internal] += -self.value/h
            MNA[self.branch_num,self.n_internal] += self.value/h
            MNA[self.branch_num,self.branch_num] += -1
            RHS[self.branch_num] += self.ic*self.value/h
    def load_ac(self,MNA,RHS,freq): 
        '''capacitor MNA stamping for AC
            N+   N-  i  RHS
        N+            1
        N-           -1 
        i   sC   -sC  -1 
        s = j*2*pi*freq
        
        param:
            freq_delta: the variation of freq between two
                ac stamping
        '''
        admittance = (0+1j)*2*math.pi*self.value * freq
        MNA[self.p_internal,self.branch_num] += 1
        MNA[self.n_internal,self.branch_num] += -1
        MNA[self.branch_num,self.p_internal] += admittance
        MNA[self.branch_num,self.n_internal] += -admittance
        MNA[self.branch_num,self.branch_num] += -1
    def load_tran(self,MNA,RHS,ANS_series,iter_num,h,method='BE'):
        if(method == 'BE'):
            '''  N+   N-  i  RHS    
            N+            1  
            N-           -1
            i   C/h -C/h -1  C/h*v(t-h)
            '''
            if(self.p_internal == 0):
                v_Np = 0
            else:
                v_Np = ANS_series[self.p_internal-1,iter_num-1]
            if(self.n_internal == 0):
                v_Nn = 0
            else:
                v_Nn = ANS_series[self.n_internal-1,iter_num-1]
            v_prev = v_Np - v_Nn
            MNA[self.p_internal,self.branch_num] += 1
            MNA[self.n_internal,self.branch_num] += -1
            MNA[self.branch_num,self.p_internal] += self.value/h
            MNA[self.branch_num,self.n_internal] += -self.value/h
            MNA[self.branch_num,self.branch_num] += -1
            RHS[self.branch_num] += self.value/h*v_prev
        elif(method == 'FE'):
            '''  N+   N-   i    RHS
            N+             1    
            N-            -1
            i  C/h  -C/h   0    C/h*v(t-h)+i(t-h)
            '''
            if(self.p_internal == 0):
                v_Np = 0
            else:
                v_Np = ANS_series[self.p_internal-1,iter_num-1]
            if(self.n_internal == 0):
                v_Nn = 0
            else:
                v_Nn = ANS_series[self.n_internal-1,iter_num-1]
            v_prev = v_Np - v_Nn
            i_prev = ANS_series[self.branch_num-1,iter_num-1]
            MNA[self.p_internal,self.branch_num] += 1
            MNA[self.n_internal,self.branch_num] += -1
            MNA[self.branch_num,self.p_internal] += self.value/h
            MNA[self.branch_num,self.n_internal] += -self.value/h
            RHS[self.branch_num] += self.value/h*v_prev+i_prev
        elif(method == 'TR'):
            '''   N+    N-    i      RHS
            N+                1
            N-               -1 
            i   1    -1     -h/(2C)   v(t-h)+i(t-h)*h/(2C) 
            ''' 
            if(self.p_internal == 0):
                v_Np = 0
            else:
                v_Np = ANS_series[self.p_internal-1,iter_num-1]
            if(self.n_internal == 0):
                v_Nn = 0
            else:
                v_Nn = ANS_series[self.n_internal-1,iter_num-1]
            v_prev = v_Np - v_Nn
            i_prev = ANS_series[self.branch_num-1,iter_num-1]
            self.MNA[self.p_internal,self.branch_num] += 1
            self.MNA[self.n_internal,self.branch_num] += -1
            self.MNA[self.branch_num,self.p_internal] += 1
            self.MNA[self.branch_num,self.n_internal] += -1
            self.MNA[self.branch_num,self.branch_num] += -h/(2*self.value)
            self.RHS[self.branch_num] += v_prev+i_prev*h/(2*self.value)
        else:
            raise UnsupportedMethod('{} is unsupported now,support FE,BE,TR'.format(method))
        
class Inductor(DualPortDevice):
    '''Inductor,inherit from DualPortDevice
    attributes:
        device_type = 'l'
        branch_flag = True
        ic:initial condition for tran analysis
        branch_num: the internal variable represent the  current variable
            we introduced for a branch whose current cannot be determined 
            by its terminal voltages
    '''
    def __init__(self,name,value,p_internal,n_internal,ic,branch_num):
        super().__init__('l',name,value,p_internal,n_internal,True)
        self.ic = ic
        self.branch_num = branch_num
    def load_op(self,MNA,RHS,uic_flag=False,h=1.):
        if(not uic_flag):
            ''' MNA DC-stamp for L
                N+     N-     i
            N+                1
            N-               -1
            i   1     -1
            '''
            MNA[self.p_internal,self.branch_num] += 1.
            MNA[self.n_internal,self.branch_num] += -1.
            MNA[self.branch_num,self.p_internal] += 1.
            MNA[self.branch_num,self.n_internal] += -1.
        else:
            '''Use initial condition for L
                  N+   N-   i    RHS
            N+              1     0
            N-             -1     0
            br    1   -1   -L/h  -I0*L/h
            '''
            MNA[self.p_internal,self.branch_num] += 1
            MNA[self.n_internal,self.branch_num] += -1
            MNA[self.branch_num,self.p_internal] += 1
            MNA[self.branch_num,self.n_internal] += -1
            MNA[self.branch_num,self.branch_num] += -self.value/h
            RHS[self.branch_num] += -self.ic*self.value/h
    def load_ac(self,MNA,RHS,freq):
        # inductor stamping
        '''  N+  N-  i
        N+           1
        N-          -1
        br   1  -1  -sL
        s = j*2*pi*freq
        '''
        impedance = (0+1j)*2*math.pi*self.value * freq
        MNA[self.p_internal,self.branch_num] += 1
        MNA[self.n_internal,self.branch_num] += -1
        MNA[self.branch_num,self.p_internal] += 1
        MNA[self.branch_num,self.n_internal] += -1
        MNA[self.branch_num,self.branch_num] += -impedance
    def load_tran(self,MNA,RHS,ANS_series,iter_num,h,method='BE'):
        if(method == 'BE'):
            '''N+   N-   i    RHS
            N+           1    0
            N-          -1     0
            br 1   -1  -L/h  -L/h*i(t-h)
            '''
            i_prev = ANS_series[self.branch_num-1,iter_num-1]
            MNA[self.p_internal,self.branch_num] += 1
            MNA[self.n_internal,self.branch_num] += -1
            MNA[self.branch_num,self.p_internal] += 1
            MNA[self.branch_num,self.n_internal] += -1
            MNA[self.branch_num,self.branch_num] += -self.value/h
            RHS[self.branch_num] += -self.value/h*i_prev
        elif(method == 'FE'):
            '''N+   N-   i    RHS
            N+           1
            N-          -1
            i            1    i(t-h)+h*v(t-h)/L
            '''
            i_prev = ANS_series[self.branch_num-1,iter_num-1]
            if(self.p_internal == 0):
                v_Np = 0
            else:
                v_Np = ANS_series[self.p_internal-1,iter_num-1]
            if(self.n_internal == 0):
                v_Nn = 0
            else:
                v_Nn = ANS_series[self.n_internal-1,iter_num-1]
            v_prev = v_Np - v_Nn
            MNA[self.p_internal,self.branch_num] += 1
            MNA[self.n_internal,self.branch_num] += -1
            MNA[self.branch_num,self.branch_num] += 1
            RHS[self.branch_num] += i_prev+h*v_prev/self.value
        elif(method == 'TR'):
            '''N+    N-     i     RHS
            N+              1     0
            N-             -1     0
            i  h/2L -h/2L  -1    -i(t-h)-h/2L*v(t-h)                    
            '''
            if(self.p_internal == 0):
                v_Np = 0
            else:
                v_Np = ANS_series[self.p_internal-1,iter_num-1]
            if(self.n_internal == 0):
                v_Nn = 0
            else:
                v_Nn = ANS_series[self.n_internal-1,iter_num-1]
            v_prev = v_Np - v_Nn
            i_prev = ANS_series[self.branch_num-1,iter_num-1]
            MNA[self.p_internal,self.branch_num] += 1
            MNA[self.n_internal,self.branch_num] += -1
            MNA[self.branch_num,self.p_internal] += h/(2*self.value)
            MNA[self.branch_num,self.n_internal] += -h/(2*self.value)
            MNA[self.branch_num,self.branch_num] += -1
            RHS[self.branch_num] += -i_prev-h*v_prev/(2*self.value)
        else:
            raise UnsupportedMethod('{} is unsupported now,support FE,BE,TR'.format(method))

class ISource(DualPortDevice):
    '''Independent current source,inherit from DualPortDevice
    attributes:
        device_type = 'i'
        branch_flag = False
        ac: ac value,complex form
        tran: time_function instance,callable
    '''
    def __init__(self,name,dc,p_internal,n_internal,ac,tran):
        super().__init__('i',name,dc,p_internal,n_internal,False)
        self.ac = ac
        self.tran = tran
    def load_op(self,MNA,RHS,dc_sweep=False,src1=None,src1_val=None,\
                src2=None,src2_val=None,tran_init=False,tran_start=None):
        '''RHS
        N+ -Ik
        N- +Ik
        '''
        if(dc_sweep):
            if(src1 == self.name):
                stamp_value = src1_val
            elif(src2 == self.name):
                stamp_value = src2_val
            else:
                stamp_value = self.value
        elif(tran_init and self.tran):
            stamp_value = self.tran(tran_start)
        else:
            stamp_value = self.value         
        RHS[self.p_internal] += -stamp_value
        RHS[self.n_internal] += stamp_value        
    def load_ac(self,MNA,RHS):
        RHS[self.p_internal] += -self.ac
        RHS[self.n_internal] += self.ac
    def load_tran(self,MNA,RHS,time):
        if(self.tran):
            stamp_value = self.tran(time)
        else:
            stamp_value = self.value
        RHS[self.p_internal] += -stamp_value
        RHS[self.n_internal] += stamp_value
    
class VSource(DualPortDevice):
    '''Independent voltage source,inherit from DualPortDevice
    attributes:
        device_type = 'v'
        branch_flag = True
        branch_num: the internal variable represent the  current variable
            we introduced for a branch whose current cannot be determined 
            by its terminal voltages
        ac: ac value,complex form 
        tran: time_function instance,callable
    '''
    def __init__(self,name,dc,p_internal,n_internal,ac,tran,branch_num):
        super().__init__('v',name,dc,p_internal,n_internal,True)
        self.ac = ac
        self.tran = tran
        self.branch_num = branch_num
    def load_op(self,MNA,RHS,dc_sweep=False,src1=None,src1_val=None,\
                src2=None,src2_val=None,tran_init=False,tran_start=None):
        '''MNA:                          RHS:
                    N+      N-      ik    
        N+          0       0       1     0
        N-          0       0       -1    0
        branch k    1       -1      0     Vk
        '''
        if(dc_sweep):
            if(src1 == self.name):
                stamp_value = src1_val
            elif(src2 == self.name):
                stamp_value = src2_val
            else:
                stamp_value = self.value
        elif(tran_init and self.tran):
            stamp_value = self.tran(tran_start)
        else:
            stamp_value = self.value
        MNA[self.p_internal,self.branch_num] += 1.
        MNA[self.n_internal,self.branch_num] += -1.
        MNA[self.branch_num,self.p_internal] += 1.
        MNA[self.branch_num,self.n_internal] += -1.
        RHS[self.branch_num] += stamp_value
    def load_ac(self,MNA,RHS):
        MNA[self.p_internal,self.branch_num] += 1.
        MNA[self.n_internal,self.branch_num] += -1.
        MNA[self.branch_num,self.p_internal] += 1.
        MNA[self.branch_num,self.n_internal] += -1.
        RHS[self.branch_num] += self.ac
    def load_tran(self,MNA,RHS,time):
        if(self.tran):
            stamp_value = self.tran(time)
        else:
            stamp_value = self.value
        MNA[self.p_internal,self.branch_num] += 1
        MNA[self.n_internal,self.branch_num] += -1
        MNA[self.branch_num,self.p_internal] += 1
        MNA[self.branch_num,self.n_internal] += -1
        RHS[self.branch_num] += stamp_value

class VCVS(DualPortDevice):
    '''Voltage Controlled Voltage Source,inherit from DualPortDevice
    attributes:
        device_type = 'e'
        branch_flag = True
        branch_num: the internal variable represent the  current variable
            we introduced for a branch whose current cannot be determined 
            by its terminal voltages
        p_internal_ctrl:internal representation of positive control node
        n_internal_ctrl:internal representation of negative control node
    '''
    def __init__(self,name,vol_gain,p_internal,n_internal,branch_num,p_internal_ctrl,n_internal_ctrl):
        super().__init__('e',name,vol_gain,p_internal,n_internal,True)
        self.branch_num = branch_num
        self.p_internal_ctrl = p_internal_ctrl
        self.n_internal_ctrl = n_internal_ctrl
    def load(self,MNA,RHS):
        '''   N+  N-  NC+  NC-  ik
        N+                      +1
        N-                      -1
        NC+
        NC-
        br-VS +1  -1  -Ek  Ek
        '''
        MNA[self.p_internal,self.branch_num] += 1.
        MNA[self.n_internal,self.branch_num] += -1.
        MNA[self.branch_num,self.p_internal] += 1.
        MNA[self.branch_num,self.n_internal] += -1.
        MNA[self.branch_num,self.p_internal_ctrl] += -self.value
        MNA[self.branch_num,self.n_internal_ctrl] += self.value
    
class VCCS(DualPortDevice):
    '''Voltage Controlled Current Source,inherit from DualPortDevice
    attributes:
        device_type = 'g'
        branch_flag = False
        p_internal_ctrl:internal representation of positive control node
        n_internal_ctrl:internal representation of negative control node
    '''
    def __init__(self,name,transconductance,p_internal,n_internal,p_internal_ctrl,n_internal_ctrl):
        super().__init__('g',name,transconductance,p_internal,n_internal,False)
        self.p_internal_ctrl = p_internal_ctrl
        self.n_internal_ctrl = n_internal_ctrl
    def load(self,MNA,RHS):
        '''   NC+   NC-
        N+    Gk    -Gk
        N-   -Gk    Gk
        '''
        MNA[self.p_internal,self.p_internal_ctrl] += self.value
        MNA[self.p_internal,self.n_internal_ctrl] += -self.value
        MNA[self.n_internal,self.p_internal_ctrl] += -self.value
        MNA[self.n_internal,self.n_internal_ctrl] += self.value

class CCCS(DualPortDevice):
    '''Current Controlled Currrent Source,inherit from DualPortDevice
    attributes:
        device_type = 'f'
        branch_flag = True
        branch_ctrl:the internal variable represent the branch current
            we introduced as control current
    '''
    def __init__(self,name,cur_gain,p_internal,n_internal,branch_ctrl):
        super().__init__('f',name,cur_gain,p_internal,n_internal,True)
        self.branch_ctrl = branch_ctrl
    def load(self,MNA,RHS):
        '''   N+  N-  NC+  NC-  ic
        N+                      Fk
        N-                     -Fk
        Decleration: here I don't stamp matrix components
            related to Control Branch according to Pro. Shis
        '''
        MNA[self.p_internal,self.branch_ctrl] += self.value
        MNA[self.n_internal,self.branch_ctrl] += -self.value
class CCVS(DualPortDevice):
    '''Current Controlled Voltage Source,inherit from DualPortDevice
    attributes:
        device_type = 'h'
        branch_flag = True
        branch_num: the internal variable represent the  current variable
            we introduced for a branch whose current cannot be determined 
            by its terminal voltages
        branch_ctrl: the internal variable represent the branch current
            we introduced as control current
    '''
    def __init__(self,name,transresistance,p_internal,n_internal,branch_num,branch_ctrl):
        super().__init__('h',name,transresistance,p_internal,n_internal,True)
        self.branch_num = branch_num
        self.branch_ctrl = branch_ctrl
    def load(self,MNA,RHS):
        '''      N+  N-  NC+   NC-  ik  ic
        N+                          +1   
        N-                          -1   
        NC+
        NC-   
        br-vs    +1  -1                 -Hk
        '''
        MNA[self.p_internal,self.branch_num] += 1.
        MNA[self.n_internal,self.branch_num] += -1.
        MNA[self.branch_ctrl,self.p_internal] += 1.
        MNA[self.branch_ctrl,self.n_internal] += -1.
        MNA[self.branch_num,self.branch_ctrl] += -self.value

class Diode(DualPortDevice):
    '''Diode,inherit from DualPortDevice
    attributes:
        device_type = 'd'
        branch_flag = False
        model: model for the diode
        ic: initial condition for tran analysis
    '''
    def __init__(self,name,p_internal,n_internal,model,ic):
        super().__init__('d',name,0,p_internal,n_internal,False)
        self.model = model
        self.ic = ic
        self.IS = 1  #default saturation current,
        #self.IS = 0.5e-16    #from dic p53
        self.alpha = 40 #default alpha
        #self.alpha = 1/0.026 #from dic p53
        self.vd = 0.1
        self.id = self.IS*(math.exp(self.alpha*self.vd)-1)
        self.equivG = self.IS*self.alpha*math.exp(self.alpha*self.vd)
        self.equivCur = self.id-self.equivG*self.vd
    def init_state(self):
        self.vd = 0.
        self.id = self.IS*(math.exp(self.alpha*self.vd)-1)
        self.equivG = self.IS*self.alpha*math.exp(self.alpha*self.vd)
        self.equivCur = self.id-self.equivG*self.vd
    def update_state(self,v_p,v_n,CONVERGE_CRITERIA):
        if(self.model == 'diode'):
            if(abs(v_p-v_n-self.vd) < CONVERGE_CRITERIA):
                converge_flag = True
            else:
                converge_flag = False
            self.vd = v_p - v_n
            self.id = self.IS*(math.exp(self.alpha*self.vd)-1)
            #self.equivG = self.id*self.alpha
            self.equivG = self.alpha*self.IS*math.exp(self.alpha*self.vd)
            self.equivCur = self.id-self.equivG*self.vd
        else:
            pass
        return converge_flag
    def load(self,MNA,RHS):
        '''   N+     N-     RHS
        N+   G0(n)  -G0(n)  -I0(n)
        N-  -G0(n)  G0(n)   I0(n)
        '''
        MNA[self.p_internal,self.p_internal] += self.equivG
        MNA[self.p_internal,self.n_internal] += -self.equivG
        MNA[self.n_internal,self.p_internal] += -self.equivG
        MNA[self.n_internal,self.n_internal] += self.equivG
        RHS[self.p_internal] += -self.equivCur
        RHS[self.n_internal] += self.equivCur
    def get_Id(self,Vd):
        Id = self.IS*(math.exp(self.alpha*Vd)-1)
        return Id
    def get_gm(self,Vd):
        pass
    def tangent_generator(self):
        '''
        For HW4
        Generate tangent_data for N-R
        f(x) = f(a) + f`(x)(x-a)
        Id = Id(self.vd) + self.equivG*(V-self.vd)
        '''
        m = 2/3+self.alpha*math.exp(self.alpha*self.vd)
        c = -m*self.vd+2/3*self.vd-5/3+math.exp(self.alpha*self.vd)
        return (m,c)

# Other Devices

class MOS():
    '''Mos Transistor
    '''
    def __init__(self,name,model,node_d,node_g,node_s,node_b,length,width):
        self.device_type = 'mos'
        self.branch_flag = False
        self.name = name
        self.model = model
        self.node_d = node_d
        self.node_g = node_g
        self.node_s = node_s
        self.node_b = node_b
        self.length = length
        self.width = width
        # CONSTANTs:from DIC p69
        self.K_NMOS = 1.15e-4
        self.K_PMOS = -3e-5
        self.LAMDA_NMOS = 0.06
        self.LAMDA_PMOS = -0.1
        self.VTH_NMOS = 0.43
        self.VTH_PMOS = -0.4
        
        self.v_GS = 0.6 if(self.model == 'nmos') else -0.6
        self.v_DS = 0.5 if(self.model == 'nmos') else 0.5
        self.gds = self.get_gds(self.v_GS,self.v_DS)
        self.gm = self.get_gm(self.v_GS,self.v_DS)
        Id = self.get_Id(self.v_GS,self.v_DS)
        self.equiv_Id=Id-self.gm*self.v_GS-self.gds*self.v_DS
    def init_state(self):
        self.v_GS = 0.6 if(self.model == 'nmos') else -0.6
        self.v_DS = 0.5 if(self.model == 'nmos') else 0.5
        self.gds = self.get_gds(self.v_GS,self.v_DS)
        self.gm = self.get_gm(self.v_GS,self.v_DS)
        Id = self.get_Id(self.v_GS,self.v_DS)
        self.equiv_Id=Id-self.gm*self.v_GS-self.gds*self.v_DS
    def get_Id(self,vgs,vds,method=1):
        if(self.model == 'nmos'):
            if(vgs < self.VTH_NMOS):
                # cut-off region
                # Vgs < vt
                Id = 0
            elif(self.VTH_NMOS <= vgs and vgs-self.VTH_NMOS < vds):
                # saturation region
                # vgs >= vt,vds > vgs-vt
                Id = self.K_NMOS/2*(self.width/self.length)*(vgs-self.VTH_NMOS)**2*(1+self.LAMDA_NMOS*vds)
            else:
                # triode region
                if(vds >= 0):
                    Id = self.K_NMOS*(self.width/self.length)*((vgs-self.VTH_NMOS)*vds-vds**2/2)*(1+self.LAMDA_NMOS*vds)
                else:
                    # vds<0
                    if(method == 1):
                        #remove CLM
                        Id = self.K_NMOS*(self.width/self.length)*((vgs-self.VTH_NMOS)*vds-vds**2/2)
                    elif(method == 2):
                        #flip
                        if(vds >= -(vgs-self.VTH_NMOS)):
                            #Inverse-Linear  
                            Id = -self.K_NMOS*(self.width/self.length)*(-(vgs-self.VTH_NMOS)*vds-vds**2/2)*(1-self.LAMDA_NMOS*vds)
                        else:
                            #Invere-Saturation
                            #Id = -self.K_NMOS/2*(self.width/self.length)*(vgs-self.VTH_NMOS)**2*(1-self.LAMDA_NMOS*vds)
                            Id = -self.K_NMOS/2*(self.width/self.length)*(vgs-self.VTH_NMOS)**2
                    else:
                        # No operation
                        Id = self.K_NMOS*(self.width/self.length)*((vgs-self.VTH_NMOS)*vds-vds**2/2)*(1+self.LAMDA_NMOS*vds)                    
            return Id
        elif(self.model == 'pmos'):
            if(self.VTH_PMOS < vgs):
                # cut-off:vgs > vthp
                Id = 0
            elif(vgs<=self.VTH_PMOS and vds<=vgs-self.VTH_PMOS):
                # saturation:vgs<=vthp,vds<=vgs-vthp 
                Id = self.K_PMOS/2*(self.width/self.length)*(vgs-self.VTH_PMOS)**2*(1+self.LAMDA_PMOS*vds)
            else:
                if(vds <= 0):
                   
                    Id = self.K_PMOS*(self.width/self.length)*((vgs-self.VTH_PMOS)*vds-vds**2/2)*(1+self.LAMDA_PMOS*vds)
                else:
                    # vds > 0
                    if(method == 1):
                        # remove CLM
                        Id = self.K_PMOS*(self.width/self.length)*((vgs-self.VTH_PMOS)*vds-vds**2/2)
                    elif(method == 2):
                        # Flip
                        if(vds < -(vgs-self.VTH_PMOS)):
                            # inverse linear
                            Id = -self.K_PMOS*(self.width/self.length)*(-(vgs-self.VTH_PMOS)*vds-vds**2/2)*(1-self.LAMDA_PMOS*vds)
                        else:
                            # inverse saturation
                            #Id = -self.K_PMOS/2*(self.width/self.length)*(vgs-self.VTH_PMOS)**2*(1-self.LAMDA_PMOS*vds)
                            Id = -self.K_PMOS/2*(self.width/self.length)*(vgs-self.VTH_PMOS)**2
                    else:
                        # No operation
                        Id = self.K_PMOS*(self.width/self.length)*((vgs-self.VTH_PMOS)*vds-vds**2/2)*(1+self.LAMDA_PMOS*vds)
            return Id
        else:
            pass
    def get_gm(self,vgs,vds,method=1):
        if(self.model == 'nmos'):
            if(vgs < self.VTH_NMOS):
                #cut off
                gm = 0
            elif(self.VTH_NMOS <= vgs and vgs-self.VTH_NMOS < vds):
                #saturation
                gm = self.K_NMOS*(self.width/self.length)*(vgs-self.VTH_NMOS)*(1+self.LAMDA_NMOS*vds)
            else:
                #triode
                if(vds >= 0):
                    gm = self.K_NMOS*(self.width/self.length)*(1+self.LAMDA_NMOS*vds)*vds
                else:
                    # vds < 0
                    if(method == 1):
                        # remove CLM
                        gm = self.K_NMOS*(self.width/self.length)*vds
                    elif(method == 2):
                        # Flip
                        if(vds >= -(vgs-self.VTH_NMOS)):
                            # inverse linear
                            gm = self.K_NMOS*(self.width/self.length)*(1-self.LAMDA_NMOS*vds)*vds
                        else:
                            # inverse saturation
                            #gm = -self.K_NMOS*(self.width/self.length)*(vgs-self.VTH_NMOS)*(1-self.LAMDA_NMOS*vds)
                            gm = -self.K_NMOS*(self.width/self.length)*(vgs-self.VTH_NMOS)
                    else:
                        # No operation
                        gm = self.K_NMOS*(self.width/self.length)*(1+self.LAMDA_NMOS*vds)*vds
            return gm
        elif(self.model == 'pmos'):
            if(self.VTH_PMOS < vgs):
                #cutoff
                gm = 0
            elif(vgs<=self.VTH_PMOS and vds<=vgs-self.VTH_PMOS):
                #saturation
                gm = self.K_PMOS*(self.width/self.length)*(vgs-self.VTH_PMOS)*(1+self.LAMDA_PMOS*vds)
            else:
                #triode
                if(vds <= 0):
                    gm = self.K_PMOS*(self.width/self.length)*vds*(1+self.LAMDA_PMOS*vds)
                else:
                    # vds > 0
                    if(method == 1):
                        # remove CLM
                        gm = self.K_PMOS*(self.width/self.length)*vds
                    elif(method == 2):
                        # Flip
                        if(vds < -(vgs-self.VTH_PMOS)):
                            # inverse linear
                            gm = self.K_PMOS*(self.width/self.length)*vds*(1-self.LAMDA_PMOS*vds)
                        else:
                            # inverse saturation
                            #gm = -self.K_PMOS*(self.width/self.length)*(vgs-self.VTH_PMOS)*(1-self.LAMDA_PMOS*vds)
                            gm = -self.K_PMOS*(self.width/self.length)*(vgs-self.VTH_PMOS)
                    else:
                        # No operation
                        gm = self.K_PMOS*(self.width/self.length)*vds*(1+self.LAMDA_PMOS*vds)
            return gm
        else:
            pass
    def get_gds(self,vgs,vds,method=1):
        if(self.model == 'nmos'):
            if(vgs < self.VTH_NMOS):
                #cutoff
                gds = 0
            elif(self.VTH_NMOS <= vgs and vgs-self.VTH_NMOS < vds):
                # saturation
                gds = self.K_NMOS/2*(self.width/self.length)*(vgs-self.VTH_NMOS)**2*self.LAMDA_NMOS
            else:
                if(vds >= 0):
                    part1 = (vgs-self.VTH_NMOS-vds)*(1+self.LAMDA_NMOS*vds)
                    part2 = self.LAMDA_NMOS*((vgs-self.VTH_NMOS)*vds-vds**2/2)
                    gds = self.K_NMOS*(self.width/self.length)*(part1+part2)
                else:
                    # vds < 0
                    if(method == 1):
                        # remove CLM
                        gds = self.K_NMOS*(self.width/self.length)*(vgs-self.VTH_NMOS-vds)
                    elif(method == 2):
                        # Flip
                        if(vds >= -(vgs-self.VTH_NMOS)):
                            # inverse linear
                            part1 = (-vgs+self.VTH_NMOS-vds)*(1-self.LAMDA_NMOS*vds)
                            part2 = self.LAMDA_NMOS*((vgs-self.VTH_NMOS)*vds+vds**2/2)
                            gds = -self.K_NMOS*(self.width/self.length)*(part1+part2)
                        else:
                            # inverse saturation
                            # gds = self.K_NMOS/2*(self.width/self.length)*(vgs-self.VTH_NMOS)**2*self.LAMDA_NMOS
                            gds = 0
                    else:
                        # No operation
                        part1 = (vgs-self.VTH_NMOS-vds)*(1+self.LAMDA_NMOS*vds)
                        part2 = self.LAMDA_NMOS*((vgs-self.VTH_NMOS)*vds-vds**2/2)
                        gds = self.K_NMOS*(self.width/self.length)*(part1+part2)
            return gds
        elif(self.model == 'pmos'):
            if(self.VTH_PMOS < vgs):
                #cutoff
                gds = 0
            elif(vgs<=self.VTH_PMOS and vds<=vgs-self.VTH_PMOS):
                #saturation
                gds = self.K_NMOS/2*(self.width/self.length)*(vgs-self.VTH_PMOS)**2*(self.LAMDA_PMOS)
            else:
                #triode
                if(vds <= 0):
                    part1 = (vgs-self.VTH_PMOS-vds)*(1+self.LAMDA_PMOS*vds)
                    part2 = self.LAMDA_PMOS*((vgs-self.VTH_PMOS)*vds-vds**2/2)
                    gds = self.K_PMOS*(self.width/self.length)*(part1+part2)
                else:
                    # vds > 0
                    if(method == 1):
                        # remove CLM
                        gds = self.K_PMOS*(self.width/self.length)*(vgs-self.VTH_PMOS-vds)
                    elif(method == 2):
                        # Flip
                        if(vds < -(vgs-self.VTH_PMOS)):
                            # inverse linear
                            part1 = (-vgs+self.VTH_PMOS-vds)*(1-self.LAMDA_PMOS*vds)
                            part2 = self.LAMDA_PMOS*((vgs-self.VTH_PMOS)*vds+vds**2/2)
                            gds = -self.K_PMOS*(self.width/self.length)*(part1+part2)
                        else:
                            # inverse saturatoin
                            # gds = self.K_NMOS/2*(self.width/self.length)*(vgs-self.VTH_PMOS)**2*(self.LAMDA_PMOS)
                            gds = 0
                    else:
                        # No operation
                        part1 = (vgs-self.VTH_PMOS-vds)*(1+self.LAMDA_PMOS*vds)
                        part2 = self.LAMDA_PMOS*((vgs-self.VTH_PMOS)*vds-vds**2/2)
                        gds = self.K_PMOS*(self.width/self.length)*(part1+part2)
            return gds
        else:
            pass
    def update_state(self,v_d,v_g,v_s,CONVERGE_CRITERIA,method=1):
        if(abs(v_g-v_s-self.v_GS) <= CONVERGE_CRITERIA and abs(v_d-v_s-self.v_DS) <= CONVERGE_CRITERIA):
            converge_flag = True
        else:
            converge_flag = False       
            #update vgs,vds  
            self.v_GS = v_g-v_s
            self.v_DS = v_d-v_s
            Id = self.get_Id(self.v_GS,self.v_DS,method)
            self.gm = self.get_gm(self.v_GS,self.v_DS,method)
            self.gds = self.get_gds(self.v_GS,self.v_DS,method)
            self.equiv_Id = Id-self.gm*self.v_GS-self.gds*self.v_DS
        return converge_flag
    def load(self,MNA,RHS): 
        '''   Nd        Ns          Ng     RHS
        Nd  gds(n) -gds(n)-gm(n)   gm(n)   -Ids(n)  
        Ns -gds(n) gds(n)+gm(n)    -gm(n)  Ids(n)
        '''
        MNA[self.node_d,self.node_d] += self.gds
        MNA[self.node_s,self.node_d] += -self.gds
        MNA[self.node_d,self.node_s] += -self.gds-self.gm
        MNA[self.node_s,self.node_s] += self.gds+self.gm
        MNA[self.node_d,self.node_g] += self.gm
        MNA[self.node_s,self.node_g] += -self.gm
        RHS[self.node_d] += -self.equiv_Id
        RHS[self.node_s] += self.equiv_Id
    
# Time function for tran analysis

class PulseSource():
    """Square wave aka pulse function
    Attributes:
    v1 : float
        Square wave low value.
    v2 : float
        Square wave high value.
    td : float
        Delay time to the first ramp, in seconds. Negative values are considered
        as zero.
    tr : float
        Rise time in seconds, from the low value ``v1`` to the pulse high value
        ``v2``.
    tf : float
        Fall time in seconds, from the pulse high value ``v2`` to the low value
        ``v1``.
    pw : float
        Pulse width in seconds.
    per : float
        Periodicity interval in seconds.
    """
    # PULSE(V1 V2 TD TR TF PW PER)
    def __init__(self, v1, v2, td, tr, tf, pw, per):
        self.device_type = 'pulse'
        self.v1 = v1
        self.v2 = v2
        self.td = max(td, 0.0)
        self.tr = tr
        self.tf = tf
        self.pw = pw  
        self.per = per

    def __call__(self, time):
        """Evaluate the pulse function at the given time."""
        if time is None:
            time = 0
        time = time - self.per * int(time / self.per)
        if time < self.td:
            return self.v1
        elif time < self.td + self.tr:
            return self.v1 + ((self.v2 - self.v1) / (self.tr)) * (time - self.td)
        elif time < self.td + self.tr + self.pw:
            return self.v2
        elif time < self.td + self.tr + self.pw + self.tf:
            return self.v2 + ((self.v1 - self.v2) / (self.tf)) * (time - (self.td + self.tr + self.pw))
        else:
            return self.v1


class SinSource():
    '''SinSource(Vo Va Freq Td Df Phase)
    attributes:
        vo: float-> offset voltage
        va: float-> peak amplitude of voltage
        freq: float-> frequency
        td: float,optional-> time delay before beginning 
            the sinusoidal time variation, in seconds. 
            Defaults to 0.
        df: float,optional-> damping factor in 1/s,
            Defaults to 0(no damping)
        phase: float,optional-> phase advance in degrees,
            Default to 0(no phase delay)
    '''
    def __init__(self,vo,va,freq,td,df,phase):
        self.device_type = 'sin'
        self.vo = vo
        self.va = va
        self.freq = freq
        self.td = td
        self.df = df
        self.phase = phase
    def __call__(self,time):
        '''
        Evaluate the sine function at the given time
        '''
        if(time is None):
            time = 0
        if(time < self.td):
            return self.vo + self.va*math.sin(math.pi*self.phase/180.)
        else:
            return self.vo + self.va*math.exp((self.td-time)*self.df) \
                    * math.sin(2*math.pi*self.freq*(time-self.td)+math.pi*self.phase/180.)

class PWLSource():
    """Piece-Wise Linear (PWL) waveform
    Attributes:
    x : sequence-like
        The abscissa values of the interpolation points.
    y : sequence-like
        The ordinate values of the interpolation points.
    repeat : boolean, optional
        Whether the waveform should be repeated after its end. If set to
        ``True``, ``repeat_time`` also needs to be set to define when the
        repetition begins. Defaults to ``False``.
    repeat_time : float, optional
        In case the waveform is set to be repeated, setting the ``repeat`` flag
        above, the parameter, defined in seconds, set the first time instant at
        which the waveform repetition happens.
    td : float, optional
        Time delay before the signal begins, in seconds. Defaults to zero.
    """

    def __init__(self, x, y, repeat=False, repeat_time=0, td=0):
        self.device_type = 'pwl'
        self.x = x
        self.y = y
        self.repeat = repeat
        self.repeat_time = repeat_time
        if self.repeat_time == max(x):
            self.repeat_time = 0
        self.td = td
        self._type = "V"
        self._f = InterpolatedUnivariateSpline(self.x, self.y, k=1)

    def __call__(self, time):
        """Evaluate the PWL function at the given time."""
        time = self._normalize_time(time)
        return self._f(time)

    def _normalize_time(self, time):
        if time is None:
            time = 0
        if time <= self.td:
            time = 0
        elif time > self.td:
            time = time - self.td
            if self.repeat:
                if time > max(self.x):
                    time = (time - max(self.x)) % \
                           (max(self.x) - self.repeat_time) + \
                           self.repeat_time
                else:
                    pass
        return time

class CONSTSource():
    '''
    Const value time function
    '''
    def __init__(self,value):
        self.value = value
    def __call__(self,time):
        if(time == 0):
            return 0
        else:
            return self.value

def main():
    test1 = MOS('m1','nmos',1,2,3,4,1,1)
    test2 = MOS('m2','pmos',1,2,3,4,1,1)
    gds1 = test1.get_gds(0.6,0.5)
    gds2 = test2.get_gds(-0.6,0.5)
    gm1 = test1.get_gm(0.6,0.5)
    gm2 = test2.get_gm(-0.6,0.5)
    Id1 = test1.get_Id(0.6,0.5)
    Id2 = test2.get_Id(-0.6,0.5)
    eqId1 = Id1-gm1*0.6-gds1*0.5
    eqId2 = Id2-gm2*(-0.6)-gds2*0.5
    #gm = test.get_gm(-0.8,-0.8)
    #gds = test.get_gds(-0.8,-0.8)
    print('test1')
    print(gds1,gm1,eqId1)
    print('test2')
    print(gds2,gm2,eqId2)
    
if __name__ == '__main__':
    main()
