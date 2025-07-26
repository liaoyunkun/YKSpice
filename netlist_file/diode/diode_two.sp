nonlinear tran simulation of two diodes
*from lecture8 page24
C1 2 0 1
Is 0 1 1 const(1)
D1 1 0 diode
D2 2 0 diode
R1 1 0 1000 
R2 1 2 1m
.TRAN 0.01 1 0
.plot tran v(1) v(2)
.END



