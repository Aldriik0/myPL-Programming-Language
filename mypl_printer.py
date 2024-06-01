"""Print Visitor for pretty printing a MyPL program.

NAME: <your name here>
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from mypl_token import Token, TokenType
from mypl_ast import *


class PrintVisitor(Visitor):
    """Visitor implementation to pretty print MyPL program."""

    def __init__(self):
        self.indent = 0

    # Helper Functions
        
    def output(self, msg):
        """Prints message without ending newline.

        Args:
           msg -- The string to print.

        """
        print(msg, end='')

        
    def output_indent(self):
        """Prints an initial indent string."""
        self.output('  ' * self.indent)


    def output_semicolon(self, stmt):
        """Prints a semicolon if the type of statment should end in a
        semicolon.
        
        Args:
            stmt -- The statement to print a semicolon after.

        """
        if type(stmt) in [VarDecl, AssignStmt, ReturnStmt, CallExpr]:
            self.output(';')

    # Visitor Functions
    
    def visit_program(self, program):
        for struct in program.struct_defs:
            struct.accept(self)
            self.output('\n')
        for fun in program.fun_defs:
            fun.accept(self)
            self.output('\n')            

            
    def visit_struct_def(self, struct_def):
        self.output('struct ' + struct_def.struct_name.lexeme + ' {\n')
        self.indent += 1
        for var_def in struct_def.fields:
            self.output_indent()
            var_def.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output('}\n')


    def visit_fun_def(self, fun_def):
        fun_def.return_type.accept(self)
        self.output(' ' + fun_def.fun_name.lexeme + '(')
        for i in range(len(fun_def.params)):
            fun_def.params[i].accept(self)
            if i < len(fun_def.params) - 1:
                self.output(', ')
        self.output(') {\n')
        self.indent += 1
        for stmt in fun_def.stmts:
            self.output_indent()
            stmt.accept(self)
            self.output_semicolon(stmt)
            self.output('\n')
        self.indent -= 1
        self.output('}\n')


    # TODO: Finish the rest of the visitor functions below

    def visit_data_type(self, data_type):
        if data_type.is_array:
            self.output('array ' + data_type.type_name.lexeme + ' ')
        else:
            self.output(data_type.type_name.lexeme + ' ')
        
    def visit_var_def(self, var_def):
        data_type = var_def.data_type
        data_type.accept(self)
        self.output(var_def.var_name.lexeme)
        
    def visit_expr(self, expr):
        if expr.not_op:
            self.output('not ')
        expr.first.accept(self)
        if expr.op != None:
            self.output( ' ' + expr.op.lexeme)
        if expr.rest != None:
            self.output(' ')
            expr.rest.accept(self)
            
        
        
    def visit_call_expr(self, call_expr):
        self.output(call_expr.fun_name.lexeme + '(')
        i = 0
        for arg in call_expr.args:
            if i != 0:
                self.output(', ')
            arg.accept(self)
            i += 1
        self.output(')')
        
    def visit_complex_term(self, complex_term):
        complex_term.expr.first.accept(self)
        if complex_term.expr.op != None:
            self.output(' ' + complex_term.expr.op.lexeme + ' ')
        if complex_term.expr.rest != None:
            complex_term.expr.rest.accept(self)
        
    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)
        
    def visit_simple_rvalue(self, simple_rvalue):
        if simple_rvalue.value.token_type == TokenType.STRING_VAL:
            self.output('"' + simple_rvalue.value.lexeme + '"')
        else:
            self.output(simple_rvalue.value.lexeme)
        
    def visit_new_rvalue(self, new_rvalue):
        self.output('new ' + new_rvalue.type_name.lexeme)
        if new_rvalue.array_expr != None:
            self.output('[')
            new_rvalue.array_expr.accept(self)
            self.output(']')
        self.output('(')
        for i in range(len(new_rvalue.struct_params)):
            new_rvalue.struct_params[i].accept(self)
            if i < len(new_rvalue.struct_params) - 1:
                self.output(', ')
        self.output(')')
        
        
    def visit_var_rvalue(self, var_rvalue):
        for id in var_rvalue.path:
            if id != var_rvalue.path[0]:
                self.output('.')
            
            self.output(id.var_name.lexeme)
            
            if id.array_expr != None:
                self.output('[')
                id.array_expr.accept(self)
                self.output(']')
        
            
        
    def visit_return_stmt(self, return_stmt):
        self.output('return ')
        return_stmt.expr.accept(self)
        
    def visit_var_decl(self, var_decl):
        var_def = var_decl.var_def
        var_def.accept(self)
        if var_decl.expr != None:
            self.output(' = ')
            var_decl.expr.accept(self)
        
    def visit_assign_stmt(self, assign_stmt):
        for lvalue in assign_stmt.lvalue:
            if lvalue != assign_stmt.lvalue[0]:
                self.output('.')
            self.output(lvalue.var_name.lexeme)
            if lvalue.array_expr != None:
                self.output('[')
                lvalue.array_expr.accept(self)
                self.output(']')
            
        self.output(' = ')
        assign_stmt.expr.accept(self)
        
    def visit_while_stmt(self, while_stmt):
        self.output('while (')
        while_stmt.condition.accept(self)
        self.output(') {\n')
        for stmt in while_stmt.stmts:
            self.output_indent()
            self.output_indent()
            self.output_indent()
            stmt.accept(self)
            self.output_semicolon(stmt)
            self.output('\n')
        self.output_indent()
        self.output_indent()
        self.output_indent()
        self.output('}\n')
        
    def visit_for_stmt(self, for_stmt):
        self.output('for (')
        for_stmt.var_decl.accept(self)
        self.output('; ')
        for_stmt.condition.accept(self)
        self.output('; ')
        for_stmt.assign_stmt.accept(self)
        self.output(') {\n')
        for stmt in for_stmt.stmts:
            self.output_indent()
            self.output_indent()
            stmt.accept(self)
            self.output_semicolon(stmt)
            self.output('\n')
        self.output_indent()
        self.output('}\n')
        
        
    def visit_if_stmt(self, if_stmt):
        self.output('if (')
        if_stmt.if_part.condition.accept(self)
        self.output(') {\n')
        for stmt in if_stmt.if_part.stmts:
            self.output_indent()
            self.output_indent()
            self.output_indent()
            stmt.accept(self)
            self.output_semicolon(stmt)
            self.output('\n')
        self.output_indent()
        self.output('}\n')
        for i, elseif in enumerate(if_stmt.else_ifs[:-1]):
            self.output_indent()
            self.output('elseif (')
            elseif.condition.accept(self)
            self.output(') {\n')
            for stmt in elseif.stmts:
                self.output_indent()
                self.output_indent()
                stmt.accept(self)
                self.output_semicolon(stmt)
                self.output('\n')
                
            self.output_indent()
            self.output('}\n')
        
        if len(if_stmt.else_stmts) != 0:
            for else_stmt in if_stmt.else_stmts:
                self.output_indent()
                self.output('else {\n')
                for stmt in else_stmt.stmts:
                    self.output_indent()
                    self.output_indent()
                    stmt.accept(self)
                    self.output_semicolon(stmt)
                    self.output('\n')
                self.output_indent()
                self.output('}\n')
                
            
