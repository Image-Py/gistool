import numpy as np
import pandas as pd

def get_lst(lst, lab, area, df):
    uq = df['COUNTRG'][df['UP']!=-1].unique()
    uq = pd.DataFrame(uq, columns=['COUNTRG'])
    info = df.reset_index().merge(uq.reset_index(), on='COUNTRG')
    idx = np.zeros(len(df)+1, dtype=np.uint8)
    idx[info['index_x']+1] = info['index_y']+1

    countlab = idx[lab] * area
    freq = np.bincount(countlab.ravel())
    f = lambda i:np.linspace(1,11,i, endpoint=False, dtype=np.uint8)
    lut = np.hstack([f(i) for i in freq[1:]])
    msk = countlab>0
    vlst, vlab = lst[msk], countlab[msk]
    sortidx = np.argsort(vlab * 100000 + vlst)
    rst = np.zeros_like(lab, dtype=np.uint8)
    newidx = np.arange(len(sortidx))
    newidx[sortidx] = np.arange(len(sortidx))
    rst[msk] = lut[newidx]
    return rst

def get_ndvi(ndvi, lab, area, df):
    uq = df['COUNTRG'][df['UP']!=-1].unique()
    uq = pd.DataFrame(uq, columns=['COUNTRG'])
    info = df.reset_index().merge(uq.reset_index(), on='COUNTRG')
    idx = np.zeros(len(df)+1, dtype=np.uint8)
    idx[info['index_x']+1] = info['index_y']+1

    f = lambda d, u:np.searchsorted([0, d, u, 1], np.linspace(-1,1,256))
    sinfo = info[['index_x', 'index_y', 'UP', 'DOWN']]
    lut = np.zeros((len(df)+1,256), dtype=np.uint8)
    for i in sinfo.index:
        lut[sinfo.loc[i,'index_x']+1] = f(*sinfo.loc[i,['DOWN','UP']])
    return lut[lab.ravel(), ndvi.ravel()].reshape(lab.shape)

def count_grade(ndvi, lst):
    #          LST = 0 1 2 3 4 5 6 7 8 9 X
    idx = np.array([[0,0,0,0,0,0,0,0,0,0,0], # N
                    [0,1,1,1,1,1,2,2,4,4,4], # D
                    [0,1,1,1,1,1,2,2,3,3,3], # V
                    [0,1,1,1,1,1,1,1,1,1,1]], dtype=np.uint8)# I
    return idx[ndvi.ravel(), lst.ravel()].reshape(ndvi.shape)

def get_grade(ndvi, lst, lab, area, df):
    rst_lst = get_lst(lst[0], lab[0], area[0]>0, df)
    rst_ndvi = get_ndvi(ndvi[0], lab[0], area[0]>0, df)
    grade = count_grade(rst_ndvi, rst_lst)
    return (grade, lab[1], lab[2])