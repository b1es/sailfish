#!/usr/bin/python -u

# Sample dummy simulation illustrating how to load geometry from a
# boolean numpy array.

import sys
import numpy

from sailfish import lbm
from sailfish import geo

import optparse
from optparse import OptionGroup, OptionParser, OptionValueError


class LBMGeo(geo.LBMGeo3D):
    def define_nodes(self):
        self.set_geo_from_bool_array(self.sim.geometry)

    def init_dist(self, dist):
        self.velocity_to_dist((0, 0, 0), (0.0, 0.0, 0.0), dist)
        self.fill_dist((0, 0, 0), dist)

class LSim(lbm.FluidLBMSim):
    filename = 'bool'

    def __init__(self, geo_class, args=sys.argv[1:], defaults=None):
        opts = []
        opts.append(optparse.make_option('--geo', dest='geo', type='string', help='file defining the geometry',
                                         default=None))

        lbm.FluidLBMSim.__init__(self, geo_class, options=opts, args=args, defaults=defaults)

        if self.options.geo is not None:
            geo = numpy.logical_not(numpy.load(self.options.geo))
        else:
            raise ValueError('Geometry file must be specified')

        orig_shape = geo.shape
        new_shape = list(orig_shape)

        # Add walls around the whole simulation domain.
        new_shape[0] += 2
        new_shape[1] += 2
        new_shape[2] += 2

        # Make sure the x dimension is a multiple of the block size.
        new_shape[2] = ((new_shape[2] / self.options.block_size) + 1) * self.options.block_size

        # Perform funny gymnastics to extend the array to the new shape.  numpy's
        # resize can only be used on the 1st axis if the position of the data in
        # the array is not to be changed.
        geo = numpy.resize(geo, (new_shape[0], orig_shape[1], orig_shape[2]))
        geo = numpy.rollaxis(geo, 1, 0)
        geo = numpy.resize(geo, (new_shape[1], new_shape[0], orig_shape[2]))
        geo = numpy.rollaxis(geo, 0, 2)
        geo = numpy.rollaxis(geo, 2, 0)
        geo = numpy.resize(geo, (new_shape[2], new_shape[0], new_shape[1]))
        geo = numpy.rollaxis(geo, 0, 3)

        geo[:,:,orig_shape[2]:new_shape[2]] = True
        geo[:,-2:,:] = True
        geo[-2:,:,:] = True

        # Make sure the walls are _around_ the simulation domain.
        geo = numpy.roll(geo, 1, 0)
        geo = numpy.roll(geo, 1, 1)
        geo = numpy.roll(geo, 1, 2)

        self.options.lat_nx = geo.shape[2]
        self.options.lat_ny = geo.shape[1]
        self.options.lat_nz = geo.shape[0]
        self.geometry = geo

if __name__ == '__main__':
    sim = LSim(LBMGeo)
    sim.run()