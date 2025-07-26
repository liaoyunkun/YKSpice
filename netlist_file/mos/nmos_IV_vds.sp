nmos circuit- I/V
*vgs fixed, vds range from 0~1.8
Vin 1 0 1
Vdd 3 0 1.8
M1 2 1 0 0 NMOS l=2u w=8u
R1 2 3 5000
.DC Vdd 0 1.8 0.1
.plot dc i(M1)
.end

