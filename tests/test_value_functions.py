import winreg

import pytest

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

def test_add_value_non_existent_key():
    p=RegPath(r'HKCU\Software\winreglib\test\nonExistent')
    v=p.value('newValue')
    assert not v.exists()
    v.set('test')
    assert v.exists()
    assert v.get()=='test'
    assert v.path==p
    v.delete()
    v.path.delete()

def test_change_value():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('AnotherValue')
    assert v.exists()
    v.set(4)
    assert v.exists()
    assert v.get()==4
    assert v.path==p
    v.set(3)


def test_get_value():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('AnotherValue')
    assert v.exists()
    assert v.get()==3

def test_get_value_non_existent():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('nonExistent')
    assert not v.exists()
    with pytest.raises(OSError):
        v.get()

def test_get_value_default():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('')
    assert v.exists()
    assert v.get()=='this is default'

def test_get_value_non_existent_key():
    p=RegPath(r'HKCU\Software\winreglib\test\nonExistent')
    v=p.value('nonExistent')
    assert not v.path.exists()
    with pytest.raises(OSError):
        v.get()


def test_case_insensitive_value():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('newValue')
    v.set('test')
    v=p.value('NEWVALUE')
    assert v.exists()
    v.delete()

def test_expanding_string_value():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('nonExpandValue')
    v.set('test')
    v=p.value('nonExpandValue')
    v.get()
    assert v.type==winreg.REG_SZ
    v.delete()
    v=p.value('expandValue')
    v.set(v.ExpandingString('test'))
    v=p.value('expandValue')
    v.get()
    assert v.type==winreg.REG_EXPAND_SZ
    v.delete()


def test_delete_value():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('newValue')
    v.set('test')
    assert v.exists()
    v.delete()
    assert not v.exists()

def test_delete_value_non_existent():
    p=RegPath(r'HKCU\Software\winreglib\test')
    v=p.value('nonExistent')
    assert not v.exists()
    v.delete()
    assert not v.exists()

def test_delete_value_non_existent_key():
    p=RegPath(r'HKCU\Software\winreglib\test\nonExistent')
    v=p.value('newValue')
    assert not v.exists()
    v.delete()
    assert not v.exists()
