elmore delay
vin 1 0 1 1 tran pulse(0 1 1 0.2 0.2 6 12)
r1 1 2 1k
c1 2 0 100u
r2 2 3 1k
c2 3 0 100u
r3 2 4 1k
c3 4 0 100u
r4 4 5 1k
c4 5 0 100u
r5 4 6 1k
c5 6 0 100u
r6 6 7 1k
c6 7 0 100u
.tran 0.1 20 0.0
.plot tran v(1) v(2) v(3) v(4) v(5) v(6) v(7)
.end



