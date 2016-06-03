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
