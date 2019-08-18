from imagepy.core.engine import Table
from imagepy import IPy
import geopandas as gpd
import geonumpy.util as gutil


class ShowCRS(Table):
	title = 'Show WKT CRS'

	def run(self, tps, snap, data, para = None):
		if not isinstance(data, gpd.GeoDataFrame):
			return IPy.alert('geo table needed!')
		IPy.show_log(tps.title, gutil.makecrs(data.crs).to_wkt())

class EPSG(Table):
	title = 'Project By EPSG'
	para = {'code':4326}
	view = [(int, 'code', (1000, 9999), 0, 'epsg', '')]

	def run(self, tps, snap, data, para = None):
		if not isinstance(data, gpd.GeoDataFrame):
			return IPy.alert('geo table needed!')
		newdata = data.to_crs(para['code'])
		IPy.show_table(newdata, tps.title+'-%d'%para['code'])

class WKT(Table):
	title = 'Project By WKT'
	para = {'path':''}

	def show(self):
		filt = '|'.join(['%s files (*.%s)|*.%s'%(i.upper(),i,i) for i in ['PRJ']])
		return IPy.getpath('Build idx', filt, 'open', self.para)

	def run(self, tps, snap, data, para = None):
		if not isinstance(data, gpd.GeoDataFrame):
			return IPy.alert('geo table needed!')
		with open(para['path']) as f:
			newdata = data.to_crs(f.read())
			IPy.show_table(newdata, tps.title+'-prj')

plgs = [ShowCRS, EPSG, WKT]