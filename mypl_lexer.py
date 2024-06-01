"""The MyPL Lexer class.

NAME: Connor Jones
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_token import *
from mypl_error import *


class Lexer:
    """For obtaining a token stream from a program."""

    def __init__(self, in_stream):
        """Create a Lexer over the given input stream.

        Args:
            in_stream -- The input stream. 

        """
        self.in_stream = in_stream
        self.line = 1
        self.column = 0


    def read(self):
        """Returns and removes one character from the input stream."""
        self.column += 1
        return self.in_stream.read_char()

    
    def peek(self):
        """Returns but doesn't remove one character from the input stream."""
        return self.in_stream.peek_char()

    
    def eof(self, ch):
        """Return true if end-of-file character"""
        return ch == ''

    
    def error(self, message, line, column):
        raise LexerError(f'{message} at line {line}, column {column}')

    
    def next_token(self):
        """Return the next token in the lexer's input stream."""
        # read initial character
        ch = self.read()
        
        # First check for an end of the stream just in case the file is blank
        if self.eof(ch):
            return Token(TokenType.EOS, '', self.line, self.column)    
        #Assessing the punctuation tokens
        elif ch == ';':
            return Token(TokenType.SEMICOLON, ';', self.line, self.column)
        elif ch == '(':
            return Token(TokenType.LPAREN, '(', self.line, self.column)
        elif ch == ')':
            return Token(TokenType.RPAREN, ')', self.line, self.column)
        elif ch == '[':
            return Token(TokenType.LBRACKET, '[', self.line, self.column)
        elif ch == ']':
            return Token(TokenType.RBRACKET, ']', self.line, self.column)
        elif ch == '{':
            return Token(TokenType.LBRACE, '{', self.line, self.column)
        elif ch == '}':
            return Token(TokenType.RBRACE, '}', self.line, self.column)
        elif ch == '.':
            return Token(TokenType.DOT, '.', self.line, self.column)
        elif ch == ',':
            return Token(TokenType.COMMA, ',', self.line, self.column)   
        #Assessing the arithmetic tokens
        elif ch == '+':
            return Token(TokenType.PLUS, '+', self.line, self.column)
        elif ch == '-':
            return Token(TokenType.MINUS, '-', self.line, self.column)
        elif ch == '*':
            return Token(TokenType.TIMES, '*', self.line, self.column)
        elif ch == '/':
            #check to see if it's not a comment
            if self.peek() != '/':
                return Token(TokenType.DIVIDE, '/', self.line, self.column)
            #if it is a comment, it will be assessed later
            elif self.peek() == '/':
                start_col = self.column
                self.read()
                comment_lex = ""
                while self.peek() != '\n' and self.peek() != '':
                    comment_lex += self.read()
                return Token(TokenType.COMMENT, comment_lex, self.line, start_col)
        #Assessing the equals sign and checking to see if it is an assignment
        #or if it is a equal token
        elif ch == '=':
            if self.peek() == '=':
                #take the other = off the input stream 
                self.read()
                #Make sure to take into account the addition to the column count
                return Token(TokenType.EQUAL, '==', self.line, self.column - 1)
            else:
                return Token(TokenType.ASSIGN, '=', self.line, self.column)
        #Assessing the relational comparators
        elif ch == '!':
            if self.peek() == '=':
                #take the = off the input stream 
                self.read()
                #Make sure to take into account the addition to the column count
                return Token(TokenType.NOT_EQUAL, '!=', self.line, self.column - 1)
            else:
                self.error("Expected character '=' not found", self.line, self.column)
        elif ch == '<':
            if self.peek() == '=':
                #take the = off the input stream 
                self.read()
                #Make sure to take into account the addition to the column count
                return Token(TokenType.LESS_EQ, '<=', self.line, self.column - 1)
            else:
                return Token(TokenType.LESS, '<', self.line, self.column)
        elif ch == '>':
            if self.peek() == '=':
                #take the = off the input stream
                self.read()
                #Take into account the addition to the column count
                return Token(TokenType.GREATER_EQ, '>=', self.line, self.column - 1)
            else:
                return Token(TokenType.GREATER, '>', self.line, self.column)
        elif ch.isalpha():
            #using string_id to have ch add onto
            string_id = ch
            #keeping track of the column that I started on
            start_col = self.column
            #While the letter is still alphanumeric or an underscore keep adding onto
            #the string_id to get the full word
            while str(self.peek()).isalpha() or str(self.peek()).isdigit() or str(self.peek()) == '_':
                string_id += str(self.read())
       
            #Filter out the reserved words
            if string_id == 'struct':
                return Token(TokenType.STRUCT, string_id, self.line, start_col)
            elif string_id == 'array':
                return Token(TokenType.ARRAY, string_id, self.line, start_col)
            elif string_id == 'for':
                return Token(TokenType.FOR, string_id, self.line, start_col)
            elif string_id == 'while':
                return Token(TokenType.WHILE, string_id, self.line, start_col)
            elif string_id == 'if':
                return Token(TokenType.IF, string_id, self.line, start_col)
            elif string_id == 'elseif':
                return Token(TokenType.ELSEIF, string_id, self.line, start_col)
            elif string_id == 'else':
                return Token(TokenType.ELSE, string_id, self.line, start_col)
            elif string_id == 'new':
                return Token(TokenType.NEW, string_id, self.line, start_col)
            elif string_id == 'return':
                return Token(TokenType.RETURN, string_id, self.line, start_col)
            #Filter out the data types
            elif string_id == 'int':
                return Token(TokenType.INT_TYPE, string_id, self.line, start_col)
            elif string_id == 'double':
                return Token(TokenType.DOUBLE_TYPE, string_id, self.line, start_col)
            elif string_id == 'string':
                return Token(TokenType.STRING_TYPE, string_id, self.line, start_col)
            elif string_id == 'bool':
                return Token(TokenType.BOOL_TYPE, string_id, self.line, start_col)
            elif string_id == 'void':
                return Token(TokenType.VOID_TYPE, string_id, self.line, start_col)
            elif string_id == 'null':
                return Token(TokenType.NULL_VAL, string_id, self.line, start_col)
            elif string_id == "true":
                return Token(TokenType.BOOL_VAL, string_id, self.line, start_col)
            elif string_id == 'false':
                return Token(TokenType.BOOL_VAL, string_id, self.line, start_col)
            elif string_id == 'and':
                return Token(TokenType.AND, string_id, self.line, start_col)
            elif string_id == 'or':
                return Token(TokenType.OR, string_id, self.line, start_col)
            elif string_id == 'not':
                return Token(TokenType.NOT, string_id, self.line, start_col)
            #if it is none of the above, then it is an id for a variable
            else:
                return Token(TokenType.ID, string_id, self.line, start_col)        
        #Taking care of the numeric values
        elif ch.isdigit():
            string_int = ch
            start_col = self.column
            if ch == '0':
                if self.peek().isnumeric():
                    self.error("Invalid number format, no leading zeros allowed", self.line, self.column)
            while str(self.peek()).isdigit():
                string_int += str(self.read())
            
            if str(self.peek()) == '.':
                string_int += str(self.read())
                if not self.peek().isdigit():
                    self.error("Invalid format for double value", self.line, self.column) 
                while str(self.peek()).isdigit():
                    string_int += str(self.read())
       
                return Token(TokenType.DOUBLE_VAL, string_int, self.line, start_col)
            elif string_int.isnumeric():
                return Token(TokenType.INT_VAL, string_int, self.line, start_col)
            else:
                return Token(TokenType.ID, string_id, self.line, start_col)
        elif ch == '"':
            start_col = self.column
            string_lexeme = self.read()
            if string_lexeme == '"':
                return Token(TokenType.STRING_VAL, '', self.line, start_col)
            while self.peek() != '"':
                string_lexeme += self.read()
                if self.peek() == '\n':
                    tmp = self.read()
                    if self.peek() == '\n':
                        self.error("Reached newline while reading string", self.line, self.column)
                    string_lexeme += tmp
            string_lexeme = string_lexeme.replace('"', '')
            #consume the remaining quotation mark"
            self.read()
            return Token(TokenType.STRING_VAL, string_lexeme, self.line, start_col)
        elif ch == '_':
            self.error("Invalid use of '_' (Note that using '_' should happen for naming values in ids)", self.line, self.column)
        #Newline and space
        elif ch == '\n':
            self.column = 0
            self.line += 1
            return self.next_token()    
        elif ch.isspace():
            return self.next_token()
        else:
            error_msg = "Unexpected symbol {ch} found"
            self.error(error_msg, self.line, self.column)
        
        # TODO: finish the rest of the next_token function
