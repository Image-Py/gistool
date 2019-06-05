from .geo_struct import *
from .geo_prj import *
import gdal#, cv2
from PIL import Image, ImageDraw
from osgeo import osr, ogr
from time import time
from numpy.linalg import inv
from scipy.ndimage import map_coordinates
from shapely.affinity import affine_transform
from shapely.ops import transform
from skimage.io import imsave
from shapely.geometry import GeometryCollection

def shp2raster(shape, scale, margin=0.05, value=0, width=0, dtype=np.uint8, bounds=None):
    shapes = shape['shape'].values
    kmargin = margin/(1-2*margin)
    geoms = list(shape['shape'].values)
    bounds = bounds or GeometryCollection(geoms).bounds
    l,t,r,b = bounds
    w,h = r-l, b-t
    if isinstance(scale, tuple):
        W, H = np.array(scale) * (1-margin*2)
        scale = max(w/W, h/H)
    offsetx, offsety = l-w*kmargin, b+h*kmargin
    shp = np.array((h,w))*(1+(kmargin*2))/scale
    rst = np.zeros(shp.astype(np.int), dtype=dtype)
    m = [1/scale, 0, 0, -1/scale, -offsetx/scale, offsety/scale]
    img = Image.fromarray(rst)
    draw = ImageDraw.Draw(img)
    for i in range(len(shapes)):
        gs = affine_transform(shapes[i], m)
        for g in gs:
            pts = np.array(g.exterior.xy).T.astype(np.int).ravel()
            if width==0 and value==0: draw.polygon(list(pts), i+1)
            if width==0 and value!=0: draw.polygon(list(pts), value)
            if width!=0: draw.line(list(pts), value, width)
        
        #pgs = [np.array(g.exterior.xy).T.astype(np.int) for g in gs]
        #if style=='lab':cv2.fillPoly(rst, pgs, i+1)
        #else: cv2.drawContours(rst, pgs, -1, 255, style)
    rst = np.array(img)
    m = np.array([offsetx, scale, 0, offsety, 0, -scale]).reshape((2,3))
    return (rst, shape.prj, m)

def mp2pm(boxs, m1, prj1, prj2, m2, t1 = lambda x:x, t2 = lambda x:x):
    box = t1(np.dot(m1[:,1:], np.array(boxs).T) + m1[:,:1])
    ct = osr.CoordinateTransformation(prj1, prj2)
    box = t2(np.array(ct.TransformPoints(box.T)).T)
    return np.dot(inv(m2[:,1:]), box[:2]-m2[:,:1]).T
        
