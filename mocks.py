# Mocks for testing


class xbmc(object):

    class Keyboard(object):
        def __init__(self, placeholder, header, hidden):
            self.placeholder = placeholder
            self.header = header
            self.hidden = hidden

        def doModal(self):
            pass

        def isConfirmed(self):
            return True

        def getText(self):
            return 'bad'

    @staticmethod
    def log(msg, level):
        pass

    LOGERROR = 'ERROR'


class xbmcplugin(object):

    dir_items = []
    @staticmethod
    def addDirectoryItem(handle, url, listitem, isFolder):
        xbmcplugin.dir_items.append((handle, url, listitem, isFolder))

    @staticmethod
    def endOfDirectory(handle):
        pass


class xbmcgui(object):
    class ListItem(object):

        def __init__(self, caption):
            self.caption = caption

        def setInfo(self, type, infoLabels):
            self.type = type
            self.infoLabels = infoLabels
