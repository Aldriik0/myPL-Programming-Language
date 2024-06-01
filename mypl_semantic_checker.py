"""Semantic Checker Visitor for semantically analyzing a MyPL program.

NAME: Connor Jones
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from mypl_error import *
from mypl_token import Token, TokenType
from mypl_ast import *
from mypl_symbol_table import SymbolTable


BASE_TYPES = ['int', 'double', 'bool', 'string']
BUILT_INS = ['print', 'input', 'itos', 'itod', 'dtos', 'dtoi', 'stoi', 'stod',
             'length', 'get']

class SemanticChecker(Visitor):
    """Visitor implementation to semantically check MyPL programs."""

    def __init__(self):
        self.structs = {}
        self.functions = {}
        self.symbol_table = SymbolTable()
        self.curr_type = None


    # Helper Functions

    def error(self, msg, token):
        """Create and raise a Static Error."""
        if token is None:
            raise StaticError(msg)
        else:
            m = f'{msg} near line {token.line}, column {token.column}'
            raise StaticError(m)


    def get_field_type(self, struct_def, field_name):
        """Returns the DataType for the given field name of the struct
        definition.

        Args:
            struct_def: The StructDef object 
            field_name: The name of the field

        Returns: The corresponding DataType or None if the field name
        is not in the struct_def.

        """
        for var_def in struct_def.fields:
            if var_def.var_name.lexeme == field_name:
                return var_def.data_type
        return None

        
    # Visitor Functions
    
    def visit_program(self, program):
        # check and record struct defs
        for struct in program.struct_defs:
            struct_name = struct.struct_name.lexeme
            if struct_name in self.structs:
                self.error(f'duplicate {struct_name} definition', struct.struct_name)
            self.structs[struct_name] = struct
        # check and record function defs
        for fun in program.fun_defs:
            fun_name = fun.fun_name.lexeme
            if fun_name in self.functions: 
                self.error(f'duplicate {fun_name} definition', fun.fun_name)
            if fun_name in BUILT_INS:
                self.error(f'redefining built-in function', fun.fun_name)
            if fun_name == 'main' and fun.return_type.type_name.lexeme != 'void':
                self.error('main without void type', fun.return_type.type_name)
            if fun_name == 'main' and fun.params: 
                self.error('main function with parameters', fun.fun_name)
            self.functions[fun_name] = fun
        # check main function
        if 'main' not in self.functions:
            self.error('missing main function', None)
        # check each struct
        for struct in self.structs.values():
            struct.accept(self)
        # check each function
        for fun in self.functions.values():
            fun.accept(self)
    
    def visit_struct_def(self, struct_def):
        self.symbol_table.push_environment()
        for field in struct_def.fields:
            field.accept(self)
        self.symbol_table.pop_environment()
        
    def visit_fun_def(self, fun_def):
        self.symbol_table.push_environment()
        fun_def.return_type.accept(self)
        self.symbol_table.add('return', self.curr_type)
        for param in fun_def.params:
            param.accept(self)
        for stmt in fun_def.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()
        
    def visit_return_stmt(self, return_stmt):
        return_stmt.expr.accept(self)
        if not self.curr_type.type_name.lexeme == self.symbol_table.get('return').type_name.lexeme and self.curr_type.type_name.lexeme != 'void':
            self.error(f'Trying to retrun type {self.curr_type.type_name.lexeme} requires {self.symbol_table.get('return').type_name.lexeme}', self.curr_type.type_name)
        if not self.curr_type.is_array == self.symbol_table.get('return').is_array:
            self.error(f'Mismatching types trying to pass an array to non-array', self.curr_type.type_name)
        
    def visit_var_decl(self, var_decl):
        var_decl.var_def.accept(self)
        if not var_decl.expr == None:
            var_decl.expr.accept(self)
            if isinstance(var_decl.expr.first, SimpleTerm):
                if isinstance(var_decl.expr.first.rvalue, VarRValue):
                    if var_decl.var_def.data_type.is_array == True:
                        self.curr_type.is_array = True  
            if not self.curr_type.type_name.lexeme == var_decl.var_def.data_type.type_name.lexeme and not self.curr_type.type_name.lexeme == 'void':
                self.error(f'Trying to assign a {self.curr_type.type_name.lexeme} to a {var_decl.var_def.data_type.type_name.lexeme}', self.curr_type.type_name)
            if not self.curr_type.is_array == var_decl.var_def.data_type.is_array and not self.curr_type.type_name.lexeme == 'void':
                self.error(f'Trying to assign an array type to a non-array type', self.curr_type.type_name)
        
    def visit_assign_stmt(self, assign_stmt):
        tmp = self.symbol_table.get(assign_stmt.lvalue[len(assign_stmt.lvalue)-1].var_name.lexeme)
        if not assign_stmt.expr == None:
            assign_stmt.expr.accept(self)
            for i in range(len(assign_stmt.lvalue)):
                if not assign_stmt.lvalue[i].array_expr == None:
                    self.curr_type.is_array = False
            if not tmp == None:
                if self.curr_type.type_name.lexeme != tmp.type_name.lexeme and self.curr_type.type_name.lexeme != 'void':
                    if self.curr_type.type_name != 'bool' or tmp.type_name.lexeme != 'double':
                        self.error(f'Invalid assignment {tmp.type_name.lexeme}', tmp.type_name)
                if self.curr_type.is_array != tmp.is_array and self.curr_type.type_name.lexeme != 'void':
                        if tmp.is_array == False:
                            self.error(f'Invalid assignment {tmp.type_name.lexeme}', tmp.type_name)
                        
            struct_var = self.symbol_table.get(assign_stmt.lvalue[0].var_name.lexeme)
            tempo = self.symbol_table.get(assign_stmt.lvalue[0].var_name.lexeme)
            for i in range(len(assign_stmt.lvalue)):
                if not self.symbol_table.get(assign_stmt.lvalue[i].var_name.lexeme) == None:
                    tempo = self.symbol_table.get(assign_stmt.lvalue[i].var_name.lexeme)
                    
            if tempo != None:
                if tempo.type_name.lexeme in self.structs:
                    for i in range(len(self.structs[tempo.type_name.lexeme].fields)):
                        if self.structs[tempo.type_name.lexeme].fields[i].var_name.lexeme == assign_stmt.lvalue[len(assign_stmt.lvalue)-1].var_name.lexeme:
                            if self.curr_type.type_name in BASE_TYPES:
                                if self.curr_type.type_name.lexeme != self.structs[tempo.type_name.lexeme].fields[i].data_type.type_name.lexeme and self.structs[tempo.type_name.lexeme].fields[i].data_type.type_name.lexeme != 'void':
                                    if self.curr_type.type_name.lexeme != 'double' or self.structs[tempo.type_name.lexeme].fields[i].data_type.type_name.lexeme != 'bool':
                                        self.error(f'Invalid assignment {self.structs[tempo.type_name.lexeme].fields[i].data_type.type_name.lexeme}', tempo.type_name.lexeme)
            else:
                self.error(f'Struct {assign_stmt.lvalue[0].var_name.lexeme} not declared', assign_stmt.lvalue[0].var_name)
            if self.symbol_table.get(assign_stmt.lvalue[0].var_name.lexeme).type_name.lexeme in self.structs:
                for k in range(len(assign_stmt.lvalue)):
                    tmp = assign_stmt.lvalue[k]
                    for i in self.structs:
                        for j in range(len(self.structs[i].fields)):
                            if tmp.var_name.lexeme == self.structs[i].fields[j].var_name.lexeme:
                                if tmp.array_expr == None and self.structs[i].fields[j].data_type.is_array == True and k != (len(assign_stmt.lvalue) - 1):
                                    self.error(f'Invalid array assignment {tmp.var_name.lexeme}', tmp.var_name)
                            
    def visit_while_stmt(self, while_stmt):
        self.symbol_table.push_environment()
        while_stmt.condition.accept(self)
        if not self.curr_type.type_name.lexeme == 'bool':
            self.error(f'Need a boolean expression in condition, received {self.curr_type.type_name.lexeme}', self.curr_type.type_name)
        for stmt in while_stmt.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()
        
    def visit_for_stmt(self, for_stmt):
        self.symbol_table.push_environment()
        for_stmt.var_decl.accept(self)
        for_stmt.condition.accept(self)
        if not self.curr_type.type_name.lexeme == 'bool':
            self.error(f'Need a boolean expression in condition, received {self.curr_type.type_name.lexeme}', self.curr_type.type_name)
        for_stmt.assign_stmt.accept(self)
        for stmt in for_stmt.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()
    
    def visit_if_stmt(self, if_stmt):
        self.symbol_table.push_environment()
        if_stmt.if_part.condition.accept(self)
        if isinstance(if_stmt.if_part.condition.first, ComplexTerm):
            pass
        elif isinstance(if_stmt.if_part.condition.first.rvalue, VarRValue):
            if len(if_stmt.if_part.condition.first.rvalue.path) > 0:
                if if_stmt.if_part.condition.first.rvalue.path[len(if_stmt.if_part.condition.first.rvalue.path) - 1].array_expr == None:
                    if not self.symbol_table.get(if_stmt.if_part.condition.first.rvalue.path[len(if_stmt.if_part.condition.first.rvalue.path) - 1].var_name.lexeme) == None:
                        if self.symbol_table.get(if_stmt.if_part.condition.first.rvalue.path[len(if_stmt.if_part.condition.first.rvalue.path) - 1].var_name.lexeme).is_array == True:
                            print('here')
                            self.error(f'Need indexing on variable declared as an array', self.curr_type.type_name)
        if not self.curr_type.type_name.lexeme == 'bool':
                self.error(f'Need a boolean expression in condition, received {self.curr_type.type_name.lexeme}', self.curr_type.type_name)                        
        for stmt in if_stmt.if_part.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()
        
        for else_if in if_stmt.else_ifs:
            self.symbol_table.push_environment()
            else_if.condition.accept(self)
            if isinstance(else_if.condition.first, ComplexTerm):
                pass
            if isinstance(else_if.condition.first.rvalue, VarRValue):
                if len(else_if.condition.first.rvalue.path) > 0:
                    if else_if.condition.first.rvalue.path[len(else_if.condition.first.rvalue.path) - 1].array_expr == None and self.symbol_table.get(else_if.condition.first.rvalue.path[len(else_if.condition.first.rvalue.path) - 1].var_name.lexeme).is_array == True:
                        if else_if.condition.first.rvalue.path[len(else_if.condition.first.rvalue.path) - 1].array_expr == None:
                            self.error(f'Need indexing on variable declared as an array', self.curr_type.type_name)
            if not self.curr_type.type_name.lexeme == 'bool':
                self.error(f'Need a boolean expression in condition, received {self.curr_type.type_name.lexeme}', self.curr_type.type_name)
            for stmt in else_if.stmts:
                stmt.accept(self)
            self.symbol_table.pop_environment()
        
        for else_stmt in if_stmt.else_stmts:
            self.symbol_table.push_environment()
            for stmt in else_stmt.stmts:
                stmt.accept(self)
            self.symbol_table.pop_environment()
    
    def visit_call_expr(self, call_expr):
        #check to see if the function is a built in
        if call_expr.fun_name.lexeme in BUILT_INS:
            #input doesn't require a param, so check that first
            if call_expr.fun_name.lexeme == 'input':
                #verify that it has no params passed in
                if not len(call_expr.args) == 0:
                    self.error(f'Passed in {len(call_expr.args)}, expecting 0', call_expr.fun_name)
                self.curr_type = DataType(False, Token(TokenType.STRING_TYPE, 'string', call_expr.fun_name.line, call_expr.fun_name.line))
            elif call_expr.fun_name.lexeme == 'get':
                if not len(call_expr.args) == 2:
                    self.error(f'Passed in {len(call_expr.args)}, expecting 2', call_expr.fun_name)
                #check the validity of the arguments
                call_expr.args[0].accept(self)
                if not self.curr_type.type_name.lexeme == 'int' and not self.curr_type.is_array:
                    self.error(f'First argument expecting int, received {self.curr_type.type_name.lexeme}', self.curr_type.type_name)
                call_expr.args[1].accept(self)
                if not self.curr_type.type_name.lexeme == 'string' and not self.curr_type.is_array:
                    self.error(f'Second argument expecting string, received {self.curr_type.type_name.lexeme}', self.curr_type.type_name)
            else:
                #check for exactly one paramter
                if not len(call_expr.args) == 1:
                    self.error(f'Passed in {len(call_expr.args)}, expecting 1', call_expr.fun_name)
                #time to check each built in is receiving their proper argument type
                call_expr.args[0].accept(self)
                if call_expr.fun_name.lexeme == 'itos':
                    if not self.curr_type.type_name.lexeme == 'int':
                        self.error(f'Passed in {self.curr_type.type_name.lexeme}, expecting int', self.curr_type.type_name)
                    self.curr_type = DataType(False, Token(TokenType.STRING_TYPE, 'string', call_expr.fun_name.line, call_expr.fun_name.line))
                if call_expr.fun_name.lexeme == 'itod':
                    if not self.curr_type.type_name.lexeme == 'int':
                        self.error(f'Passed in {self.curr_type.type_name.lexeme}, expecting int', self.curr_type.type_name)
                    self.curr_type = DataType(False, Token(TokenType.DOUBLE_TYPE, 'double', call_expr.fun_name.line, call_expr.fun_name.line))
                if call_expr.fun_name.lexeme == 'dtos':    
                    if not self.curr_type.type_name.lexeme == 'double':
                        self.error(f'Passed in {self.curr_type.type_name.lexeme}, expecting double', self.curr_type.type_name)
                    self.curr_type = DataType(False, Token(TokenType.STRING_TYPE, 'string', call_expr.fun_name.line, call_expr.fun_name.line))
                if call_expr.fun_name.lexeme == 'dtoi':    
                    if not self.curr_type.type_name.lexeme == 'double':
                        self.error(f'Passed in {self.curr_type.type_name.lexeme}, expecting double', self.curr_type.type_name)
                    self.curr_type = DataType(False, Token(TokenType.INT_TYPE, 'int', call_expr.fun_name.line, call_expr.fun_name.line))
                if call_expr.fun_name.lexeme == 'stoi':
                    if not self.curr_type.type_name.lexeme == 'string':
                        self.error(f'Passed in {self.curr_type.type_name.lexeme}, expecting string', self.curr_type.type_name)
                    self.curr_type = DataType(False, Token(TokenType.INT_TYPE, 'int', call_expr.fun_name.line, call_expr.fun_name.line))
                if call_expr.fun_name.lexeme == 'stod':
                    if not self.curr_type.type_name.lexeme == 'string':
                        self.error(f'Passed in {self.curr_type.type_name.lexeme}, expecting string', self.curr_type.type_name)
                    self.curr_type = DataType(False, Token(TokenType.DOUBLE_TYPE, 'double', call_expr.fun_name.line, call_expr.fun_name.line))
                if call_expr.fun_name.lexeme == 'print':
                    if self.curr_type.type_name.lexeme in self.structs:
                        self.error(f'Function print cannot take in struct data types', self.curr_type.type_name)
                    if self.curr_type.is_array:
                        self.error(f'Function print cannot take in array data types', self.curr_type.type_name)
                    self.curr_type = DataType(False, Token(TokenType.VOID_TYPE, 'void', call_expr.fun_name.line, call_expr.fun_name.line))
                if call_expr.fun_name.lexeme == 'length':
                    if (self.curr_type.type_name.lexeme == 'int' and not self.curr_type.is_array) or (self.curr_type.type_name.lexeme == 'double' and not self.curr_type.is_array):
                        self.error(f'Invalid arguments passed in', self.curr_type.type_name)
                    self.curr_type = DataType(False, Token(TokenType.INT_TYPE, 'int', call_expr.fun_name.line, call_expr.fun_name.line))
        elif call_expr.fun_name.lexeme in self.functions:
            function = self.functions[call_expr.fun_name.lexeme]
            if not len(call_expr.args) == len(function.params):
                self.error(f'Passed in {len(call_expr.args)}, expecting {len(function.params)}', call_expr.fun_name)
            for i in range(0, len(call_expr.args)):
                call_expr.args[i].accept(self)
                if not self.curr_type.type_name.lexeme == function.params[i].data_type.type_name.lexeme and not self.curr_type.type_name.lexeme == 'void':
                    self.error(f'Mismatching parameter types, passed in {self.curr_type.type_name.lexeme}, expecting {function.params[i].data_type.type_name.lexeme}', self.curr_type.type_name)
            self.curr_type = function.return_type
        else:
            self.error(f'Function {call_expr.fun_name.lexeme} not declared', call_expr.fun_name)
    
    def visit_expr(self, expr):
        expr.first.accept(self)
        if not expr.op == None:
            tmp_curr = self.curr_type
            expr.rest.accept(self)
            if tmp_curr.type_name.lexeme == 'void' or self.curr_type.type_name.lexeme == 'void':
                pass
            elif tmp_curr.type_name.lexeme != self.curr_type.type_name.lexeme:
                self.error(f'Trying to perform an operation on mismatched types', self.curr_type.type_name)
            if expr.op.lexeme == '>':
                if tmp_curr.type_name.lexeme == 'bool' or self.curr_type.type_name.lexeme == 'bool':
                    self.error(f'Trying to perform a int/double operation on a bool', tmp_curr.type_name)
                tmp_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
                self.curr_type = DataType(False, tmp_token)
            elif expr.op.lexeme == '<':
                if tmp_curr.type_name.lexeme == 'bool' or self.curr_type.type_name.lexeme == 'bool':
                    self.error(f'Trying to perform a int/double operation on a bool', tmp_curr.type_name)
                tmp_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
                self.curr_type = DataType(False, tmp_token)
            elif expr.op.lexeme == '>=':
                if tmp_curr.type_name.lexeme == 'bool' or self.curr_type.type_name.lexeme == 'bool':
                    self.error(f'Trying to perform a int/double operation on a bool', tmp_curr.type_name)
                tmp_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
                self.curr_type = DataType(False, tmp_token)
            elif expr.op.lexeme == '<=':
                if tmp_curr.type_name.lexeme == 'bool' or self.curr_type.type_name.lexeme == 'bool':
                    self.error(f'Trying to perform a int/double operation on a bool', tmp_curr.type_name)
                tmp_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
                self.curr_type = DataType(False, tmp_token)
            elif expr.op.lexeme == '==':
                tmp_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
                self.curr_type = DataType(False, tmp_token)
            elif expr.op.lexeme == '!=':
                tmp_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
                self.curr_type = DataType(False, tmp_token)
            elif expr.op.lexeme == 'and':
                tmp_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
                self.curr_type = DataType(False, tmp_token)
            elif expr.op.lexeme == 'or':
                tmp_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
                self.curr_type = DataType(False, tmp_token) 
                
        if expr.not_op == True:
            self.curr_type.type_name.lexeme = 'bool'
            self.curr_type.type_name.token_type = TokenType.BOOL_TYPE
            if expr.op == None and hasattr(expr.first, 'expr'):
                if expr.first.expr.op.lexeme == '+':
                    self.error(f'Trying to apply not to a numeric operation', self.curr_type.type_name)
                if expr.first.expr.op.lexeme == '-':
                    self.error(f'Trying to apply not to a numeric operation', self.curr_type.type_name)
                if expr.first.expr.op.lexeme == '*':
                    self.error(f'Trying to apply not to a numeric operation', self.curr_type.type_name)
                if expr.first.expr.op.lexeme == '/':
                    self.error(f'Trying to apply not to a numeric operation', self.curr_type.type_name)
       
    def visit_data_type(self, data_type):
        # note: allowing void (bad cases of void caught by parser)
        name = data_type.type_name.lexeme
        if name == 'void' or name in BASE_TYPES or name in self.structs:
            self.curr_type = data_type
        else: 
            self.error(f'invalid type "{name}"', data_type.type_name)
    
    def visit_var_def(self, var_def):
        var_def.data_type.accept(self)
        if self.symbol_table.exists_in_curr_env(var_def.var_name.lexeme) and self.curr_type.type_name.lexeme != self.symbol_table.get(var_def.var_name.lexeme).type_name.lexeme:
            self.error(f'Illegal case of shadowing', var_def.var_name)
        
        self.symbol_table.add(var_def.var_name.lexeme, self.curr_type)
        
    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)
        
    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)
        
    def visit_simple_rvalue(self, simple_rvalue):
        value = simple_rvalue.value
        line = simple_rvalue.value.line
        column = simple_rvalue.value.column
        type_token = None 
        if value.token_type == TokenType.INT_VAL:
            type_token = Token(TokenType.INT_TYPE, 'int', line, column)
        elif value.token_type == TokenType.DOUBLE_VAL:
            type_token = Token(TokenType.DOUBLE_TYPE, 'double', line, column)
        elif value.token_type == TokenType.STRING_VAL:
            type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
        elif value.token_type == TokenType.BOOL_VAL:
            type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
        elif value.token_type == TokenType.NULL_VAL:
            type_token = Token(TokenType.VOID_TYPE, 'void', line, column)
        self.curr_type = DataType(False, type_token)
        
    def visit_new_rvalue(self, new_rvalue):
        tmp = self.curr_type
        if new_rvalue.type_name.lexeme in self.structs:
            struct = self.structs[new_rvalue.type_name.lexeme]
            if not new_rvalue.struct_params == None:
                if not len(new_rvalue.struct_params) == len(struct.fields):
                    self.error(f'Passed in {len(new_rvalue.struct_params)}, expecting {len(struct.fields)}', new_rvalue.type_name)
                for i in range(0, len(new_rvalue.struct_params)):
                    field = struct.fields[i]
                    new_rvalue.struct_params[i].accept(self)
                    if not field.data_type.type_name.lexeme == self.curr_type.type_name.lexeme and not self.curr_type.type_name.lexeme == 'void':
                        self.error(f'Passed in type {self.curr_type.type_name.lexeme}, expecting {field.data_type.type_name.lexeme}', self.curr_type.type_name)
                    if not field.data_type.is_array == self.curr_type.is_array and not self.curr_type.type_name.lexeme == 'void':
                        self.error(f'Mismatch between array and non-array', self.curr_type.type_name)
        if not new_rvalue.array_expr == None:
            self.curr_type = DataType(True, new_rvalue.type_name)
        else:
            self.curr_type = DataType(False, new_rvalue.type_name)
            
    def visit_var_rvalue(self, var_rvalue):
        #first let's clear just standard variables
        if len(var_rvalue.path) == 1:
            #check to see if var exists
            var = var_rvalue.path[0]
            if not self.symbol_table.exists(var.var_name.lexeme):
                self.error(f'Variable {var.var_name.lexeme} not declared', var.var_name)
            self.curr_type = self.symbol_table.get(var.var_name.lexeme)
            if not var.array_expr == None:
                self.curr_type = self.symbol_table.get(var.var_name.lexeme)
                self.curr_type.is_array = False
        elif self.symbol_table.get(var_rvalue.path[0].var_name.lexeme).type_name.lexeme in self.structs:
            struct = self.structs[self.symbol_table.get(var_rvalue.path[0].var_name.lexeme).type_name.lexeme]
            for i in range(1, len(var_rvalue.path)):
                #check if it's an actual field in the struct
                if self.get_field_type(struct, var_rvalue.path[i].var_name.lexeme).type_name.lexeme == None:
                    self.error(f'{var_rvalue.path[i].var_name.lexeme} not a valid field in struct {var_rvalue.path[0].var_name.lexeme}', var_rvalue.path[i].var_name)
                self.curr_type = self.get_field_type(struct, var_rvalue.path[i].var_name.lexeme)
                if self.curr_type.type_name.lexeme in self.structs:
                    struct = self.structs[self.curr_type.type_name.lexeme]
        else:
            self.error(f'Variable {var_rvalue.path[0].var_name.lexeme} not declared', var_rvalue.path[0].var_name)
