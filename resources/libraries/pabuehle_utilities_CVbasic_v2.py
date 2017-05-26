# -*- coding: utf-8 -*-
from pabuehle_utilities_general_v2 import *
import cv2, textwrap
from PIL import Image, ImageDraw, ImageFont, ExifTags

###############################################################################
# Description:
#    This is a collection of basic Computer Vision utility / helper functions.
#
# Typical meaning of variable names:
#    pt                     = 2D point (column,row)
#    img                    = image
#    width,height (or w/h)  = image dimensions
#    bbox                   = bbox object (stores: left, top,right,bottom co-ordinates)
#    rect                   = rectangle (order: left, top, right, bottom)
#    angle                  = rotation angle in degree
#    scale                  = image up/downscaling factor
#
# Python 2 vs 3:
#    This code was partly automatically converted from python 2 to 3 using 'futurize'.
#    http://python-future.org/compatible_idioms.html
#
# NOTE:
# - All points are (column,row order). This is similar to OpenCV and other packages.
#   However, OpenCV indexes images as img[row,col] (but using OpenCVs Point class it's: img[Point(x,y)] )
# - all rotations are counter-clockwise, all angles are in degree
# - This code was automatically converted by 'futurize' to run in python 2 and 3.
###############################################################################


####################################
# Image transformation
####################################
def imread(imgPath, boThrowErrorIfExifRotationTagSet = True):
    # Use OpenCV to load image. However OpenCV ignores the exifTags, e.g. to indicate
    # that the image is rotated, hence need to perform rotation manually.
    if not os.path.exists(imgPath):
        raise Exception("ERROR: image path does not exist: " + imgPath)
    rotation = getRotationFromExifTag(imgPath)
    if boThrowErrorIfExifRotationTagSet and rotation != 0:
        print("Error: exif roation tag set, image needs to be rotated by %d degrees." % rotation)
    img = cv2.imread(imgPath)
    if img is None:
        raise Exception("ERROR: cannot load image " + imgPath)
    if rotation != 0:
        img = imrotate(img, -90).copy()  # got this error occassionally without copy "TypeError: Layout of the output array img is incompatible with cv::Mat"
    return img

def imwrite(img, imgPath):
    cv2.imwrite(imgPath, img)

def imresize(img, scale, interpolation = cv2.INTER_LINEAR):
    return cv2.resize(img, (0,0), fx=scale, fy=scale, interpolation=interpolation)

def imresizeToSize(img, targetWidth, targetHeight):
    return cv2.resize(img, (targetWidth,targetHeight))

def imresizeMaxDim(img, maxDim, boUpscale = False, interpolation = cv2.INTER_LINEAR):
    scale = 1.0 * maxDim / max(img.shape[:2])
    if scale < 1  or boUpscale:
        img = imresize(img, scale, interpolation)
    else:
        scale = 1.0
    return img, scale

def imresizeAndPad(img, width, height, pad_value = 0):
    # resize image
    imgWidth, imgHeight = imWidthHeight(img)
    scale = min(float(width) / float(imgWidth), float(height) / float(imgHeight))
    imgResized = imresize(img, scale) #, interpolation=cv2.INTER_NEAREST)
    resizedWidth, resizedHeight = imWidthHeight(imgResized)

    # pad image
    top  = int(max(0, np.round((height - resizedHeight) / 2)))
    left = int(max(0, np.round((width  - resizedWidth)  / 2)))
    bottom = height - top  - resizedHeight
    right  = width  - left - resizedWidth
    return cv2.copyMakeBorder(imgResized, top, bottom, left, right,
                              cv2.BORDER_CONSTANT, value=[pad_value, pad_value, pad_value])

