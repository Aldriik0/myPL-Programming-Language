"""MyPL simple syntax checker (parser) implementation.

NAME: Connor Jones
DATE: Spring 2024
CLASS: CPSC 326
"""

from mypl_error import *
from mypl_token import *
from mypl_lexer import *


class SimpleParser:

    def __init__(self, lexer):
        """Create a MyPL syntax checker (parser). 
        
        Args:
            lexer -- The lexer to use in the parser.

        """
        self.lexer = lexer
        self.curr_token = None

        
    def parse(self):
        """Start the parser."""
        self.advance()
        while not self.match(TokenType.EOS):
            if self.match(TokenType.STRUCT):
                self.struct_def()
            else:
                self.fun_def()
        self.eat(TokenType.EOS, 'expecting EOF')

        
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
        """Returns true if the current token is a binary operation token."""
        ts = [TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE,
              TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS,
              TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ,
              TokenType.NOT_EQUAL]
        return self.match_any(ts)

    
    #----------------------------------------------------------------------
    # Recursive descent functions
    #----------------------------------------------------------------------
        
    def struct_def(self):
        """<struct_def> ::= struct ID LBRACE <fields> RBRACE"""
        self.advance()
        self.eat(TokenType.ID, "ID Expected after struct declaration")
        self.eat(TokenType.LBRACE, "Missing Left-Brace")
        self.fields()
        self.eat(TokenType.RBRACE, "Right-Brace expected to match Left-Brace")
        
    def fields(self):
        """<fields> ::= ( <data_type> ID SEMICOLON )*"""
        while not self.match(TokenType.RBRACE):
            self.data_type_def()
            self.eat(TokenType.ID, "ID expected after data type declaration")
            self.eat(TokenType.SEMICOLON, "Semicolon not found after statement")
            
    def fun_def(self):
        """<fun_def> ::= ( <data_type> | VOID_TYPE ) ID LPAREN <params> RPAREN 
                            LBRACE ( <stmt> )* RBRACE"""             
        if not self.match(TokenType.VOID_TYPE):
            self.data_type_def()
        elif self.match(TokenType.VOID_TYPE):
            self.advance()  
        self.eat(TokenType.ID, "ID expected after data type declaration")
        self.eat(TokenType.LPAREN, "Left-Paren expected")
        
        self.params()
        
        self.eat(TokenType.RPAREN, "Right-Paren missing to match Left-Paren")
        self.eat(TokenType.LBRACE, "Missing left brace")
        
        while not self.match(TokenType.RBRACE):
            self.stmt_def()
        
        self.eat(TokenType.RBRACE, "Missing right brace")


            

    def params(self):
        """<params> ::= <data_type> ID (COMMA <data_type> ID)* | e"""
        if self.match(TokenType.RPAREN):
            return
            
        self.data_type_def()
        self.eat(TokenType.ID, "ID expected after data type declaration")
        while self.match(TokenType.COMMA):
            self.eat(TokenType.COMMA, "comma expected to separate paramters")
            self.data_type_def()
            self.eat(TokenType.ID, "Expecting ID")
        
    
    def data_type_def(self):
        """<data_type> ::=  <base_type> | ID | ARRAY ( <base_type> | ID )"""
        if self.match(TokenType.ID):
            self.advance()
        elif self.match(TokenType.ARRAY):
            self.advance()
            if not self.match(TokenType.ID):
                self.base_type_def()
            else:
                self.advance()
        else:
            self.base_type_def()
            
        
    def base_type_def(self):
        """<base_type> ::= INT_TYPE | DOUBLE_TYPE | BOOL_TYPE | STRING_TYPE"""
        self.advance()

    def stmt_def(self):
        """<stmt> ::= <while_stmt> | <if_stmt> | <for_stmt> | <return_stmt> SEMICOLON
                        | <vdecl_stmt> SEMICOLON | <assign_stmt> SEMICOLON
                        | <call_expr> SEMICOLON """
        if self.match(TokenType.WHILE):
            self.while_stmt_def()
        elif self.match(TokenType.IF) or self.match(TokenType.ELSE):
            if self.match(TokenType.IF):
                self.if_flag = True
            elif self.match(TokenType.ELSE) and not hasattr(self, 'is_flag'):
                self.error("Invalid syntax, if needed before the use of else")
            self.if_stmt_def()
        elif self.match(TokenType.FOR):
            self.for_stmt_def()
        elif self.match(TokenType.RETURN):
            self.return_stmt_def()
            self.eat(TokenType.SEMICOLON, "Semicolon expected")
        else:
            if self.match(TokenType.ID):
                self.advance()
                if self.match(TokenType.LPAREN):
                    self.call_expr_def()
                    self.eat(TokenType.SEMICOLON, "Semicolon expected")
                elif self.match(TokenType.ID):
                    self.vdecl_stmt_def()
                    self.eat(TokenType.SEMICOLON, "Semicolon expected")
                elif self.match(TokenType.LBRACKET) or self.match(TokenType.DOT) or self.match(TokenType.ASSIGN):
                    self.assign_stmt_def()
                    self.eat(TokenType.SEMICOLON, "Semicolon expected")
            else:
                self.data_type_def()
                self.vdecl_stmt_def()
                self.eat(TokenType.SEMICOLON, "Semicolon expected")
                    
    
    def vdecl_stmt_def(self):
        """<vdecl_stmt> ::= <data_type> ID (ASSIGN <expr> | e) """
        self.eat(TokenType.ID, "ID expected after data type declaration")
        if self.match(TokenType.ASSIGN):
            self.advance()
            self.expr_def()
        
    def assign_stmt_def(self):
        """<assign_stmt> ::= <lvalue> ASSIGN <expr> """
        if self.match(TokenType.ASSIGN):
            self.advance()
        else:
            self.lvalue_def()
            self.eat(TokenType.ASSIGN, "Expecting assignment symbol")
        self.expr_def()
        
        
    def lvalue_def(self):
        """<lvalue> ::= ID (LBRACKET <expr> RBRACKET | e)(DOT ID (LBRACKET <expr> RBRACKET | e))* """
        if self.match(TokenType.ID): #sometimes lvalue is called when the ID has already bee processed
            self.advance()           #this check eliminates the other case
        if self.match(TokenType.LBRACKET):
            self.advance()
            self.expr_def()
            self.eat(TokenType.RBRACKET, "Right bracket expected")
        if self.match(TokenType.DOT):
            while self.match(TokenType.DOT):
                self.advance()
                self.eat(TokenType.ID, "ID expected")
                if self.match(TokenType.LBRACKET):
                    self.advance()
                    self.expr_def()
                    self.eat(TokenType.RBRACKET, "Right bracket expected")

                
    
    def if_stmt_def(self):
        """<if_stmt> ::= IF LPAREN <expr> RPAREN LBRACE (<stmt>)* RBRACE <if_stmt_t>"""
        if self.match(TokenType.IF):
            self.advance()
            self.eat(TokenType.LPAREN, "Left paren expected")
            self.expr_def()
            self.eat(TokenType.RPAREN, "Missing right paren")
            self.eat(TokenType.LBRACE, "Missing left brace")
            while True:
                if self.match(TokenType.RBRACE):
                    break
                else:
                    self.stmt_def()
            self.advance()
            self.if_stmt_t_def()
        else:
            self.error("Invalid syntax, if needed before the use of else")
    
    def if_stmt_t_def(self):
        """<if_stmt_t> ::= ELSEIF LPAREN <expr> RPAREN LBRACE (<stmt>)* RBRACE <if_stmt_t>
                            | ELSE LBRACE (<stmt>)* RBRACE | e """
        if self.match(TokenType.ELSEIF):
            self.advance()
            self.eat(TokenType.LPAREN, "Missing left paren")
            self.expr_def()
            self.eat(TokenType.RPAREN, "Missing right paren")
            self.eat(TokenType.LBRACE, "Missing left brace")
            while True:
                if self.match(TokenType.RBRACE):
                    break
                else:
                    self.stmt_def()
            self.advance()
            self.if_stmt_t_def()
        elif self.match(TokenType.ELSE):
            self.advance()
            self.eat(TokenType.LBRACE, "Missing left brace")
            while True:
                if self.match(TokenType.RBRACE):
                    break
                else:
                    self.stmt_def()
            self.advance()
    
    def while_stmt_def(self):
        """<while_stmt> ::= WHILE LPAREN <expr> RPAREN LBRACE (<stmt>)* RBRACE """
        self.eat(TokenType.WHILE, "Expecting while reserved word")
        self.eat(TokenType.LPAREN, "Missing left paren")
        self.expr_def()
        self.eat(TokenType.RPAREN, "Missing right paren")
        self.eat(TokenType.LBRACE, "Missing left brace")
        while True:
            if self.match(TokenType.RBRACE):
                break
            else:
                self.stmt_def()
        self.advance()
        
    def for_stmt_def(self):
        """<for_stmt> ::= FOR LPAREN <vdecl_stmt> SEMICOLON <expr> SEMICOLON
                            <assign_stmt> RPAREN LBRACE (<stmt>)* RBRACE """
        self.eat(TokenType.FOR, "For key word expected")
        self.eat(TokenType.LPAREN, "Left paren missing")
        self.data_type_def()
        self.vdecl_stmt_def()
        self.eat(TokenType.SEMICOLON, "Missing ';'")
        self.expr_def()
        self.eat(TokenType.SEMICOLON, "Missing ';'")
        self.assign_stmt_def()
        self.eat(TokenType.RPAREN, "Missing right paren")
        self.eat(TokenType.LBRACE, "Missing left brace")
        while True:
            if self.match(TokenType.RBRACE):
                break
            else:
                self.stmt_def()
        self.advance()
    
    def call_expr_def(self):
        """<call_expr> ::= ID LPAREN (<expr> (COMMA <expr>)* | e) RPAREN """
        if self.match(TokenType.ID):
            self.eat(TokenType.ID, "Missing ID")
        self.eat(TokenType.LPAREN, "Missing left paren")
        if not self.match(TokenType.RPAREN):
            self.expr_def()
            while True:
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
                self.expr_def()
        self.eat(TokenType.RPAREN, "Missing right paren")
        
    def return_stmt_def(self):
        """<return_stmt> ::= RETURN <expr> """
        self.eat(TokenType.RETURN, "Expecting return reserved word")
        self.expr_def()
    
    def expr_def(self):
        """<expr> ::= (<rvalue> | NOT <expr> | LPAREN <expr> RPAREN)(<bin_op><expr> | e) """
        if self.match(TokenType.NOT):
            self.advance()
            self.expr_def()
        elif self.match(TokenType.LPAREN):
            self.advance()
            self.expr_def()
            self.eat(TokenType.RPAREN, "Missing right paren")
        else:
            self.rvalue_def()
            
        
        if self.is_bin_op():
            self.bin_op_def()
            self.expr_def()
            
    
    def bin_op_def(self):
        """<bin_op> ::= PLUS | MINUS | TIMES | DIVIDE | AND | OR | EQUAL | LESS
                        | GREATER | LESS_EQ | GREATER_EQ | NOT_EQUAL """
        if self.is_bin_op():
            self.advance()
    
    def rvalue_def(self):
        """<rvalue> ::= <base_rvalue> | NULL_VAL | <new_rvalue> | <var_rvalue>
                        | <call_expr> """
        if self.match_any([TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL, TokenType.STRING_VAL]):
            self.base_rvalue_def()
        elif self.match(TokenType.NULL_VAL):
            self.advance()
        elif self.match(TokenType.NEW):
            self.new_rvalue_def()
        elif self.match(TokenType.ID):
            self.advance()
            if self.match(TokenType.LPAREN):
                self.call_expr_def()
            else:
                self.var_rvalue_def()
        else:
            self.error("Invalid Syntax")
           
        
    
    def new_rvalue_def(self):
        """<new_rvalue> ::= NEW ID LPAREN (<expr> (COMMA <expr>)* | e) RPAREN
                            | NEW (ID | <base_type>) LBRACKET <expr> RBRACKET """
        self.eat(TokenType.NEW, "Missing new reserved word")
        if self.match(TokenType.ID):
            self.advance()
            if self.match(TokenType.LPAREN):
                self.advance()
                if not self.match(TokenType.RPAREN):
                    self.expr_def()
                    while True:
                        if self.match(TokenType.RPAREN):
                            break
                        self.eat(TokenType.COMMA, "Missing comma separating parameters")
                        self.expr_def()
                
                self.advance()
            elif self.match(TokenType.LBRACKET):
                self.advance()
                self.expr_def()
                self.eat(TokenType.RBRACKET, "Missing right bracket")
        else:
            self.base_type_def()
            self.eat(TokenType.LBRACKET, "Missing left bracket")
            self.expr_def()
            self.eat(TokenType.RBRACKET, "Missing right bracket")
                            
    def base_rvalue_def(self):
        """<base_rvalue> ::= INT_VAL | DOUBLE_VAL | BOOL_VAL | STRING_VAL """
        if self.match_any([TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL, TokenType.STRING_VAL]):
            self.advance()
        
    def var_rvalue_def(self):
        """<var_rvalue> ::= ID(LBRACKET <expr> RBRACKET | e)(DOT ID (LBRACKET <expr> RBRACKET | e))* """
        if self.match(TokenType.LBRACKET):
            self.advance()
            self.expr_def()
            self.eat(TokenType.RBRACKET, "Missing right bracket")
        while True:
            if not self.match(TokenType.DOT):
                break
            self.advance()
            self.eat(TokenType.ID, "ID expected after '.'")
            if self.match(TokenType.LBRACKET):
                self.advance()
                self.expr_def()
                self.eat(TokenType.RBRACKET, "Missing right bracket")