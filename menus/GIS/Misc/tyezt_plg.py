from imagepy.core.engine import Free
from imagepy import IPy
import pygis.draw as gisdraw
import pygis.io as gisio
import pandas as pd
import geopandas as gpd
import numpy as np
from skimage.io import imsave
import pyproj
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
from skimage.io import imread
import os.path as osp

def draw(report, date):
    root, name = osp.split(report)
    print(root, name)
    rpt = pd.read_excel(root+'/上报表格.xlsx')
    month, day = int(date), int(date%1*100)

    bound = gpd.read_file(root+'/data/陆地国界.shp')
    back = gpd.read_file(root+'/data/地理区划_大类.shp')
    line = gpd.read_file(root+'/data/地理区划_line.shp')
    river = gpd.read_file(root+'/data/我国主要河流.shp')
    area = gpd.read_file(root+'/data/全国县级行政区划2015.shp')
    rec = gpd.read_file(root+'/data/南海-矩形.shp')
    pro = gpd.read_file(root+'/data/省界_2015.shp')

    rpt = rpt[rpt['time']<=date]
    #rpt['time'] = rpt['time'].apply(lambda x:int(x.split('月')[0]))
    rpt['long'] = rpt['province']+'_'+rpt['city']+'_'+rpt['county']
    area['long'] = area['Province']+'_'+area['City']+'_'+area['County']

    new_back = back.to_crs(rec.crs)
    new_line = line.to_crs(rec.crs)
    new_river = river.to_crs(rec.crs)
    new_bound = bound.to_crs(rec.crs)
    new_area = area.to_crs(rec.crs)
    new_pro = pro.to_crs(rec.crs)

    roi = new_area.merge(rpt[['long', 'time']], on='long', how='inner')

    roi_pro = new_pro[np.array([i in roi['Province'].unique() for i in pro['Province']])]

    lut = np.array([[255,255,255], # 底色
                    [0  ,0  ,0  ], # 省界
                    [156,156,156], # 国界粗
                    [0  ,0  ,0  ], # 国界细
                    [0  , 77,168], # 一级区划
                    [169,  0,230], # 南北部
                    [56 ,168,0  ], # 东西部
                    [10 ,147,252], # 河流
                    [254,255,229], # =======
                    [236,255,229],
                    [254,237,204], # 底图颜色
                    [228,246,255],
                    [242,243,243], # =======
                    [168,0  ,0  ], # 1月
                    [255,0  ,0  ],
                    [255,127,127],
                    [252,196,76 ],
                    [250,250,100],
                    [152,230,0  ],
                    [190,232,255],
                    [0  ,197,255],
                    [223,115,255]],# 9月
                   dtype=np.uint8)

    roi = roi[roi['time']<=6]
    # 纸张
    paper = gisdraw.make_paper(new_back, (17538, 12400), margin=0.08)

    '''
    rgb = lut[paper[0]]
    imsave('rst.png', rgb)
    print('here')
    input()
    '''
    # 背景
    gisdraw.draw_polygon(paper, new_back, new_back['color_No_'].astype(int)+7, 0)
    gisdraw.draw_polygon(paper, new_back, 1, 10)

    # 国界
    gisdraw.draw_line(paper, new_bound, 2, 80)
    gisdraw.draw_line(paper, new_bound, 3, 10)

    # 灾区
    gisdraw.draw_polygon(paper, roi, roi['time']+12, 0)
    gisdraw.draw_polygon(paper, roi, 2, 10)

    # 入侵省份
    gisdraw.draw_polygon(paper, roi_pro, 1, 15)
    # 南北东西界线， 河流
    gisdraw.draw_line(paper, new_river, 7, 30)
    gisdraw.draw_line(paper, new_line, new_line['class'].astype(int)+3, 30)

    # 入侵省份文字
    gisdraw.draw_lab(paper, roi_pro, 'name', 1, ('simsun.ttc', 180), 'center')

    # 比例尺
    gisdraw.draw_unit(paper, 3000, -500, 0.3, 150, ('times.ttf', 200), 1, 'km', 20)

    # 指北针
    gisdraw.draw_N(paper, -1800, 1200, ('msyh.ttc', 300), 20, 400, 1)

    body = [('图例', 'simkai.ttf', 300),
            ('line', 7, '主要河流'),
            ('rect', 0, '入侵省份'),
            ('入侵县(区)', 'simsun.ttc', 240),
            ('rect', 21, '9月份入侵'),
            ('rect', 20, '8月份入侵'),
            ('rect', 19, '7月份入侵'),
            ('rect', 18, '6月份入侵'),
            ('rect', 17, '5月份入侵'),
            ('rect', 16, '4月份入侵'),
            ('rect', 15, '3月份入侵'),
            ('rect', 14, '2月份入侵'),
            ('rect', 13, '1月份入侵'),
            ('气象地理区划', 'simsun.ttc', 240),
            ('line', 4, '一级区划线'),
            ('line', 5, '二级区划线'),
            ('line', 6, '二级区划线')]

    body = body[:4] + body[-4-month:]

    # 图例
    gisdraw.draw_style(paper, 800, -500, body, mar=(100, 100), recsize=(500,250,30),
                       font=('simsun.ttc', 240, 1), box=20)

    # 标题
    gisdraw.draw_text(paper, '我国草地贪夜蛾入侵分布示意图\n截至2019年%d月%d日'%(month, day),
                      (800,570), 1, ('simkai.ttf', 480), 'lt')

    # 标尺
    paper[0][-400:] = 0
    gisdraw.draw_ruler(paper, 600, 400, -600, -400, 5, {'init': 'epsg:4326'}, ('times.ttf', 200), 1, 20, 100)

    prj1, prj2 = pyproj.CRS({'init': 'epsg:4326'}), pyproj.CRS(rec.crs)
    ct = pyproj.Transformer.from_crs(prj1, prj2)
    print(ct.transform(125.87, 27.7))

    #https://www.cnblogs.com/arxive/p/6103358.html?utm_source=itdadao&utm_medium=referral
    rec_lt = [[4072223.5615089145], [2546481.2812095657]]
    rec_rb = [[5762914.442890676], [67330.48957465217]]
    new_lt = [[5948691], [3028251]]
    loc = np.dot(np.linalg.inv(paper[2][:,1:]), new_lt-paper[2][:,:1])
    offset = rec_lt - np.dot(paper[2][:,1:]*2, loc)
    new_m = np.hstack((offset, paper[2][:,1:]*2))

    paper = (paper[0], paper[1], new_m)
    lt = np.dot(np.linalg.inv(paper[2][:,1:]), rec_lt-paper[2][:,:1])
    rb = np.dot(np.linalg.inv(paper[2][:,1:]), rec_rb-paper[2][:,:1])


    clip_back = gpd.overlay(rec, new_back)
    gisdraw.draw_polygon(paper, clip_back, clip_back['color_No_'].astype(int)+7, 0)
    gisdraw.draw_polygon(paper, gpd.overlay(rec, new_pro), 1, 10)

    geom = rec['geometry'][0]
    lines = [geom.intersection(i) for i in new_bound['geometry'] if i.intersects(geom)]
    clip_bound = gpd.GeoDataFrame(lines, columns=['geometry'])
    clip_bound.crs = rec.crs
    gisdraw.draw_line(paper, clip_bound, 2, 50)
    gisdraw.draw_line(paper, clip_bound, 3, 10)

    clip_roi = gpd.overlay(rec, roi)
    gisdraw.draw_polygon(paper, clip_roi, clip_roi['time']+12, 0)
    gisdraw.draw_polygon(paper, clip_roi, 2, 5)

    clip_pro = gpd.overlay(rec, roi_pro)
    gisdraw.draw_lab(paper, clip_pro, 'name', 1, ('simsun.ttc', 120), 'center')

    gisdraw.draw_ruler(paper, int(lt[0]), int(lt[1]), int(rb[0]), int(rb[1]), 5,
                       {'init': 'epsg:4326'}, ('times.ttf', 120), 1, 10, 50)

    gisdraw.draw_text(paper, '南海诸岛', (-2100,-1100), 1, ('simkai.ttf', 240), 'lt')

    rgb = lut[paper[0]]
    gisdraw.draw_mask(rgb, imread(root+'/data/mark.png'))
    imsave(root+'/imgs/2019-%.2d-%.2d.png'%(month, day), rgb)
    return rgb
    
    imsave(root+'rst.png', rgb)
    paper = [(rgb[:,:,i], paper[1], paper[2]) for i in (0,1,2)]
    gisio.write_tif(paper, 'rst.tif')

class Plugin(Free):
    title = '草地贪夜蛾制图'

    para = {'path':'', 'time':0.0}

    def load(self):
        self.filt = ['xlsx']
        return True

    def show(self):
        filt = '|'.join(['%s files (*.%s)|*.%s'%(i.upper(),i,i) for i in self.filt])
        rst = IPy.getpath('Import sequence', filt, 'open', self.para)
        if not rst: return rst

        self.view = [(float, 'time', (1, 12.31), 2, '入侵时间', '(月.日)用小数表示')]
        return IPy.get_para(self.title, self.view, self.para)

    def run(self, para = None):
        try:
            img = draw(para['path'], para['time'])
            IPy.show_img([img], '草地贪夜蛾分布示意图')
        except: 
            IPy.alert('请检查数据格式！')