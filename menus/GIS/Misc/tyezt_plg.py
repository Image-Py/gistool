from imagepy.core.engine import Free
from imagepy import IPy
import pygis.draw as gisdraw
import pygis.io as gisio
import pandas as pd
import geopandas as gpd
import numpy as np
from skimage.io import imsave, imread
import pyproj
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
import os.path as osp

def draw(report, date, text, point=False, limit=True, check=False):
    #report = './20190705.xlsx'
    #date = 10.0

    root, name = osp.split(report)
    rpt = pd.read_excel(report, encoding='gbk')
    
    month, day = int(date), int(round(date%1*100))

    rpt['province'] = rpt['省']
    rpt['city'] = rpt['市']
    rpt['city'].fillna('市辖区', inplace=True)
    rpt['county'] = rpt['县']
    rpt['time'] = rpt['首次查见日期'].apply(lambda a:a.month+a.day/100)

    bound = gpd.read_file(root+'/data/陆地国界.shp')
    back = gpd.read_file(root+'/data/地理区划_大类.shp')
    line = gpd.read_file(root+'/data/地理区划_line.shp')
    river = gpd.read_file(root+'/data/我国主要河流.shp')
    area = gpd.read_file(root+'/data/全国县级行政区划2015.shp')
    rec = gpd.read_file(root+'/data/南海-矩形.shp')
    pro = gpd.read_file(root+'/data/省界_2015.shp')
    rpt = rpt[rpt['time']<=date]
    rpt['long'] = rpt['province']+'_'+rpt['county']
    area['long'] = area['Province']+'_'+area['County']

    rptset = set(rpt['long'])
    areaset = set(area['long'])

    outarea = sorted(list(rptset-areaset))
    outdf = pd.DataFrame(outarea, columns=['new area'])
    if check: return outdf
    new_back = back.to_crs(rec.crs)
    new_line = line.to_crs(rec.crs)
    new_river = river.to_crs(rec.crs)
    new_bound = bound.to_crs(rec.crs)
    new_area = area.to_crs(rec.crs)
    new_pro = pro.to_crs(rec.crs)

    roi = new_area.merge(rpt[['long', 'time']], on='long', how='inner')

    roi_pro = new_pro#new_pro[np.array([i in roi['Province'].unique() for i in pro['Province']])]

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
                    [115,223,255],
                    [0  ,77 ,168],
                    [223,115,255]],# 9月
                    dtype=np.uint8)

    # 纸张
    paper = gisdraw.make_paper(new_back, (17538, 12400), margin=0.08)

    # 背景
    gisdraw.draw_polygon(paper, new_back, new_back['color_No_'].astype(int)+7, 0)
    gisdraw.draw_polygon(paper, new_back, 1, 10)

    # 国界
    gisdraw.draw_line(paper, new_bound, 2, 80)
    gisdraw.draw_line(paper, new_bound, 3, 10)

    # 灾区
    if point:
        roip = gpd.GeoDataFrame(roi.centroid.buffer(15000), columns=['geometry'], crs=roi.crs)
        gisdraw.draw_polygon(paper, roi, 2, 10)
    else: roip = roi
    gisdraw.draw_polygon(paper, roip, roi['time'].astype(int)+12, 0)
    gisdraw.draw_polygon(paper, roip, 1, 5)

    # 入侵省份
    gisdraw.draw_polygon(paper, roi_pro, 1, 15)
    # 南北东西界线， 河流
    gisdraw.draw_line(paper, new_river, 7, 30)
    if limit: gisdraw.draw_line(paper, new_line, new_line['class'].astype(int)+3, 30)

    # 入侵省份文字
    gisdraw.draw_lab(paper, roi_pro, 'name', 1, (root+'/fonts/simsun.ttc', 180), 'center')

    # 比例尺
    gisdraw.draw_unit(paper, 3000, -500, 0.3, 150, (root+'/fonts/times.ttf', 200), 1, 'km', 20)

    # 指北针
    gisdraw.draw_N(paper, -1800, 1200, (root+'/fonts/msyh.ttc', 300), 20, 400, 1)

    bins = list(np.bincount(rpt['time'])[1:])+['-']*10
    c_or_r = ['rect', 'circle'][point]
    body = [('图例', root+'/fonts/simkai.ttf', 300),
            ('line', 7, '主要河流'),
            ('rect', 0, '省界'),
            ('入侵县(区)', root+'/fonts/simsun.ttc', 240),
            (c_or_r, 21, '9月(%s个)'%bins[8]),
            (c_or_r, 20, '8月(%s个)'%bins[7]),
            (c_or_r, 19, '7月(%s个)'%bins[6]),
            (c_or_r, 18, '6月(%s个)'%bins[5]),
            (c_or_r, 17, '5月(%s个)'%bins[4]),
            (c_or_r, 16, '4月(%s个)'%bins[3]),
            (c_or_r, 15, '3月(%s个)'%bins[2]),
            (c_or_r, 14, '2月(%s个)'%bins[1]),
            (c_or_r, 13, '1月(%s个)'%bins[0]),
            ('气象地理区划', root+'/fonts/simsun.ttc', 240),
            ('line', 4, '一级区划线'),
            ('line', 5, '二级区划线'),
            ('line', 6, '二级区划线')]

    body = body[:4] + body[-4-month:]
    if not limit: body = body[:-2]

    # 图例
    gisdraw.draw_style(paper, 800, -500, body, mar=(100, 100), recsize=(500,250,5),
                       font=(root+'/fonts/simsun.ttc', 240, 1), box=20)

    # 标题
    gisdraw.draw_text(paper, '我国草地贪夜蛾入侵分布示意图\n截至2019年%d月%d日'%(month, day),
                      (800,570), 1, (root+'/fonts/simkai.ttf', 480), 'lt', 'center')

    # 标尺
    paper[-400:] = 0
    gisdraw.draw_ruler(paper, 600, 400, -600, -400, 5, {'init': 'epsg:4326'}, (root+'/fonts/times.ttf', 200), 1, 20, 100)

    prj1, prj2 = pyproj.CRS({'init': 'epsg:4326'}), pyproj.CRS(rec.crs)
    ct = pyproj.Transformer.from_crs(prj1, prj2)
    print(ct.transform(125.87, 27.7))

    #https://www.cnblogs.com/arxive/p/6103358.html?utm_source=itdadao&utm_medium=referral
    rec_lt = [[4072223.5615089145], [2546481.2812095657]]
    rec_rb = [[5762914.442890676], [67330.48957465217]]
    new_lt = [[5948691], [3028251]]
    loc = np.dot(np.linalg.inv(paper.mat[:,1:]), new_lt-paper.mat[:,:1])
    offset = rec_lt - np.dot(paper.mat[:,1:]*2, loc)
    new_m = np.hstack((offset, paper.mat[:,1:]*2))

    paper.mat = new_m
    lt = np.dot(np.linalg.inv(paper.mat[:,1:]), rec_lt-paper.mat[:,:1])
    rb = np.dot(np.linalg.inv(paper.mat[:,1:]), rec_rb-paper.mat[:,:1])


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
    if point:
        clip_roip = gpd.GeoDataFrame(clip_roi.centroid.buffer(10000), columns=['geometry'], crs=clip_roi.crs)
        gisdraw.draw_polygon(paper, clip_roi, 2, 5)
    else: clip_roip = clip_roi
    gisdraw.draw_polygon(paper, clip_roip, clip_roi['time'].astype(int)+12, 0)
    gisdraw.draw_polygon(paper, clip_roip, 2, 5)

    clip_pro = gpd.overlay(rec, roi_pro)
    gisdraw.draw_lab(paper, clip_pro, 'name', 1, (root+'/fonts/simsun.ttc', 120), 'center')

    gisdraw.draw_ruler(paper, int(lt[0]), int(lt[1]), int(rb[0]), int(rb[1]), 5,
                       {'init': 'epsg:4326'}, (root+'/fonts/times.ttf', 120), 1, 10, 50)

    gisdraw.draw_text(paper, '南海诸岛', (-2100,-1100), 1, (root+'/fonts/simkai.ttf', 240), 'lt')

    #mskimg = np.load(root+'/data/mark.npy')
    mskimg = imread(root+['/data/mark2.png','/data/mark1.png'][limit])

    gisdraw.draw_text(paper, '\n'.join(text), (3000,-1500), 1, (root+'/fonts/simsun.ttc', 200), 'lb', 'left')
    #print(mskimg.shape)
    rgb = lut[paper]
    del bound, back, line, river, area, rec, pro
    del rpt, new_back, new_line, new_river, new_bound, new_area, new_pro
    del roi, roi_pro, clip_back
    gisdraw.draw_mask(rgb, mskimg)
    del mskimg, paper
    imsave(root+'/imgs/2019-%.2d-%.2d.png'%(month, day), rgb)
    return rgb

