""" WinRegistry
    ~~~~~~~~~~~

    Usage::
        >>> from winregistry import WinRegistry as Reg
        >>> reg = Reg()
        >>> path = r'HKLM\SOFTWARE\remove_me'
        >>> reg.create_key(path + r'\test')
        >>> True if 'remove_me' in reg.read_key(r'HKLM\SOFTWARE')['keys'] else False
        True
        >>> reg.write_value(path, 'Value name', b'21', 'REG_BINARY')
        >>> reg.read_key(path)
        {'keys': ['test'], 'values': [{'value': 'Value name', 'data': b'21...
        >>> reg.read_value(path, 'Value name')
        {'value': 'Value name', 'data': b'21', 'type': 'REG_BINARY'}
        >>> reg.delete_value(path, 'Value name')
        >>> reg.delete_key(path + r'\test')
        >>> reg.read_key(path)
        {'keys': [], 'values': [], 'modify': datetime.datetime(2017, 4, 16...
        >>> reg.delete_key(path)
        >>> True if 'remove_me' in reg.read_key(r'HKLM\SOFTWARE')['keys'] else False
        False
"""
from datetime import datetime, timedelta
import winreg


WINREG_TYPES = ['REG_NONE',              # 0 == winreg.REG_NONE
                'REG_SZ',                # 1 == winreg.REG_SZ
                'REG_EXPAND_SZ',         # 2 == winreg.REG_EXPAND_SZ
                'REG_BINARY',            # 3 == winreg.REG_BINARY
                'REG_DWORD',             # 4 == winreg.REG_DWORD
                                         # 4 == winreg.REG_DWORD_LITTLE_ENDIAN
                # 'REG_DWORD_LITTLE_ENDIAN',
                'REG_DWORD_BIG_ENDIAN',  # 5 == winreg.REG_DWORD_BIG_ENDIAN
                'REG_LINK',              # 6 == winreg.REG_LINK
                'REG_MULTI_SZ',          # 7 == winreg.REG_MULTI_SZ
                'REG_RESOURCE_LIST',     # 8 == winreg.REG_RESOURCE_LIST
                                         # 9 == winreg.REG_FULL_RESOURCE_DESCRIPTOR
                'REG_FULL_RESOURCE_DESCRIPTOR',
                # 10 == winreg.REG_RESOURCE_REQUIREMENTS_LIST:
                'REG_RESOURCE_REQUIREMENTS_LIST']

SHORT_ROOTS = {
    'HKCR': 'HKEY_CLASSES_ROOT',
    'HKCU': 'HKEY_CURRENT_USER',
    'HKLM': 'HKEY_LOCAL_MACHINE',
    'HKU': 'HKEY_USERS',
    'HKCC': 'HKEY_CURRENT_CONFIG'}


class WinRegistry(object):
    """ Minimalist Python library aimed at working with Windows registry
    """

    def __init__(self, host=None):
        self.host = host
        self.root = None
        self.root_handle = None


    def close(self):
        ''' Close registry handle
        '''
        self.root_handle.Close()


    def read_value(self, key, value, key_wow64_32key=False):
        ''' Read named value in registry
        '''
        try:
            handle = self._get_handle(key, winreg.KEY_READ, key_wow64_32key)
            reg_value = winreg.QueryValueEx(handle, value)
            handle.Close()
        except:
            raise
        reg_type = WINREG_TYPES[reg_value[1]]
        data = {'value': value, 'data': reg_value[0], 'type': reg_type}
        return data


    def write_value(self, key, value, data=None, reg_type='REG_SZ', key_wow64_32key=False):
        ''' Write data in named value in registry
        '''
        try:
            handle = self._get_handle(key, winreg.KEY_SET_VALUE, key_wow64_32key)
            winreg.SetValueEx(handle, value, 0, getattr(winreg, reg_type), data)
            handle.Close()
        except:
            raise


    def delete_value(self, key, value, key_wow64_32key=False):
        ''' Delete named value in registry
        '''
        try:
            handle = self._get_handle(key, winreg.KEY_SET_VALUE, key_wow64_32key)
            winreg.DeleteValue(handle, value)
            handle.Close()
        except:
            raise


    def read_key(self, key, key_wow64_32key=False):
        ''' Read named key in registry
        '''
        resp = {'keys': [], 'values': []}

        try:
            handle = self._get_handle(key, winreg.KEY_READ, key_wow64_32key)
            keys_num, values_num, modify = winreg.QueryInfoKey(handle)
            resp['modify'] = datetime(1601, 1, 1) + timedelta(microseconds=modify/10)
        except:
            raise

        for key_i in range(0, keys_num):
            resp['keys'].append(winreg.EnumKey(handle, key_i))

        for key_i in range(0, values_num):
            value = {}
            value['value'], value['data'], value['type'] = winreg.EnumValue(handle, key_i)
            value['type'] = WINREG_TYPES[value['type']]
            resp['values'].append(value)

        handle.Close()

        return resp


    def create_key(self, key, key_wow64_32key=False):
        ''' Create named key in registry
        '''
        handle = None
        subkeys = key.split('\\')
        i = 0

        while (i < len(subkeys)) and (not handle):
            try:
                current = '\\'.join(subkeys[:len(subkeys) - i])
                handle = self._get_handle(current, winreg.KEY_WRITE, key_wow64_32key)
            except FileNotFoundError:
                i += 1

        tail = '\\'.join(subkeys[len(subkeys) - i:])
        winreg.CreateKeyEx(handle, tail, 0, self._get_access(winreg.KEY_WRITE))
        handle.Close()


    def delete_key(self, key, key_wow64_32key=False):
        ''' Delete named key from registry
        '''
        try:
            parental, subkey = self._parse_subkey(key)

            handle = self._get_handle(parental, winreg.KEY_WRITE, key_wow64_32key)

            winreg.DeleteKey(handle, subkey)

            handle.Close()
        except:
            raise

    def _get_handle(self, key, access, key_wow64_32key=False):
        key_handle = None
        root, path = self._parse_root(key)
        access = self._get_access(access, key_wow64_32key)

        try:
            if root != self.root or not self.root_handle:
                self.root_handle = winreg.ConnectRegistry(self.host, root)
            key_handle = winreg.OpenKey(self.root_handle, path, 0, access)
        except:
            raise

        return key_handle


    def _get_access(self, access, key_wow64_32key=False):
        x64_key = winreg.KEY_WOW64_32KEY if key_wow64_32key else winreg.KEY_WOW64_64KEY
        return access | x64_key


    @staticmethod
    def _parse_root(path):
        try:
            _root, key_path = path.split('\\', 1)
        except:
            raise Exception('Error while parsing registry path "{0}"'.format(path))
        try:
            _root = _root.upper()
            _root = SHORT_ROOTS[_root] if _root in SHORT_ROOTS else _root
            reg_root = getattr(winreg, _root)
        except:
            raise Exception('None exist root key "{}"'.format(_root))
        if not key_path:
            raise Exception('Not found existsing key in "{}"'.format(path))
        return (reg_root, key_path)


    @staticmethod
    def _parse_subkey(key):
        try:
            parental, subkey = key.rsplit(sep='\\', maxsplit=1)
        except:
            raise Exception('Error while parsing registry key "{}"'.format(key))

        if not parental or not subkey:
            raise Exception('Not found existsing parental (or child) key in "{}"'.format(key))

        return (parental, subkey)
