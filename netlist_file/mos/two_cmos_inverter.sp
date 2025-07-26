two coms inverter-transient simulation
Vin 1 0 1 pulse(0 1 0 0 0 1.0 1.5)
Vdd 3 0 1.8 
M1 4 1 0 0 NMOS l=2u W=2u
M2 4 1 3 3 PMOS l=2u W=5u
R1 4 0 5k
M3 2 4 0 0 NMOS l=2u W=2u
M4 2 4 3 3 PMOS l=2u W=5u
R2 2 0 5K
.tran 0.1 2 0
.plot tran v(1) v(4) v(2)
.end



