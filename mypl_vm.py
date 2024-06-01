"""Implementation of the MyPL Virtual Machine (VM).

NAME: Connor Jones
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_error import *
from mypl_opcode import *
from mypl_frame import *


class VM:

    def __init__(self):
        """Creates a VM."""
        self.struct_heap = {}        # id -> dict
        self.array_heap = {}         # id -> list
        self.next_obj_id = 2024      # next available object id (int)
        self.frame_templates = {}    # function name -> VMFrameTemplate
        self.call_stack = []         # function call stack

    
    def __repr__(self):
        """Returns a string representation of frame templates."""
        s = ''
        for name, template in self.frame_templates.items():
            s += f'\nFrame {name}\n'
            for instr in template.instructions:
                s += f'  {i}: {instr}\n'
        return s

    
    def add_frame_template(self, template):
        """Add the new frame info to the VM. 

        Args: 
            frame -- The frame info to add.

        """
        self.frame_templates[template.function_name] = template

    
    def error(self, msg, frame=None):
        """Report a VM error."""
        if not frame:
            raise VMError(msg)
        pc = frame.pc - 1
        instr = frame.template.instructions[pc]
        name = frame.template.function_name
        msg += f' (in {name} at {pc}: {instr})'
        raise VMError(msg)

    
    #----------------------------------------------------------------------
    # RUN FUNCTION
    #----------------------------------------------------------------------
    
    def run(self, debug=False):
        """Run the virtual machine."""

        # grab the "main" function frame and instantiate it
        if not 'main' in self.frame_templates:
            self.error('No "main" functrion')
        frame = VMFrame(self.frame_templates['main'])
        self.call_stack.append(frame)

        # run loop (continue until run out of call frames or instructions)
        while self.call_stack and frame.pc < len(frame.template.instructions):
            # get the next instruction
            instr = frame.template.instructions[frame.pc]
            # increment the program count (pc)
            frame.pc += 1
            # for debugging:
            if debug:
                print('\n')
                print('\t FRAME.........:', frame.template.function_name)
                print('\t PC............:', frame.pc)
                print('\t INSTRUCTION...:', instr)
                val = None if not frame.operand_stack else frame.operand_stack[-1]
                print('\t NEXT OPERAND..:', val)
                cs = self.call_stack
                fun = cs[-1].template.function_name if cs else None
                print('\t NEXT FUNCTION..:', fun)

            #------------------------------------------------------------
            # Literals and Variables
            #------------------------------------------------------------

            if instr.opcode == OpCode.PUSH:
                frame.operand_stack.append(instr.operand)

            elif instr.opcode == OpCode.POP:
                frame.operand_stack.pop()
                
            elif instr.opcode == OpCode.STORE:
                tmp = frame.operand_stack.pop()
                if len(frame.variables) <= instr.operand:
                    frame.variables.append(tmp)
                else:
                    frame.variables[instr.operand] = tmp
            elif instr.opcode == OpCode.LOAD:
                tmp = frame.variables[instr.operand]
                frame.operand_stack.append(tmp)
            # TODO: Fill in rest of ops

            
            #------------------------------------------------------------
            # Operations
            #------------------------------------------------------------

            # TODO: Fill in rest of ops
            elif instr.opcode == OpCode.ADD:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error(f'Invalid addition between a null-type and non-null type')
                frame.operand_stack.append(y + x)
            elif instr.opcode == OpCode.SUB:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error(f'Invalid subtraction between a null-type and non-null type')
                frame.operand_stack.append(y - x)
            elif instr.opcode == OpCode.MUL:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error(f'Invalid multiplication between a null-type and non-null type')
                frame.operand_stack.append(y * x)
            elif instr.opcode == OpCode.DIV:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error(f'Invalid division between a null-type and non-null type')
                if x == 0:
                    self.error(f'Invalid division by zero')
                if isinstance(x, int):
                    frame.operand_stack.append(y//x)
                else:
                    frame.operand_stack.append(y/x)
            elif instr.opcode == OpCode.CMPLT:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error(f'Invalid comparison between a null-type and non-null type')
                frame.operand_stack.append(y < x)
            elif instr.opcode == OpCode.CMPLE:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error(f'Invalid comparison between a null-type and non-null type')
                frame.operand_stack.append(y <= x)
            elif instr.opcode == OpCode.CMPEQ:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                frame.operand_stack.append(y == x)
            elif instr.opcode == OpCode.CMPNE:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                frame.operand_stack.append(y != x)
            elif instr.opcode == OpCode.AND:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error(f'Invalid comparison between a null-type and non-null type')
                frame.operand_stack.append(y and x)
            elif instr.opcode == OpCode.OR:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error(f'Invalid comparison between a null-type and non-null type')
                frame.operand_stack.append(y or x)
            elif instr.opcode == OpCode.NOT:
                x = frame.operand_stack.pop()
                if x == None:
                    self.error(f'Invalid comparison between a null-type and non-null type')
                frame.operand_stack.append(not x)

            #------------------------------------------------------------
            # Branching
            #------------------------------------------------------------
            elif instr.opcode == OpCode.JMP:
                frame.pc = instr.operand
            elif instr.opcode == OpCode.JMPF:
                x = frame.operand_stack.pop()
                if x == False:
                    frame.pc = instr.operand

            # TODO: Fill in rest of ops
            
                    
            #------------------------------------------------------------
            # Functions
            #------------------------------------------------------------
            elif instr.opcode == OpCode.CALL:
                fun_name = instr.operand
                new_frame_template = self.frame_templates[fun_name]
                new_frame = VMFrame(new_frame_template)
                self.call_stack.append(new_frame)
                for i in range(0, new_frame_template.arg_count):
                    arg = frame.operand_stack.pop()
                    new_frame.operand_stack.append(arg)
                frame = new_frame
            elif instr.opcode == OpCode.RET:
                return_val = frame.operand_stack.pop()
                self.call_stack.pop()
                if not frame.template.function_name == 'main':
                    frame = self.call_stack[-1]
                frame.operand_stack.append(return_val)

            # TODO: Fill in rest of ops

            
            #------------------------------------------------------------
            # Built-In Functions
            #------------------------------------------------------------

            # TODO: Fill in rest of ops
            elif instr.opcode == OpCode.WRITE:
                x = frame.operand_stack.pop()
                if x == None:
                    print('null', end='')
                elif isinstance(x, bool):
                    if x == True:
                        print('true', end='')
                    else:
                        print('false', end='')
                else:
                    print(x, end='')
            elif instr.opcode == OpCode.READ:
                x = input()
                frame.operand_stack.append(x)
            elif instr.opcode == OpCode.LEN:
                x = frame.operand_stack.pop()
                if x == None:
                    self.error(f'Null value')
                if isinstance(x, str):
                    frame.operand_stack.append(len(x))
                else:
                    frame.operand_stack.append(len(self.array_heap[x]))
            elif instr.opcode == OpCode.GETC:
                x = frame.operand_stack.pop()
                if x == None:
                    self.error(f'Must be a valid string')
                y = frame.operand_stack.pop()
                if y == None:
                    self.error(f'Index must be of type int')
                if y >= len(x) or y < 0:
                    self.error(f'Invalid index for string')
                frame.operand_stack.append(x[y])
            elif instr.opcode == OpCode.TOINT:
                x = frame.operand_stack.pop()
                if x == None:
                    self.error(f'NoneType cannot be converted to int type')
                if type(x) == str:
                    if not x.isnumeric():
                        self.error(f'Item must be a valid number')
                frame.operand_stack.append(int(x))
            elif instr.opcode == OpCode.TODBL:
                x = frame.operand_stack.pop()
                if x == None:
                    self.error(f'NoneType cannot be converted to double type')
                if type(x) == str:
                    for ch in x:
                        if ch.isalpha():
                            self.error(f'Must be a valid number')
                if type(x) == int:
                    frame.operand_stack.append(x/1.0)
                else:
                    frame.operand_stack.append(float(x))
            elif instr.opcode == OpCode.TOSTR:
                x = frame.operand_stack.pop()
                if x == None:
                    self.error(f'NoneType cannot be converted to string type')
                frame.operand_stack.append(str(x))
            
            #------------------------------------------------------------
            # Heap
            #------------------------------------------------------------


            # TODO: Fill in rest of ops
            elif instr.opcode == OpCode.ALLOCS:
                oid = self.next_obj_id
                self.next_obj_id += 1
                frame.operand_stack.append(oid)
                self.struct_heap[oid] = {}
            elif instr.opcode == OpCode.SETF:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if not y in self.struct_heap:
                    self.error(f'Object not found')
                self.struct_heap[y][instr.operand] = x
            elif instr.opcode == OpCode.GETF:
                x = frame.operand_stack.pop()
                if not x in self.struct_heap:
                    self.error(f'Object not found')
                frame.operand_stack.append(self.struct_heap[x][instr.operand])
            elif instr.opcode == OpCode.ALLOCA:
                oid = self.next_obj_id
                self.next_obj_id += 1
                x = frame.operand_stack.pop()
                frame.operand_stack.append(oid)
                if x == None:
                    self.error(f'Size of array must be of int-type')
                if x < 0:
                    self.error(f'Size of array must be zero or greater')
                self.array_heap[oid] = []
                if x > 0:
                    for i in range(0, x):
                        self.array_heap[oid].append(None)
            elif instr.opcode == OpCode.SETI:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                z = frame.operand_stack.pop()
                if not z in self.array_heap:
                    self.error(f'Array object not found')
                if y == None:
                    self.error(f'Array index must be of int-type')    
                if y < 0 or y >= len(self.array_heap[z]):
                    self.error(f'Cannot reach index {y}')
                self.array_heap[z][y] = x
            elif instr.opcode == OpCode.GETI:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if not y in self.array_heap:
                    self.error(f'Array object not found')
                if x == None:
                    self.error(f'Array index must be of int-type')
                if x < 0 or x >= len(self.array_heap[y]):
                    self.error(f'Cannot reach index {x}')
                frame.operand_stack.append(self.array_heap[y][x])
            
            #------------------------------------------------------------
            # Special 
            #------------------------------------------------------------

            elif instr.opcode == OpCode.DUP:
                x = frame.operand_stack.pop()
                frame.operand_stack.append(x)
                frame.operand_stack.append(x)

            elif instr.opcode == OpCode.NOP:
                # do nothing
                pass

            else:
                self.error(f'unsupported operation {instr}')
