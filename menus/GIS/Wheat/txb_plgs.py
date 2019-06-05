from ....gis import geo_util, geo_struct, geo_indicate
from ....plant import wheat
from imagepy import IPy
from imagepy.core import ImagePlus
from imagepy.core.engine import Simple
from imagepy.core.manager import ImageManager, TableManager
import numpy as np

class TXB(Simple):
    title = 'Tiao Xiu Bing'
    note = ['all']
    
    para = {'ndvi':None, 'lst':None, 'lab':None, 'area':None, 'df':None}
    
    view = [('img', 'ndvi', 'ndvi', ''),
            ('img', 'lst', 'lst', ''),
            ('img', 'lab', 'label', ''),
            ('img', 'area', 'area', ''),
            ('tab', 'df', 'data frame', '')] 
            
    def run(self, ips, imgs, para = None):
        ndvi = ImageManager.get(para['ndvi'])
        lst = ImageManager.get(para['lst'])
        lab = ImageManager.get(para['lab'])
        area = ImageManager.get(para['area'])

        ndvi = list(zip(ndvi.imgs, ndvi.data['prjs'], ndvi.data['trans']))[0]
        lst = list(zip(lst.imgs, lst.data['prjs'], lst.data['trans']))[0]
        lab = list(zip(lab.imgs, lab.data['prjs'], lab.data['trans']))[0]
        area = list(zip(area.imgs, area.data['prjs'], area.data['trans']))[0]
        df = TableManager.get(para['df']).data
        rst = wheat.get_grade(ndvi, lst, lab, area, df)
        ips = ImagePlus([rst[0]], 'tiao xiu bing')
        ips.data['prjs'], ips.data['trans'] = [rst[1]], [rst[2]]
        IPy.show_ips(ips)

plgs = [TXB]