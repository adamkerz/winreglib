# winreglib - A Pathlib style object oriented interface to the Windows Registry

Examples:

    > from winreglib import RegPath
    > p=RegPath(r'HKLM\Software')
    > for k in p.subkeys():
    >     print(k)
