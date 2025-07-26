R+diode circuit to observe convergence of diode stamp
*from Lecture8 page43
v1 1 0 1 1 tran sin(0 1 1 0 0)
r1 1 2 1n
d1 2 0 diode
.tran 0.01 2 0
.plot tran v(1) v(2)
.end