def raster2des(raster, des, step=10, out='in'):
    imgd, prjd, md = des
    if out != 'in': imgd = np.zeros(imgd.shape, dtype=out)
    img, prjs, ms = raster
    hs, ws = img.shape
    xx = np.linspace(0,ws,100).reshape((-1,1))*[1,0]
    yy = np.linspace(0,hs,100).reshape((-1,1))*[0,1]
    xy = np.vstack((xx, xx+[0,hs+1], yy, yy+[ws+1,0]))
    xy = mp2pm(xy, ms, prjs, prjd, md).astype(np.int)
    
    (left, top), (right, bot) = xy.min(axis=0)-step, xy.max(axis=0)+step
    left, right = np.clip((left, right), 0, imgd.shape[1])
    top, bot = np.clip((top, bot), 0, imgd.shape[0])
    hb, wb = bot-top, right-left

    block = np.ones((hb//step+2, wb//step+2))
    xy = np.array(np.where(block)).T*step+[top,left]
    xs, ys = mp2pm(xy[:,::-1], md, prjd, prjs, ms).T
    xs.shape = ys.shape = block.shape
    
    rc = np.array(np.where(np.ones((hb, wb))))/step
    xs = map_coordinates(xs, rc, cval=-100, order=1)
    ys = map_coordinates(ys, rc, cval=-100, order=1)
    vs = map_coordinates(img, np.array([ys, xs]), prefilter=False)
    vs = vs.reshape((hb, wb))
    sliced = imgd[top:bot, left:right]
    msk = vs>sliced
    sliced[msk] = vs[msk]
    return (imgd, prjd, md)

def rasters2des(rasters, des, step=10, out='auto'):
    if out == 'auto': 
        des = (np.zeros(des[0].shape, dtype=rasters[0][0].dtype), des[1], des[2])
    elif out != 'in': des = (np.zeros(des[0].shape, dtype=out), des[1], des[2])
    for raster in rasters: raster2des(raster, des, step)
    return des

'''
def rasters2one(rasters, des, step=10, t1 = lambda x:x, t2 = lambda x:x, output = None):
    total = time()
    channels = [np.zeros_like(des.imgs[0], i.dtype) for i in rasters[0].imgs]
    prjd, md = des.prj, des.m
    for rs in rasters:
        start = time()
        prjs, ms = rs.prj, rs.m
        hs, ws = rs.imgs[0].shape
        xx = np.linspace(0,ws,100).reshape((-1,1))*[1,0]
        yy = np.linspace(0,hs,100).reshape((-1,1))*[0,1]
        xy = np.vstack((xx, xx+[0,hs+1], yy, yy+[ws+1,0]))
        xy = mp2pm(xy, ms, prjs, prjd, md, t2=t2).astype(np.int)
        
        (left, top), (right, bot) = xy.min(axis=0)-step, xy.max(axis=0)+step
        left, right = np.clip((left, right), 0, des.imgs[0].shape[1])
        top, bot = np.clip((top, bot), 0, des.imgs[0].shape[0])
        hb, wb = bot-top, right-left

        block = np.ones((hb//step+2, wb//step+2))
        xy = np.array(np.where(block)).T*step+[top,left]
        xs, ys = mp2pm(xy[:,::-1], md, prjd, prjs, ms, t1=t1).T
        xs.shape = ys.shape = block.shape
        
        rc = np.array(np.where(np.ones((hb, wb))))/step
        xs = map_coordinates(xs, rc, cval=-100, order=1)
        ys = map_coordinates(ys, rc, cval=-100, order=1)
        for imgs, imgd in zip(rs.imgs, channels):
            vs = map_coordinates(imgs, np.array([ys, xs]), prefilter=False)
            vs = vs.reshape((hb, wb))
            sliced = imgd[top:bot, left:right]
            msk = vs>sliced
            sliced[msk] = vs[msk]
        # print('slice:', time()-start)
    # print('total time:', time()-total)
    return Raster(channels, des.prj, des.m)
'''

def get_bounds(shape, k=None):
    geoms = list(shape['shape'].values)
    box = GeometryCollection(geoms).bounds
    w, h = box[2] - box[0], box[3] - box[1]
    ox, oy = (box[2]+box[0])/2, (box[3]+box[1])/2
    if w/h > k: h = w/k
    else: w = h * k
    return (ox-w/2, oy-h/2, ox+w/2, oy+h/2)

def shape2one(shape, raster):
    m = np.array([[0,1,0],[0,0,1]])
    trans = lambda x, y : mp2pm(np.array([x, y]).T, m,
                                shape.prj, raster.prj, raster.m).T
    newshp = shape.copy()
    newshp.prj = raster.prj
    newshp['shape'] = [transform(trans, i) for i in shape['shape']]
    return newshp

def shape2prj(shape, prj):
    m = np.array([[0,1,0],[0,0,1]])
    t2 = lambda x: x#wgs84togcj02(x.T).T
    def trans(x, y):
        return mp2pm(np.array([x,y]).T, m, shape.prj, prj, m, t2=t2).T
    newshp = shape.copy()
    newshp.prj = prj
    newshp['shape'] = [transform(trans, i) for i in shape['shape']]
    return newshp

def shape2gaode(shape):
    wgs = osr.SpatialReference()
    wgs.SetWellKnownGeogCS('WGS84')
    m = np.array([[0,1,0],[0,0,1]])
    t2 = lambda x: x#wgs84togcj02(x.T).T
    def trans(x, y):
        return mp2pm(np.array([x,y]).T, m, shape.prj, wgs, m, t2=t2).T
    return Shape(transform(trans, shape.shape), wgs, shape.df)
    
def shape2gdweb(shape):
    def trans(x, y):
        return (gaode_adjust(np.array([x, y]).T)).T
    return Shape(transform(trans, shape.shape), shape.prj, shape.df)

def rasters2gaode(rasters, des, step=10):
    return rasters2one(
        rasters, des, step,
        lambda xy : gaode2wgs(xy.T).T,
        lambda xy : wgs2gaode(xy.T).T)

# wgs: 116.46706996,39.99188446, 116.473207,39.993202(

if __name__ == '__main__':
    shp = read_shp('../../tasks/country_china_wheat_2018/region.shp')
    from time import time
    start = time()
    raster = shp2raster(shp, 250, 0, style='lab')
    print(time()-start)
    plt.imshow(raster.imgs[0])
    plt.show()
    '''
    shp = shape2gaode(shp)
    shpw = shape2gdweb(shp)
    
    rst = shp2raster(shpw, 0.01, 0, style=1)
    write_tif(rst, 'china_wgs.tif')
    png = np.array([[0,0,0,0],[0,0,0,255]], dtype=np.uint8)[rst.imgs[0]//255]
    imsave('china.png', png)


    '''
