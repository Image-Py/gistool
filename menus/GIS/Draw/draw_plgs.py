from imagepy.core.engine import Table, Free, Simple
from imagepy import IPy
from imagepy.core import ImagePlus
import numpy as np
from glob import glob
import geopandas as gpd
from imagepy.core.manager import ImageManager
import geonumpy.util as gutil
import geonumpy.io as gio
import geonumpy.draw as gdraw
import geonumpy as gnp

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

class DrawPolygon(Table):
	title = 'Draw Shp Polygon'

	para = {'paper':None, 'value':0, 'color':(0,0,0), 'field':None, 'lw':0}
	view = [('img', 'paper', 'paper', ''),
			(int, 'value', (-1, 1000), 0, 'value', ''),
			('lab', None, 'black color means use the value upon'),
			('color', 'color', 'color', ''),
			('lab', None, 'field will disable value and color'),
			('field', 'field', 'field', 'draw'),
			(int, 'lw', (0, 1024), 0, 'width', 'pix')]

	def run(self, tps, snap, data, para=None):
		ips = ImageManager.get(para['paper'])
		ips.snapshot()
		color = para['value'] if para['color']==(0,0,0) else para['color']
		if para['field'] != 'None': color = para['field']
		gdraw.draw_polygon(ips.img, data, color, para['lw'])
		ips.update()

class DrawLine(Table):
	title = 'Draw Shp LinsString'

	para = {'paper':None, 'value':0, 'color':(0,0,0), 'field':None, 'lw':0}
	view = [('img', 'paper', 'paper', ''),
			(int, 'value', (-1, 1000), 0, 'value', ''),
			('lab', None, 'black color means use the value upon'),
			('color', 'color', 'color', ''),
			('lab', None, 'field will disable value and color'),
			('field', 'field', 'field', 'draw'),
			(int, 'lw', (0, 1024), 0, 'width', 'pix')]

	def run(self, tps, snap, data, para=None):
		ips = ImageManager.get(para['paper'])
		ips.snapshot()
		color = para['value'] if para['color']==(0,0,0) else para['color']
		if para['field'] != 'None': color = para['field']
		gdraw.draw_line(ips.img, data, color, para['lw'])
		ips.update()

plgs = [MakePaper, DrawPolygon, DrawLine]