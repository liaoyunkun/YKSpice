coms inverter-transient simulation
Vin 1 0 1 0 tran pulse (0 1 0 0 0 1.0 1.5)
Vdd 3 0 1.8
M1 2 1 0 0 NMOS l=2u W=2u
M2 2 1 3 3 PMOS l=2u W=4u
R1 2 0 5k
.tran 0.1 2 0
.plot tran v(1) v(2)
.end
