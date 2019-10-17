""" 
    Collection of functions to edit actors looks and other features.
"""

from vtkplotter import *


def set_wireframe(actor):
    actor.wireframe(value=True)

def set_solid(actor):
    actor.wireframe(value=False)

def set_color(actor, color):
    actor.color(c=color)

def set_line(actor, lw=None, c=None):
    if lw is not None:
        actor.lw(lineWidth=lw)
    if c is not None:
        actor.lc(lineColor=c)

def upsample(actor, fact=1):
    actor.subdivide(N=fact)

def downsample(actor, fact=0.5):
    actor.decimate(fraction=fact)

def smooth(actor, factor=15):
    actor.smoothLaplacian(niter=factor)

def edit_actor(actor, 
    wireframe=False, solid=False, 
    color=False, line=False, line_kwargs={}, 
    upsample=False, downsample=False, smooth=False):

    if wireframe:
        set_wireframe(actor)
    if solid:
        set_solid(actor)
    if color:
        set_color(actor, color)
    if line:
        set_line(actor, **line_kwargs)
    if upsample:
        upsample(actor)
    if downsample:
        downsample(actor)
    if smooth:
        smooth(actor)