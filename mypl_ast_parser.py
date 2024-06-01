"""MyPL AST parser implementation.

NAME: <your-name-here>
DATE: Spring 2024
CLASS: CPSC 326
"""

from mypl_error import *
from mypl_token import *
from mypl_lexer import *
from mypl_ast import *


class ASTParser:

    def __init__(self, lexer):
        """Create a MyPL syntax checker (parser). 
        
        Args:
            lexer -- The lexer to use in the parser.

        """
        self.lexer = lexer
        self.curr_token = None

        
    def parse(self):
        """Start the parser, returning a Program AST node."""
        program_node = Program([], [])
        self.advance()
        while not self.match(TokenType.EOS):
            if self.match(TokenType.STRUCT):
                self.struct_def(program_node)
            else:
                self.fun_def(program_node)
        self.eat(TokenType.EOS, 'expecting EOF')
        
        
        return program_node

        
    #----------------------------------------------------------------------
    # Helper functions
    #----------------------------------------------------------------------

    def error(self, message):
        """Raises a formatted parser error.

        Args:
            message -- The basic message (expectation)

        """
        lexeme = self.curr_token.lexeme
        line = self.curr_token.line
        column = self.curr_token.column
        err_msg = f'{message} found "{lexeme}" at line {line}, column {column}'
        raise ParserError(err_msg)


    def advance(self):
        """Moves to the next token of the lexer."""
        self.curr_token = self.lexer.next_token()
        # skip comments
        while self.match(TokenType.COMMENT):
            self.curr_token = self.lexer.next_token()

            
    def match(self, token_type):
        """True if the current token type matches the given one.

        Args:
            token_type -- The token type to match on.

        """
        return self.curr_token.token_type == token_type

    
    def match_any(self, token_types):
        """True if current token type matches on of the given ones.

        Args:
            token_types -- Collection of token types to check against.

        """
        for token_type in token_types:
            if self.match(token_type):
                return True
        return False

    
    def eat(self, token_type, message):
        """Advances to next token if current tokey type matches given one,
        otherwise produces and error with the given message.

        Args: 
            token_type -- The totken type to match on.
            message -- Error message if types don't match.

        """
        if not self.match(token_type):
            self.error(message)
        self.advance()

        
    def is_bin_op(self):
        """Returns true if the current token is a binary operator."""
        ts = [TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE,
              TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS,
              TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ,
              TokenType.NOT_EQUAL]
        return self.match_any(ts)


    #----------------------------------------------------------------------
    # Recursive descent functions
    #----------------------------------------------------------------------


    # TODO: Finish the recursive descent functions below. Note that
    # you should copy in your functions from HW-2 and then instrument
    # them to build the corresponding AST objects.
    def struct_def(self, program):
        """<struct_def> ::= struct ID LBRACE <fields> RBRACE"""
        self.advance()
        struct_node = StructDef(None, [])
        struct_node.struct_name = self.curr_token
        self.eat(TokenType.ID, "ID Expected after struct declaration")
        self.eat(TokenType.LBRACE, "Missing Left-Brace")
        self.fields(struct_node)
        program.struct_defs.append(struct_node)
        self.eat(TokenType.RBRACE, "Right-Brace expected to match Left-Brace")
        
    def fields(self, struct):
        """<fields> ::= ( <data_type> ID SEMICOLON )*"""
        while not self.match(TokenType.RBRACE):
            var_def = VarDef(DataType(False, Token), Token)
            self.data_type_def(var_def.data_type)
            var_def.var_name = self.curr_token
            self.eat(TokenType.ID, "ID expected after data type declaration")
            self.eat(TokenType.SEMICOLON, "Semicolon not found after statement")
            struct.fields.append(var_def)
            
    def fun_def(self, program):
        """<fun_def> ::= ( <data_type> | VOID_TYPE ) ID LPAREN <params> RPAREN 
                            LBRACE ( <stmt> )* RBRACE"""   
        fun_node = FunDef(DataType, Token, [], [])
        if not self.match(TokenType.VOID_TYPE):
            data_type = DataType(False, Token)
            self.data_type_def(data_type)
            fun_node.return_type = data_type
        elif self.match(TokenType.VOID_TYPE):
            data_type = DataType(False, self.curr_token)
            fun_node.return_type = data_type
            self.advance()  
        fun_node.fun_name = self.curr_token
        self.eat(TokenType.ID, "ID expected after data type declaration")
        self.eat(TokenType.LPAREN, "Left-Paren expected")
        
        self.params(fun_node)
        
        self.eat(TokenType.RPAREN, "Right-Paren missing to match Left-Paren")
        self.eat(TokenType.LBRACE, "Missing left brace")
        
        while not self.match(TokenType.RBRACE):
            self.stmt_def(fun_node)
        
        self.eat(TokenType.RBRACE, "Missing right brace")
        program.fun_defs.append(fun_node)

    def params(self, fun):
        """<params> ::= <data_type> ID (COMMA <data_type> ID)* | e"""
        if self.match(TokenType.RPAREN):
            return
        var = VarDef(DataType, Token)
        data_type_node = DataType(False, Token)
        self.data_type_def(data_type_node)
        var.data_type = data_type_node
        var.var_name = self.curr_token
        self.eat(TokenType.ID, "ID expected after data type declaration")
        fun.params.append(var)
        while self.match(TokenType.COMMA):
            self.eat(TokenType.COMMA, "comma expected to separate paramters")
            var = VarDef(DataType, Token)
            data_type_node = DataType(False, Token)
            self.data_type_def(data_type_node)
            var.data_type = data_type_node
            var.var_name = self.curr_token
            self.eat(TokenType.ID, "Expecting ID")
            fun.params.append(var)

    def data_type_def(self, data_type):
        """<data_type> ::=  <base_type> | ID | ARRAY ( <base_type> | ID )"""
        dt = DataType(False, Token)
        if self.match(TokenType.ID):
            dt.type_name = self.curr_token
            self.advance()
        elif self.match(TokenType.ARRAY):
            dt.is_array = True
            self.advance()
            if not self.match(TokenType.ID):
                dt.type_name = self.curr_token
                self.base_type_def()
            else:
                dt.type_name = self.curr_token
                self.advance()
        else:
            dt.type_name = self.curr_token
            self.base_type_def()
            
        data_type.is_array = dt.is_array
        data_type.type_name = dt.type_name
   
    def base_type_def(self):
        """<base_type> ::= INT_TYPE | DOUBLE_TYPE | BOOL_TYPE | STRING_TYPE"""
        self.advance()

    def stmt_def(self, def_node):
        """<stmt> ::= <while_stmt> | <if_stmt> | <for_stmt> | <return_stmt> SEMICOLON
                        | <vdecl_stmt> SEMICOLON | <assign_stmt> SEMICOLON
                        | <call_expr> SEMICOLON """
        stmt_node = Stmt()
        if self.match(TokenType.WHILE):
            stmt_node = WhileStmt(Expr, [])
            self.while_stmt_def(stmt_node)
        elif self.match(TokenType.IF) or self.match(TokenType.ELSE):
            if self.match(TokenType.IF):
                self.if_flag = True
            elif self.match(TokenType.ELSE) and not hasattr(self, 'is_flag'):
                self.error("Invalid syntax, if needed before the use of else")
            stmt_node = IfStmt(BasicIf, [], [])
            self.if_stmt_def(stmt_node)
        elif self.match(TokenType.FOR):
            stmt_node = ForStmt(VarDecl, Expr, AssignStmt, [])
            self.for_stmt_def(stmt_node)
        elif self.match(TokenType.RETURN):
            stmt_node = ReturnStmt(Expr)
            self.return_stmt_def(stmt_node)
            self.eat(TokenType.SEMICOLON, "Semicolon expected")
        else:
            if self.match(TokenType.ID):
                tmp = self.curr_token
                self.advance()
                if self.match(TokenType.LPAREN):
                    stmt_node = CallExpr(Token, [])
                    stmt_node.fun_name = tmp
                    self.call_expr_def(stmt_node)
                    self.eat(TokenType.SEMICOLON, "Semicolon expected")
                elif self.match(TokenType.ID):
                    stmt_node = VarDecl(VarDef(DataType(False, tmp), None), None)
                    stmt_node.var_def.data_type.is_array = False
                    stmt_node.var_def.data_type.type_name = tmp
                    self.vdecl_stmt_def(stmt_node)
                    self.eat(TokenType.SEMICOLON, "Semicolon expected")
                elif self.match(TokenType.LBRACKET) or self.match(TokenType.DOT) or self.match(TokenType.ASSIGN):
                    stmt_node = AssignStmt([], None)
                    var_ref = VarRef(Token, None)
                    var_ref.var_name = tmp
                    stmt_node.lvalue.append(var_ref)
                    self.assign_stmt_def(stmt_node)
                    self.eat(TokenType.SEMICOLON, "Semicolon expected")
            else:
                stmt_node = VarDecl(VarDef(DataType, Token), None)
                data_type = DataType(False, Token)
                self.data_type_def(data_type)
                stmt_node.var_def.data_type = data_type
                self.vdecl_stmt_def(stmt_node)
                self.eat(TokenType.SEMICOLON, "Semicolon expected")
        
        def_node.stmts.append(stmt_node)

    def vdecl_stmt_def(self, vdecl):
        """<vdecl_stmt> ::= <data_type> ID (ASSIGN <expr> | e) """
        vdecl.var_def.var_name = Token
        vdecl.var_def.var_name = self.curr_token
        self.eat(TokenType.ID, "ID expected after data type declaration")
        if self.match(TokenType.ASSIGN):
            self.advance()
            vdecl.expr = Expr(False, ExprTerm, Token, '')
            expr_node = Expr(False, ExprTerm, None, None)
            self.expr_def(expr_node)
            vdecl.expr = expr_node
        
    def assign_stmt_def(self, assign_stmt):
        """<assign_stmt> ::= <lvalue> ASSIGN <expr> """
        if self.match(TokenType.ASSIGN):
            self.advance()
        else:
            self.lvalue_def(assign_stmt)
            self.eat(TokenType.ASSIGN, "Expecting assignment symbol")
        expr_node = Expr(False, ExprTerm, None, None)
        self.expr_def(expr_node)
        assign_stmt.expr = expr_node
  
    def lvalue_def(self, assign_stmt):
        """<lvalue> ::= ID (LBRACKET <expr> RBRACKET | e)(DOT ID (LBRACKET <expr> RBRACKET | e))* """
        var_ref = VarRef(Token, None)
        if self.match(TokenType.ID):
            var_ref.var_name = self.curr_token
            self.advance()
        else:
            if not assign_stmt.lvalue:
                pass
            else:
                var_ref = assign_stmt.lvalue[0]
                del assign_stmt.lvalue[0]
        if self.match(TokenType.LBRACKET):
            self.advance()
            expr_node = Expr(False, ExprTerm, Token, None)
            self.expr_def(expr_node)
            var_ref.array_expr = expr_node
            self.eat(TokenType.RBRACKET, "Right bracket expected")
        assign_stmt.lvalue.append(var_ref)
        if self.match(TokenType.DOT):
            while self.match(TokenType.DOT):
                var_ref = VarRef(Token, None)
                self.advance()
                var_ref.var_name = self.curr_token
                self.eat(TokenType.ID, "ID expected")
                if self.match(TokenType.LBRACKET):
                    self.advance()
                    expr_node = Expr(False, ExprTerm, Token, None)
                    self.expr_def(expr_node)
                    var_ref.array_expr = Expr(False, ExprTerm, Token, None)
                    var_ref.array_expr = expr_node
                    self.eat(TokenType.RBRACKET, "Right bracket expected")
                assign_stmt.lvalue.append(var_ref)

    def if_stmt_def(self, if_stmt):
        """<if_stmt> ::= IF LPAREN <expr> RPAREN LBRACE (<stmt>)* RBRACE <if_stmt_t>"""
        if self.match(TokenType.IF):
            self.advance()
            self.eat(TokenType.LPAREN, "Left paren expected")
            basic_if = BasicIf(Expr, [])
            expr_node = Expr(False, ExprTerm, Token, Expr)
            self.expr_def(expr_node)
            basic_if.condition = expr_node
            self.eat(TokenType.RPAREN, "Missing right paren")
            self.eat(TokenType.LBRACE, "Missing left brace")
            while True:
                if self.match(TokenType.RBRACE):
                    break
                else:
                    self.stmt_def(basic_if)
            self.advance()
            if_stmt.if_part = basic_if
            self.if_stmt_t_def(if_stmt)
        else:
            self.error("Invalid syntax, if needed before the use of else")
    
    def if_stmt_t_def(self, if_stmt):
        """<if_stmt_t> ::= ELSEIF LPAREN <expr> RPAREN LBRACE (<stmt>)* RBRACE <if_stmt_t>
                            | ELSE LBRACE (<stmt>)* RBRACE | e """
        if self.match(TokenType.ELSEIF):
            self.advance()
            self.eat(TokenType.LPAREN, "Missing left paren")
            basic_if = BasicIf(Expr, [])
            expr_node = Expr(False, ExprTerm, Token, Expr)
            self.expr_def(expr_node)
            basic_if.condition = expr_node
            self.eat(TokenType.RPAREN, "Missing right paren")
            self.eat(TokenType.LBRACE, "Missing left brace")
            if self.match(TokenType.RBRACE):
                if_stmt.else_ifs.append(basic_if)
            
            while True:
                if self.match(TokenType.RBRACE):
                    break
                else:
                    self.stmt_def(basic_if)
                    if_stmt.else_ifs.append(basic_if)
            
            self.advance()
            self.if_stmt_t_def(if_stmt)
        elif self.match(TokenType.ELSE):
            self.advance()
            self.eat(TokenType.LBRACE, "Missing left brace")
            basic_if = BasicIf(None, []) #actually using none, since conditions on else is impossible
            while True:
                if self.match(TokenType.RBRACE):
                    break
                else:
                    self.stmt_def(basic_if)
                    if_stmt.else_stmts.append(basic_if)
            self.advance()
            
    
    def while_stmt_def(self, while_stmt):
        """<while_stmt> ::= WHILE LPAREN <expr> RPAREN LBRACE (<stmt>)* RBRACE """
        self.eat(TokenType.WHILE, "Expecting while reserved word")
        self.eat(TokenType.LPAREN, "Missing left paren")
        expr_node = Expr(False, ExprTerm, Token, Expr)
        self.expr_def(expr_node)
        while_stmt.condition = expr_node
        self.eat(TokenType.RPAREN, "Missing right paren")
        self.eat(TokenType.LBRACE, "Missing left brace")
        while True:
            if self.match(TokenType.RBRACE):
                break
            else:
                self.stmt_def(while_stmt)
        self.advance()
        
    def for_stmt_def(self, for_stmt):
        """<for_stmt> ::= FOR LPAREN <vdecl_stmt> SEMICOLON <expr> SEMICOLON
                            <assign_stmt> RPAREN LBRACE (<stmt>)* RBRACE """
        self.eat(TokenType.FOR, "For key word expected")
        self.eat(TokenType.LPAREN, "Left paren missing")
        var_decl = VarDecl(VarDef(DataType, Token), None)
        data_type = DataType(False, Token)
        self.data_type_def(data_type)
        var_decl.var_def.data_type = data_type
        self.vdecl_stmt_def(var_decl)
        for_stmt.var_decl = var_decl
        self.eat(TokenType.SEMICOLON, "Missing ';'")
        expr_node = Expr(False, ExprTerm, Token, Expr)
        self.expr_def(expr_node)
        for_stmt.condition = expr_node
        self.eat(TokenType.SEMICOLON, "Missing ';'")
        assign_stmt = AssignStmt([], Expr)
        self.assign_stmt_def(assign_stmt)
        for_stmt.assign_stmt = assign_stmt
        self.eat(TokenType.RPAREN, "Missing right paren")
        self.eat(TokenType.LBRACE, "Missing left brace")
        while True:
            if self.match(TokenType.RBRACE):
                break
            else:
                self.stmt_def(for_stmt)
        self.advance()
    
    def call_expr_def(self, call_expr):
        """<call_expr> ::= ID LPAREN (<expr> (COMMA <expr>)* | e) RPAREN """
        
        self.eat(TokenType.LPAREN, "Missing left paren")
        if not self.match(TokenType.RPAREN):
            expr_node = Expr(False, ExprTerm, None, None)
            self.expr_def(expr_node)
            call_expr.args.append(expr_node)
            while True:
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
                expr_node = Expr(False, ExprTerm, None, None)
                self.expr_def(expr_node)
                call_expr.args.append(expr_node)
        self.eat(TokenType.RPAREN, "Missing right paren")
        
    def return_stmt_def(self, return_stmt):
        """<return_stmt> ::= RETURN <expr> """
        self.eat(TokenType.RETURN, "Expecting return reserved word")
        expr_node = Expr(False, ExprTerm, Token, Expr)
        self.expr_def(expr_node)
        return_stmt.expr = expr_node
    
    def expr_def(self, expr):
        """<expr> ::= (<rvalue> | NOT <expr> | LPAREN <expr> RPAREN)(<bin_op><expr> | e) """
        if self.match(TokenType.NOT):
            expr.not_op = True
            self.advance()
            expr.op = None
            expr.rest = None
            self.expr_def(expr)
            expr.not_op = True
        elif self.match(TokenType.LPAREN):
            self.advance()
            expr_term = ComplexTerm(Expr)
            expr_node = Expr(False, ExprTerm, None, None)
            self.expr_def(expr_node)
            expr_term.expr = expr_node
            expr.first = expr_term
            self.eat(TokenType.RPAREN, "Missing right paren")
        else:
            expr_term = SimpleTerm(RValue)
            expr.op = None
            self.rvalue_def(expr_term)
            expr.first = expr_term
            expr.rest = None
        
        if self.is_bin_op():
            expr.op = self.curr_token
            self.bin_op_def()
            expr_node = Expr(False, ExprTerm, None, None)
            self.expr_def(expr_node)
            expr.rest = expr_node
    
    def bin_op_def(self):
        """<bin_op> ::= PLUS | MINUS | TIMES | DIVIDE | AND | OR | EQUAL | LESS
                        | GREATER | LESS_EQ | GREATER_EQ | NOT_EQUAL """
        if self.is_bin_op():
            self.advance()
    
    def rvalue_def(self, simple_term):
        """<rvalue> ::= <base_rvalue> | NULL_VAL | <new_rvalue> | <var_rvalue>
                        | <call_expr> """
        if self.match_any([TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL, TokenType.STRING_VAL]):
            rval = SimpleRValue(Token)
            rval.value = self.curr_token
            self.base_rvalue_def()
        elif self.match(TokenType.NULL_VAL):
            rval = SimpleRValue(Token)
            rval.value = self.curr_token
            self.advance()
        elif self.match(TokenType.NEW):
            rval = NewRValue(Token, None, None)
            self.new_rvalue_def(rval)
        elif self.match(TokenType.ID):
            tmp = self.curr_token
            self.advance()
            if self.match(TokenType.LPAREN):
                rval = CallExpr(Token, [])
                rval.fun_name = tmp
                self.call_expr_def(rval)
            else:
                rval = VarRValue([])
                var_ref = VarRef(Token, None)
                var_ref.var_name = tmp
                self.var_rvalue_def(rval, var_ref)
        else:
            self.error("Invalid Syntax")
        
        simple_term.rvalue = rval
 
    def new_rvalue_def(self, new_rval):
        """<new_rvalue> ::= NEW ID LPAREN (<expr> (COMMA <expr>)* | e) RPAREN
                            | NEW (ID | <base_type>) LBRACKET <expr> RBRACKET """
        self.eat(TokenType.NEW, "Missing new reserved word")
        if self.match(TokenType.ID):
            new_rval.type_name = self.curr_token
            self.advance()
            if self.match(TokenType.LPAREN):
                new_rval.struct_params = []
                self.advance()
                if not self.match(TokenType.RPAREN):
                    expr_node = Expr(False, ExprTerm, Token, Expr)
                    self.expr_def(expr_node)
                    new_rval.struct_params.append(expr_node)
                    while True:
                        if self.match(TokenType.RPAREN):
                            break
                        self.eat(TokenType.COMMA, "Missing comma separating parameters")
                        expr_node = Expr(False, ExprTerm, Token, Expr)
                        self.expr_def(expr_node)
                        new_rval.struct_params.append(expr_node)
                
                self.advance()
            elif self.match(TokenType.LBRACKET):
                self.advance()
                expr_node = Expr(False, ExprTerm, Token, Expr)
                self.expr_def(expr_node)
                new_rval.array_expr = expr_node
                self.eat(TokenType.RBRACKET, "Missing right bracket")
        else:
            new_rval.type_name = self.curr_token
            self.base_type_def()
            self.eat(TokenType.LBRACKET, "Missing left bracket")
            expr_node = Expr(False, ExprTerm, Token, Expr)
            self.expr_def(expr_node)
            new_rval.array_expr = expr_node
            self.eat(TokenType.RBRACKET, "Missing right bracket")
                            
    def base_rvalue_def(self):
        """<base_rvalue> ::= INT_VAL | DOUBLE_VAL | BOOL_VAL | STRING_VAL """
        if self.match_any([TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL, TokenType.STRING_VAL]):
            self.advance()
        
    def var_rvalue_def(self, var_rval, start_var_ref):
        """<var_rvalue> ::= ID(LBRACKET <expr> RBRACKET | e)(DOT ID (LBRACKET <expr> RBRACKET | e))* """
        if self.match(TokenType.LBRACKET):
            self.advance()
            expr_node = Expr(False, ExprTerm, None, None)
            self.expr_def(expr_node)
            start_var_ref.array_expr = expr_node
            self.eat(TokenType.RBRACKET, "Missing right bracket")
        else:
            start_var_ref.array_expr = None
        var_rval.path.append(start_var_ref)
        while True:
            if not self.match(TokenType.DOT):
                break
            self.advance()
            var_ref = VarRef(Token, None)
            var_ref.var_name = self.curr_token
            self.eat(TokenType.ID, "ID expected after '.'")
            if self.match(TokenType.LBRACKET):
                self.advance()
                expr_node = Expr(False, ExprTerm, None, None)
                self.expr_def(expr_node)
                var_ref.array_expr = Expr
                var_ref.array_expr = expr_node
                self.eat(TokenType.RBRACKET, "Missing right bracket")
                var_rval.path.append(var_ref)
            else:
                var_rval.path.append(var_ref) 