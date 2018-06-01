# This module include database classes

import os
import numpy as np
import pandas as pd
import datetime as dt
from . import funDB
import time


class Database(object):
    r"""Base class Database SMAP

        Arguments:
            rootDB:
            subsetName:
    """

    def __init__(self, rootDB, subsetName):
        self.__rootDB = rootDB
        self.__subsetName = subsetName
        rootName, crd, indSub, indSkip = funDB.readDBinfo(
            rootDB=rootDB, subsetName=subsetName)
        self.__crd = crd
        self.__indSub = indSub
        self.__indSkip = indSkip
        self.__rootName = rootName

    @property
    def rootName(self):
        return self.__rootName

    @property
    def crd(self):
        return self.__crd

    @property
    def indSub(self):
        return self.__indSub

    @property
    def rootDB(self):
        return self.__rootDB

    @property
    def subsetName(self):
        return self.__subsetName

    @property
    def indSkip(self):
        return self.__indSkip

    @property
    def nGrid(self):
        return len(self.crd)

    def __repr__(self):
        return 'later'


class Dataset(Database):
    r"""Base class Database SMAP
    Arguments:
    """

    def __init__(self, *, rootDB, subsetName, yrLst,
                 var=('varConstLst_Noah', 'varConstLst_Noah'),
                 targetName='SMAP_AM'):
        super().__init__(rootDB, subsetName)
        self.__yrLst = yrLst
        self.__time = funDB.readDBtime(
            rootDB=self.rootDB, rootName=self.rootName, yrLst=yrLst)

        # input data
        self.__input = None
        self.__statInput = None
        self.__normInput = None

        # input variable
        if isinstance(var[0], list):
            self.__varInputTs = var[0]
        else:
            self.__varInputTs = funDB.readVarLst(
                rootDB=self.rootDB, varLst=var[0])
        if isinstance(var[1], list):
            self.__varInputConst = var[1]
        else:
            self.__varInputConst = funDB.readVarLst(
                rootDB=self.rootDB, varLst=var[1])
        self.__varInput = self.__varInputTs + self.__varInputConst

        # target data
        self.__target = None
        self.__varTarget = targetName
        self.__statTarget = None
        self.__normTarget = None

    @property
    def time(self):
        return self.__time

    @property
    def yrLst(self):
        return self.__yrLst

    @property
    def input(self):
        return self.__input

    @property
    def statInput(self):
        return self.__statInput

    @property
    def normInput(self):
        return self.__normInput

    @property
    def varInputTs(self):
        return self.__varInputTs

    @property
    def varInputConst(self):
        return self.__varInputConst

    @property
    def varInput(self):
        return self.__varInput

    @property
    def target(self):
        return self.__target

    @property
    def varTarget(self):
        return self.__varTarget

    @property
    def statTarget(self):
        return self.__statTarget

    @property
    def normTarget(self):
        return self.__normTarget

    def readTarget(self, *, loadData=True, loadStat=True, loadNorm=False):
        nt = len(self.time)
        ngrid = len(self.indSub)
        data = funDB.readDataTS(
            rootDB=self.rootDB, rootName=self.rootName, indSub=self.indSub,
            indSkip=self.indSkip, yrLst=self.yrLst, fieldName=self.varTarget,
            nt=nt, ngrid=ngrid)
        stat = funDB.readStat(rootDB=self.rootDB, fieldName=self.varTarget)
        dataNorm = (data-stat[2])/stat[3]
        if loadData is True:
            self.__target = data
        if loadStat is True:
            self.__statTarget = stat
        if loadNorm is True:
            self.__normTarget = dataNorm

    def readInput(self, *, loadData=False, loadStat=True, loadNorm=True):
        nt = len(self.time)
        ngrid = len(self.indSub)
        nvar = len(self.varInput)
        data = np.ndarray([ngrid, nt, nvar])
        dataNorm = np.ndarray([ngrid, nt, nvar])
        stat = np.ndarray([4, nvar])

        # time series
        k = 0
        for var in self.varInputTs:
            dataTemp = funDB.readDataTS(
                rootDB=self.rootDB, rootName=self.rootName, indSub=self.indSub,
                indSkip=self.indSkip, yrLst=self.yrLst, fieldName=var,
                nt=nt, ngrid=ngrid)
            statTemp = funDB.readStat(rootDB=self.rootDB, fieldName=var)
            dataNormTemp = (dataTemp-statTemp[2])/statTemp[3]
            data[:, :, k] = dataTemp
            dataNorm[:, :, k] = dataNormTemp
            stat[:, k] = statTemp
            k = k+1

        # const
        for var in self.varInputConst:
            dataTemp = funDB.readDataConst(
                rootDB=self.rootDB, rootName=self.rootName, indSub=self.indSub,
                indSkip=self.indSkip, yrLst=self.yrLst, fieldName=var,
                ngrid=ngrid)
            statTemp = funDB.readStat(
                rootDB=self.rootDB, fieldName=var, isConst=True)
            dataNormTemp = (dataTemp-statTemp[2])/statTemp[3]
            data[:, :, k] = np.repeat(np.reshape(
                dataTemp, [ngrid, 1]), nt, axis=1)
            dataNorm[:, :, k] = np.repeat(np.reshape(
                dataNormTemp, [ngrid, 1]), nt, axis=1)
            stat[:, k] = statTemp
            k = k+1

        if loadData is True:
            self.__input = data
        if loadStat is True:
            self.__statInput = stat
        if loadNorm is True:
            dataNorm[np.where(np.isnan(dataNorm))] = 0
            self.__normInput = dataNorm