# ToDo: single function which takes resizeMethod as input
# def imresizeMinDim(img, minDim):
#     scale = min(1.0, 1.0 * minDim / min(img.shape[:2]))
#     if scale < 1:
#         img = imresize(img, scale)
#     return img, scale
#
# def imresizeMaxWidth(img, maxWidth, boUpscale = False, interpolation = cv2.INTER_LINEAR):
#     scale = 1.0 * maxWidth / img.shape[:1]
#     if scale < 1  or boUpscale:
#         img = imresize(img, scale, interpolation)
#     else:
#         scale = 1.0
#     return img, scale
#
# def imresizeMaxPixels(img, maxNrPixels):
#     nrPixels = (img.shape[0] * img.shape[1])
#     scale = min(1.0,  1.0 * maxNrPixels / nrPixels)
#     if scale < 1:
#         img = imresize(img, scale)
#     return img, scale

def imrotate(img, angle, resample = Image.BILINEAR, expand = True):
    imgPil = imconvertCv2Pil(img)
    imgPil = imgPil.rotate(angle, resample, expand)
    return imconvertPil2Cv(imgPil)
    #NOTE: the code below rotates the image, but does not
    #  change the size of the image to make sure it fits
    #w, h = imWidthHeight(img)
    #if centerPt == None:
    #    centerPt = (w/2.0, h/2.0)
    #rotMat = cv2.getRotationMatrix2D(centerPt, angle, 1.0)
    #return cv2.warpAffine(img, rotMat, (w,h))

def imRigidTransform(img, srcPts, dstPts):
    srcPts = np.array([srcPts], np.int)
    dstPts = np.array([dstPts], np.int)
    M = cv2.estimateRigidTransform(srcPts, dstPts, False)
    if transformation is not None:
        return cv2.warpAffine(img, M)
    else:
        return None

def imConcat(img1, img2):
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    if len(img2.shape) == 3:
        newImg = np.zeros((max(h1, h2), w1+w2, img1.shape[2]), img1.dtype)
        newImg[:h1, :w1      , :] = img1
        newImg[:h2, w1:w1+w2 , :] = img2
    else:
        newImg = np.zeros((max(h1, h2), w1+w2), img1.dtype)
        newImg[:h1, :w1]      = img1
        newImg[:h2, w1:w1+w2] = img2
    return newImg

def imconvertCv2Pil(img):
    return Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))

