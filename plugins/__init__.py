import os
_pluginList = []
for item in os.listdir(__path__[0]):
    if not item.startswith('_') and item.endswith('.py'):
        item = item[:-3]
        _pluginList.append(item)
_imports = __import__('plugins', fromlist=_pluginList)
allPlugins = []
for module in _pluginList:
    locals()[module] = getattr(_imports, module)
    allPlugins.append(getattr(_imports, module))
del _pluginList
del _imports
del item
del module
del os
