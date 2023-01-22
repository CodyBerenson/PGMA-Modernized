from .keywords import Keywords


ROBOT_LIBRARY_SCOPE = 'GLOBAL'

class robot(Keywords):
    """ RequestsLibrary is a HTTP client keyword library that uses
    the requests module from Kenneth Reitz
    https://github.com/kennethreitz/requests
        Examples:
        | ${path}               | HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run |
        | Write Registry Value  | ${path}           | Notepad | notepad.exe               |
        | ${autorun} =          | Read Registry Key | ${path} |                           |
        | Log                   | ${autorun}        |         |                           |
        | Delete Registry Value | ${path}           | Notepad |                           |
    """
