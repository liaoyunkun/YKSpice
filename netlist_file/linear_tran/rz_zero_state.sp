a simple RC circuit: zero_state_response
R1 1 2 2
C1 2 0 0.20 
V1 1 0 1 const(1)
.TRAN 0.01 3 0
*demo for .plot command
.plot tran V(2) V(2,1)
.END


