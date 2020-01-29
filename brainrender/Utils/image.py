from skimage import measure
import numpy as np
from brainio import brainio


def marching_cubes_to_obj(marching_cubes_out, output_file):
    """
    Saves the output of skimage.measure.marching_cubes as an .obj file

    :param marching_cubes_out: tuple
    :param output_file: str

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
    """
    Reorients the image to the coordinate space of the atlas

    :param image_path: str
    :param threshold: float
    :param invert_axes: tuple (Default value = None)
    :param image: 
    :param orientation:  (Default value = "saggital")

    """
    # TODO: move this to brainio
    if invert_axes is not None:
        for axis in invert_axes:
            image = np.flip(image, axis=axis)

    if orientation != "saggital":
        if orientation == "coronal":
            transposition = (2, 1, 0)
        elif orientation == "horizontal":
            transposition = (1, 2, 0)

        image = np.transpose(image, transposition)
    return image


def image_to_surface(image_path, obj_file_path, voxel_size=1.0,
                     threshold=0, invert_axes=None, orientation="saggital",
                     step_size=1):
    """
    Saves the surface of an image as an .obj file

    :param image_path: str
    :param output_file: obj_file_path
    :param voxel_size: float (Default value = 1.0)
    :param threshold: float (Default value = 0)
    :param invert_axes: tuple (Default value = None)
    :param obj_file_path: 
    :param orientation:  (Default value = "saggital")
    :param step_size:  (Default value = 1)

    """

    image = brainio.load_any(image_path)

    image = reorient_image(image, invert_axes=invert_axes,
                           orientation=orientation)
    verts, faces, normals, values = \
        measure.marching_cubes_lewiner(image, threshold, step_size=step_size)

    # Scale to atlas spacing
    if voxel_size != 1.:
        verts = verts * voxel_size

    faces = faces + 1

    marching_cubes_to_obj((verts, faces, normals, values), obj_file_path)
