"""
Windows Registry Terminology:

KEY - like a folder
VALUE - like a file, has a name, a type and a value (for want of a better word)

Keys and values are case insensitive.
"""
import winreg


__version__   = "0.0.2"
__author__    = "Adam Kerz"
__copyright__ = "Copyright (C) 2016 Adam Kerz"



# ----------------------------------------
# Helper functions
# ----------------------------------------
def _open_key(reg_path,access=winreg.KEY_READ):
    return winreg.OpenKey(reg_path.hkey_constant,reg_path.path,0,access)



# ----------------------------------------
# RegValue class
# ----------------------------------------
class RegValue(object):
    """Represents a value at a particular path in the registry."""
    def __init__(self,path,name,value=None,type=None):
        self.path=path
        self.name=name
        self.value=value
        self.type=type


    def exists(self):
        """Tries to get this value to see if it exists."""
        try:
            self.get()
            return True
        except OSError:
            return False


    def get(self):
        """Returns the value or raises an exception if the key or value do not exist."""
        handle=_open_key(self.path)
        try:
            self.value,self.type=winreg.QueryValueEx(handle,self.name)
        finally:
            handle.Close()
        return self.value


    def set(self,value,type=None):
        """
        Sets the value or raises an exception if the key doesn't exist or permission is denied.
        If not provided, determines the type by examining the type of `value`:
            str - REG_SZ
            bytes - REG_BINARY
            int - REG_DWORD
        """
        handle=_open_key(self.path,winreg.KEY_WRITE)
        if type is None: type=self._determine_value_type(value)
        try:
            winreg.SetValueEx(handle,self.name,0,type,value)
            self.value=value
            self.type=type
        finally:
            handle.Close()


    def delete(self):
        """Deletes a value if it exists or returns if it wasn't found. TODO: inconsistent behaviour?"""
        handle=_open_key(self.path,winreg.KEY_WRITE)
        try:
            winreg.DeleteValue(handle,self.name)
        except OSError as ex:
            if ex.winerror==2:
                # value not found, so ignore
                return
            else:
                raise
        finally:
            handle.Close()


    @classmethod
    def _determine_value_type(cls,value):
        if isinstance(value,bytes):
            return winreg.REG_BINARY
        if isinstance(value,str):
            return winreg.REG_SZ
        if isinstance(value,int):
            return winreg.REG_DWORD
        return None



# ----------------------------------------
# RegPath class
# ----------------------------------------
class RegPath(object):
    HKEY_CONSTANTS={
        'HKEY_CURRENT_USER':winreg.HKEY_CURRENT_USER,
        'HKEY_LOCAL_MACHINE':winreg.HKEY_LOCAL_MACHINE,
        'HKEY_CLASSES_ROOT':winreg.HKEY_CLASSES_ROOT,
        'HKEY_USERS':winreg.HKEY_USERS,
        'HKEY_CURRENT_CONFIG':winreg.HKEY_CURRENT_CONFIG,
    }
    HKEY_CONSTANTS_SHORT={
        'HKCU':winreg.HKEY_CURRENT_USER,
        'HKLM':winreg.HKEY_LOCAL_MACHINE,
        'HKCR':winreg.HKEY_CLASSES_ROOT,
        'HKU':winreg.HKEY_USERS,
        'HKCC':winreg.HKEY_CURRENT_CONFIG,
    }
    HKEY_CONSTANTS.update(HKEY_CONSTANTS_SHORT)
    HKEYS={value:key for key,value in HKEY_CONSTANTS.items()}
    for key,value in HKEY_CONSTANTS_SHORT.items(): HKEYS[value]=key
    UNSET_VALUE=object()


    # ----------------------------------------
    # Construction
    # ----------------------------------------
    def __init__(self,path,hkey_constant=None):
        path.rstrip('\\')
        if hkey_constant:
            self.hkey_constant=hkey_constant
            self.path=path
        else:
            self.hkey_constant,self.path=self._split_path(path)


    def __truediv__(self,path):
        """
        Creates a new reg path by appending the given path component.

            p=RegPath(r'HKCU\Software')/'longer'
            assert p.name=='longer'
        """
        return RegPath(self.path+'\\'+path,self.hkey_constant)


    # ----------------------------------------
    # properties
    # ----------------------------------------
    # TODO: cache results of these functions - path objects should be considered immutable
    @property
    def hkey(self):
        """Short string version of this path's HKEY."""
        return self.HKEYS[self.hkey_constant]

    @property
    def name(self):
        """The key name."""
        return self.path.rsplit('\\',1)[-1]

    @property
    def parent(self):
        """A `RegPath` object that is the parent of this key."""
        return RegPath(self.path.rsplit('\\',1)[0],self.hkey_constant)


    # ----------------------------------------
    # Key manipulation
    # ----------------------------------------
    def exists(self):
        """Opens (and then closes) the key to see if it exists."""
        try:
            handle=_open_key(self)
        except OSError:
            return False
        else:
            handle.Close()
            return True


    def create(self):
        """Either creates the key if it doesn't exist or opens (and then closes) the handle if it does."""
        handle=winreg.CreateKey(self.hkey_constant,self.path)
        handle.Close()


    def delete(self,recurse=False):
        """Deletes an existing key. Must not have any subkeys."""
        if recurse:
            for k in self.subkeys():
                k.delete(recurse=True)
        handle=_open_key(self.parent)
        winreg.DeleteKey(handle,self.name)
        handle.Close()



    def subkeys(self):
        """A generator that yields a RegPath for each subkey in this key"""
        # open the key and make sure it exists
        handle=_open_key(self)
        i=0
        while True:
            try:
                yield self/winreg.EnumKey(handle,i)
                i+=1
            except OSError:
                break
        handle.Close()


    def subvalues(self):
        """A generator that yields a RegPath for each subvalue in this key"""
        # open the key and make sure it exists
        handle=_open_key(self)
        i=0
        while True:
            try:
                (name,value,type)=winreg.EnumValue(handle,i)
                v=RegValue(self,name,value,type)
                yield v
                i+=1
            except OSError:
                break
        handle.Close()


    # ----------------------------------------
    # Value manipulation
    # ----------------------------------------
    def value(self,name):
        """Returns a `RegValue` object for the value `name` at this path."""
        return RegValue(self,name)


    # ----------------------------------------
    # helper methods
    # ----------------------------------------
    @classmethod
    def _split_path(cls,keyPath):
        hkey,path=keyPath.split('\\',1)
        if hkey not in cls.HKEY_CONSTANTS:
            raise Exception('HKEY not recognised: {}'.format(hkey))
        return cls.HKEY_CONSTANTS[hkey],path



    def __str__(self):
        return '{}\\{}'.format(self.HKEYS[self.hkey_constant],self.path)
