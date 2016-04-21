import winreg

from winreglib import RegPath


def test_constants():
    assert RegPath.HKEYS=={winreg.HKEY_CURRENT_USER:'HKCU',winreg.HKEY_LOCAL_MACHINE:'HKLM',winreg.HKEY_CLASSES_ROOT:'HKCR',winreg.HKEY_USERS:'HKU',winreg.HKEY_CURRENT_CONFIG:'HKCC'}


# creation methods
def test_create():
    p=RegPath(r'HKLM\Software')
    assert p.hkey=='HKLM'
    assert p.path=='Software'

    p=RegPath(r'HKCU\Software')
    assert p.hkey=='HKCU'
    assert p.path=='Software'

    p=RegPath(r'HKCU\Software\longer')
    assert p.hkey=='HKCU'
    assert p.path==r'Software\longer'
    assert p.name==r'longer'

def test_truediv_operator():
    p=RegPath(r'HKLM\Software')/'longer'
    assert p.hkey=='HKLM'
    assert p.path==r'Software\longer'
    assert p.name==r'longer'


# tests functions
def test_exists():
    p=RegPath(r'HKCU\Software\winreglib\test')
    assert p.exists()
    assert p.value('AnotherValue').exists()
    assert not (p/'AnotherValue').exists()
    assert (p/'subkey1').exists()
    assert not (p/'DoesNotExist').exists()


# getters methods
def test_enumerate_key():
    p=RegPath(r'HKCU\Software\winreglib\test')
    assert [k.name for k in p.subkeys()]==['subkey1','subkey2','subkey3']

def test_enumerate_key_values():
    p=RegPath(r'HKCU\Software\winreglib\test')
    assert [v.name for v in p.subvalues()]==['','AnotherValue']


# setters/modifiers
# key methods
def test_add_key():
    p=RegPath(r'HKCU\Software\winreglib\test')/'newKey'
    assert not p.exists()
    p.create()
    assert p.exists()
    p.delete()



def test_delete_key():
    p=RegPath(r'HKCU\Software\winreglib\test')/'newKey'
    p.create()
    assert p.exists()
    p.delete()
    assert not p.exists()


# value methods
def test_add_value():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('newValue')
    assert not v.exists()
    v.set('test')
    assert v.exists()
    assert v.get()=='test'
    assert v.path==p
    v.delete()


def test_delete_value():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('newValue')
    v.set('test')
    assert v.exists()
    v.delete()
    assert not v.exists()
