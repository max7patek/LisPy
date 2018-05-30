#!/usr/bin/env python

"""
This is an interpreter for LisPy, a Lisp-y syntax wrapper for Python.
Implemented with PLY (Python Lex-Yacc) by David M. Beazley.

LisPy is a Lisp-like language that is built off of Python's builtin modules.
It was developed for use in the Metaprogramming ESC Student Taught Class at the
University of Virginia.
"""

__author__ = "Maxwell Patek"
__license__ = "GNU LGPL v3.0"
__version__ = "1.0"
__maintainer__ = "Maxwell Patek"
__email__ = "mtp4be@virginia.edu"
__status__ = "Prototype"




reserved = {
    'nil' : 'NIL',
    'def' : 'DEF',
    'let' : 'LET',

}

tokens = (
    'NAME','NUMBER','STRING',
    'LPAREN','RPAREN',
    'COMMA',
    'QUOTE', 'NIL'
    )

# Tokens

t_QUOTE   = r'\''
t_COMMA   = r','
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_NAME    = r'[a-zA-Z_][a-zA-Z0-9_?]*'
t_STRING  = r'"([^"\n]|(\\"))*"'
#t_COMMA = r','

def t_NUMBER(t): # Numbers can be at least one digit followed by an optional decimal component or just a decimal component
    r'[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)'
    #r'\d+\.\d*|\d*\.\d+|\d+'
    t.value = float(t.value)
    return t
#
# def t_STRING(t):
#     r'"([^"\n]|(\\"))*"'
#     print(t.value)

# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
import ply.lex as lex
lexer = lex.lex()



class Expression:
    def __init__(self, list):
        self.list = list

class Symbol:
    def __init__(self, name):
        self.name = name

class Quoted:
    def __init__(self, data):
        self.data = data

class Commad:
    def __init__(self, data):
        self.data = data

def add(*args):
    if isinstance(args[0], float) or isinstance(args[0], int):
        return sum(args)
    if isinstance(args[0], str):
        return ''.join(args)
    l = []
    for i in args:
        l.extend(i)
    return l

def my_and(*args):
    for i in args:
        if not truth(i):
            return False
    return True

def my_or(*args):
    for i in args:
        if truth(i):
            return True
    return False

def equal(*args):
    for i in range(1, len(args)):
        if not args[i-1] == args[i]:
            return False
    return True

def mult(*args):
    m = 1
    for i in args:
        m *= i
    return m

def truth(thing):
    if not hasattr(thing, '__len__'):
        return False
    return len(thing) != 0



from collections import ChainMap
import pickle
import os
if not os.path.exists("programs"):
    os.makedirs("programs")

base = {
    'add' : add,
    'mult' : mult,
    'map' : map,
    'list' : list,
    'dict' : dict,
    'zip' : zip,
    'def' : 'def',
    'set' : 'set',
    'cond' : 'cond',
    'macro' : 'macro',
    'negative?' : lambda i: [1] if i < 0 else [],
    'equal?' : equal,
    'not' : lambda i: [] if truth(i) else [1],
    'and' : my_and,
    'or' : my_or,
    'nth' : lambda n, i: i[int(n)],
    'len' : len,
    'true' : [1],
    'nil' : [],
    'quit' : 'quit',
    'open' : open,
    'save' : lambda o, f: pickle.dump(o, open("programs/"+f, "w")),
    'load' : pickle.load
}
base.update(dict(type({}).__dict__))
base.update(dict(type('').__dict__))
base.update(dict(type([]).__dict__))
base['__env__'] = base

names = ChainMap(base)
#names = names.new_child()

class ScopedFunction:
    def __init__(self, expression, environment, params):
        self.exp = expression
        self.env = environment
        self.params = params
    def __call__(self, *args):
        #print(dict(zip(self.params, args)))
        context = self.env.new_child(dict(zip(self.params, args)))
        #print('expression', self.exp)
        ret = eval(self.exp, context)
        #print(ret)
        return ret

