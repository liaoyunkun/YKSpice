netlist for cmos inverter's voltage transfer characteristic
Vin 1 0 1
Vdd 3 0 1.8
M1 2 1 0 0 NMOS l=2u W=2u
M2 2 1 3 3 PMOS l=2u W=8u
*R1 2 0 5k
.DC Vin 0 1.8 0.02
.plot dc v(2)
.end


