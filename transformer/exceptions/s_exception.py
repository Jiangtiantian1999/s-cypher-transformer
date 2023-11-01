from antlr4 import *
from antlr4 import Recognizer, Token
from antlr4.error.ErrorListener import *
from antlr4.error.Errors import RecognitionException
from antlr4 import InputStream

# 语法错误报告
class SCypherErrorListener(ErrorListener) :
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        stack = recognizer.getRuleInvocationStack()
        stack.reverse()
        print("rule stack: ", str(stack))
        print("line", line, ":", column, "at", offendingSymbol, ":", msg)

    def underlineError(self, recognizer, offending_token: Token, line, column):
        tokens = recognizer.getInputStream()
        input_ = str(tokens.getTokenSource().getInputStream())
        lines = input_.split("\n")
        errorLine = lines[line - 1]
        print(errorLine)
        for i in range(0, column):
            print(" ")
        start = offending_token.start
        stop = offending_token.stop
        if start >= 0 and stop >= 0:
            for i in range(start, stop + 1):
                print("^")
        print("\n")

# 语法错误恢复
class SCypherErrorStrategy(BailErrorStrategy):
    def recover(self, recognizer: Parser, e: RecognitionException):
        recognizer.errHandler.reportError(recognizer, e)
        super().recover(recognizer, e)

class FormatError(Exception):
    def __int__(self, message):
        super().__init__(message)


class TimeZoneError(Exception):
    def __int__(self, message):
        super().__init__(message)


class GraphError(Exception):
    def __int__(self, message):
        super().__init__(message)


class ClauseError(Exception):
    def __int__(self, message):
        super().__init__(message)


class SyntaxError(Exception):
    def __int__(self, message):
        super().__init__(message)
