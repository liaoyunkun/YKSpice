RLC under damping oscillation
c1 1 0 1 ic=1
r1 1 2 1
L1 2 0 2
.tran 0.1 30 0 uic
.plot tran v(1)
.end
