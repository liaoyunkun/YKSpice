five coms inverter-transient simulation
Vin 1 0 1 0 tran pulse (0 1 0 0 0 1.0 1.5)
Vdd 3 0 1.8
M1 4 1 0 0 NMOS l=2u W=2u
M2 4 1 3 3 PMOS l=2u W=4u
R1 4 0 6k
M3 5 4 0 0 NMOS l=2u W=2u
M4 5 4 3 3 PMOS l=2u W=4u
R2 5 0 6k
M5 6 5 0 0 NMOS l=2u W=2u
M6 6 5 3 3 PMOS l=2u W=4u
R3 6 0 6k
M7 7 6 0 0 NMOS l=2u W=2u
M8 7 6 3 3 PMOS l=2u W=4u
R4 7 0 6k
M9 2 7 0 0 NMOS l=2u W=2u
M10 2 7 3 3 PMOS l=2u W=4u
R5 2 0 6k
.tran 0.1 2 0
.plot tran v(1) v(2)
.end



