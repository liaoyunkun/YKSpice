two order RC filter
vin 1 0 1 AC 1
r1 1 2 1k
c1 2 0 1u
r2 2 3 1k
c2 3 0 10n
.AC DEC 10 1 20000
.plot AC VM(3)
.end
