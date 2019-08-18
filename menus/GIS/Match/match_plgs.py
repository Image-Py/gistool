from imagepy import IPy
from imagepy.core.engine import Free, Simple, Table
from imagepy.core.manager import ImageManager, TableManager
import os.path as osp
import geonumpy.match as gmt
import geonumpy.util as gutil
import geonumpy as gnp
from glob import glob

class BuildIdx(Free):
    title = 'Build Bound Index'
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

class MakePaper(Table):
    title = 'Make Bound Image'
    note = ['snap', 'row_msk']
    para = {'type':'uint8', 'chan':1, 'width':1024, 'height':768, 'scale':0, 'mar':0}
    view = [(int, 'width', (100, 20480), 0, 'width', 'pix'),
            (int, 'height', (100, 20480), 0, 'height', 'pix'),
            (float, 'scale', (0, 1000), 2, 'scale', 'unit'),
            (float, 'mar', (0, 0.25), 2, 'margin', 'ratio'),
            (int, 'chan', (1, 1024), 0, 'channels', 'n'),
            (list, 'type', ['uint8', 'int16', 'int32', 'float32'], str, 'data', 'type')]

    def run(self, tps, snap, data, para=None):
        box = gutil.shp2box(snap, para['scale'] or (para['width'], para['height']), para['mar'])
        IPy.show_img([gnp.frombox(*box, para['chan'], dtype=para['type'])], tps.title+'-boximg')

class MatchImgDes(Simple):
    title = 'Match Img To Des'
    note = ['all']

    para = {'temp':None, 'step':10, 'order':'nearest', 'chans':[]}
    
    view = [('img', 'temp', 'temp', ''),
            (int, 'step', (1,100), 0, 'step', ''),
            (list, 'order', ['nearest', 'linear'], str, 'interpolate', ''),
            ()] 

    def load(self, ips):
        chans = ['Channel %s'%i for i in range(ips.get_nchannels())]
        self.view[-1] = ('chos', 'chans', chans, 'Channels')
        return True
            
    #process
    def run(self, ips, imgs, para = None):
        ipst = ImageManager.get(para['temp'])
        chans = ['Channel %s'%i for i in range(ips.get_nchannels())]
        chans = [chans.index(i) for i in para['chans']]
        order = {'nearest':0, 'linear':1}[para['order']]
        rst = gmt.match_multi(imgs, ipst.img, chans, step=para['step'], order=order)
        ipst.update()

class MatchImgShp(Simple):
    title = 'Match Img To Shp'
    note = ['all']

    para = {'temp':None, 'step':10, 'order':'nearest', 'chans':[], 
            'width':1024, 'height':768, 'scale':0, 'mar':0}
    
    view = [('tab', 'temp', 'temp', ''),
            (int, 'width', (100, 20480), 0, 'width', 'pix'),
            (int, 'height', (100, 20480), 0, 'height', 'pix'),
            (float, 'scale', (0, 1000), 2, 'scale', 'unit'),
            (float, 'mar', (0, 0.25), 2, 'margin', 'ratio'),
            (int, 'step', (1,100), 0, 'step', ''),
            (list, 'order', ['nearest', 'linear'], str, 'interpolate', ''),
            ()] 

    def load(self, ips):
        chans = ['Channel %s'%i for i in range(ips.get_nchannels())]
        self.view[-1] = ('chos', 'chans', chans, 'Channels')
        return True

    #process
    def run(self, ips, imgs, para = None):
        table = TableManager.get(para['temp']).get_subtab()
        box = gutil.shp2box(table, para['scale'] or (para['width'], para['height']), para['mar'])
        chans = ['Channel %s'%i for i in range(ips.get_nchannels())]
        chans = [chans.index(i) for i in para['chans']]
        order = {'nearest':0, 'linear':1}[para['order']]
        rst = gmt.match_multi(imgs, box, chans, step=para['step'], order=order)
        IPy.show_img([rst], ips.title+'-merge')

class MatchImgCrs(Simple):
    title = 'Match Img To Crs'
    note = ['all']

    para = {'step':10, 'order':'nearest', 'chans':[], 'crs':4326, 
            'wkt':'', 'width':1024, 'height':768, 'scale':0, 'mar':0}
    
    view = [(int, 'crs', (1000,9999), 0, 'crs', 'epsg'),
            ('path', 'wkt', 'prj file', ['prj']),
            ('lab', None, '=== select a prj file will disable the epsg code ==='),
            (int, 'width', (100, 20480), 0, 'width', 'pix'),
            (int, 'height', (100, 20480), 0, 'height', 'pix'),
            (float, 'scale', (0, 1000), 2, 'scale', 'unit'),
            (int, 'step', (1,100), 0, 'step', ''),
            (list, 'order', ['nearest', 'linear'], str, 'interpolate', ''),
            ()] 

    def load(self, ips):
        chans = ['Channel %s'%i for i in range(ips.get_nchannels())]
        self.view[-1] = ('chos', 'chans', chans, 'Channels')
        return True
            
    #process
    def run(self, ips, imgs, para = None):
        prj = None
        if para['wkt'] != '':
            with open(para['wkt']) as f:
                prj = f.read()
        crs = gutil.makecrs(prj or para['crs'])
        table = gmt.build_index(imgs).to_crs(crs)
        box = gutil.shp2box(table, para['scale'] or (para['width'], para['height']), para['mar'])
        chans = ['Channel %s'%i for i in range(ips.get_nchannels())]
        chans = [chans.index(i) for i in para['chans']]
        order = {'nearest':0, 'linear':1}[para['order']]
        rst = gmt.match_multi(imgs, box, chans, step=para['step'], order=order)
        IPy.show_img([rst], ips.title+'-merge')

