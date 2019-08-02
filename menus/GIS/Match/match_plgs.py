from imagepy import IPy
from imagepy.core.engine import Free, Simple, Table
from imagepy.core.manager import ImageManager
import os.path as osp
import pygis.match as gmt
from glob import glob

class BuildIdx(Free):
    title = 'Build Box Index'
    para = {'path':''}
    filt = ['HDF', 'TIF', 'TIFF']

    def show(self):
        filt = '|'.join(['%s files (*.%s)|*.%s'%(i.upper(),i,i) for i in self.filt])
        return IPy.getpath('Build idx', filt, 'open', self.para)

    #process
    def run(self, para = None):
        p, f = osp.split(para['path'])
        name, ext = osp.splitext(f)
        s = p+'/*'+ext
        gdf = gmt.build_index(glob(s))
        IPy.show_table(gdf, '%s-idx'%name)

class MatchIdx(Table):
    title = 'Match By Index'
    para = {'step':10, 'order':0, 'temp':None, 'chans':[]}
    
    view = [('img', 'temp', 'image', 'temp'),
            (int, 'step', (1, 100), 0, 'step', 'sample'),
            (int, 'order', (0,1), 0, 'order', 'inerpolate'),
            ()]

    def load(self, tps):
        self.view[3] = ('chos', 'chans', list(tps.data['channels'][0]), 'Channels')
        return True

    def run(self, tps, snap, data, para=None):
        img = ImageManager.get(para['temp']).img
        chans = list(data['channels'][0])
        chans = [chans.index(i) for i in para['chans']]
        nimg = gmt.match_idx(data, img, step=para['step'], order=para['order'], chan=chans)
        IPy.show_img([nimg], tps.title+'-match')

class MatchImgs(Simple):
    title = 'Match Images'
    note = ['all']

    para = {'temp':None, 'step':10, 'order':'nearest'}
    
    view = [('img', 'temp', 'temp', ''),
            (int, 'step', (1,100), 0, 'step', ''),
            (list, 'order', ['nearest', 'linear'], str, 'interpolate', '')] 
            
    #process
    def run(self, ips, imgs, para = None):
        temp = ImageManager.get(para['temp']).img
        order = {'nearest':0, 'linear':1}[para['order']]
        rst = gmt.match_multi(imgs, temp, step=para['step'], order=order)
        IPy.show_img([rst], ips.title+'-match')

plgs = [BuildIdx, MatchImgs, MatchIdx]