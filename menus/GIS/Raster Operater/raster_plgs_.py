from ....gis import geo_util, geo_struct, geo_indicate
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
        if not('prjs' in ips.data and 'trans' in ips.data):
            return IPy.alert('need projection and transform matrix!')
        objs = ImageManager.get(para['fragments'])
        if not('prjs' in objs.data and 'trans' in objs.data):
            return IPy.alert('need projection and transform matrix!')
        goal = (imgs[0], ips.data['prjs'][0], ips.data['trans'][0])
        rasters = zip(objs.imgs, objs.data['prjs'], objs.data['trans'])
        
        rst = geo_util.rasters2des(list(rasters), goal, para['step'])
        
        ips = ImagePlus([rst[0]], ips.title+'-combine')
        ips.data['prjs'], ips.data['trans'] = [rst[1]], [rst[2]]
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
        rs1 = zip(ips1.imgs, ips1.data['prjs'], ips1.data['trans'])
        rs2 = zip(ips2.imgs, ips2.data['prjs'], ips2.data['trans'])
        rsts = []
        for r1, r2 in zip(rs1, rs2):
            rsts.append(geo_indicate.count_ndvi(r1, r2))
        imgs, prjs, trans = zip(*rsts)
        ips = ImagePlus(imgs, ips1.title+'-ndvi')
        ips.data['prjs'], ips.data['trans'] = prjs, trans
        IPy.show_ips(ips)

plgs = [RasterCombine, NDVI]