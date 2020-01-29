""" 
    Collection of functions to edit actors looks and other features.
"""

def set_wireframe(actor):
    """
    set an actor's look to wireframe

    :param actor: 

    """
    actor.wireframe(value=True)

def set_solid(actor):
    """
    set an actor's look to solid

    :param actor: 

    """
    actor.wireframe(value=False)

def set_color(actor, color):
    """
    set an actor's look to a specific color

    :param actor: 
    :param color: 

    """
    actor.color(c=color)

def set_line(actor, lw=None, c=None):
    """
    set an actor's look to specify the line width and color

    :param actor: 
    :param lw:  (Default value = None)
    :param c:  (Default value = None)

    """
    if lw is not None:
        actor.lw(lineWidth=lw)
    if c is not None:
        actor.lc(lineColor=c)

def upsample_actor(actor, fact=1):
    """
    Increase resolution of actor

    :param actor: 
    :param fact:  (Default value = 1)

    """
    actor.subdivide(N=fact)

def downsample_actor(actor, fact=0.5):
    """
    Reduce resolution of actor

    :param actor: 
    :param fact:  (Default value = 0.5)

    """
    actor.decimate(fraction=fact)

def smooth_actor(actor, factor=15):
    """
    Smooth an actor's mesh

    :param actor: 
    :param factor:  (Default value = 15)

    """
    actor.smoothLaplacian(niter=factor)

def edit_actor(actor, 
    wireframe=False, solid=False, 
    color=False, line=False, line_kwargs={}, 
    upsample=False, downsample=False, smooth=False):
    """
    Apply a set of functions to edit an actor's look. 

    :param actor: 
    :param wireframe: if true, change look to wireframe (Default value = False)
    :param solid: if true change look to soi=lid (Default value = False)
    :param color: specify new color (Default value = False)
    :param line: if true, edit the line's look (Default value = False)
    :param line_kwargs: specify width and color of line (Default value = {})
    :param upsample: if true, increase resolution (Default value = False)
    :param downsample: if true, decrease resolution (Default value = False)
    :param smooth: if true, smoothen actor (Default value = False)

    """

    if wireframe:
        set_wireframe(actor)
    if solid:
        set_solid(actor)
    if color:
        set_color(actor, color)
    if line:
        set_line(actor, **line_kwargs)
    if upsample:
        upsample_actor(actor)
    if downsample:
        downsample_actor(actor)
    if smooth:
        smooth_actor(actor)