class Plugin(Free):
    title = '草地贪夜蛾制图'

    para = {'path':'', 'time':0.0, 'check':False, 'line':True, 'type':'area', 
        't1':'注：'+' '*40, 't2':'','t3':'','t4':'','t5':'','t6':'','t7':'','t8':''}

    def load(self):
        self.filt = ['xlsx']
        return True

    def show(self):
        filt = '|'.join(['%s files (*.%s)|*.%s'%(i.upper(),i,i) for i in self.filt])
        rst = IPy.getpath('Import sequence', filt, 'open', self.para)
        if not rst: return rst

        self.view = [(float, 'time', (1, 12.31), 2, '入侵时间', '(月.日)用小数表示'),
                     (bool, 'check', '县名称检查'),
                     (bool, 'line', '显示2级区划线'),
                     (list, 'type', ['点图', '面图'], str, '灾区标识', ''),
                     ('lab', '', '='*20+' 以下是备注 '+'='*20),
                     (str, 't1', '备注1：', ''),
                     (str, 't2', '备注2：', ''),
                     (str, 't3', '备注3：', ''),
                     (str, 't4', '备注4：', ''),
                     (str, 't5', '备注5：', ''),
                     (str, 't6', '备注6：', ''),
                     (str, 't7', '备注7：', ''),
                     (str, 't8', '备注8：', '')]
        return IPy.get_para(self.title, self.view, self.para)

    def run(self, para = None):
        path = para['path']
        date = para['time']
        check = para['check']
        line = para['line']
        point = para['type'] == '点图'
        text = [para['t%d'%i] for i in (1,2,3,4,5,6,7,8)]
        text = [i for i in text if len(i)>1]

        try:
            rst = draw(path, date, text, point, line, check)
            if check: IPy.show_table(rst, '新增地名列表')
            else: IPy.show_img([rst], '草地贪夜蛾分布示意图')
        except: 
            IPy.alert('请检查数据格式！')