def PIcon(icon):#{{{1
    try:
        from PyKDE4.kdeui import KIcon
        return KIcon(icon)
    except ImportError:
        from PyQt4.QtGui import QIcon
        return QIcon('icons/%s.png' % icon)
