from imagepy.core.engine import Table
from imagepy.plugins.gistool.gis import geo_util
from imagepy import IPy
from imagepy.core import ImagePlus

class Shp2Raster(Table):
	title = 'Shapefile To Raster'

	para = {'scale':1000, 'margin':0, 'mode':'lab'}
		
	view = [(int, 'scale', (1,1e8), 3, 'scale', 'unit/pix'),
			(float, 'margin', (0, 0.3), 2, 'margin', ''),
			(list, 'mode', ['label', 'line'], str, 'mode', '')]

	def run(self, tps, snap, data, para=None):
		raster = geo_util.shp2raster(data, para['scale'], margin=para['margin'], style='lab')
		ips = ImagePlus(raster.imgs, tps.title)
		ips.data['prj'], ips.data['trans'] = raster.prj, raster.m
		IPy.show_ips(ips)

plgs = [Shp2Raster]