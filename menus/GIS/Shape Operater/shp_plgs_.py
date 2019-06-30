from imagepy.core.engine import Table
from ....gis import geo_util
from imagepy import IPy
from imagepy.core import ImagePlus

class Shp2Raster(Table):
	title = 'Shapefile To Raster'

	para = {'scale':1000, 'margin':0, 'value':0, 'width':0}
	
	view = [(int, 'scale', (1,1e8), 3, 'scale', 'unit/pix'),
			(float, 'margin', (0, 0.3), 2, 'margin', ''),
			(int, 'value', (0,255), 0, 'color', ''),
			(int, 'width', (0,10), 0, 'line widht', 'pix')]

	def run(self, tps, snap, data, para=None):
		raster = geo_util.shp2raster(data, para['scale'], margin=para['margin'], 
			value=para['value'], width=para['width'])
		ips = ImagePlus([raster[0]], tps.title)
		ips.data['prjs'], ips.data['trans'] = [raster[1]], [raster[2]]
		IPy.show_ips(ips)

plgs = [Shp2Raster]