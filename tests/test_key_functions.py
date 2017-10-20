import winreg

import pytest

from winreglib import RegPath


# tests
def test_exists():
    p=RegPath(r'HKCU\Software\winreglib\test')
    assert p.exists()
    assert p.value('AnotherValue').exists()
    assert not (p/'AnotherValue').exists()
    assert (p/'subkey1').exists()
    assert not (p/'DoesNotExist').exists()


# getters
def test_enumerate_key():
    p=RegPath(r'HKCU\Software\winreglib\test')
    assert [k.name for k in p.subkeys()]==['subkey1','subkey2','subkey3']

def test_enumerate_key_values():
    p=RegPath(r'HKCU\Software\winreglib\test')
    assert [v.name for v in p.subvalues()]==['','AnotherValue']


# setters/modifiers
def test_add_key():
    p=RegPath(r'HKCU\Software\winreglib\test')/'newKey'
    assert not p.exists()
    p.create()
    assert p.exists()
    p.delete()

def test_add_key_and_parents():
    p=RegPath(r'HKCU\Software\winreglib\test')/'parentKey'/'childKey'
    assert not p.parent.exists()
    assert not p.exists()
    p.create()
    assert p.exists()
    p.parent.delete(recurse=True)


def test_case_insensitive_key():
    p=RegPath(r'HKCU\Software\winreglib\test')/'newKey'
    assert not p.exists()
    p.create()
    assert p.exists()
    p=p.parent/'NEWKEY'
    assert p.exists()
    p.delete()


def test_delete_key():
    p=RegPath(r'HKCU\Software\winreglib\test')/'newKey'
    p.create()
    assert p.exists()
    p.delete()
    assert not p.exists()

def test_delete_key_recurse():
    p=RegPath(r'HKCU\Software\winreglib\test')/'newKey'
    p.create()
    assert p.exists()
    p=p/'twoDeep'
    p.create()
    assert p.exists()
    with pytest.raises(OSError):
        p.parent.delete()
    p.parent.delete(recurse=True)
    assert not p.exists()

def test_delete_key_non_existent():
    p=RegPath(r'HKCU\Software\winreglib\test')/'nonExistent'
    assert not p.exists()
    p.delete()
    assert not p.exists()
