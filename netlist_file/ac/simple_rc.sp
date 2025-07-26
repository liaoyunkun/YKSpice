simple one order rc-circuit for ac simulation
vdc 1 0 1 AC 1
r1 1 2 1k
c1 2 0 100u
.AC DEC 10 1 100
.plot ac vm(2)
.end

