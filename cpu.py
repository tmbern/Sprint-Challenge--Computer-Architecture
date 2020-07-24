"""CPU functionality."""

import sys
HLT = 0b00000001
LDI = 0b10000010
PRN = 0b01000111
MUL = 0b10100010
PUSH = 0b01000101
POP = 0b01000110
CALL = 0b01010000
RET = 0b00010001
ADD = 0b10100000
SUB = 0b10100001
DIV = 0b10100011
CMP = 0b10100111
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110

SP = 7

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0

        # the spec indicates that the register 7 is reserved for the stack pointer
        # self.reg[7] = 0XF4
        # the stack pointer should start out at register 7. this will be 
        # incremented or decremented as we pop and push. 
        # self.sp = self.reg[7]
        
        self.reg[SP] = 0XF4

        # flag      
        self.flag = 0b00000000

    def load(self):
        """Load a program into memory."""

        address = 0

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

        with open(sys.argv[1]) as f:
            for line in f:
                value = line.split("#")[0].strip()
                if value == '':
                    continue
                value = int(value, 2)
                self.ram[address] = value
                address +=1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "DIV":
            self.reg[reg_a] /= self.reg[reg_b]
        
        # `FL` bits: `00000LGE`
        # * `L` Less-than: during a `CMP`, set to 1 if registerA is less than registerB,
        # zero otherwise.
        # * `G` Greater-than: during a `CMP`, set to 1 if registerA is greater than
        # registerB, zero otherwise.
        # * `E` Equal: during a `CMP`, set to 1 if registerA is equal to registerB, zero
        # otherwise.
        elif op == "CMP":
            if self.reg[reg_a] == self.reg[reg_b]:
                self.flag = 0b00000001
            elif self.reg[reg_a] > self.reg[reg_b]:
                self.flag = 0b00000010
            else:
                self.flag = 0b00000100
        else:
            raise Exception("Unsupported ALU operation")

    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value

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



        running = True
        while running:
            instruction = self.ram_read(self.pc)
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

                       
            if instruction == HLT:
                # When HLT set run to False to exit the loop
                running = False
                self.pc += 1

            elif instruction == LDI:
                # sets a register to a specific value. This requires the next two bytes of 
                # data. So we need to increment the PC counter by 3
                self.reg[operand_a] = operand_b
                self.pc +=3
            
            elif instruction == PRN:
                print(self.reg[operand_a])
                self.pc += 2
            
            elif instruction == MUL:
                # multipy the values in two registers together and store result in registerA
                result = self.reg[operand_a] * self.reg[operand_b]
                self.reg[operand_a] = result
                self.pc +=3

            elif instruction == PUSH:
                # Push the value in the given register on the stack.
                # 1. Decrement the `SP`.
                # 2. Copy the value in the given register to the address pointed to by `SP`.
                self.reg[SP] -= 1
                value = self.reg[operand_a]
                self.ram[self.reg[SP]] = value
                self.pc +=2

            elif instruction == POP:
                # Pop the value at the top of the stack into the given register.
                # 1. Copy the value from the address pointed to by `SP` to the given register.
                # 2. Increment `SP`.
                value = self.ram[self.reg[SP]]
                self.reg[operand_a] = value
                self.reg[SP] += 1
                self.pc += 2

            elif instruction == CALL:
                # Calls a subroutine (function) at the address stored in the register.
                # 1. The address of the ***instruction*** _directly after_ `CALL` is
                # pushed onto the stack. This allows us to return to where we left off when the subroutine finishes executing.
                # 2. The PC is set to the address stored in the given register. We jump to that location in RAM and execute the 
                # first instruction in the subroutine. The PC can move forward or backwards from its current location.
                
                self.reg[SP] -= 1
                self.ram[self.reg[SP]] = self.pc + 2
                self.pc = self.reg[operand_a]

            elif instruction == RET:
                # Return from subroutine.
                # Pop the value from the top of the stack and store it in the `PC`.
                self.pc = self.ram[self.reg[SP]]
                self.reg[SP] += 1

            elif instruction == ADD:
                self.alu("ADD", operand_a, operand_b)
                self.pc += 3
            
            elif instruction == CMP:
                self.alu('CMP', operand_a, operand_b)
                self.pc += 3
            
            elif instruction == JMP:
                # Jump to the address stored in the given register.
                # Set the `PC` to the address stored in the given register.
                self.pc = self.reg[operand_a]
            
            elif instruction == JEQ:
                # If `equal` flag is set (true), jump to the address stored in the given register.
                if self.flag == 1:
                    self.pc = self.reg[operand_a]
                else:
                    self.pc += 2

            elif instruction == JNE:
                # If `E` flag is clear (false, 0), jump to the address stored in the given
                # register.
                if self.flag != 1:
                    self.pc = self.reg[operand_a]
                else:
                    self.pc += 2
            else:
                print(f'{instruction} not found at address {self.pc}')
                sys.exit(1)
