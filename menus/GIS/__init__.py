import os.path as osp
from imagepy import IPy
from imagepy.core.manager import ConfigManager

path = osp.abspath(osp.dirname(__file__))
ConfigManager.set('watermark', osp.join(path, '../../data/watermark.png'))

IPy.curapp.SetTitle('植被定量遥感分析')

# catlog = ['GIS Data IO', 'Shape Operater', 'Raster Operater', 'Draw', '-', 'Wheat', '-', 'Update GIS Toolkit']
catlog = ['GIS Data IO', '-', 'Shape CRS', 'Draw', '-', 'Match', 'Repair', '-', 'Map Viewer', 'Misc', 'Update GIS Toolkit']