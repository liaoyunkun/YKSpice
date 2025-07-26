nmos's i/v curve
*vgs changes.
Vin 1 0 1
Vdd 3 0 1.8
M1 2 1 0 0 NMOS l=2u
R1 2 3 5000
.DC Vin 0 1.8 0.1
.plot DC i(M1)
.end


