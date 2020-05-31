"""
Brandon Zupan

Holds a function that animates two images
"""

import os
from PIL import Image
from numpy import arange


def animate_icon(score, standard):
    """
    Creates gif that fades between the two icons
    Inputs: Path to score icon, path to standard icon, time of animation in seconds
    Output: Path to the new gif icon
    """
    FRAMERATE = 10
    #LENGTH = 4  #in seconds
    IMAGE_SIZE = (512,512)

    score_icon = Image.open(score).convert("RGBA")
    score_icon = score_icon.resize(IMAGE_SIZE)
    standard_icon = Image.open(standard).convert("RGBA")
    standard_icon = standard_icon.resize(IMAGE_SIZE)

    print(score_icon)
    print(standard_icon)

    #new_image = Image.blend(score_icon, standard_icon, 0.5)

    #new_image.save("testimage.png")

    #frames = LENGTH*FRAMERATE

    file_number = 0

    #1/4 of time on statics and 1
    for i in range(10):
        file_name = f"image_animation/{file_number}.png"
        score_icon.save(file_name)
        file_number += 1

    for i in arange(0, 1, 0.1):
        file_name = f"image_animation/{file_number}.png"

        frame = Image.blend(score_icon, standard_icon, i)
        frame.save(file_name)
        file_number += 1

    for i in range(10):
        file_name = f"image_animation/{file_number}.png"
        standard_icon.save(file_name)
        file_number += 1

    for i in arange(0, 1, 0.1):
        file_name = f"image_animation/{file_number}.png"

        frame = Image.blend(standard_icon, score_icon, i)
        frame.save(file_name)
        file_number += 1

    #Generate the animation using ffmpeg
    ffmpeg_mp4 = f"ffmpeg -y -r {FRAMERATE} -f image2 -s 512x512 -i image_animation/%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p mp4_icon.mp4"
    os.system(ffmpeg_mp4)
    ffmpeg_palette = f"ffmpeg -y -i mp4_icon.mp4 -filter_complex \"[0:v] palettegen\" palette.png"
    os.system(ffmpeg_palette)
    ffmpeg_gif = "ffmpeg -y -i mp4_icon.mp4 -i palette.png -filter_complex \"[0:v][1:v] paletteuse\" gif_icon.gif"
    os.system(ffmpeg_gif)

    return "gif_icon.gif"

# start = time.time()
# animate_icon("sample-out.png", "icons/white.png")
# animate_icon("icons/orangewhite.png", "sample-out.png")
# end = time.time()
# print(end - start)
