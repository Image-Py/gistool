from osgeo import gdal, osr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapefile

from shapely.geometry import MultiPolygon, Polygon

class Shape:
    def __init__(self, shape, prj, df):
        self.shape, self.prj, self.df = shape, prj, df

class Raster:
    def __init__(self, imgs, prj, m):
        self.imgs, self.prj, self.m = imgs, prj, m

def read_tif(path, chans=[0]):
    ds = gdal.Open(path)
    prj = osr.SpatialReference()
    prj.ImportFromWkt(ds.GetProjection())
    m = ds.GetGeoTransform()
    m = np.array(m).reshape((2,3))
    imgs = [ds.GetRasterBand(i+1).ReadAsArray() for i in chans]
    return Raster(imgs, prj, m)

def read_hdf(path, chans=None):
    ds = gdal.Open(path)
    sds = ds.GetSubDatasets()
    imgs = []
    if chans is None: chans = range(len(sds))
    for i in chans:
        ds = gdal.Open(sds[i][0])
        img = ds.ReadAsArray()
        m = ds.GetGeoTransform()
        m = np.array(m).reshape((2,3))
        prj = osr.SpatialReference()
        prj.ImportFromWkt(ds.GetProjection())
        imgs.append(img)
    return Raster(imgs, prj, m)
    
def read_shp(path, encoding='utf-8'):
    sf = shapefile.Reader(path, encoding=encoding)
    shapes, records = sf.shapes(), sf.records()
    dfs = sf.records()
    fields = [i[0] for i in sf.fields]
    shps = []
    for shp in shapes:
        arr = np.array(shp.points)
        parts = list(shp.parts) + [None]
        parts = zip(parts[:-1], parts[1:])
        shps.append(MultiPolygon([Polygon(arr[s:e]) for s,e in parts]))
    prj = osr.SpatialReference()
    f = open(path.replace('shp', 'prj'))
    prj.ImportFromWkt(f.read())
    prj.MorphFromESRI()
    f.close()
    df = pd.DataFrame(records, columns=fields[1:])
    df['shape'], df.prj = shps, prj
    return df

def write_tif(raster, path):
    driver = gdal.GetDriverByName("GTiff")
    imgs, prj, m = raster.imgs, raster.prj, raster.m
    tps = {np.uint8:gdal.GDT_Byte, np.int16:gdal.GDT_Int16,
           np.int32:gdal.GDT_Int32, np.uint16:gdal.GDT_UInt16,
           np.uint32:gdal.GDT_UInt32, np.float32:gdal.GDT_Float32,
           np.float64:gdal.GDT_Float64}
    tif = driver.Create(path, imgs[0].shape[1], imgs[0].shape[0],
                        len(raster.imgs), tps[imgs[0].dtype.type])
    tif.SetGeoTransform(m.ravel())
    tif.SetProjection(prj.ExportToWkt())
    for i in range(len(imgs)):
        tif.GetRasterBand(i+1).WriteArray(imgs[i])
    
def plot_shp(shp, color='blue'):
    for geom in shp['shape']:
        for g in geom:
            plt.plot(g.exterior.xy[0], g.exterior.xy[1], color, lw=1)
    plt.gca().set_aspect('equal')

def show_raster(raster, c=0):
    plt.imshow(raster.imgs[c])

if __name__ == '__main__':
    shp = read_shp('../../tasks/country_china_wheat_2018/region.shp')
    #plot_shp(shp)
