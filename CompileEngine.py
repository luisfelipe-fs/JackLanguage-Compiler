from JackTokenizer import JackTokenizer
from Token import Token
from CompilerException import CompilerException
from EOFException import EOFException

class CompilerEngine (JackTokenizer):
    B_OPERATOR = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
    U_OPERATOR = ['-', '~']
    KEYWORD_CONSTANTS = ['true', 'false', 'null', 'this']
    STATEMENTS = ['let', 'if', 'while', 'do', 'return']
    KEYWORD_TYPES = ['int', 'char', 'boolean']
    KEYWORD_SUBROUTINE = ['constructor', 'function', 'method']
    KEYWORD_CLASS_VAR_TYPE = ['static', 'field']
    TERM_TYPES = [Token.TK_INT, Token.TK_STRING, Token.TK_IDENTIFIER]
    REPLACEMENTS = {'<': '&lt;', '>': '&gt;', '"': '&quot;', '&': '&amp;'}
    
    def __init__ (self, path):
        super().__init__(path)
        self.path = path
        self.xml = str()
        self.advance()

    def xmlContent (self):
        tokenClass = self.tokenType()
        currentToken = self.getToken()
        if tokenClass != Token.TK_STRING:
            try:
                currentToken = REPLACEMENTS[currentToken]
            except:
                pass
            return currentToken
        else:
            return currentToken[1:-1]

    def generateXML (self):
        with open(self.path+'.xml', 'w+') as f:
            f.write(self.xml)

    def error (self, expected):
        raise CompilerException("Line %s: Expected '%s', got '%s'." % (self.getLine()+1, expected, self.getToken()))

    def eat (self, *types):
        if self.tokenType() not in types:
            self.error(types)
        self.xml += '<%s>%s</%s>\n'%(self.tokenType(), self.xmlContent(), self.tokenType())
        self.advance()

    def cEat (self, symbol): # Conditional Eat
        if self.getToken().__eq__(symbol):
            self.eat(self.tokenType())
        else:
            self.error(symbol)

    def compileTerm (self):
        self.xml += '<term>\n'
        if self.getToken() in self.KEYWORD_CONSTANTS:
            self.eat(Token.TK_KEYWORD)
        else:
            self.eat(Token.TK_INT, Token.TK_STRING, Token.TK_IDENTIFIER)
        self.xml += '</term>\n'

    def compileExpression (self):
        self.xml += '<expression>\n'
        self.compileTerm()
        if self.getToken() in self.B_OPERATOR:
            self.eat(Token.TK_SYMBOL)
            self.compileTerm()
        self.xml += '</expression>\n'

    def compileExpressionList (self):
        self.xml += '<expressionList>\n'
        if self.tokenType() in self.TERM_TYPES or self.getToken() in self.KEYWORD_CONSTANTS:
            self.compileExpression()
            while self.getToken().__eq__(','):
                self.eat(Token.TK_SYMBOL)
                self.compileExpression()
        self.xml += '</expressionList>\n'

    def compileSubroutineCall (self):
        self.eat(Token.TK_IDENTIFIER)
        if self.getToken().__eq__('.'):
            self.eat(Token.TK_SYMBOL)
            self.eat(Token.TK_IDENTIFIER)
            self.cEat('(')
            self.compileExpressionList()
            self.cEat(')')
        elif self.getToken().__eq__('('):
            self.cEat('(')
            self.compileExpressionList()
            self.cEat(')')

    def compileStatements (self):
        self.xml += '<statements>\n'
        while self.getToken() in self.STATEMENTS:
            if self.getToken().__eq__('let'):
                self.compileLet()
            elif self.getToken().__eq__('if'):
                self.compileIf()
            elif self.getToken().__eq__('while'):
                self.compileWhile()
            elif self.getToken().__eq__('do'):
                self.compileDo()
            elif self.getToken().__eq__('return'):
                self.compileReturn()
        self.xml += '</statements>\n'

    def compileLet (self):
        self.xml += '<letStatement>\n'
        self.cEat('let')
        self.eat(Token.TK_IDENTIFIER)
        if self.getToken().__eq__('['):
            self.eat(Token.TK_SYMBOL)
            self.compileExpression()
            if self.getToken().__eq__(']'):
                self.eat(Token.TK_SYMBOL)
            else:
                self.error(']')
        self.cEat('=')
        self.compileExpression()
        self.cEat(';')
        self.xml += '</letStatement>\n'

    def compileIf (self):
        self.xml += '<ifStatement>\n'
        self.cEat('if')
        self.cEat('(')
        self.compileExpression()
        self.cEat(')')
        self.cEat('{')
        self.compileStatements()
        self.cEat('}')
        try:
            if self.getToken().__eq__('else'):
                self.eat(Token.TK_KEYWORD)
                self.cEat('{')
                self.compileStatements()
                self.cEat('}')
        except EOFException:
            pass
        self.xml += '</ifStatement>\n'

    def compileWhile (self):
        self.xml += '<whileStatement>\n'
        self.cEat('while')
        self.cEat('(')
        self.compileExpression()
        self.cEat(')')
        self.cEat('{')
        self.compileStatements()
        self.cEat('}')
        self.xml += '</whileStatement>'

    def compileDo (self):
        self.xml += '<doStatement>\n'
        self.cEat('do')
        self.compileSubroutineCall()
        self.cEat(';')
        self.xml += '</doStatement>\n'

    def compileReturn (self):
        self.xml += '<returnStatement>\n'
        self.cEat('return')
        if self.getToken().__eq__(';'):
            self.eat(Token.TK_SYMBOL)
            self.xml += '</returnStatement>\n'
            return
        self.compileExpression()
        self.cEat(';')
        self.xml += '</returnStatement>\n'

    def compileType (self):
        if self.getToken() in self.KEYWORD_TYPES:
            self.eat(Token.TK_KEYWORD)
        elif self.tokenType().__eq__(Token.TK_IDENTIFIER):
            self.eat(Token.TK_IDENTIFIER)
        else:
            self.error(self.KEYWORD_TYPES+[Token.TK_IDENTIFIER])

    def compileVarDec (self):
        self.cEat('var')
        self.compileType()
        while self.getToken().__eq__(','):
            self.eat(Token.TK_SYMBOL)
            self.eat(Token.TK_IDENTIFIER)
        self.cEat(';')

    def compileSubroutineBody (self):
        self.xml += '<subroutineBody>\n'
        self.cEat('{')
        while self.getToken().__eq__('var'):
            self.compileVarDec()
        self.compileStatements()
        self.cEat('}')
        self.xml += '</subroutineBody>\n'

    def compileParameterList (self):
        self.xml += '<parameterList>\n'
        if self.getToken() in self.KEYWORD_TYPES or self.tokenType().__eq__(Token.TK_IDENTIFIER):
            self.compileType()
            self.eat(Token.TK_IDENTIFIER)
            while self.getToken().__eq__(','):
                self.eat(Token.TK_SYMBOL)
                self.compileType()
                self.eat(Token.TK_IDENTIFIER)
        self.xml += '</parameterList>\n'

    def compileSubroutineDec (self):
        self.xml += '<subroutineDec>\n'
        if self.getToken() in self.KEYWORD_SUBROUTINE:
            self.eat(Token.TK_KEYWORD)
        else:
            self.error(self.KEYWORD_SUBROUTINE)
        if self.getToken() in self.KEYWORD_TYPES+['void']:
            self.eat(Token.TK_KEYWORD)
        elif self.tokenType().__eq__(Token.TK_IDENTIFIER):
            self.eat(Token.TK_IDENTIFIER)
        else:
            self.error(self.KEYWORD_TYPES+['void']+Token.TK_IDENTIFIER)
        self.eat(Token.TK_IDENTIFIER)
        self.cEat('(')
        self.compileParameterList()
        self.cEat(')')
        self.compileSubroutineBody()
        self.xml += '</subroutineDec>\n'

    def compileClassVarDec (self):
        self.xml += '<classVarDec>\n'
        if self.getToken() in self.KEYWORD_CLASS_VAR_TYPE:
            self.eat(Token.TK_KEYWORD)
        else:
            self.error(self.KEYWORD_CLASS_VAR_TYPE)
        self.compileType()
        self.eat(Token.TK_IDENTIFIER)
        while self.getToken().__eq__(','):
            self.eat(Token.TK_SYMBOL)
            self.eat(Token.TK_IDENTIFIER)
        self.cEat(';')
        self.xml += '</classVarDec>\n'

    def compileClass (self):
        self.xml += '<class>\n'
        self.cEat('class')
        self.eat(Token.TK_IDENTIFIER)
        self.cEat('{')
        while self.getToken() in self.KEYWORD_CLASS_VAR_TYPE:
            self.compileClassVarDec()
        while self.getToken() in self.KEYWORD_SUBROUTINE:
            self.compileSubroutineDec()
        self.cEat('}')
        self.xml += '</class>\n'
