from skimage import measure
import numpy as np
from brainio import brainio

from BrainRender.Utils import actors_funcs


def marching_cubes_to_obj(marching_cubes_out, output_file):
    """[Saves the output of skimage.measure.marching_cubes as an .obj file]

    Arguments:
        marching_cubes_out {[tuple]} -- [skimage.measure.marching_cubes output]
        output_file {[str]} -- [File to write to]
    """

    verts, faces, normals, _ = marching_cubes_out
    with open(output_file, 'w') as f:
        for item in verts:\
            f.write(f"v {item[0]} {item[1]} {item[2]}\n")
        for item in normals:
            f.write(f"vn {item[0]} {item[1]} {item[2]}\n")
        for item in faces:
            f.write(f"f {item[0]}//{item[0]} {item[1]}//{item[1]} "
                    f"{item[2]}//{item[2]}\n")
        f.close()


def reorient_image(image, invert_axes=None, orientation="saggital"):
    """[Reorients the image to the coordinate space of the atlas]

    Arguments:
        image_path {[str]} -- [Path of image file]
        threshold {[float]} -- [Image threshold to define the surface] (default: {0})
        invert_axes {[tuple]} -- [Tuple of axes to invert (if not in the same orientation as the atlas] (default: {None})
    """
    # TODO: move this to brainio
    if invert_axes is not None:
        for axis in invert_axes:
            image = np.flip(image, axis=axis)

    if orientation is not "saggital":
        if orientation is "coronal":
            transposition = (2, 1, 0)
        elif orientation is "horizontal":
            transposition = (1, 2, 0)

        image = np.transpose(image, transposition)
    return image


def image_to_surface(image_path, obj_file_path, voxel_size=1.0,
                     threshold=0, invert_axes=None, orientation="saggital",
                     step_size=1):
    """[Saves the surface of an image as an .obj file]

    Arguments:
        image_path {[str]} -- [Path of image file]
        output_file {[obj_file_path]} -- [File to write to]
        voxel_size {[float]} -- [Voxel size of the image (in um). Only isotropic voxels supported currently] (default: {1})
        threshold {[float]} -- [Image threshold to define the surface] (default: {0})
        invert_axes {[tuple]} -- [Tuple of axes to invert (if not in the same orientation as the atlas] (default: {None})
    """

    image = brainio.load_any(image_path)

    image = reorient_image(image, invert_axes=invert_axes,
                           orientation=orientation)
    verts, faces, normals, values = \
        measure.marching_cubes_lewiner(image, threshold, step_size=step_size)

    # Scale to atlas spacing
    if voxel_size is not 1:
        verts = verts * voxel_size

    faces = faces + 1

    marching_cubes_to_obj((verts, faces, normals, values), obj_file_path)
