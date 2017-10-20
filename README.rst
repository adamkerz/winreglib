=========
winreglib
=========

A Pathlib style object oriented interface to the Windows Registry

Examples::

    from winreglib import RegPath
    # enumerate keys
    p=RegPath(r'HKLM\Software')
    for k in p.subkeys():
        print(k.name)

    # set a value (creates keys and values as required)
    new_path=(p/'winreglib')
    new_path.value('test').set('apples')
