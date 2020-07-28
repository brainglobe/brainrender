try:
    import cv2
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "You need opencv to save videos in brainrender, please install opencv with: "
        + "pip install opencv-python"
    )

"""
    Collection of utility functions useful when deaing with cv2
    'cap' objects
"""


def cap_set_frame(cap, frame_number):
    """
        Sets an opencv video capture object to a specific frame
    """
    cap.set(1, frame_number)


def get_cap_selected_frame(cap, show_frame):
    """ 
        Gets a frame from an opencv video capture object to a specific frame
    """
    cap_set_frame(cap, show_frame)
    ret, frame = cap.read()

    if not ret:
        return None
    else:
        return frame


def get_video_params(cap):
    """ 
        Gets video parameters from an opencv video capture object
    """
    if isinstance(cap, str):
        cap = cv2.VideoCapture(cap)

    frame = get_cap_selected_frame(cap, 0)
    if frame.shape[1] == 3:
        is_color = True
    else:
        is_color = False
    cap_set_frame(cap, 0)

    nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    return nframes, width, height, fps, is_color


def open_cvwriter(
    filepath, w=None, h=None, framerate=None, format=".mp4", iscolor=False
):
    """
        Creats an instance of cv.VideoWriter to write frames to video using python opencv
        :param filepath: str, path to file to save
        :param w,h: width and height of frame in pixels
        :param framerate: fps of output video
        :param format: video format
        :param iscolor: bool, set as true if images are rgb, else false if they are gray
    """
    try:
        if "avi" in format:
            fourcc = cv2.VideoWriter_fourcc("M", "J", "P", "G")
        else:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        videowriter = cv2.VideoWriter(
            filepath, fourcc, framerate, (w, h), iscolor
        )
    except:
        raise ValueError("Could not create videowriter")
    else:
        return videowriter


def save_videocap_to_video(cap, savepath, fmt, fps=30, iscolor=True):
    """
        Saves the content of a videocapture opencv object to a file
    """
    if "." not in fmt:
        fmt = "." + fmt
    # Creat video writer
    nframes, width, height, _, _ = get_video_params(cap)
    writer = open_cvwriter(
        savepath, w=width, h=height, framerate=fps, format=fmt, iscolor=iscolor
    )

    # Save frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame.shape[2] == 4:  # rgba to rgb
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

        writer.write(frame)

    # Release everything if job is finished
    cap.release()
    writer.release()