def imconvertCv2Ski(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def imconvertCv2Numpy(img):
    (b,g,r) = cv2.split(img)
    return cv2.merge([r,g,b])

def imconvertPil2Cv(pilImg):
    return imconvertPil2Numpy(pilImg)[:, :, ::-1]

def imconvertPil2Numpy(pilImg):
    return np.array(pilImg.convert('RGB')).copy()

def imconvertNumpy2Cv(img):
    return np.dstack((img[:,:,2], img[:,:,1], img[:,:,0]))

def imconvertSki2Cv(imgSki):
    return cv2.cvtColor(imgSki, cv2.COLOR_BGR2RGB)



####################################
# Image info
####################################
def imWidth(input):
    return imWidthHeight(input)[0]

def imHeight(input):
    return imWidthHeight(input)[1]

def imWidthHeight(input):
    if isString(input):
        width, height = Image.open(input).size #this does not load the full image, hence fast
    else:
        width, height = (input.shape[1], input.shape[0])
    return width,height

def getRotationFromExifTag(imgPath):
    # read exif tags from image, if present
    try:
        exifTags = Image.open(imgPath)._getexif()
    except:
        exifTags = None

    #rotate the image if orientation exif tag is present
    rotation = 0
    tag2Id = {v: k for k, v in list(ExifTags.TAGS.items())}
    orientationExifId = tag2Id['Orientation']
    if exifTags != None and orientationExifId != None and orientationExifId in exifTags:
        orientation = exifTags[orientationExifId]
        if orientation == 1 or orientation == 0:
            rotation = 0 #no need to do anything
        elif orientation == 6:
            rotation = -90
        elif orientation == 8:
            rotation = 90
        else:
            raise Exception("ERROR: orientation = " + str(orientation) + " not_supported!")
    return rotation



####################################
# Visualization
####################################
def imshow(img, waitDuration=0, maxDim = None, windowName = 'img', boUpscale = False):
    if isString(img): # isinstance(img, basestring): #test if 'img' is a string
        img = cv2.imread(img)
    if maxDim is not None:
        scaleVal = 1.0 * maxDim / max(img.shape[:2])
        if scaleVal < 1 or boUpscale:
            img = imresize(img, scaleVal)
    cv2.imshow(windowName, img)
    cv2.waitKey(waitDuration)

def plotHeatMap(img, heatGrayImg, alpha=0.5, drawColorbar = True, subplotString = None):
    # assert(heatGrayImg.
    plt.figure(frameon=False)
    if subplotString:
        plt.subplot(subplotString)
    plt.imshow(img, cmap=plt.cm.gray) #, interpolation='nearest', extent=extent)
    plt.hold(True)
    plt.imshow(heatGrayImg, cmap=plt.cm.jet, alpha=alpha) #, interpolation='bilinear', extent=extent)
    if drawColorbar:
        plt.colorbar()
    return plt

def drawLine(img, pt1, pt2, color = (0, 255, 0), thickness = 2):
    cv2.line(img, tuple(toIntegers(pt1)), tuple(toIntegers(pt2)), color, thickness)

def drawLines(img, pt1s, pt2s, color = (0, 255, 0), thickness = 2):
    for pt1,pt2 in zip(pt1s,pt2s):
        drawLine(img, pt1, pt2, color, thickness)

def drawPolygon(img, pts, boCloseShape = False, color = (0, 255, 0), thickness = 2):
    for i in range(len(pts) - 1):
        drawLine(img, pts[i], pts[i+1], color = color, thickness = thickness)
    if boCloseShape:
        drawLine(img, pts[len(pts)-1], pts[0], color = color, thickness = thickness)

def drawRectangles(img, rects, color = (0, 255, 0), thickness = 2):
    for rect in rects:
        pt1 = tuple(toIntegers(rect[0:2]))
        pt2 = tuple(toIntegers(rect[2:]))
        cv2.rectangle(img, pt1, pt2, color, thickness)

def drawCircle(img, centerPt, radius, color = (0, 255, 0), thickness = 2):
    radius = int(round(radius))
    centerPt = tuple(toIntegers(centerPt))
    cv2.circle(img, centerPt, radius, color, thickness)

def drawCircles(img, centerPts, radius, color = (0, 255, 0), thickness = 2):
    for centerPt in centerPts:
        drawCircle(img, centerPt, radius, color, thickness)

def drawCrossbar(img, pt):
    (x,y) = pt
    cv2.rectangle(img, (0, y),            (x, y), (255, 255, 0), 1)
    cv2.rectangle(img, (x, 0),            (x, y), (255, 255, 0), 1)
    cv2.rectangle(img, (img.shape[1],y),  (x, y), (255, 255, 0), 1)
    cv2.rectangle(img, (x, img.shape[0]), (x, y), (255, 255, 0), 1)

def drawText(img, pt, text, textWidth=None, color = (255,255,255), colorBackground = None, font = ImageFont.truetype("arial.ttf", 16)):
    pilImg = imconvertCv2Pil(img)
    pilImg = pilDrawText(pilImg,  pt, text, textWidth, color, colorBackground, font)
    return imconvertPil2Cv(pilImg)

def pilDrawText(pilImg, pt, text, textWidth=None, color = (255,255,255), colorBackground = None, font = ImageFont.truetype("arial.ttf", 16)):
    pt = pt[:]  # create copy
    draw = ImageDraw.Draw(pilImg)
    if textWidth == None:
        lines = [text]
    else:
        lines = textwrap.wrap(text, width=textWidth)

    for line in lines:
        width, height = font.getsize(line)
        if colorBackground != None:
            draw.rectangle((pt[0], pt[1], pt[0] + width, pt[1] + height), fill=tuple(colorBackground[::-1]))
        draw.text(pt, line, fill = tuple(color), font = font)
        pt[1] += height
    return pilImg

def pilDrawPoints(pilImg, pts, color=(0,255,0), thickness=2):
    draw = ImageDraw.Draw(pilImg)
    for (x,y) in pts:
        draw.rectangle((x-thickness, y-thickness, x+thickness, y+thickness), fill=color)

def getImgGridFromDirectory(imgDir, gridSize=(6, 3), thumbWidth=100, thumbHeight=50, borderSize=5,
                            borderColor=(255, 255, 255)):
    # load all images
    thumbs = []
    imgFilenames = getFilesInDirectory(imgDir)
    for imgIndex in range(0, gridSize[0] * gridSize[1]):
        printProgressBar(1.0 * imgIndex / (gridSize[0] * gridSize[1]))
        thumb = imread(imgDir + imgFilenames[imgIndex])
        thumb = imresizeToSize(thumb, thumbWidth, thumbHeight)
        thumbs.append(thumb)

    # construct grid image
    imgWidth  = gridSize[0] * thumbWidth  + (gridSize[0] - 1) * borderSize
    imgHeight = gridSize[1] * thumbHeight + (gridSize[1] - 1) * borderSize
    gridImg = np.zeros((imgHeight, imgWidth, 3), np.uint8)
    for i in range(0, 3):
        gridImg[:, :, i] = borderColor[i]
    thumbCounter = 0
    for indexCol in range(0, gridSize[0]):
        for indexRow in range(0, gridSize[1]):
            left = indexCol * thumbWidth  + indexCol * borderSize
            top  = indexRow * thumbHeight + indexRow * borderSize
            right  = left + thumbWidth
            bottom = top  + thumbHeight
            gridImg[top:bottom, left:right, :] = thumbs[thumbCounter]
            thumbCounter += 1
    return gridImg



####################################
# Points and rectangles
####################################
def ptClip(pt, maxWidth, maxHeight):
    pt = list(pt)
    pt[0] = max(pt[0], 0)
    pt[1] = max(pt[1], 0)
    pt[0] = min(pt[0], maxWidth)
    pt[1] = min(pt[1], maxHeight)
    return pt

def ptRotate(pt, angle, centerPt=[0, 0]):
    theta = - angle / 180.0 * pi  # counter-clockwise rotation, conform with OpenCV
    ptRot = [0, 0]
    ptRot[0] = cos(theta) * (pt[0] - centerPt[0]) - sin(theta) * (pt[1] - centerPt[1]) + centerPt[0]
    ptRot[1] = sin(theta) * (pt[0] - centerPt[0]) + cos(theta) * (pt[1] - centerPt[1]) + centerPt[1]
    return ptRot

def rectRotate(rect, angle, centerPt=[]):
    left, top, right, bottom = rect
    if centerPt == []:
        centerPt = [0.5 * (left + right), 0.5 * (top + bottom)]
    leftTopRot     = ptRotate([left, top],     angle, centerPt)
    rightTopRot    = ptRotate([right, top],    angle, centerPt)
    leftBottomRot  = ptRotate([left, bottom],  angle, centerPt)
    rightBottomRot = ptRotate([right, bottom], angle, centerPt)
    return [leftTopRot, rightTopRot, leftBottomRot, rightBottomRot]



####################################
# Random
####################################
def getColor(index):
    colors = getColorsPalette()
    return colors[index % len(colors)]

def getRandomColor():
    return getRandomListElement(getColorsPalette())

def getColorsPalette():
    # Todo: use instead color palette specified in matplotlib
    # import matplotlib as mpl; colormap = mpl.cm.Dark2.colors
    # cmap = plt.get_cmap('autumn_r')
    # cmaplist = [cmap(i) for i in range(cmap.N)]
    # colors = getColumns(cmaplist, [0,1,2])
    colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255]]
    for i in range(len(colors)):
        for dim in range(3):
            for s in (0.25, 0.5, 0.75):
                if colors[i][dim] != 0:
                    newColor = copy.deepcopy(colors[i])
                    newColor[dim] = int(round(newColor[dim] * s))
                    colors.append(newColor)
    return colors

