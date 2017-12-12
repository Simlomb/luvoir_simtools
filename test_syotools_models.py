#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 12:22:25 2017

@author: gkanarek

Run from the command line:
    $ python test_syotools_models
Or, to save the output in a file:
    $ python test_syotools_models > model_test.log
"""
from __future__ import print_function

from syotools import cdbs

from syotools.models import Camera, Telescope, Spectrograph, PhotometricExposure, SpectrographicExposure
from syotools.utils.jsonunit import str_jsunit
import astropy.units as u 
from syotools.utils import pre_encode
#from pprint import pprint

def test_photetc(print_models=True):

    print("\n\n==Instantiating models==")
    print("(setting verbose = True)\n")
    
    e, c, t = PhotometricExposure(), Camera(), Telescope()
    t.add_camera(c)
    c.add_exposure(e)
    e.verbose = True
    
    if print_models:
        print("\n\n==Parameter values (aka defaults):==")
        print("\n=TELESCOPE=\n")
        for attr in t._tracked_attributes:
            print('{}: {}'.format(attr, str_jsunit(getattr(t,attr))))
        #pprint(t.encode(), indent=2)
        print("\n=CAMERA=\n")
        for attr in c._tracked_attributes:
            print('{}: {}'.format(attr, str_jsunit(getattr(c,attr))))
        #pprint(c.encode(), indent=2)
        print("\n=EXPOSURE=\n")
        for attr in e._tracked_attributes:
            print('{}: {}'.format(attr, str_jsunit(getattr(e, attr))))
        #pprint(e.encode(), indent=2)
    
    print("\n\n==Setting spectrum to QSO & recalculating==\n")
    e.sed_id = 'qso'
    
    print("\n\n==Current unkown: {}==".format(e.unknown))
    print("\nSNR: {}".format(e.snr))
    
    print("\n\n==Setting unknown to 'magnitude'==\n")
    e.unknown = "magnitude"
    print("\nMagnitude: {}".format(e.magnitude))
    
    print("\n\n==Setting unknown to 'exptime'==\n")
    e.unknown = "exptime"
    print("\nExptime: {}".format(e.exptime))

def test_specetc(print_models=True):
    
    print("\n\n==Instantiating models==")
    print("(setting verbose = True)\n")
    
    e, s, t = SpectrographicExposure(), Spectrograph(), Telescope()
    t.add_spectrograph(s)
    s.add_exposure(e)
    e.verbose = True

    print(e.zmin, e.zmax)
    
    if print_models:
        print("\n\n==Parameter values (aka defaults):==")
        print("\n=TELESCOPE=\n")
        for attr in t._tracked_attributes:
            print('{}: {}'.format(attr, str_jsunit(getattr(t,attr))))
        #pprint(t.encode(), indent=2)
        print("\n=SPECTROGRAPH=\n")
        for attr in s._tracked_attributes:
            print('{}: {}'.format(attr, str_jsunit(getattr(s,attr))))
        #pprint(s.encode(), indent=2)
        print("\n=EXPOSURE=\n")
        for attr in e._tracked_attributes:
            print('{}: {}'.format(attr, str_jsunit(getattr(e,attr))))
        #pprint(e.encode(), indent=2)
        
    print("\n\nSetting spectrograph mode to 'G300M'")
    s.mode = "G300M"
    
    print("\n\n==Setting SED to QSO at z=0.04 & recalculating==\n")
    e.disable() #since we're updating more than one parameter, turn off calculations
    e.sed_id = 'qso'
    e.redshift = 1.0
    e.enable() #turn calculations back on again
    
    print("\n\n==Current unknown: {}==".format(e.unknown))
    print("\nSNR: {}".format(e.recover('snr')))
    
    print("No other unknown types currently supported.")
    
    """
    print("\n\n==Setting unknown to 'magnitude'==\n")
    e.unknown = "magnitude"
    print("\nMagnitude: {}".format(e.magnitude))
    
    print("\n\n==Setting unknown to 'exptime'==\n")
    e.unknown = "exptime"
    print("\nExptime: {}".format(e.exptime))"""

def test_camera():
    c = Camera()
    t = Telescope()
    t.aperture = pre_encode(15.08 * u.m)
    t.add_camera(c)
    sval = [49.70, 11.58, 257.88, 530.75, 962.04, 2075.26, 1819.15, 8058.30, 11806.49, 15819.07]
    
    expt = 3600. * u.s
    qe = c.recover('total_qe')
    fsky = c._fsky()
    wav = c.recover("pivotwave")
    print("Sky counts:")
    for i in range(c.n_bands):
        skc = (fsky[i] * expt * qe[i]).value
        rat = skc / sval[i] * 100.
        print("{:8.2f} ({:5.1f}% of spreadsheet value) at {:4.0f}".format(skc, rat, wav[i]))

if __name__ == "__main__":
    #test_photetc()
    #test_specetc()
    test_camera()