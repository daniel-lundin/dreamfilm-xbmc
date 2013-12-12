# Mocks for testing


class Xbmc(object):

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

    def log(self, msg, level):
        pass

    class Player(object):
        def play(self, *args, **kwargs):
            print 'playing'
            print ", ".join(args)

    LOGERROR = 'ERROR'
    LOGNOTICE = 'NOTICE'


class Xbmcplugin(object):

    def __init__(self):
        self.dir_items = []

    def addDirectoryItem(self, handle, url, listitem, isFolder):
        self.dir_items.append((handle, url, listitem, isFolder))

    def endOfDirectory(self, handle):
        pass


class Xbmcgui(object):
    class ListItem(object):

        def __init__(self, *args, **kwargs):
            if len(args) == 1:
                self.caption = args[0]

        def setInfo(self, type, infoLabels):
            self.type = type
            self.infoLabels = infoLabels

        def setThumbnailImage(self, thumb_url):
            pass
