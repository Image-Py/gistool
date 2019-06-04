from imagepy.plugins.gistool.gis import geo_util, geo_struct
from imagepy import IPy
from imagepy.core import ImagePlus
from imagepy.core.engine import Simple
from imagepy.core.manager import ImageManager
import numpy as np

class RasterCombine(Simple):
    title = 'Raster Combine'
    note = ['8-bit', '16-bit', 'int']
    
    para = {'fragments':None, 'step':10}
    
    view = [('img', 'fragments', 'fragments', ''),
            (int, 'step', (1,100), 0, 'step', '')] 
            
    #process
    def run(self, ips, imgs, para = None):
        if not('prj' in ips.data and 'trans' in ips.data):
            return IPy.alert('need projection and transform matrix!')
        objs = ImageManager.get(para['fragments'])
        if not('prjs' in objs.data and 'trans' in objs.data):
            return IPy.alert('need projection and transform matrix!')

        goal = geo_struct.Raster(imgs, ips.data['prj'], ips.data['trans'])
        objs = zip(objs.imgs, objs.data['prjs'], objs.data['trans'])
        rasters = [geo_struct.Raster([i[0]], i[1], i[2]) for i in objs]
        rst = geo_util.rasters2one(rasters, goal, para['step'])

        ips = ImagePlus(rst.imgs, ips.title+'-combine')
        ips.data['prj'], ips.data['trans'] = goal.prj, goal.m
        IPy.show_ips(ips)

class NDVI(Simple):
    title = 'Count NDVI'
    note = ['all']
    
    para = {'b1':None, 'b2':None}
    
    view = [('img', 'b1', 'b1', ''),
            ('img', 'b2', 'b2', '')] 
            
    #process
    def run(self, ips, imgs, para = None):
        ips1 = ImageManager.get(para['b1'])
        ips2 = ImageManager.get(para['b2'])
        imgs = []
        for i in range(len(ips1.imgs)):
            b2, b1 = ips2.imgs[i], ips1.imgs[i]
            b1 = np.clip(b1, 1, 1e8, out=b1)
            b2 = np.clip(b2, 1, 1e8, out=b2)
            ndvi = (((b2-b1)/(b2+b1)+1)/2*255+0.5).astype(np.uint8)
            imgs.append(ndvi)
        ips = ImagePlus(imgs, ips1.title+'-ndvi')
        ips.data = ips1.data
        IPy.show_ips(ips)

plgs = [RasterCombine, NDVI]