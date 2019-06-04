from imagepy.core.util import fileio
from ....gis import geo_struct
from imagepy import IPy
from imagepy.core import ImagePlus
from imagepy.core.engine import Free
import os.path as osp
import gdal, numpy as np
from glob import glob

class OpenShp(fileio.Reader):
    title = 'Shapefile Open'
    filt = ['SHP']

    #process
    def run(self, para = None):
        a = geo_struct.read_shp(para['path'], 'gbk')
        fp, fn = osp.split(para['path'])
        fn, fe = osp.splitext(fn)
        IPy.show_table(a, fn)

class OpenHdf(fileio.Reader):
    title = 'Hdf Open'
    filt = ['HDF']

    #process
    def run(self, para = None):
        fp, fn = osp.split(para['path'])
        fn, fe = osp.splitext(fn)
        raster = geo_struct.read_hdf(para['path'])
        ips = ImagePlus(raster.imgs, fn)
        IPy.show_ips(ips)

        ips.data['prj'] = raster.prj
        ips.data['trans'] = raster.m

class OpenHdfS(Free):
    title = 'HDF Sequence'
    para = {'path':'', 'start':0, 'end':0, 'step':1, 'chans':[], 'title':'sequence'}

    def load(self):
        self.filt = ['HDF']
        return True

    def show(self):
        filt = '|'.join(['%s files (*.%s)|*.%s'%(i.upper(),i,i) for i in self.filt])
        rst = IPy.getpath('Import sequence', filt, 'open', self.para)
        if not rst: return rst
        ds = gdal.Open(self.para['path'])
        sds = ds.GetSubDatasets()
        files = self.getfiles(self.para['path'])
        nfs = len(files)
        self.para['end'] = nfs-1
        self.view = [(str, 'title', 'Title',''), 
                     (int, 'start', (0, nfs-1), 0, 'Start', '0~{}'.format(nfs-1)),
                     (int, 'end',   (0, nfs-1), 0, 'End', '0~{}'.format(nfs-1)),
                     (int, 'step',  (0, nfs-1), 0, 'Step', ''),
                     ('chos', 'chans', [i[0] for i in sds], 'Channels')]
        return IPy.get_para('Import sequence', self.view, self.para)

    def getfiles(self, name):
        p,f = osp.split(name)
        s = p+'/*.'+name.split('.')[-1]
        return glob(s)

    def readimgs(self, names, idx, raster):
        rasters = []
        for i in range(len(names)):
            self.progress(i, len(names))
            rs =  geo_struct.read_hdf(names[i], idx)
            if rs.imgs[0].shape!=raster.imgs[0].shape: continue
            if rs.imgs[0].dtype!=raster.imgs[0].dtype: continue
            rasters.append(rs)
        return rasters

    #process
    def run(self, para = None):
        if len(para['chans']) == 0: return
        #try:
        ds = gdal.Open(para['path'])
        sds = ds.GetSubDatasets()
        idx = [i[0] for i in sds]
        idx = [idx.index(i) for i in para['chans']]
        raster =  geo_struct.read_hdf(para['path'], idx)
        #except:
        #    IPy.alert('unknown img format!')
        #    return
        
        files = self.getfiles(para['path'])
        files.sort()
        rasters = self.readimgs(files[para['start']:para['end']+1:para['step']], idx, raster)
        for i in range(len(idx)):
            imgs, ms, prjs = [], [], []
            for rs in rasters:
                imgs.append(rs.imgs[i])
                ms.append(rs.m)
                prjs.append(rs.prj)
            ips = ImagePlus(imgs, '%s-%s'%(para['title'],idx[i]))
            ips.data['trans'] = ms
            ips.data['prjs'] = prjs
            IPy.show_ips(ips)

plgs = [OpenShp, OpenHdf, OpenHdfS]