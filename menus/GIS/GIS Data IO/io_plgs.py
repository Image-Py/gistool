from imagepy.core.util import fileio
import geonumpy.io as gio
from imagepy import IPy
from imagepy.core import ImagePlus
from imagepy.core.engine import Free, Simple
import os.path as osp
import gdal, numpy as np
from glob import glob

from imagepy.core.util import tableio
from imagepy.core.manager import *

class OpenShp(fileio.Reader):
    title = 'Shapefile Open'
    filt = ['SHP']

    #process
    def run(self, para = None):
        a = gio.read_shp(para['path'], encoding='gbk')
        fp, fn = osp.split(para['path'])
        fn, fe = osp.splitext(fn)
        IPy.show_table(a, fn)

def show_shp(data, title):
    IPy.show_table(data, title)
    
ViewerManager.add('shp', show_shp)

write_shp = lambda path, data: gio.write_shp(data, path)
read_shp = lambda path: gio.read_shp(path)

ReaderManager.add('shp', read_shp, tag='tab')
WriterManager.add('shp', write_shp, tag='tab')

class OpenShp(tableio.Reader):
    title = 'Shapefile Open'
    filt = ['shp']

class WriteShp(tableio.Writer):
    title = 'Shapefile Write'
    filt = ['shp']

def open_raster(para):
    fp, fn = osp.split(para['path'])
    fn, fe = osp.splitext(fn)
    raster = gio.read_raster(para['path'])
    ips = IPy.show_img([raster], fn)

def write_raster(img, para):
    fp, fn = os.path.split(para['path'])
    fn, fe = os.path.splitext(fn)
    gio.write_tif(img, para['path'])

class OpenHdf(fileio.Reader):
    title = 'Geo Hdf Open'
    filt = ['HDF']

    def run(self, para = None):
        open_raster(para)

class SaveHdf(fileio.Writer):
    title = 'Geo Hdf Write'
    filt = ['HDF']

    def run(self, ips, imgs, para = None):
        write_raster(ips.img, para)

class OpenTif(fileio.Reader):
    title = 'Geo Tif Open'
    filt = ['TIF']

    def run(self, para = None):
        open_raster(para)

class SaveTif(fileio.Writer):
    title = 'Geo Tif Write'
    filt = ['TIF']

    def run(self, ips, imgs, para = None):
        write_raster(ips.img, para)

class OpenGeoSequence(Free):
    title = 'Geo Sequence Open'
    para = {'path':'', 'start':0, 'end':0, 'step':1, 'chans':[], 'title':'sequence'}

    def load(self):
        self.filt = ['HDF', 'TIF', 'TIFF']
        return True

    def show(self):
        filt = '|'.join(['%s files (*.%s)|*.%s'%(i.upper(),i,i) for i in self.filt])
        rst = IPy.getpath('Import sequence', filt, 'open', self.para)
        if not rst: return rst
        shp, prj, m, chans = gio.read_raster_box(self.para['path'])
        files = self.getfiles(self.para['path'])
        nfs = len(files)
        self.para['end'] = nfs-1
        self.view = [(str, 'title', 'Title',''), 
                     (int, 'start', (0, nfs-1), 0, 'Start', '0~{}'.format(nfs-1)),
                     (int, 'end',   (0, nfs-1), 0, 'End', '0~{}'.format(nfs-1)),
                     (int, 'step',  (0, nfs-1), 0, 'Step', ''),
                     ('chos', 'chans', chans, 'Channels')]
        return IPy.get_para('Import sequence', self.view, self.para)

    def getfiles(self, name):
        p,f = osp.split(name)
        s = p+'/*.'+name.split('.')[-1]
        return glob(s)

    def readimgs(self, names, idx, shp0):
        rasters = []
        for i,name in enumerate(names):
            self.progress(i, len(names))
            shp, prj, m, chans = gio.read_raster_box(name)
            if shp!=shp0: continue
            rs =  gio.read_raster(name, idx)
            rasters.append(rs)
        return rasters

    #process
    def run(self, para = None):
        if len(para['chans']) == 0: return
        shp, prj, m, chans = gio.read_raster_box(para['path'])
        idx = [chans.index(i) for i in para['chans']]
        print(para['chans'], idx, '==========')
        files = self.getfiles(para['path'])
        rasters = self.readimgs(files, idx, shp)
        IPy.show_img(rasters, para['title'])

class SaveGeoSequence(Simple):
    title = 'Geo Sequence Save'
    note = ['all']
    para = {'path':'','name':'','format':'png'}
    #para = {'path':'./','name':'','format':'png'}

    def load(self, ips):
        self.view = [(str, 'name', 'Name', ''),
            (list, 'format', ['TIF', 'HDF'], str, 'Format', '')]
        return True

    def show(self):
        self.para['name'] = self.ips.title
        rst = IPy.get_para('Save sequence', self.view, self.para)
        if not rst :return rst
        return IPy.getdir('Save sequence', '', self.para)

    #process
    def run(self, ips, imgs, para = None):
        path = para['path']+'/'+para['name']
        print(path)
        for i in range(len(imgs)):
            self.progress(i, len(imgs))
            name = '%s-%.4d.%s'%(path,i,para['format'])
            gio.write_tif(imgs[i], name)

plgs = [OpenShp, WriteShp, '-', OpenTif, SaveTif, '-', OpenHdf, SaveHdf, '-', OpenGeoSequence, SaveGeoSequence]