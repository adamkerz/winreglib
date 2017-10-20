"""
Windows Registry Terminology:

KEY - like a folder
VALUE - like a file, has a name, a type and a value (for want of a better word)

Keys and values are case insensitive.
"""
import winreg


__version__   = "0.1.0"
__author__    = "Adam Kerz"
__copyright__ = "Copyright (C) 2016-17 Adam Kerz"


__ALL__=['RegPath','RegValue']


# ----------------------------------------
# Helper functions
# ----------------------------------------
def _ignore_file_not_found_error(fn,finallyFn=None):
    """Tries to execute fn and returns None if it raises a FileNotFoundError: [WinError 2]. Raises all other exceptions. Optional function to call on finally."""
    try:
        return fn()
    except OSError as e:
        # FileNotFoundError
        if e.winerror==2: return None
        raise
    finally:
        if callable(finallyFn): finallyFn()

def _open_key(reg_path,access=winreg.KEY_READ,error_on_non_existent=True):
    """Tries to open the key with the given security access and returns a winreg.handle object. Errors if not found, unless error_on_non_existent is True, in which case None is returned."""
    fn=lambda: winreg.OpenKey(reg_path.hkey_constant,reg_path.path,0,access)
    if error_on_non_existent: return fn()
    return _ignore_file_not_found_error(fn)



# ----------------------------------------
# RegPath class
# ----------------------------------------
class RegPath(object):
    """Represents a particular path in the registry."""

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
        # accept RegPath objects
        if isinstance(path,RegPath):
            self.hkey_constant=hkey_constant if hkey_constant else path.hkey_constant
            self.path=path.path
        else:
            # and strings
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
        """Returns True if the key exists."""
        # open (and then close) the key to see if it exists
        try:
            handle=_open_key(self)
        except OSError as e:
            if e.winerror==2: return False
            raise
        else:
            handle.Close()
            return True


    def create(self):
        """Ensures the key (and all parent keys) exist, creating them if they don't."""
        # this either creates the key (and all parent keys) if it doesn't exist or just opens the handle if it does
        handle=winreg.CreateKey(self.hkey_constant,self.path)
        handle.Close()


    def delete(self,recurse=False):
        """Deletes an existing key and any values it has. Will only delete subkeys if `recurse` is True otherwise will error."""
        # delete subkeys if recurse
        if recurse:
            for k in self.subkeys():
                k.delete(recurse=True)
        # then delete this key, ignoring it not existing
        handle=_open_key(self.parent,error_on_non_existent=False)
        if not handle: return
        _ignore_file_not_found_error(lambda:winreg.DeleteKey(handle,self.name),finallyFn=lambda:handle.Close())


    def subkeys(self):
        """A generator that yields a `RegPath` for each subkey in this key"""
        # open the key and make sure it exists
        handle=_open_key(self)
        try:
            # iterate until an exception is raised, telling us we have no more data
            i=0
            while True:
                yield self/winreg.EnumKey(handle,i)
                i+=1
        except OSError as e:
            # 259=No more data is available
            if e.winerror==259: return
            raise
        finally:
            handle.Close()


    def subvalues(self):
        """A generator that yields a `RegPath` for each subvalue in this key"""
        # open the key and make sure it exists
        handle=_open_key(self)
        try:
            # iterate until an exception is raised, telling us we have no more data
            i=0
            while True:
                (name,value,type)=winreg.EnumValue(handle,i)
                v=RegValue(self,name,value,type)
                yield v
                i+=1
        except OSError as e:
            # 259=No more data is available
            if e.winerror==259: return
            raise
        finally:
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



# ----------------------------------------
# RegValue class
# ----------------------------------------
class RegValue(object):
    """Represents a value at a particular path in the registry."""

    class ExpandingString(str):
        """Subclass of `str` that indicates the reg type to use: `REG_EXPAND_SZ`"""
        def __init__(self,value):
            # somehow, magically, `value` is extended and not needed to be passed to the constructor
            super(RegValue.ExpandingString,self).__init__()


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
        except OSError as e:
            if e.winerror==2: return False
            raise


    def get(self):
        """Returns the value or raises an exception if the key or value do not exist."""
        handle=_open_key(self.path)
        try:
            self.value,self.type=winreg.QueryValueEx(handle,self.name)
            if self.type==winreg.REG_EXPAND_SZ:
                self.value=RegValue.ExpandingString(self.value)
        finally:
            handle.Close()
        return self.value


    def set(self,value,type=None):
        """
        Sets the value and creates the key if it doesn't exist.
        If not provided, determines the type by examining the type of `value`:
            str - REG_SZ
            bytes - REG_BINARY
            int - REG_DWORD
        """
        handle=winreg.CreateKey(self.path.hkey_constant,self.path.path)
        if type is None: type=self._determine_value_type(value)
        try:
            winreg.SetValueEx(handle,self.name,0,type,value)
            self.value=value
            self.type=type
        finally:
            handle.Close()


    def delete(self):
        """Deletes a value. Just returns if it wasn't found or the key doesn't exist."""
        handle=_open_key(self.path,winreg.KEY_WRITE,error_on_non_existent=False)
        if not handle: return
        _ignore_file_not_found_error(lambda:winreg.DeleteValue(handle,self.name),finallyFn=lambda:handle.Close())


    @classmethod
    def _determine_value_type(cls,value):
        # TODO: improve type handling and incorporate other types
        if isinstance(value,bytes):
            return winreg.REG_BINARY
        if isinstance(value,RegValue.ExpandingString):
            return winreg.REG_EXPAND_SZ
        if isinstance(value,str):
            return winreg.REG_SZ
        if isinstance(value,int):
            return winreg.REG_DWORD
        return None
