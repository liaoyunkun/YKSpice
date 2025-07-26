rc attennuation circuit
r1 1 0 1k
c1 1 0 100u ic=1
.tran 0.01  0.7 0 uic
.plot tran v(1)
.end
