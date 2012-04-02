"""
Package holding the user interface files for Pythagora.

The correct version of each UI is created depending on the availability of PyKDE.
"""

import sys
if '--nokde' in sys.argv:
    KDE = False
else:
    try:
        import PyKDE4
        KDE = True
        del PyKDE4
    except ImportError:
        KDE = False
del sys

def get_uis():
    import os
    uiList = []
    for item in os.listdir(__path__[0]):
        if not item.startswith('_') and item.endswith('.py'):
            uiList.append(item[:-3])

    if KDE:
        uiList = filter(lambda value: not value.endswith('_Qt'), uiList)
    else:
        uiList = filter(lambda value: value+'_Qt' not in uiList, uiList)

    imports = __import__('ui', fromlist=uiList)

    ui_forms = []
    for module in uiList:
        module = getattr(imports, module)
        items = dir(module)
        forms = filter(lambda value: value.startswith('Ui_'), items)
        for form in forms:
            form = getattr(module, form)
            name = form.__name__[3:]
        ui_forms.append((name, form))

    for ui in uiList:
        del globals()[ui]

    return ui_forms

for name, form in get_uis():
    locals()[name] = form

del get_uis
del name
del form

