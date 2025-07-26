# Readme
## The modules of my spice
* myspice.py:定义了MySpice类，顶层类，负责沟通parser与solver以及画图
* myparser.py:定义了MyParser类，负责网表解析
* mysolver.py:定义了Solver类，负责OP,DC,AC,TRAN,N-R迭代
* devices.py:定义了一系列器件类以及timefunction
* utilites:一些辅助函数
* error_define.py:定义了一系列可能会出现的异常
* test.py:进行测试的一个脚本