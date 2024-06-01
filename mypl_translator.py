''' Translator from myPL -> Rust

Name: Connor Jones
Term: Spring 2024
Class: CPSC 326

'''

from mypl_token import *
from mypl_ast import *
import os.path
import subprocess

class Translator (Visitor):
    
    def __init__(self):
        ''' Begins translation of the AST into Rust '''
        self.file = open('exec.rs', 'w')
        self.indent = 0
        self.structs = {}
    #Helper Functions
    
    def output(self, msg):
        self.file.write(msg)
    
    def output_indent(self):
        self.output('  ' * self.indent)
        
    def run_file(self):
        command = "rustc exec.rs -o exec"
        
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during compilation: {e}")
            exit(1)
            
        try:
            subprocess.run("./exec", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during execution: {e}")
            exit(1)
        
        try:
            os.remove("exec")
        except OSError as e:
            print(f"Error deleting executable: {e}")
        
        
    #Visitor Functions
    
    def visit_program(self, program):
        self.output('#[allow(unused_imports)]\n')
        self.output('use std::io;\n')
        self.output('#[allow(unused_imports)]\n')
        self.output('use std::ptr::null;\n\n')
        
        for struct in program.struct_defs:
            struct_name = struct.struct_name.lexeme
            self.structs[struct_name] = struct
            self.output('#[allow(warnings)]\n')
            struct.accept(self)
            self.output('\n')
        for fun in program.fun_defs:
            self.output('#[allow(warnings)]\n')
            fun.accept(self)
            self.output('\n')

    def visit_struct_def(self, struct_def):
        self.output('struct ' + struct_def.struct_name.lexeme + ' {\n')
        self.indent +=1
        for field in struct_def.fields:
            self.output_indent()
            #var_def here
            self.output('r#' + field.var_name.lexeme + ': Option<')
            if field.data_type.type_name.lexeme in self.structs:
                self.output('Box<')
                field.data_type.accept(self)
                self.output('>')
            else:
                field.data_type.accept(self)
            self.output('>,\n')
        self.indent -= 1
        self.output('}\n')

    def visit_fun_def(self, fun_def):
        self.output('fn ' + fun_def.fun_name.lexeme + '(')
        for param in fun_def.params:
            self.output(f'{param.var_name.lexeme}: ')
            param.data_type.accept(self)
            if len(fun_def.params) > 1 and not param == fun_def.params[-1]:
                self.output(', ')
        self.output(') ')
        if not fun_def.return_type.type_name.lexeme == 'void':
            self.output('-> ')
            fun_def.return_type.accept(self)
            self.output(' {\n')
        else:
            self.output('{\n')
        self.indent += 1
        self.output_indent()
        self.output('let mut input = String::new();\n')
        for stmt in fun_def.stmts:
            stmt.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output('}\n')

    def visit_return_stmt(self, return_stmt):
        self.output_indent()
        self.output('return ')
        return_stmt.expr.accept(self)
        
    def visit_var_decl(self, var_decl):
        self.output_indent()
        self.output(f'let mut {var_decl.var_def.var_name.lexeme}: ')
        var_decl.var_def.data_type.accept(self)
        if not var_decl.expr == None:
            self.output(' = ')
            var_decl.expr.accept(self)
        self.output(';\n')

    def visit_assign_stmt(self, assign_stmt):
        self.output_indent()
        if len(assign_stmt.lvalue) == 1:
            var = assign_stmt.lvalue[0]
            if not var.array_expr == None:
                self.output(f'{var.var_name.lexeme}[')
                var.array_expr.accept(self)
                self.output(' as i32] ')
            else:
                self.output(f'{var.var_name.lexeme} ')
            self.output('= ')
            assign_stmt.expr.accept(self)
        else:
            self.output_indent()
            for i in range(len(assign_stmt.lvalue)):
                if not i == 0:
                    self.output('.')
                self.output(assign_stmt.lvalue[i].var_name.lexeme)
                if not assign_stmt.lvalue[i].array_expr == None:
                    self.output('[')
                    assign_stmt.lvalue[i].array_expr.accept(self)
                    self.output(']')
            self.output(' = ')
            if isinstance(assign_stmt.expr.first, SimpleTerm):
                if isinstance(assign_stmt.expr.first.rvalue, NewRValue):
                    self.output('Some(Box::new(')
                    assign_stmt.expr.accept(self)
                    self.output('))')
                else:
                    assign_stmt.expr.accept(self)
            else:
                assign_stmt.expr.accept(self)

    def visit_while_stmt(self, while_stmt):
        self.output_indent()
        self.output('while(')
        while_stmt.condition.accept(self)
        self.output(') {\n')
        self.indent += 1
        for stmt in while_stmt.stmts:
            stmt.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output_indent()
        self.output('}\n')

    def visit_for_stmt(self, for_stmt):
        for_stmt.var_decl.accept(self)
        self.output_indent()
        self.output('while(')
        for_stmt.condition.accept(self)
        self.output(') {\n')
        self.indent += 1
        for stmt in for_stmt.stmts:
            stmt.accept(self)
            self.output(';\n')
        for_stmt.assign_stmt.accept(self)
        self.output(';\n')
        self.indent -= 1
        self.output_indent()
        self.output('}\n')

    def visit_if_stmt(self, if_stmt):
        self.output_indent()
        self.output('if (')
        if_stmt.if_part.condition.accept(self)
        self.output(') {\n')
        self.indent += 1
        for stmt in if_stmt.if_part.stmts:
            stmt.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output_indent()
        self.output('}\n')
        for elseif in if_stmt.else_ifs:
            self.output_indent()
            self.output('else if (')
            elseif.condition.accept(self)
            self.output(') {\n')
            self.indent += 1
            for stmt in elseif.stmts:
                stmt.accept(self)
                self.output(';\n')
            self.indent -= 1
            self.output_indent()
            self.output('}\n')
        if len(if_stmt.else_stmts) > 0:
            else_stmt = if_stmt.else_stmts[0]
            self.output_indent()
            self.output('else {\n')
            self.indent += 1
            for stmt in else_stmt.stmts:
                stmt.accept(self)
                self.output(';\n')
            self.indent -= 1
            self.output_indent()
            self.output('}\n')
    
    def visit_call_expr(self, call_expr):
        self.output_indent()
        fun_name = call_expr.fun_name.lexeme
        if fun_name == 'print':
            self.output('let result = ')
            for arg in call_expr.args:
                arg.accept(self)
            if isinstance(call_expr.args[0].first, SimpleTerm):
                if isinstance(call_expr.args[0].first.rvalue, CallExpr):
                    pass
                else:
                    self.output(';\n')
            else:
                self.output(';\n')
            self.output(';\n')
            self.output_indent()
            self.output('print!("{}", result)')
        elif fun_name == 'input':
            self.output('io::stdin().read_line(&mut input).expect("Failed to read input").to_string()')
        elif fun_name == 'itos':
            self.output('Some(')
            for arg in call_expr.args:
                arg.accept(self)
            self.output(').expect("Failed to convert int").to_string()')
        elif fun_name == 'itod':
            self.output('Some(')
            for arg in call_expr.args:
                arg.accept(self)
            self.output(').expect("Failed to convert int") as f64')
        elif fun_name == 'dtos':
            self.output('Some(')
            for arg in call_expr.args:
                arg.accept(self)
            self.output(').expect("Failed to convert float").to_string()')
        elif fun_name == 'dtoi':
            self.output('Some(')
            for arg in call_expr.args:
                arg.accept(self)
            self.output(').expect("Failed to convert double") as i32')
        elif fun_name == 'stoi':
            self.output('Some(')
            for arg in call_expr.args:
                arg.accept(self)
            self.output(').expect("Failed to convert int").parse().expect("Failed to make int")')
        elif fun_name == 'stod':
            self.output('Some(')
            for arg in call_expr.args:
                arg.accept(self)
            self.output(').expect("Failed to convert int").parse().expect("Failed to make double")')
        elif fun_name == 'length':
            if isinstance(call_expr.args[0].first, SimpleTerm):
                if isinstance(call_expr.args[0].first.rvalue, SimpleTerm):
                    self.output('Some(')
                    call_expr.args[0].accept(self)
                    self.output(').expect("Failed to get a length").chars().count()')
                else:
                    call_expr.args[0].accept(self)
                    self.output('.len() as i32')
            else:
                call_expr.args[0].accept(self)
                self.output('.len() as i32')
        elif fun_name == 'get':
            self.output('Some(')
            call_expr.args[1].accept(self)
            self.output(').expect("Failed to read string").chars().nth(')
            call_expr.args[0].accept(self)
            self.output(').expect("Failed to convert char").to_string()')
        else:
            self.output(f'{fun_name}(')
            for arg in call_expr.args:
                arg.accept(self)
                self.output(', ')
            self.output(')')
        
    def visit_expr(self, expr):
        if expr.not_op:
            self.output('!(')
            expr.first.accept(self)
            if not expr.op == None:
                self.output(f' {expr.op.lexeme} ')
                expr.rest.accept(self)
            self.output(')')
        else:
            expr.first.accept(self)
            if not expr.op == None:
                self.output(f' {expr.op.lexeme} ')
                expr.rest.accept(self)
    
    def visit_data_type(self, data_type):
        type_name = data_type.type_name.lexeme
        if data_type.is_array:
            if type_name == 'int':
                self.output('Vec<i32>')
            elif type_name == 'double':
                self.output('Vec<f64>')
            elif type_name == 'string':
                self.output('Vec<String>')
            elif type_name == 'bool':
                self.output('Vec<bool>')
            else:
                self.output(f'Vec<{type_name}>')
        else:
            if type_name == 'int':
                self.output('i32')
            elif type_name == 'double':
                self.output('f64')
            elif type_name == 'string':
                self.output('String')
            elif type_name == 'bool':
                self.output('bool')
            elif type_name == 'void':
                pass
            else:
                self.output(type_name)

    def visit_var_def(self, var_def):
        #Nothing to do here
        pass

    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)

    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)

    def visit_simple_rvalue(self, simple_rvalue):
        if simple_rvalue.value.token_type == TokenType.STRING_VAL:
            self.output(f'String::from("{simple_rvalue.value.lexeme}")')
        else:
            self.output(simple_rvalue.value.lexeme)
            
    def visit_new_rvalue(self, new_rvalue):
        if not new_rvalue.array_expr == None:
            self.output('Vec::with_capacity(')
            new_rvalue.array_expr.accept(self)
            self.output(')')
        else:
            self.output(new_rvalue.type_name.lexeme + ' { ')
            #now to take into account the struct
            struct = self.structs[new_rvalue.type_name.lexeme]
            for i in range(len(new_rvalue.struct_params)):
                if isinstance(new_rvalue.struct_params[i].first, SimpleTerm):
                    if isinstance(new_rvalue.struct_params[i].first.rvalue, SimpleRValue):
                        if new_rvalue.struct_params[i].first.rvalue.value.lexeme == 'null':
                            self.output(f'{struct.fields[i].var_name.lexeme}: None,')
                        else:
                            self.output(struct.fields[i].var_name.lexeme + ': Some(')
                            new_rvalue.struct_params[i].accept(self)
                            self.output('), ')
                    elif isinstance(new_rvalue.struct_params[i].first.rvalue, NewRValue):
                        self.output(f'{struct.fields[i].var_name.lexeme}: Some(Box::new(')
                        new_rvalue.struct_params[i].accept(self)
                        self.output(')), ')
                else:
                    self.output(struct.fields[i].var_name.lexeme + ': Some(')
                    new_rvalue.struct_params[i].accept(self)
                    self.output('), ')
            self.output('}')
            
    def visit_var_rvalue(self, var_rvalue):
        if len(var_rvalue.path) == 1:
            if var_rvalue.path[0].array_expr == None:
                self.output(var_rvalue.path[0].var_name.lexeme)
            else:
                self.output('[')
                var_rvalue.path[0].array_expr.accept(self)
                self.output(']')
        else:
            for i in range(len(var_rvalue.path)):
                if not i == 0:
                    self.output('.')
                self.output(var_rvalue.path[i].var_name.lexeme)
                if not var_rvalue.path[i].array_expr == None:
                    self.output('[')
                    var_rvalue.path[i].array_expr.accept(self)
                    self.output(']')
                if i >= 1 and i+1 < len(var_rvalue.path):
                    self.output('.unwrap()')
            self.output('.unwrap_or_default()')
                
            