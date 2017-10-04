#!/usr/bin/env python
import os
import subprocess
import ConfigParser
import pandas as pd
import numpy as np

class flow:
    """
    flow python interface.
    """
    def __init__(self):
        #Directory
        self.srcDir   = "/path/to/srcCode/"
        self.shedsDir = "/path/to/sheds/"
        self.outDir   = "/path/to/outputs/"

        self.dataDir  = os.path.join(self.outDir,"data")
        self.mapDir   = os.path.join(self.outDir,"map")
        self.exeDir   = os.path.join(self.outDir,"exe")
        self.shedsLnk = os.path.join(self.outDir,"sheds")
        self.hiresDir = os.path.join(self.mapDir,"hires")

        #Domain to construct river network
        self.north    = 0.
        self.south    = 0.
        self.west     = 0.
        self.east     = 0.
        self.gSize    = 1. #network resolution

        #Your input runoff information
        self.northIn  = 0.
        self.southIn  = 0.
        self.westIn   = 0.
        self.eastIn   = 0.
        self.gSizeIn  = 1. #input resolution

        self.latOrder = "StoN/NtoS" #latitude order
        self.diminfo  = "diminfo_30min.txt" #name of diminfo, should represent input resolution.
        self.inpmat   = "inpmat-30min" #name of inpmat, should represent input resolution.


    def setDirs(self):
        print "setting directory..."

        if os.path.exists(self.outDir) == False:
            os.makedirs(self.outDir)

        if os.path.exists(self.dataDir) == False:
            os.makedirs(self.dataDir)

        if os.path.exists(self.mapDir) == False:
            os.makedirs(self.mapDir)

        if os.path.exists(self.exeDir) == False:
            os.makedirs(self.exeDir)

        subprocess.call(["ln","-s",self.shedsDir+str("/"),self.shedsLnk])

        if os.path.exists(self.hiresDir) == False:
            os.makedirs(self.hiresDir)

        print "setting directory...done."


    def buildNetworks(self):
        print "[building river networks]"
        print "reading Sheds location.txt..."
        subprocess.call(["cp",os.path.join(self.shedsDir,"location.txt"),os.path.join(self.hiresDir,"location.txt")])
#        location = pd.read_csv(os.path.join(self.hiresDir,"location.txt"),skipinitialspace=True,delimiter=" ",index_col=0,header=-1)
        L = [l.strip().split() for l in open(os.path.join(self.hiresDir,"location.txt"))]
        class dummy:pass
        location = dummy()
        location.loc = dict( (l[0],l[1:]) for l in L)
