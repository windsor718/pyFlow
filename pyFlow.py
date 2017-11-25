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
        # Directory
        self.srcDir   = "/path/to/srcCode/"
        self.shedsDir = "/path/to/sheds/"
        self.outDir   = "/path/to/outputs/"

        self.dataDir  = os.path.join(self.outDir,"data")
        self.mapDir   = os.path.join(self.outDir,"map")
        self.exeDir   = os.path.join(self.outDir,"exe")
        self.shedsLnk = os.path.join(self.outDir,"sheds")
        self.hiresDir = os.path.join(self.mapDir,"hires")

        # Domain to construct river network
        self.north    = 0.
        self.south    = 0.
        self.west     = 0.
        self.east     = 0.
        self.gSize    = 1. #network resolution

        # Your input runoff information
        self.northIn  = 0.
        self.southIn  = 0.
        self.westIn   = 0.
        self.eastIn   = 0.
        self.gSizeIn  = 1. #input resolution

        self.latOrder = "StoN/NtoS" #latitude order
        self.diminfo  = "diminfo_Reg.InpRes.txt" #name of diminfo, with which should represent input resolution.
        self.inpmat   = "inpmat_Reg.InpRes" #name of inpmat, with which should represent input resolution. No need to specify extention.

        # empirical deriveation of river width and height.
        ## Climatology info. for empirical equation.
        self.climRnof     = "/path/to/RunoffClimatology"
        self.climN        = 0.
        self.climS        = 0.
        self.climE        = 0.
        self.climW        = 0.
        self.climGSize    = 1. # runoff climatology resolution

        self.climLatOrder = "StoN/NtoS" 
        self.climDiminfo  = "diminfo_Reg.InpRes.txt" #name of diminfo, with which should represent input resolution.
        self.climInpmat   = "inpmat_Reg.InpRes" #name of inpmat, with which should represent input resolution. No need to specify extention.

        ## parameters for empirical equation
        self.HC           = 0.14
        self.HP           = 0.40
        self.HMIN         = 2.00

        self.WC           = 0.40
        self.WP           = 0.75
        self.WMIN         = 10.0



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
        L = [l.strip().split() for l in open(os.path.join(self.hiresDir,"location.txt"))]
        class dummy:pass
        location = dummy()
        location.loc = dict( (l[0],l[1:]) for l in L)

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


    def generateInpmat(self,gSizeIn,westIn,eastIn,northIn,southIn,latOrder,inpmat,diminfo):
        print "[generating input matrix]"
        os.chdir(self.mapDir)
        subprocess.call([os.path.join(self.srcDir,"generate_inpmat"),str(gSizeIn),str(westIn),str(eastIn),str(northIn),str(southIn),str(latOrder),inpmat+".bin",inpmat+".txt",diminfo])


    def calcEmpirical(self):
        print "[calculating empirical parameters]"
        os.chdir(self.mapDir)
        outclm = "calc_outclm"
        rivwth = "calc_rivwth"
        clim   = self.climRnof.split("/")[-1]
        print clim
        subprocess.call(["cp", os.path.join(self.srcDir,outclm), "../"])
        subprocess.call(["cp", os.path.join(self.srcDir,rivwth), "../"])
        subprocess.call(["cp", self.climRnof, os.path.join(self.dataDir,clim)])
        subprocess.call(["../calc_outclm", "bin", "inpmat", self.climDiminfo, self.climRnof])
        subprocess.call(["../calc_rivwth", "bin", self.climDiminfo, str(self.HC), str(self.HP), str(self.HMIN), str(self.WC), str(self.WP), str(self.WMIN)])


    def writeCtl(self):
        os.chdir(self.exeDir)
        subprocess.call([os.path.join(self.srcDir,"s04-wrte_ctl.sh"),self.srcDir,self.mapDir,self.diminfo])
        subprocess.call([os.path.join(self.srcDir,"s05-hires_ctl.sh"),self.mapDir])


    def main(self):
        self.setDirs()
        self.buildNetworks()
        self.generateInpmat(self.gSizeIn,self.westIn,self.eastIn,self.northIn,self.southIn,self.latOrder,self.inpmat,self.diminfo)
        self.generateInpmat(self.climGSize,self.climW,self.climE,self.climN,self.climS,self.climLatOrder,self.climInpmat,self.climDiminfo)
        self.calcEmpirical()
        self.writeCtl()


    def test(self):

        #Directory
        self.srcDir   = "/data4/yuta/flowApi/src"
        self.shedsDir = "/home/yamadai/work/FLOW/data/sheds_0.005_140701"
        self.outDir   = "/data4/yuta/HyHy/src/test/jpn1deg"

        self.dataDir  = os.path.join(self.outDir,"data")
        self.mapDir   = os.path.join(self.outDir,"map")
        self.exeDir   = os.path.join(self.outDir,"exe")
        self.shedsLnk = os.path.join(self.outDir,"sheds")
        self.hiresDir = os.path.join(self.mapDir,"hires")

        #Domain to construct river network
        self.north    = 46.
        self.south    = 24.
        self.west     = 123.
        self.east     = 148.
        self.gSize    = 0.1 #network resolution

        #Your input runoff information
        self.northIn  = 90.
        self.southIn  = -90.
        self.westIn   = -180.
        self.eastIn   = 180.
        self.gSizeIn  = 0.25 #input resolution

        self.latOrder = "NtoS" #latitude order
        self.diminfo  = "diminfo_glb05deg.txt" #name of diminfo, should represent input resolution.
        self.inpmat   = "inpmat-glb05deg" #name of inpmat, should represent input resolution.

        #Climatology information
        self.climRnof     = "/data4/yuta/HyHy/CaMa-Flood_v3.6.2_20140909/map/data/runoff_1981-2000_day.bin"
        self.climN        = 90.
        self.climS        = -90.
        self.climE        = 180.
        self.climW        = -180.
        self.climGsize    = 1. # runoff climatology resolution

        self.climLatOrder = "NtoS"
        self.climDiminfo  = "diminfo_glb1deg.txt" #name of diminfo, with which should represent input resolution.
        self.climInpmat   = "inpmat_glb1deg" #name of inpmat, with which should represent input resolution. No need to specify extention.
        self.main()
        return True

if __name__ == "__main__":
    chunk = flow()
    print "Testing API..."
    flag = chunk.test()
    if flag:
        print "Testing API was successfully finished."
    else:
        print "Testing API was failed..."