class MatchIdxDes(Table):
    title = 'Match Idx To Des'
    para = {'temp':None, 'step':10, 'order':'nearest', 'chans':[]}
    
    view = [('img', 'temp', 'temp', ''),
            (int, 'step', (1,100), 0, 'step', ''),
            (list, 'order', ['nearest', 'linear'], str, 'interpolate', ''),
            ()] 

    def load(self, tps):
        self.view[-1] = ('chos', 'chans', list(tps.data['channels'][0]), 'Channels')
        return True

    def run(self, tps, snap, data, para=None):
        ipst = ImageManager.get(para['temp'])
        chans = list(data['channels'][0])
        chans = [chans.index(i) for i in para['chans']]
        order = {'nearest':0, 'linear':1}[para['order']]
        rst = gmt.match_idx(data, ipst.img, chans, step=para['step'], order=order)
        ipst.update()

class MatchIdxShp(Table):
    title = 'Match Idx To Shp'
    para = {'temp':None, 'step':10, 'order':'nearest', 'chans':[], 
            'width':1024, 'height':768, 'scale':0, 'mar':0}
    
    view = [('tab', 'temp', 'temp', ''),
            (int, 'width', (100, 20480), 0, 'width', 'pix'),
            (int, 'height', (100, 20480), 0, 'height', 'pix'),
            (float, 'scale', (0, 1000), 2, 'scale', 'unit'),
            (float, 'mar', (0, 0.25), 2, 'margin', 'ratio'),
            (int, 'step', (1,100), 0, 'step', ''),
            (list, 'order', ['nearest', 'linear'], str, 'interpolate', ''),
            ()] 

    def load(self, tps):
        self.view[-1] = ('chos', 'chans', list(tps.data['channels'][0]), 'Channels')
        return True

    def run(self, tps, snap, data, para=None):
        table = TableManager.get(para['temp']).get_subtab()
        box = gutil.shp2box(table, para['scale'] or (para['width'], para['height']), para['mar'])
        chans = list(data['channels'][0])
        chans = [chans.index(i) for i in para['chans']]
        order = {'nearest':0, 'linear':1}[para['order']]
        rst = gmt.match_idx(data, box, chans, step=para['step'], order=order)
        IPy.show_img([rst], tps.title+'-merge')

class MatchIdxCrs(Table):
    title = 'Match Idx To Crs'
    note = ['all']

    para = {'step':10, 'order':'nearest', 'chans':[], 'crs':4326, 
            'wkt':'', 'width':1024, 'height':768, 'scale':0, 'mar':0}
    
    view = [(int, 'crs', (1000,9999), 0, 'crs', 'epsg'),
            ('path', 'wkt', 'prj file', ['prj']),
            ('lab', None, '=== select a prj file will disable the epsg code ==='),
            (int, 'width', (100, 20480), 0, 'width', 'pix'),
            (int, 'height', (100, 20480), 0, 'height', 'pix'),
            (float, 'scale', (0, 1000), 2, 'scale', 'unit'),
            (int, 'step', (1,100), 0, 'step', ''),
            (list, 'order', ['nearest', 'linear'], str, 'interpolate', ''),
            ()] 

    def load(self, tps):
        self.view[-1] = ('chos', 'chans', list(tps.data['channels'][0]), 'Channels')
        return True
            
    #process
    def run(self, tps, snap, data, para=None):
        prj = None
        if para['wkt'] != '':
            with open(para['wkt']) as f:
                prj = f.read()
        crs = gutil.makecrs(prj or para['crs'])
        table = data.to_crs(crs)
        box = gutil.shp2box(table, para['scale'] or (para['width'], para['height']), para['mar'])
        chans = list(data['channels'][0])
        chans = [chans.index(i) for i in para['chans']]
        order = {'nearest':0, 'linear':1}[para['order']]
        rst = gmt.match_idx(data, box, chans, step=para['step'], order=order)
        IPy.show_img([rst], tps.title+'-merge')

plgs = [BuildIdx, MakePaper, '-', 
        MatchImgDes, MatchImgShp, MatchImgCrs, '-', 
        MatchIdxDes, MatchIdxShp, MatchIdxCrs]