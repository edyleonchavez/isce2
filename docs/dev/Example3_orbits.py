#!/usr/bin/env python3
import numpy as np
import isce
import isceobj
import stdproc
import copy
from iscesys.StdOEL.StdOELPy import create_writer
from isceobj.Orbit.Orbit import Orbit

###Load data from an insarApp run
###Load orbit2sch by default
def load_pickle(step='orbit2sch'):
    import cPickle

    insarObj = cPickle.load(open('PICKLE/{0}'.format(step), 'rb'))
    return insarObj
    
if __name__ == '__main__':
    ##### Load insarProc object
    print('Loading original and interpolated WGS84 state vectors')
    iObj = load_pickle(step='mocompath')

    ####Make a copy of the peg point data
    peg = copy.copy(iObj.peg)
    
    
    #####Copy the original state vectors
    #####These are the 10-15 vectors provided
    #####with the sensor data in WGS84 coords
    origOrbit = copy.copy(iObj.referenceFrame.getOrbit())
    print('From Original Metadata - WGS84')
    print('Number of state vectors: %d'%len(origOrbit._stateVectors))
    print('Time interval: %s %s'%(str(origOrbit._minTime),
    str(origOrbit._maxTime)))


    #####Line-by-line WGS84 interpolated orbit
    #####This was done using Hermite polynomials
    xyzOrbit =  copy.copy(iObj.referenceOrbit)
    print('Line-by-Line XYZ interpolated')
    print('Number of state vectors: %d'%len(xyzOrbit._stateVectors))
    print('Time interval: %s %s'%(str(xyzOrbit._minTime),
    str(xyzOrbit._maxTime)))

    ####Delete the insarProc object from "mocomppath"
    del iObj
    
    ####Note: 
    ####insarApp converts WGS84 orbits to SCH orbits 
    ####during the orbit2sch step

    
    ######Line-by-line SCH orbit
    ######These were generated by converting
    ######Line-by-Line WGS84 orbits
    print('Loading interpolated SCH orbits')
    iObj = load_pickle('orbit2sch')
    
    ####Copy the peg information needed for conversion
    pegHavg = copy.copy(iObj.averageHeight)
    planet = copy.copy(iObj.planet)
    
    ###Copy the orbits
    schOrbit = copy.copy(iObj.referenceOrbit)
    del iObj
    print('Line-by-Line SCH interpolated')
    print('Number of state vectors: %d'%len(schOrbit._stateVectors))
    print('Time interval: %s %s'%(str(schOrbit._minTime),
        str(schOrbit._maxTime)))
    

    ######Now convert the original state vectors to SCH coordinates
    ###stdWriter logging mechanism for some fortran modules
    stdWriter = create_writer("log","",True,filename='orb.log')
    
    print('*********************')
    orbSch = stdproc.createOrbit2sch(averageHeight=pegHavg)
    orbSch.setStdWriter(stdWriter)
    orbSch(planet=planet, orbit=origOrbit, peg=peg)
    print('*********************')
    
    schOrigOrbit = copy.copy(orbSch.orbit)
    del orbSch
    print('Original WGS84 vectors to SCH')
    print('Number of state vectors: %d'%len(schOrigOrbit._stateVectors))
    print('Time interval: %s %s'%(str(schOrigOrbit._minTime),
        str(schOrigOrbit._maxTime)))
    print(str(schOrigOrbit._stateVectors[0]))
    
    
    
    ####Line-by-line interpolation of SCH orbits
    ####Using SCH orbits as inputs
    pulseOrbit = Orbit()
    pulseOrbit.configure()
    
    #######Loop over and compare against interpolated SCH 
    for svOld in xyzOrbit._stateVectors:
        ####Get time from Line-by-Line WGS84
        ####And interpolate SCH orbit at those epochs
        ####SCH intepolation using simple linear interpolation
        ####WGS84 interpolation would use keyword method="hermite"
        svNew = schOrigOrbit.interpolate(svOld.getTime())
        pulseOrbit.addStateVector(svNew)


    ####Clear some variables
    del xyzOrbit
    del origOrbit
    del schOrigOrbit

    #####We compare the two interpolation schemes
    ####Orig WGS84 -> Line-by-line WGS84 -> Line-by-line SCH
    ####Orig WGS84 -> Orig SCH -> Line-by-line SCH
    
    ###Get the orbit information into Arrays
    (told,xold,vold,relold) = schOrbit._unpackOrbit()
    (tnew,xnew,vnew,relnew) = pulseOrbit._unpackOrbit()


    xdiff = np.array(xold) - np.array(xnew)
    vdiff = np.array(vold) - np.array(vnew)

    print('Position Difference stats')
    print('L1 mean in meters')
    print(np.mean(np.abs(xdiff), axis=0))
    print('')
    print('RMS in meters')
    print(np.sqrt(np.mean(xdiff*xdiff, axis=0)))

    print('Velocity Difference stats')
    print('L1 mean in meters/sec')
    print(np.mean(np.abs(vdiff), axis=0))
    print(' ')
    print('RMS in meters/sec')
    print(np.sqrt(np.mean(vdiff*vdiff, axis=0)))
