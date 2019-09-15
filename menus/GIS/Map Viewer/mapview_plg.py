from imagepy.core.engine import Free
from imagepy import IPy

class Plugin(Free):
    title = 'Open Map Result'
    para = {'path':''}

    def show(self):
        filt = '|'.join(['%s files (*.%s)|*.%s'%(i.upper(),i,i) for i in ['htm','html']])
        return IPy.getpath('Open..', filt, 'open', self.para)

    def run(self, para=None):
        IPy.show_md('MapViewer', '', para['path'])