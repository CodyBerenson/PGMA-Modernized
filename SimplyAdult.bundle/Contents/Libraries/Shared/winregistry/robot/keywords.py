""" 
     Class for working with Robot Testing Framework
"""
import logging

from winregistry import WinRegistry as Reg


class Keywords(object):

    def __init__(self, host=None):
        self.reg = Reg(host)

    def read_registry_key(self, key, key_wow64_32key=False):
        """ Reading registry key
        """
        resp = self.reg.read_key(key, key_wow64_32key)
        return resp


    def create_registry_key(self, key, key_wow64_32key=False):
        """ Creating registry key
        """
        self.reg.create_key(key, key_wow64_32key)


    def delete_registry_key(self, key, key_wow64_32key=False):
        """ Deleting registry key
        """
        self.reg.delete_key(key, key_wow64_32key)


    def read_registry_value(self, key, value, key_wow64_32key=False):
        """ Reading value from registry
        """
        return self.reg.read_value(key, value, key_wow64_32key)


    def write_registry_value(self, key, value, data=None, reg_type='REG_SZ', key_wow64_32key=False):
        """ Writing (or creating) data in value
        """
        self.reg.write_value(key, value, data, reg_type, key_wow64_32key)


    def delete_registry_value(self, key, value, key_wow64_32key=False):
        """ Deleting value from registry
        """
        self.reg.delete_value(key, value, key_wow64_32key)

