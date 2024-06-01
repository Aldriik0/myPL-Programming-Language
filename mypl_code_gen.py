"""IR code generator for converting MyPL to VM Instructions. 

NAME: <your name here>
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_token import *
from mypl_ast import *
from mypl_var_table import *
from mypl_frame import *
from mypl_opcode import *
from mypl_vm import *


class CodeGenerator (Visitor):

    def __init__(self, vm):
        """Creates a new Code Generator given a VM. 
        
        Args:
            vm -- The target vm.
        """
        # the vm to add frames to
        self.vm = vm
        # the current frame template being generated
        self.curr_template = None
        # for var -> index mappings wrt to environments
        self.var_table = VarTable()
        # struct name -> StructDef for struct field info
        self.struct_defs = {}

    
    def add_instr(self, instr):
        """Helper function to add an instruction to the current template."""
        self.curr_template.instructions.append(instr)

        
    def visit_program(self, program):
        for struct_def in program.struct_defs:
            struct_def.accept(self)
        for fun_def in program.fun_defs:
            fun_def.accept(self)

    
    def visit_struct_def(self, struct_def):
        # remember the struct def for later
        self.struct_defs[struct_def.struct_name.lexeme] = struct_def
   
    def visit_fun_def(self, fun_def):
        # TODO
        
        self.curr_template = VMFrameTemplate(fun_def.fun_name.lexeme, len(fun_def.params))
        self.var_table.push_environment()
        for var in fun_def.params:
            self.var_table.add(var.var_name.lexeme)
            idx = self.var_table.get(var.var_name.lexeme)
            self.add_instr(STORE(idx))
        for stmt in fun_def.stmts:
            stmt.accept(self)
        
        if not isinstance(fun_def.stmts[-1:], ReturnStmt):
            self.add_instr(PUSH(None))
            self.add_instr(RET())
        
        self.vm.add_frame_template(self.curr_template)
        self.var_table.pop_environment()

    def visit_return_stmt(self, return_stmt):
        # TODO
        return_stmt.expr.accept(self)
        self.add_instr(RET())
    
    def visit_var_decl(self, var_decl):
        # TODO
        var_name = var_decl.var_def.var_name.lexeme
        self.var_table.add(var_name)
        idx = self.var_table.get(var_name)
        if not var_decl.expr == None:
            var_decl.expr.accept(self)
            self.add_instr(STORE(idx))
        else:
            self.add_instr(PUSH(None))
            self.add_instr(STORE(idx))
 
    def visit_assign_stmt(self, assign_stmt):
        # TODO
        if len(assign_stmt.lvalue) == 1:
            var = assign_stmt.lvalue[0]
            idx = self.var_table.get(var.var_name.lexeme)
            if not var.array_expr == None:
                self.add_instr(LOAD(idx)) #load oid
                var.array_expr.accept(self) #push index
                assign_stmt.expr.accept(self) #load value
                self.add_instr(SETI()) #store value into oid[index] = value
            else:
                assign_stmt.expr.accept(self) #load value
                self.add_instr(STORE(idx)) #store into the var
        else:
            idx = self.var_table.get(assign_stmt.lvalue[0].var_name.lexeme) #retrieve the storage idx
            self.add_instr(LOAD(idx)) #laod the struct oid
            if not assign_stmt.lvalue[0].array_expr == None:
                assign_stmt.lvalue[0].array_expr.accept(self) #push the idx
                self.add_instr(GETI()) #retrieve oid[idx] which is most likely another oid
            for i in range(1, len(assign_stmt.lvalue)):
                if i == len(assign_stmt.lvalue)-1:
                    if not assign_stmt.lvalue[i].array_expr == None:
                        self.add_instr(GETF(assign_stmt.lvalue[i].var_name.lexeme)) #get the oid of the ending array
                        assign_stmt.lvalue[i].array_expr.accept(self) #get the idx
                        assign_stmt.expr.accept(self)
                        self.add_instr(SETI())
                    else:
                        assign_stmt.expr.accept(self) #push the value on the stack
                        self.add_instr(SETF(assign_stmt.lvalue[i].var_name.lexeme)) #set oid[field] = value
                else:
                    if not assign_stmt.lvalue[i].array_expr == None:
                        self.add_instr(GETF(assign_stmt.lvalue[i].var_name.lexeme)) #get the oid of the ending array
                        assign_stmt.lvalue[i].array_expr.accept(self) #get the idx
                        self.add_instr(GETI())
                    else:
                        self.add_instr(GETF(assign_stmt.lvalue[i].var_name.lexeme)) #the the next oid for the appropriate path
           

    def visit_while_stmt(self, while_stmt):
        # TODO
        self.var_table.push_environment()
        beginning_inst = len(self.curr_template.instructions)
        while_stmt.condition.accept(self)
        jmpf_idx =  len(self.curr_template.instructions)
        self.add_instr(JMPF(-1))
        
        for stmt in while_stmt.stmts:
            stmt.accept(self)
        
        self.add_instr(JMP(beginning_inst))
        self.add_instr(NOP())
        self.curr_template.instructions[jmpf_idx].operand = len(self.curr_template.instructions) -1
        self.var_table.pop_environment()

    def visit_for_stmt(self, for_stmt):
        # TODO
        self.var_table.push_environment()
        for_stmt.var_decl.accept(self)
        beginning_inst = len(self.curr_template.instructions)
        for_stmt.condition.accept(self)
        jmpf_idx = len(self.curr_template.instructions)
        self.add_instr(JMPF(-1))
        
        for stmt in for_stmt.stmts:
            stmt.accept(self)
        
        for_stmt.assign_stmt.accept(self)
        
        self.add_instr(JMP(beginning_inst))
        self.add_instr(NOP())
        self.curr_template.instructions[jmpf_idx].operand = len(self.curr_template.instructions) - 1
        self.var_table.pop_environment()
   
    def visit_if_stmt(self, if_stmt):
        # TODO
        jmps = []
        self.var_table.push_environment()
        if_stmt.if_part.condition.accept(self) #evaluate the expression
        jmpf_idx = len(self.curr_template.instructions)
        self.add_instr(JMPF(-1))
        
        for stmt in if_stmt.if_part.stmts:
            stmt.accept(self)
        
        jmps.append(len(self.curr_template.instructions))
        self.add_instr(JMP(-1))
        
        self.curr_template.instructions[jmpf_idx].operand = len(self.curr_template.instructions)    
        self.add_instr(NOP())
        self.var_table.pop_environment()
        
        if len(if_stmt.else_ifs) > 0:
            for else_if in if_stmt.else_ifs:
                self.var_table.push_environment()
                else_if.condition.accept(self)
                jmpf_idx = len(self.curr_template.instructions)
                self.add_instr(JMPF(-1))
                
                for stmt in else_if.stmts:
                    stmt.accept(self)
                
                jmps.append(len(self.curr_template.instructions))
                self.add_instr(JMP(-1))
                
                self.curr_template.instructions[jmpf_idx].operand = len(self.curr_template.instructions)
                self.add_instr(NOP())
                self.var_table.pop_environment()
        if not if_stmt.else_stmts == None:
            for else_stmt in if_stmt.else_stmts:
                
                self.var_table.push_environment()
            
                for stmt in else_stmt.stmts:
                    stmt.accept(self)
                    
                self.add_instr(NOP())
                self.var_table.pop_environment()
            
        
        for jmp in jmps:
            self.curr_template.instructions[jmp].operand = len(self.curr_template.instructions) - 1
    
    def visit_call_expr(self, call_expr):
        # TODO
        fun_name = call_expr.fun_name.lexeme
        if fun_name == 'print':
            for arg in call_expr.args:
                arg.accept(self)
            
            self.add_instr(WRITE())
        elif fun_name == 'input':
            self.add_instr(READ())
        elif fun_name == 'itos':
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(TOSTR())
        elif fun_name == 'itod':
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(TODBL())
        elif fun_name == 'dtos':
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(TOSTR())
        elif fun_name == 'dtoi':
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(TOINT())
        elif fun_name == 'stoi':
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(TOINT())
        elif fun_name == 'stod':
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(TODBL())
        elif fun_name == 'length':
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(LEN())
        elif fun_name == 'get':
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(GETC())
        else:
            for arg in call_expr.args:
                arg.accept(self)
            self.add_instr(CALL(fun_name))
  
    def visit_expr(self, expr):
        # TODO
        if not expr.op == None:
            op = expr.op.lexeme
            if op == '>=':
                expr.rest.accept(self)
                expr.first.accept(self)
                self.add_instr(CMPLE())
            elif op == '>':
                expr.rest.accept(self)
                expr.first.accept(self)
                self.add_instr(CMPLT())
            elif op == '<':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(CMPLT())
            elif op == '<=':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(CMPLE())
            elif op == '==':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(CMPEQ())
            elif op == '!=':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(CMPNE())
            elif op == 'and':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(AND())
            elif op == 'or':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(OR())
            elif op == '+':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(ADD())
            elif op == '-':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(SUB())
            elif op == '*':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(MUL())
            elif op == '/':
                expr.first.accept(self)
                expr.rest.accept(self)
                self.add_instr(DIV())
        else:
            expr.first.accept(self)
     
        if expr.not_op:
            self.add_instr(NOT())
   
    def visit_data_type(self, data_type):
        # nothing to do here
        pass
   
    def visit_var_def(self, var_def):
        # nothing to do here
        pass
   
    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)
  
    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)
 
    def visit_simple_rvalue(self, simple_rvalue):
        val = simple_rvalue.value.lexeme
        if simple_rvalue.value.token_type == TokenType.INT_VAL:
            self.add_instr(PUSH(int(val)))
        elif simple_rvalue.value.token_type == TokenType.DOUBLE_VAL:
            self.add_instr(PUSH(float(val)))
        elif simple_rvalue.value.token_type == TokenType.STRING_VAL:
            val = val.replace('\\n', '\n')
            val = val.replace('\\t', '\t')
            self.add_instr(PUSH(val))
        elif val == 'true':
            self.add_instr(PUSH(True))
        elif val == 'false':
            self.add_instr(PUSH(False))
        elif val == 'null':
            self.add_instr(PUSH(None))
  
    def visit_new_rvalue(self, new_rvalue):
        # TODO     
        if new_rvalue.type_name.lexeme in self.struct_defs:
            if not new_rvalue.array_expr == None:
                new_rvalue.array_expr.accept(self)
                self.add_instr(ALLOCA())
            else:
                struct = self.struct_defs[new_rvalue.type_name.lexeme]
                fields = []
                for field in struct.fields:
                    fields.append(field.var_name.lexeme)
                self.add_instr(ALLOCS()) #puts oid on stack
                for i in range(len(new_rvalue.struct_params)):
                    field = new_rvalue.struct_params[i]
                    self.add_instr(DUP()) #dup the oid
                    field.accept(self) #put the value on the stack
                    self.add_instr(SETF(fields[i])) #set the according field
        else:
            new_rvalue.array_expr.accept(self) #push the size on the stack
            self.add_instr(ALLOCA()) #create and push oid onto the stack
            
    def visit_var_rvalue(self, var_rvalue):
        # TODO
        
        if len(var_rvalue.path) == 1:
            var = var_rvalue.path[0]
            idx = self.var_table.get(var.var_name.lexeme)
            self.add_instr(LOAD(idx)) #load oid
            if not var.array_expr == None:
                var.array_expr.accept(self) #push the idx
                self.add_instr(GETI()) #retrieve data at oid[idx]
        else:
            
            idx = self.var_table.get(var_rvalue.path[0].var_name.lexeme)
            self.add_instr(LOAD(idx)) #load the oid
            if not var_rvalue.path[0].array_expr == None:
                var_rvalue.path[0].array_expr.accept(self) #push the idx
                self.add_instr(GETI()) #retrieve oid[idx] which is most likely another oid
            for i in range(1, len(var_rvalue.path)):
                if not var_rvalue.path[i].array_expr == None:
                    self.add_instr(GETF(var_rvalue.path[i].var_name.lexeme)) #retrieve the oid/value
                    var_rvalue.path[i].array_expr.accept(self) #push the idx
                    self.add_instr(GETI()) #get the oid[idx] value
                else:
                    self.add_instr(GETF(var_rvalue.path[i].var_name.lexeme)) #retrieve the oid/value
            