#        location.index.names = ["value name"]
#        print   "="*80
#        print   location
#        print   "-"*75

        AREAS = location.loc["area"][:]
        narea    = len(AREAS)
        print "NAREA: ",narea
        print "="*80
        csize    = location.loc["csize"][0]

        subprocess.call([os.path.join(self.srcDir,"domaininfo"),str(self.west),str(self.east),str(self.north),str(self.south),str(self.gSize),str(narea),str(csize)])
        subprocess.call(["cat","./domain.txt"])
        subprocess.call(["mv","./domain.txt",self.exeDir])
        print "reading Sheds location.txt...done"

        os.chdir(self.exeDir)
        subprocess.call([os.path.join(self.srcDir,"make_lsmask")])

        for area in AREAS:
            print "AREA: ",area
            print "constructing network..."
            subprocess.call([os.path.join(self.srcDir,"const_network"),str(area),self.shedsDir+str("/"),self.dataDir+str("/"),self.mapDir+str("/")])
            print "constructing network...done"
            print "defining catchment..."
            subprocess.call([os.path.join(self.srcDir,"define_catchment"),str(area)])
            print "defining catchment...done"
        
        subprocess.call([os.path.join(self.srcDir,"combine_area")])
        subprocess.call([os.path.join(self.srcDir,"set_map")])
        subprocess.call(["cp",os.path.join(self.mapDir,"nxtdst.bin"),os.path.join(self.mapDir,"rivlen_grid.bin")])


    def generateInpmat(self):
        print "[generating input matrix]"
        os.chdir(self.mapDir)
        subprocess.call([os.path.join(self.srcDir,"generate_inpmat"),str(self.gSizeIn),str(self.westIn),str(self.eastIn),str(self.northIn),str(self.southIn),str(self.latOrder),self.inpmat+".bin",self.inpmat+".txt",self.diminfo])


    def writeCtl(self):
        os.chdir(self.exeDir)
        subprocess.call([os.path.join(self.srcDir,"s04-wrte_ctl.sh"),self.srcDir,self.mapDir,self.diminfo])
        subprocess.call([os.path.join(self.srcDir,"s05-hires_ctl.sh"),self.mapDir])


    def main(self):
        self.setDirs()
        self.buildNetworks()
        self.generateInpmat()
        self.writeCtl()

    def test(self):

        #Directory
        self.srcDir   = "/data4/yuta/flowApi/src"
        self.shedsDir = "/data3/yuta/CaMa-Flood_v3.6.2_20140909/FLOW/data/japan_6sec"
        self.outDir   = "/data4/yuta/flowApi/test"

        self.dataDir  = os.path.join(self.outDir,"data")
        self.mapDir   = os.path.join(self.outDir,"map")
        self.exeDir   = os.path.join(self.outDir,"exe")
        self.shedsLnk = os.path.join(self.outDir,"sheds")
        self.hiresDir = os.path.join(self.mapDir,"hires")

        #Domain to construct river network
        self.north    = 50.
        self.south    = 20.
        self.west     = 120.
        self.east     = 150.
        self.gSize    = 0.01 #network resolution

        #Your input runoff information
        self.northIn  = 90
        self.southIn  = -90
        self.westIn   = -180
        self.eastIn   = 180
        self.gSizeIn  = 1. #input resolution

        self.latOrder = "NtoS" #latitude order
        self.diminfo  = "diminfo_1deg.txt" #name of diminfo, should represent input resolution.
        self.inpmat   = "inpmat-1deg" #name of inpmat, should represent input resolution.

        self.main()

        refDir = "/data3/yuta/CaMa-Flood_v3.6.2_20140909/FLOW/jpn_5km/map/"
        FILES  = ["basin.bin","bsncol.bin","elevtn.bin","fldhgt.bin","grarea.bin","inpmat-1deg.bin",\
                  "lonlat.bin","lsmask.bin","nextxy.bin","nxtdst.bin","rivlen.bin","rivseq.bin","uparea.bin"]

        FLAGS  = []
        for file in FILES:
            print file
            rslt2 = 0
            if file == "nextxy.bin":
                data = np.fromfile(os.path.join(self.mapDir,file),np.int32).reshape(2,3000,3000)
                refD = np.fromfile(os.path.join(refDir,file),np.int32).reshape(2,3000,3000)
            elif file == "inpmat-1deg.bin":
                data = np.fromfile(os.path.join(self.mapDir,file),np.int32).reshape(3,4,3000,3000)[0:2]
                refD = np.fromfile(os.path.join(refDir,file),np.int32).reshape(3,4,3000,3000)[0:2]

                data2 = np.fromfile(os.path.join(self.mapDir,file),np.float32).reshape(3,4,3000,3000)[2]
                refD2 = np.fromfile(os.path.join(refDir,file),np.float32).reshape(3,4,3000,3000)[2]
                rslt2 = (data2 - refD2).sum()
            elif file == "lsmask.bin" or file == "basin.bin" or file == "bsncol.bin":
                data = np.fromfile(os.path.join(self.mapDir,file),np.int32).reshape(3000,3000)
                refD = np.fromfile(os.path.join(refDir,file),np.int32).reshape(3000,3000)
            elif file == "lonlat.bin":
                data = np.fromfile(os.path.join(self.mapDir,file),np.float32).reshape(2,3000,3000)
                refD = np.fromfile(os.path.join(refDir,file),np.float32).reshape(2,3000,3000)
            elif file == "rivseq.bin":
                data = np.fromfile(os.path.join(self.mapDir,file),np.int32).reshape(3000,3000)
                refD = np.fromfile(os.path.join(refDir,file),np.int32).reshape(3000,3000)
            elif file == "fldhgt.bin":
                data = np.fromfile(os.path.join(self.mapDir,file),np.int32).reshape(10,3000,3000)
                refD = np.fromfile(os.path.join(refDir,file),np.int32).reshape(10,3000,3000)
            else:
                data = np.fromfile(os.path.join(self.mapDir,file),np.float32).reshape(3000,3000)
                refD = np.fromfile(os.path.join(refDir,file),np.float32).reshape(3000,3000)

            rslt = (data - refD).sum() + rslt2
            if rslt == 0.:
                flag = True
            else:
                flag = False

            FLAGS.append(flag)
            print flag

        if np.array(FLAGS).all() == True:
            print "success"
            print FLAGS
            return True
        else:
            print "failed"
            return False

if __name__ == "__main__":
    chunk = flow()
    print "Testing API..."
    flag = chunk.test()
    if flag:
        print "Testing API was successfully finished."
    else:
        print "Testing API was failed..."
