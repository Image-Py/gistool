from imagepy.core.engine import Table, Free, Simple
from imagepy import IPy
from imagepy.core import ImagePlus
import numpy as np
from glob import glob
import geopandas as gpd
from imagepy.core.manager import TableManager
import pygis.util as gutil
import pygis.io as gio
import pygis.draw as gdraw

'''
单张绘图(图，表，定值、字段)
设定索引

多张绘图(图，索引，表，定值字段)
'''
class Empty(Table):
	title = 'Make Paper'
	note = ['snap', 'row_msk']
	para = {'width':1024, 'height':768, 'margin':0.1, 'type':'8-bit', 'key':None}
	
	view = [(int, 'width', (100,10240), 0, 'width', 'pix'),
			(int, 'height', (100,10240), 0, 'height', 'pix'),
			(float, 'margin', (0, 0.3), 2, 'margin', ''),
			(list, 'type', ['8-bit', '16-bit'], str, 'type', ''),
			('field', 'key', 'key', '')]

	def run(self, tps, snap, data, para=None):
		rsts = []
		dtype = {'8-bit':np.uint8, '16-bit':np.uint16}
		size = (para['width'], para['height'])
		if para['key'] == None:
			des = shp2raster(snap, size, para['margin'], 255, 0, dtype[para['type']])
			ips = ImagePlus([des[0]], tps.title)
			ips.data['prjs'], ips.data['trans'] = [des[1]], [des[2]]
			return IPy.show_ips(ips)
		index = snap[para['key']].unique()
		for i in range(len(index)):
			self.progress(i, len(index))
			prv = snap[snap[para['key']]==index[i]]
			des = shp2raster(prv, size, para['margin'], 255, 0, dtype[para['type']])
			rsts.append(des)
		imgs, prjs, ms = zip(*rsts)
		ips = ImagePlus(imgs, tps.title)
		ips.data['prjs'], ips.data['trans'] = prjs, ms
		IPy.show_ips(ips)

class Empty(Table):
	title = 'Make Paper'
	note = ['snap', 'row_msk']
	para = {'unit':100, 'margin':0.1, 'type':'8-bit'}
	
	view = [(float, 'unit', (0.01, 10240), 3, 'unit', ''),
			(float, 'margin', (0, 0.3), 2, 'margin', ''),
			(list, 'type', ['8-bit', '16-bit'], str, 'type', '')]

	def run(self, tps, snap, data, para=None):
		shape = data.loc[tps.rowmsk]
		dtype = {'8-bit':np.uint8, '16-bit':np.uint16}[para['type']]
		ground = gutil.make_paper(shape, para['unit'], margin=para['margin'], dtype=dtype)
		gdraw.draw_polygon(ground, shape, 255, 0)
		IPy.show_img([ground], tps.title)

class BuildIndex(Free):
	title = 'Build Geo Index'
	para = {'path':''}

	def show(self):
		return IPy.getdir('geoindex', '', self.para)

	def run(self, para):
		fs = glob(para['path']+'/*.tif')
		boxes, csr = [], {}
		for i in fs:
			print('build', i, '...')
			rs = gdal.Open(i)
			csr = rs.GetProjection()
			m = rs.GetGeoTransform()
			m = np.array(m).reshape((2,3))
			shp = (rs.RasterYSize, rs.RasterXSize)
			boxes.append([raster_box(shp, csr, m), i])
		gdf = gpd.GeoDataFrame(boxes, columns=['geometry', 'path'])
		print(csr)
		gdf.crs = makeprj(csr).ExportToProj4()
		IPy.show_table(gdf, 'geoindex')

class Merge(Simple):
	title = 'Merge To Des'
	note = ['8-bit', '16-bit']
	para = {'index':None}
	view = [('tab', 'index', 'index', 'table')]

	def run(self, ips, imgs, para=None):
		idx = TableManager.get(para['index']).data
		idx = idx.to_crs(ips.data['prjs'][0])
		s = 0
		for img, prj, m in zip(imgs, ips.data['prjs'], ips.data['trans']):
			img[:] = 0; s+= 1
			self.progress(s, len(imgs))
			for i in idx.index:
				box = raster_box(img.shape, prj, m)
				if box.intersects(idx.loc[i]['geometry']):
					raster = read_tif(idx.loc[i]['path'])[0]
					raster2des(raster, (img, prj, m), 10)

'''
class Scatter(Simple):
	title = 'Scatter Chart'
	para = {'x':None, 'y':None, 's':1, 'alpha':1.0, 'rs':None, 'c':(0,0,255),
		 'cs':None, 'cm':None, 'grid':False, 'title':''}
	asyn = False
	view = [(str, 'title', 'title', ''),
			('field', 'x', 'x data', ''),
			('field', 'y', 'y data', ''),
			(int, 's', (0, 1024), 0, 'size', 'pix'),
			('field', 'rs', 'radius column', 'optional'),
			(float, 'alpha', (0,1), 1, 'alpha', '0~1'),
			('color', 'c', 'color', ''),
			('field', 'cs', 'color column', 'optional'),
			('cmap', 'cm', 'color map'),
			(bool, 'grid', 'grid')]

	def run(self, tps, snap, data, para = None):
		rs = data[para['rs']] * para['s'] if para['rs'] != 'None' else para['s']
		cs = data[para['cs']] if para['cs'] != 'None' else '#%.2x%.2x%.2x'%para['c']
		cm = ColorManager.get_lut(para['cm'])/255.0
		cm = None if para['cs'] == 'None' else colors.ListedColormap(cm, N=256)
		data.plot.scatter(x=para['x'], y=para['y'], s=rs, c=cs, alpha=para['alpha'], 
			cmap=cm, grid=para['grid'], title=para['title'])
		plt.show()
'''
plgs = [Empty, BuildIndex, Merge]