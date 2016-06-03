import winreg

from winreglib import RegPath


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


def test_case_insensitive_value():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('newValue')
    v.set('test')
    v=p.value('NEWVALUE')
    assert v.exists()
    v.delete()
