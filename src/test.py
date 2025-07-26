# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 12:30:04 2019

@author: 12117
"""
from myspice import*
def main():
    netlist = '../netlist_file/mos/tran_nmos_inverter_rev.sp'
    test = MySpice(netlist)
    test.parse()
    test.analysis()
    test.print_result()
    test.plot_v2()
if __name__ == '__main__':
    main()