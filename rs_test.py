"""Unit tests for CPSC 326 Project. 


NAME: Connor Jones
DATE: Spring 2024
CLASS: CPSC 326

"""

import pytest
import io
import subprocess

from mypl_error import *
from mypl_iowrapper import *
from mypl_token import *
from mypl_lexer import *
from mypl_ast_parser import *
from mypl_var_table import *
from mypl_code_gen import *
from mypl_vm import *
from mypl_translator import *


def build(program):
    in_stream = FileWrapper(io.StringIO(program))
    parser = ASTParser(Lexer(in_stream))
    ast = parser.parse()
    translator = Translator()
    ast.accept(translator)
    
def compile():
    try:
        subprocess.run("rustc exec.rs")
    except subprocess.CalledProcessError as e:
        print(f"Failed compile {e}")
        exit(1)
        

def test_simple_var_decls(capsys):
    program = (
        'void main() { \n'
        '  int x1 = 3; \n'
        '  double x2 = 2.7; \n'
        '  bool x3 = true; \n'
        '  string x4 = "abc"; \n'
        '  print(x1); \n'
        '  print(x2); \n'
        '  print(x3); \n'
        '  print(x4); \n'
        '} \n'
    )
    build(program)
    compile()
    subprocess.run("./exec.exe")
    captured = capsys.readouterr()
    assert captured.out == '32.7trueabc'
