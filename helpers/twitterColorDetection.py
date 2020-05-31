from PIL import Image

from helpers.acquireImage import acquireImage

def findColor(x1, y1, x2, y2, im):
    """
    Input: Corners of a box and an image
    Output: Tuple of RGB color values
    """
    boundingBox = (x1,y1,x2,y2)         
    boundingRegion = im.crop(boundingBox) 
    #boundingRegion.show()  
    boxX = x2 - x1
    boxY = y2 - y1
    
    #Initializing output
    totalColor = [0,0,0]

    #Iterate through each pixel and find its color
    for y in range(boxY):
        for x in range(boxX):
            pixelColor = boundingRegion.getpixel((x,y))

            #Iterate through R, G, and B value and add to output
            totalColor[0] = totalColor[0] + pixelColor[0]
            totalColor[1] = totalColor[1] + pixelColor[1]
            totalColor[2] = totalColor[2] + pixelColor[2]

    #Find RGB value throughout image
    totalPixels = boxX * boxY
    for i in range(len(totalColor)):
        totalColor[i] = int(totalColor[i]/totalPixels)

    return (totalColor[0], totalColor[1], totalColor[2])


def getRGB():
    """
    Outputs the RGB color values of the tower
    """
    #Get the image and its path
    imagePath = acquireImage()
    #imagePath = "tower.jpg"

    if (imagePath == -1):
        raise Exception('Image path not found')

    im = Image.open(imagePath)

    baseColor = findColor(718, 217, 731, 358, im)
    topColor = findColor(695,139,728,179, im)

    return([baseColor, topColor])

def getColorNames(baseColor, topColor):
    """
    Inputs: Base and top RGB values
    Output: List of tower colors with base first and top second
    """
    baseColorName, topColorName = ""
    if (100 < baseColor[0] < 175):
            if (50 < baseColor[1] < 150):
                    if (50 < baseColor[2] < 150):
                            baseColorName = "Orange"

    elif (175 < baseColor[0] < 255):
            if (175 < baseColor[1] < 255):
                    if (175 < baseColor[2] < 255):
                            baseColorName = "White"

    elif (0 < baseColor[0] < 100):
            if (0 < baseColor[1] < 100):
                    if (0 < baseColor[2] < 100):
                            baseColorName = "Dark"
    else:
            raise Exception("Unknown Base Color")

    if (150 < topColor[0] < 255):
            if (100 < topColor[1] < 200):
                    if (50 < topColor[2] < 150):
                            topColorName = "Orange"

            elif (200 < topColor[1] < 255):
                    topColorName = "White"

    elif (0 < topColor[0] < 100):
            topColorName = "Dark"

    else:
            raise Exception("Unknown top color")

    return((baseColorName, topColorName))

def createImage(x1,y1,x2,y2,im):
    """
    Inputs: 4 points and an image
    Output: Path to a cropped version of the image
    """
    path = "out.jpg"
    cropBox = (x1,y1,x2,y2)
    outPic = im.crop(cropBox)
    outPic.save(path)
    return path

#rgb = getRGB()
#print(getColorNames(rgb[0], rgb[1]))