class Macro:
    def __init__(self, expression, environment, params):
        self.exp = expression
        self.env = environment
        self.params = params
    def __call__(self, program):
        print(dict(zip(self.params, list(map(lambda i: eval(i, self.env), program)))))
        context = self.env.new_child(dict(zip(self.params, list(map(lambda i: eval(i, self.env), program)))))
        print('expression', self.exp)
        ret = eval(self.exp, context)
        #ret = list(map(lambda i: eval(i, context), self.exp))
        print(ret)
        return ret

def eval(thing, environment=names):
    if isinstance(thing, float) or isinstance(thing, str):# or isinstance(thing, Quoted):
        return thing
    elif isinstance(thing, Symbol):
        return environment[thing.name]
    elif isinstance(thing, Expression):
        op = eval(thing.list[0], environment)
        if op == 'def':
            # [def, name, (params), expression]
            name = thing.list[1].name
            params = list(map(lambda i: i.name, thing.list[2].list))
            expression = thing.list[3]
            function = ScopedFunction(expression, environment, params)
            # def function(*args):
            #     context = environment.new_child(dict(zip(params, args)))
            #     return eval(expression, context)
            environment[name] = function
            return function
        elif op == 'macro':
            # macro name (form) (code)
            name = thing.list[1].name
            params = list(map(lambda i: i.name, thing.list[2].list))
            expression = thing.list[3]
            #function = ScopedFunction(Expression(eval(expression)), environment, params)
            macro = Macro(Expression(eval(expression)), environment, params)
            environment[name] = macro
            return macro
        elif op == 'set':
            # [set, name, expression]
            name = thing.list[1].name
            expression = thing.list[2]
            value = eval(expression, environment)
            environment[name] = value
            return value
        elif op == 'cond':
            for i in thing.list[1:]:
                if truth(eval(i.list[0], environment)):
                    return eval(i.list[1], environment)
            else:
                return []
        elif op == 'quit':
            print("Goodbye")
            exit(0)
        elif isinstance(op, Macro):
            return eval(op(thing.list[1:]))
        else:
            # regular function call
            return op(*list(map(lambda i: eval(i, environment), thing.list[1:])))
            #return apply(op, thing.list[1:])
    elif isinstance(thing, Quoted):
        if isinstance(thing.data, Symbol):
            return thing.data
        return list(map(lambda i: eval(i.data, environment) if isinstance(i, Commad) else i, thing.data.list))
    #elif isinstance(thing, Commad):
    #    return thing
    else:
        print("CANT EVAL")
        return []

from pprint import pprint

def p_start(t):
    'start : statement'
    #print("hello")
    pprint(eval(t[1]))


def p_atomic(t):
    '''statement : NUMBER
                | NIL'''
    t[0] = t[1]
    #print(t[1])

def p_string(t):
    'statement : STRING'
    t[0] = t[1][1:-1]

def p_lookup(t):
    'statement : NAME'
    #ry:
    #    t[0] = names[t[1]]
    #except LookupError:
    t[0] = Symbol(t[1])

def p_quoted(t):
    'statement : QUOTE statement'
    t[0] = Quoted(t[2])

def p_commad(t):
    'statement : COMMA statement'
    t[0] = Commad(t[2])

def p_statement_expr(t):
    'statement : expression'
    #print(t[1])
    t[0] = Expression(t[1])

def p_expression_list(t):
    'expression : list'
    t[0] = t[1]

#def p_quoted_list(t):
#    'quoted : QUOTE list'
#    t[0] = t[2]

def p_list_parens(t):
    'list : LPAREN element RPAREN'
    t[0] = t[2]

def p_element(t):
    'element : element statement'
    #print(t[2])
    t[1].append(t[2])
    t[0] = t[1]

def p_base(t):
    'element : statement'
    #print(type(t[1]))
    t[0] = [t[1]]

def p_error(t):
    print("Syntax error at '%s'" % t)

import ply.yacc as yacc
parser = yacc.yacc()

if __name__ == "__main__":

    while True:
        try:
            s = input('>>> ')   # Use raw_input on Python 2
        except EOFError:
            break
        #try:
        parser.parse(s)
        #except KeyError as e:
        #    print("Unbound Symbol:", e)
        #except TypeError as e:
        #    print("Type Error:", e)
