import scipy.ndimage as ndimg
import numpy as np
from imagepy.core.engine import Filter, Simple
from geonumpy.pretreat import degap

class GapRepair(Simple):
    title = 'Gap Repair'
    note = ['all', 'preview']
    para = {'wild':0, 'r':0, 'dark':True, 'every':True, 'slice':False}
    view = [(float, 'wild', (-65536, 65536), 0, 'wild', 'value'),
            (int, 'r', (0,1024), 0, 'radius', 'pix'),
            (bool, 'dark', 'dark'),
            (bool, 'every', 'count msk for every slice'),
            (bool, 'slice', 'slice')]

    def load(self, ips):
        self.arange = ips.range
        self.lut = ips.lut
        ips.lut = self.lut.copy()
        return True

    def preview(self, ips, para):
        ips.lut[:] = self.lut
        thr = int((para['wild']-self.arange[0])*(
            255.0/max(1e-10, self.arange[1]-self.arange[0])))
        if para['dark']: ips.lut[:thr] = [255,0,0]
        else: ips.lut[thr:] = [255,0,0]
        ips.update()

    def cancel(self, ips):
        ips.lut = self.lut
        ips.update()

    def run(self, ips, imgs, para = None):
        if not para['slice']: 
            ips.snapshot()
            imgs = [ips.img]
        if para['every']:
            for i in range(len(imgs)): 
                img = imgs[i]
                self.progress(i+1, len(imgs))
                msk = img<para['wild'] if para['dark'] else img>=para['wild']
                gap_repair(img, msk, para['r'])
        else: 
            msk = ips.img<para['wild'] if para['dark'] else ips.img>=para['wild']
            gap_repair(imgs, msk, para['r'])
        ips.lut = self.lut

class ROIRepairMC(Simple):
    title = 'ROI Repair Channels'
    note = ['all', 'stack']
    para = {'r':0, 'slice':True}
    view = [(int, 'r', (0, 1024), 0, 'radius', 'pix'),
            (bool, 'slice', 'slice')]

    def run(self, ips, imgs, para = None):
        if not(para['slice']): 
            ips.snapshot()
            imgs = [ips.img]
        msk = ips.get_msk('in')
        gap_repair(imgs, msk, para['r'])

plgs = [GapRepair, ROIRepairMC]