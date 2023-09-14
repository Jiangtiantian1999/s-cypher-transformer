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
