"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.sp = 7 # SP Stack Pointer
        self.pc = 0
        self.fl = 4
        self.reg[self.fl] = 0b00000000
        self.status = False

        self.func_dict = {
            1: self.HLT,
            130: self.LDI,
            71: self.PRN,
            162: self.MUL, # 10100010
            69: self.PUSH,
            70: self.POP,
            80: self.CALL,
            17: self.RET,
            160: self.ADD,
            167: self.CMP, # 10100111
            84: self.JMP, # 01010100 4+16+64
            85: self.JEQ, # 01010101 1+4+16+64
            86: self.JNE # 01010110 2+4+16+64
        }

    def load(self):
        """Load a program into memory."""

        address = 0

        try:
            filename = sys.argv[1]
            with open(filename) as f:
                for address,line in enumerate(f):
                    line = line.split('#')
                    line = line[0].strip()

                    if line == "":
                        continue

                    v = int(line, 2)
                    self.ram_write(address,v)
        except FileNotFoundError:
            print(f"{sys.argv[0]}: could not find {sys.argv[1]}")
            sys.exit(2)

        # For now, we've just hardcoded a program:

        # program = [
        #     # From print8.ls8
        #     0b10000010, # LDI R0,8
        #     0b00000000,
        #     0b00001000,
        #     0b01000111, # PRN R0
        #     0b00000000,
        #     0b00000001, # HLT
        # ]

        # for instruction in program:
        #     self.ram[address] = instruction
        #     address += 1


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]


        elif op == "CMP": #LGE

            # LESS THAN
            if self.reg[reg_a] < self.reg[reg_b]:
                # print(f'{self.reg[reg_a]} & {self.reg[reg_b]}')
                # print(f'{self.reg[reg_a]} is less than {self.reg[reg_b]}')
                self.reg[self.fl] = self.reg[self.fl] | 0b00000100
                # print(f'FLAG is set to {(self.reg[self.fl])}')
            else:
                self.reg[self.fl] = self.reg[self.fl] & 0b11111011
            
            # GREATER THAN
            if self.reg[reg_a] > self.reg[reg_b]:
                self.reg[self.fl] = self.reg[self.fl] | 0b00000010
                # print(f'{self.reg[reg_a]} is greater than {self.reg[reg_b]}')
                # print(f'FLAG is set to {self.reg[self.fl]}')
            else:
                self.reg[self.fl] = self.reg[self.fl] & 0b11111101

            # EQUAL
            if self.reg[reg_a] == self.reg[reg_b]:
                self.reg[self.fl] = self.reg[self.fl] | 0b00000001
                # print(f'{self.reg[reg_a]} is equal to {self.reg[reg_b]}')
                # print(f'FLAG is set to {self.reg[self.fl]}')
            else:
                self.reg[self.fl] = self.reg[self.fl] & 0b11111110
            
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        self.status = True
        while self.status == True:

            ir = self.ram_read(self.pc) # setting the instruction register to begin from the first memory
            opa = self.ram_read(self.pc + 1)
            opb = self.ram_read(self.pc + 2)

            self.func_dict[ir](opa,opb)

    def ram_read(self,address):
        self.content = self.ram[address] # Memory Data Register (MDR) = Memory Address Register (MAR)
        return self.content

    def ram_write(self,address,data):
        self.ram[address] = data
        self.ram_read(address)

    def PUSH(self,a,b):
        self.reg[self.sp] -= 1
        self.ram_write(self.reg[self.sp],self.reg[a])
        self.pc += 2

    def POP(self,a,b):
        data = self.ram_read(self.reg[self.sp])
        self.reg[a] = data
        self.reg[self.sp] += 1
        self.pc += 2

    def HLT(self,a,b):
        # print('GoodBye')
        self.status = False

    def LDI(self, a, b):
        self.reg[a] = b
        # print(f'LDI - register {a} is {b}')
        self.pc += 3

    def PRN(self,a,b):
        value = self.reg[a]
        print(int(value))
        self.pc += 2

    def MUL(self,a,b):
        # print(a,b)
        self.alu('MUL',a,b)
        self.pc += 3

    def CALL(self,a,b):
        self.reg[self.sp] -= 1
        self.ram_write(self.reg[self.sp],self.pc + 2)
        self.pc = self.reg[a]

    def RET(self,a,b):
        self.pc = self.ram_read(self.reg[self.sp])
        self.reg[self.sp] += 1
    
    def ADD(self,a,b):
        # print(f'ADDING {a} to {b}')
        self.alu("ADD",a,b)
        self.pc += 3

    def CMP(self,a,b):
        # print(f'COMPARING {self.reg[a]} and {self.reg[b]}')
        self.alu("CMP",a,b)
        self.pc += 3

    def JMP(self,a,b):
        self.pc = self.reg[a]
        # print(f'JMP to {self.reg[a]}')

    def JEQ(self,a,b):
        if (self.reg[self.fl] & 0b00000001) == 1:
            self.pc = self.reg[a]
            # print(f'JEQ to {a}')
        else:
            self.pc += 2

    def JNE(self,a,b):
        if (self.reg[self.fl] & 0b11111110) == self.reg[self.fl]:
            self.pc = self.reg[a]
            # print(f'JNE to {a}')
        else:
            self.pc += 2