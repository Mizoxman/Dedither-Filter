# written by Mizox
# proof of concept de-dithering/denoising filter
# requires/written for python 3.10.11 and pillow 10.2.0
# written in Thonny

import PIL
from PIL import Image

def main():
    
    # take filenames and parameters
    print("Sequence mode:")
    print("1: single image")
    print("2: image sequence")
    ImgMode = input("Enter 1 or 2: ")
    SourceFileName = "0"
    SourceFilePrefix = "0"
    FileDigits = 0
    FileStart = 0
    FileEnd = 0
    SourceExt = "0"
    if (ImgMode == "1"):
        SourceFileName = input("Enter source file name: ")
    else:
        SourceFilePrefix = input("Enter sequence prefix: ")
        FileDigits = int(input("Enter number of digits for sequence number: "))
        FileStart = int(input("Enter starting value for sequence: "))
        FileEnd = int(input("Enter ending value for sequence: "))
        SourceExt = input("Enter sequence file extension: ")
    DestFileName = input("Enter output file name: ")
    RedThresh = int(input("Enter threshold for Red channel: "))
    GreenThresh = int(input("Enter threshold for Green channel: "))
    BlueThresh = int(input("Enter threshold for Blue channel: "))
    SeconThresh = int(input("Enter secondary threshold: "))
    print("Threshold modes:")
    print("1: Independent")
    print("2: Mutual")
    ThreshMode = input("Enter 1 or 2: ")
    print("")
    print("Averaging modes:")
    print("1: 3x3 average")
    print("2: 3x3 averaged LUT")
    print("3: 3x3 bit-shift LUT")
    print("4: 5x5 dynamic subset")
    AvgMode = input("Enter 1-4: ")
    print("")
    
    
    
    # loads the necessary LUTs
    
    # this lut gives a multiplication factor for the 3x3avg and 5x5 modes, used as an intermediate step to fill out a 12 bit accumulator before converting back to 8 bits
    hand = open("multiply_lut.txt")
    count = 0
    for line in hand:
        line = line.rstrip()
        count = count + 1
        key = int(line[:2])
        val = float(line[3:])
        if (count == 1):
            MultLut = {key : val}
        else:
            MultLut[key] = val
    hand.close()
    
    # this lut contains values for the 3x3 Average LUT mode
    hand = open("average_lut.txt")
    count = 0
    for line in hand:
        line = line.rstrip()
        count = count + 1
        key = line[:8]
        val = line[9:]
        if (count == 1):
            AvgLut = {key : val}
        else:
            AvgLut[key] = val
    hand.close()
    
    # this lut contains bit shift values for the 3x3 bit-shift LUT mode
    hand = open("bit_shift_lut.txt")
    count = 0
    for line in hand:
        line = line.rstrip()
        count = count + 1
        key = line[:8]
        val = line[9:]
        if (count == 1):
            ShiftLut = {key : val}
        else:
            ShiftLut[key] = val
    hand.close()
    
    # this lut dictates what order to read the samples in in the 5x5 modes
    hand = open("5x5_order_lut.txt")
    count = 0
    for line in hand:
        line = line.rstrip()
        count = count + 1
        key = int(line[:2])
        val = int(line[3:])
        if (count == 1):
            OrderLut = {key : val}
        else:
            OrderLut[key] = val
    hand.close()
    
    #print(MultLut)
    #print(ShiftLut)
    #print(OrderLut)
    print("Processing")
    
    looping = 0
    while (looping == 0):
        
        if (ImgMode == "1"):
            # open image
            try:
                SourceImage = Image.open(SourceFileName)
                looping = 1
            except:
                print("Invalid Image")
                exit()
        else:
            SourceFileName = (SourceFilePrefix + ('0' * (FileDigits - (len(str(FileStart))))) + str(FileStart) + SourceExt)
            SourceImage = Image.open(SourceFileName)
            if (FileStart >= FileEnd):
                looping = 1
        print(SourceImage.format, SourceImage.size, SourceImage.mode)
        if (SourceImage.mode != "RGB"):
            SourceImage = SourceImage.convert("RGB")
            print("Converting to RGB")
        
        xsize, ysize = SourceImage.size
        OutImage = Image.new("RGB", (xsize, ysize))
        
        x = -1
        y = -1
        
        # 3x3 avg with independent thresholds
        if (ThreshMode == "1") and (AvgMode == "1"):
            while (y < (ysize-1)):
                y = y + 1
                x = -1
                while (x < (xsize-1)):
                    x = x + 1
                    RCount = 0
                    GCount = 0
                    BCount = 0
                    #print(str(x) + " " + str(y))
                    r, g, b = SourceImage.getpixel((x,y))
                    r1 = r
                    g1 = g
                    b1 = b
                    loR = r - RedThresh
                    hiR = r + RedThresh
                    loG = g - GreenThresh
                    hiG = g + GreenThresh
                    loB = b - BlueThresh
                    hiB = b + BlueThresh
                    countx = -2
                    county = -2
                    RAccum = 0
                    GAccum = 0
                    BAccum = 0
                    while (county < 1):
                        county = county + 1
                        countx = -2
                        while (countx < 1):
                            countx = countx + 1
                            sampx = x + countx
                            sampy = y + county
                            #print(str(x) + " " + str(y) + " " + str(sampx) + " " + str(sampy))
                            if (sampx >= 0) and (sampy >= 0) and (sampx < xsize) and (sampy < ysize):
                                #print(str(sampx) + " " + str(sampy))
                                r, g, b = SourceImage.getpixel((sampx,sampy))
                                if (r >= loR) and (r <= hiR):
                                    RAccum = RAccum + r
                                    RCount = RCount + 1
                                if (g >= loG) and (g <= hiG):
                                    GAccum = GAccum + g
                                    GCount = GCount + 1
                                if (b >= loB) and (b <= hiB):
                                    BAccum = BAccum + b
                                    BCount = BCount + 1
                    RAccum = int(RAccum * MultLut.get(RCount)) + 8
                    GAccum = int(GAccum * MultLut.get(GCount)) + 8
                    BAccum = int(BAccum * MultLut.get(BCount)) + 8
                    r = RAccum >> 4
                    g = GAccum >> 4
                    b = BAccum >> 4
                    if (r >= (r1 + SeconThresh)) or (r <= (r1 - SeconThresh)):
                        r = r1
                    if (g >= (g1 + SeconThresh)) or (g <= (g1 - SeconThresh)):
                        g = g1
                    if (b >= (b1 + SeconThresh)) or (b <= (b1 - SeconThresh)):
                        b = b1
                    OutImage.putpixel( (x, y), (r, g, b) )
        
        
        # 3x3 avg with mutually-required thresholds
        if (ThreshMode == "2") and (AvgMode == "1"):
            while (y < (ysize-1)):
                y = y + 1
                x = -1
                while (x < (xsize-1)):
                    x = x + 1
                    CCount = 0
                    #print(str(x) + " " + str(y))
                    r, g, b = SourceImage.getpixel((x,y))
                    r1 = r
                    g1 = g
                    b1 = b
                    loR = r - RedThresh
                    hiR = r + RedThresh
                    loG = g - GreenThresh
                    hiG = g + GreenThresh
                    loB = b - BlueThresh
                    hiB = b + BlueThresh
                    countx = -2
                    county = -2
                    RAccum = 0
                    GAccum = 0
                    BAccum = 0
                    while (county < 1):
                        county = county + 1
                        countx = -2
                        while (countx < 1):
                            countx = countx + 1
                            sampx = x + countx
                            sampy = y + county
                            #print(str(x) + " " + str(y) + " " + str(sampx) + " " + str(sampy))
                            if (sampx >= 0) and (sampy >= 0) and (sampx < xsize) and (sampy < ysize):
                                #print(str(sampx) + " " + str(sampy))
                                r, g, b = SourceImage.getpixel((sampx,sampy))
                                if (r >= loR) and (r <= hiR) and (g >= loG) and (g <= hiG) and (b >= loB) and (b <= hiB):
                                    RAccum = RAccum + r
                                    GAccum = GAccum + g
                                    BAccum = BAccum + b
                                    CCount = CCount + 1
                    RAccum = int(RAccum * MultLut.get(CCount)) + 8
                    GAccum = int(GAccum * MultLut.get(CCount)) + 8
                    BAccum = int(BAccum * MultLut.get(CCount)) + 8
                    r = RAccum >> 4
                    g = GAccum >> 4
                    b = BAccum >> 4
                    if (r >= (r1 + SeconThresh)) or (r <= (r1 - SeconThresh)) or (g >= (g1 + SeconThresh)) or (g <= (g1 - SeconThresh)) or (b >= (b1 + SeconThresh)) or (b <= (b1 - SeconThresh)):
                        r = r1
                        g = g1
                        b = b1
                    OutImage.putpixel( (x, y), (r, g, b) )
        
        # 3x3 average LUT mode with independent thresholds
        if (ThreshMode == "1") and (AvgMode == "2"):
            while (y < (ysize-1)):
                y = y + 1
                x = -1
                while (x < (xsize-1)):
                    x = x + 1
                    RCount = 0
                    GCount = 0
                    BCount = 0
                    ICount = 0
                    #print(str(x) + " " + str(y))
                    r, g, b = SourceImage.getpixel((x,y))
                    r1 = r
                    g1 = g
                    b1 = b
                    loR = r - RedThresh
                    hiR = r + RedThresh
                    loG = g - GreenThresh
                    hiG = g + GreenThresh
                    loB = b - BlueThresh
                    hiB = b + BlueThresh
                    countx = -2
                    county = -2
                    RAccum = 0
                    GAccum = 0
                    BAccum = 0
                    RLut = ""
                    GLut = ""
                    BLut = ""
                    while (county < 1):
                        county = county + 1
                        countx = -2
                        while (countx < 1):
                            countx = countx + 1
                            sampx = x + countx
                            sampy = y + county
                            #print(str(x) + " " + str(y) + " " + str(sampx) + " " + str(sampy))
                            ICount = ICount + 1
                            if (sampx >= 0) and (sampy >= 0) and (sampx < xsize) and (sampy < ysize):
                                #print(str(sampx) + " " + str(sampy))
                                r, g, b = SourceImage.getpixel((sampx,sampy))
                                if (r >= loR) and (r <= hiR):
                                    if (ICount != 5):
                                        RLut = RLut + "1"
                                else:
                                    RLut = RLut + "0"
                                if (g >= loG) and (g <= hiG):
                                    if (ICount != 5):
                                        GLut = GLut + "1"
                                else:
                                    GLut = GLut + "0"
                                if (b >= loB) and (b <= hiB):
                                    if (ICount != 5):
                                        BLut = BLut + "1"
                                else:
                                    BLut = BLut + "0"
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                            else:
                                RLut = RLut + "0"
                                GLut = GLut + "0"
                                BLut = BLut + "0"
                                r, g, b = SourceImage.getpixel((x,y))
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                    RLut = AvgLut.get(RLut)
                    GLut = AvgLut.get(GLut)
                    BLut = AvgLut.get(BLut)
                    ICount = 0
                    while (ICount < 9):
                        if (RLut[ICount] == "1"):
                            RAccum = RAccum + RList[ICount]
                            RCount = RCount + 1
                        if (GLut[ICount] == "1"):
                            GAccum = GAccum + GList[ICount]
                            GCount = GCount + 1
                        if (BLut[ICount] == "1"):
                            BAccum = BAccum + BList[ICount]
                            BCount = BCount + 1
                        ICount = ICount + 1
                    RAccum = int(RAccum * MultLut.get(RCount)) + 8
                    GAccum = int(GAccum * MultLut.get(GCount)) + 8
                    BAccum = int(BAccum * MultLut.get(BCount)) + 8
                    r = RAccum >> 4
                    g = GAccum >> 4
                    b = BAccum >> 4
                    if (r >= (r1 + SeconThresh)) or (r <= (r1 - SeconThresh)):
                        r = r1
                    if (g >= (g1 + SeconThresh)) or (g <= (g1 - SeconThresh)):
                        g = g1
                    if (b >= (b1 + SeconThresh)) or (b <= (b1 - SeconThresh)):
                        b = b1
                    OutImage.putpixel( (x, y), (r, g, b) )
        
        # 3x3 average LUT mode with mutual thresholds
        if (ThreshMode == "2") and (AvgMode == "2"):
            while (y < (ysize-1)):
                y = y + 1
                x = -1
                while (x < (xsize-1)):
                    x = x + 1
                    CCount = 0
                    ICount = 0
                    #print(str(x) + " " + str(y))
                    r, g, b = SourceImage.getpixel((x,y))
                    r1 = r
                    g1 = g
                    b1 = b
                    loR = r - RedThresh
                    hiR = r + RedThresh
                    loG = g - GreenThresh
                    hiG = g + GreenThresh
                    loB = b - BlueThresh
                    hiB = b + BlueThresh
                    countx = -2
                    county = -2
                    RAccum = 0
                    GAccum = 0
                    BAccum = 0
                    CLut = ""
                    while (county < 1):
                        county = county + 1
                        countx = -2
                        while (countx < 1):
                            countx = countx + 1
                            sampx = x + countx
                            sampy = y + county
                            #print(str(x) + " " + str(y) + " " + str(sampx) + " " + str(sampy))
                            ICount = ICount + 1
                            if (sampx >= 0) and (sampy >= 0) and (sampx < xsize) and (sampy < ysize):
                                #print(str(sampx) + " " + str(sampy))
                                r, g, b = SourceImage.getpixel((sampx,sampy))
                                if (r >= loR) and (r <= hiR) and (g >= loG) and (g<= hiG) and (b >= loB) and (b <= hiB):
                                    if (ICount != 5):
                                        CLut = CLut + "1"
                                else:
                                    CLut = CLut + "0"
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                            else:
                                CLut = CLut + "0"
                                r, g, b = SourceImage.getpixel((x,y))
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                    CLut = AvgLut.get(CLut)
                    ICount = 0
                    while (ICount < 9):
                        if (CLut[ICount] == "1"):
                            RAccum = RAccum + RList[ICount]
                            GAccum = GAccum + GList[ICount]
                            BAccum = BAccum + BList[ICount]
                            CCount = CCount + 1
                        ICount = ICount + 1
                    RAccum = int(RAccum * MultLut.get(CCount)) + 8
                    GAccum = int(GAccum * MultLut.get(CCount)) + 8
                    BAccum = int(BAccum * MultLut.get(CCount)) + 8
                    r = RAccum >> 4
                    g = GAccum >> 4
                    b = BAccum >> 4
                    if (r >= (r1 + SeconThresh)) or (r <= (r1 - SeconThresh)) or (g >= (g1 + SeconThresh)) or (g <= (g1 - SeconThresh)) or (b >= (b1 + SeconThresh)) or (b <= (b1 - SeconThresh)):
                        r = r1
                        g = g1
                        b = b1
                    OutImage.putpixel( (x, y), (r, g, b) )
        
        # 3x3 bit-shift LUT mode with independent thresholds
        if (ThreshMode == "1") and (AvgMode == "3"):
            while (y < (ysize-1)):
                y = y + 1
                x = -1
                while (x < (xsize-1)):
                    x = x + 1
                    ICount = 0
                    #print(str(x) + " " + str(y))
                    r, g, b = SourceImage.getpixel((x,y))
                    r1 = r
                    g1 = g
                    b1 = b
                    loR = r - RedThresh
                    hiR = r + RedThresh
                    loG = g - GreenThresh
                    hiG = g + GreenThresh
                    loB = b - BlueThresh
                    hiB = b + BlueThresh
                    countx = -2
                    county = -2
                    RAccum = 0
                    GAccum = 0
                    BAccum = 0
                    RLut = ""
                    GLut = ""
                    BLut = ""
                    while (county < 1):
                        county = county + 1
                        countx = -2
                        while (countx < 1):
                            countx = countx + 1
                            sampx = x + countx
                            sampy = y + county
                            #print(str(x) + " " + str(y) + " " + str(sampx) + " " + str(sampy))
                            ICount = ICount + 1
                            if (sampx >= 0) and (sampy >= 0) and (sampx < xsize) and (sampy < ysize):
                                #print(str(sampx) + " " + str(sampy))
                                r, g, b = SourceImage.getpixel((sampx,sampy))
                                if (r >= loR) and (r <= hiR):
                                    if (ICount != 5):
                                        RLut = RLut + "1"
                                else:
                                    RLut = RLut + "0"
                                if (g >= loG) and (g <= hiG):
                                    if (ICount != 5):
                                        GLut = GLut + "1"
                                else:
                                    GLut = GLut + "0"
                                if (b >= loB) and (b <= hiB):
                                    if (ICount != 5):
                                        BLut = BLut + "1"
                                else:
                                    BLut = BLut + "0"
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                            else:
                                RLut = RLut + "0"
                                GLut = GLut + "0"
                                BLut = BLut + "0"
                                r, g, b = SourceImage.getpixel((x,y))
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                    RLut = ShiftLut.get(RLut)
                    GLut = ShiftLut.get(GLut)
                    BLut = ShiftLut.get(BLut)
                    ICount = 0
                    while (ICount < 9):
                        if (RLut[ICount] != "-"):
                            RAccum = RAccum + (RList[ICount] << int(RLut[ICount]))
                        if (GLut[ICount] != "-"):
                            GAccum = GAccum + (GList[ICount] << int(GLut[ICount]))
                        if (BLut[ICount] != "-"):
                            BAccum = BAccum + (BList[ICount] << int(BLut[ICount]))
                        ICount = ICount + 1
                    r = (RAccum + 8) >> 4
                    g = (GAccum + 8) >> 4
                    b = (BAccum + 8) >> 4
                    if (r >= (r1 + SeconThresh)) or (r <= (r1 - SeconThresh)):
                        r = r1
                    if (g >= (g1 + SeconThresh)) or (g <= (g1 - SeconThresh)):
                        g = g1
                    if (b >= (b1 + SeconThresh)) or (b <= (b1 - SeconThresh)):
                        b = b1
                    OutImage.putpixel( (x, y), (r, g, b) )
        
        # 3x3 bit-shift LUT mode with mutual thresholds
        if (ThreshMode == "2") and (AvgMode == "3"):
            while (y < (ysize-1)):
                y = y + 1
                x = -1
                while (x < (xsize-1)):
                    x = x + 1
                    ICount = 0
                    #print(str(x) + " " + str(y))
                    r, g, b = SourceImage.getpixel((x,y))
                    r1 = r
                    g1 = g
                    b1 = b
                    loR = r - RedThresh
                    hiR = r + RedThresh
                    loG = g - GreenThresh
                    hiG = g + GreenThresh
                    loB = b - BlueThresh
                    hiB = b + BlueThresh
                    countx = -2
                    county = -2
                    RAccum = 0
                    GAccum = 0
                    BAccum = 0
                    CLut = ""
                    while (county < 1):
                        county = county + 1
                        countx = -2
                        while (countx < 1):
                            countx = countx + 1
                            sampx = x + countx
                            sampy = y + county
                            #print(str(x) + " " + str(y) + " " + str(sampx) + " " + str(sampy))
                            ICount = ICount + 1
                            if (sampx >= 0) and (sampy >= 0) and (sampx < xsize) and (sampy < ysize):
                                #print(str(sampx) + " " + str(sampy))
                                r, g, b = SourceImage.getpixel((sampx,sampy))
                                if (r >= loR) and (r <= hiR) and (g >= loG) and (g <= hiG) and (b >= loB) and (b <= hiB):
                                    if (ICount != 5):
                                        CLut = CLut + "1"
                                else:
                                    CLut = CLut + "0"
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                            else:
                                CLut = CLut + "0"
                                r, g, b = SourceImage.getpixel((x,y))
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                    CLut = ShiftLut.get(CLut)
                    ICount = 0
                    while (ICount < 9):
                        if (CLut[ICount] != "-"):
                            RAccum = RAccum + (RList[ICount] << int(CLut[ICount]))
                            GAccum = GAccum + (GList[ICount] << int(CLut[ICount]))
                            BAccum = BAccum + (BList[ICount] << int(CLut[ICount]))
                        ICount = ICount + 1
                    r = (RAccum + 8) >> 4
                    g = (GAccum + 8) >> 4
                    b = (BAccum + 8) >> 4
                    if (r >= (r1 + SeconThresh)) or (r <= (r1 - SeconThresh)) or (g >= (g1 + SeconThresh)) or (g <= (g1 - SeconThresh)) or (b >= (b1 + SeconThresh)) or (b <= (b1 - SeconThresh)):
                        r = r1
                        g = g1
                        b = b1
                    OutImage.putpixel( (x, y), (r, g, b) )
        
        # 5x5 dynamic subset avg mode with independent thresholds
        if (ThreshMode == "1") and (AvgMode == "4"):
            while (y < (ysize-1)):
                y = y + 1
                x = -1
                while (x < (xsize-1)):
                    x = x + 1
                    RCount = 0
                    GCount = 0
                    BCount = 0
                    ICount = 0
                    #print(str(x) + " " + str(y))
                    r, g, b = SourceImage.getpixel((x,y))
                    r1 = r
                    g1 = g
                    b1 = b
                    loR = r - RedThresh
                    hiR = r + RedThresh
                    loG = g - GreenThresh
                    hiG = g + GreenThresh
                    loB = b - BlueThresh
                    hiB = b + BlueThresh
                    countx = -3
                    county = -3
                    RAccum = 0
                    GAccum = 0
                    BAccum = 0
                    while (county < 2):
                        county = county + 1
                        countx = -3
                        while (countx < 2):
                            countx = countx + 1
                            sampx = x + countx
                            sampy = y + county
                            #print(str(x) + " " + str(y) + " " + str(sampx) + " " + str(sampy))
                            ICount = ICount + 1
                            if (sampx >= 0) and (sampy >= 0) and (sampx < xsize) and (sampy < ysize):
                                #print(str(sampx) + " " + str(sampy))
                                r, g, b = SourceImage.getpixel((sampx,sampy))
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                            else:
                                if (ICount == 1):
                                    RList = [1024]
                                    GList = [1024]
                                    BList = [1024]
                                else:
                                    RList.append(1024)
                                    GList.append(1024)
                                    BList.append(1024)
                    ICount = 0
                    while (ICount < 25):
                        #print(ICount)
                        ICount2 = OrderLut.get(ICount)
                        r = RList[ICount2]
                        g = GList[ICount2]
                        b = BList[ICount2]
                        if (RCount < 16):
                            if (r >= loR) and (r <= hiR):
                                RAccum = RAccum + r
                                RCount = RCount + 1
                        if (GCount < 16):
                            if (g >= loG) and (g <= hiG):
                                GAccum = GAccum + g
                                GCount = GCount + 1
                        if (BCount < 16):
                            if (b >= loB) and (b <= hiB):
                                BAccum = BAccum + b
                                BCount = BCount + 1
                        ICount = ICount + 1
                    RAccum = int(RAccum * MultLut.get(RCount)) + 8
                    GAccum = int(GAccum * MultLut.get(GCount)) + 8
                    BAccum = int(BAccum * MultLut.get(BCount)) + 8
                    r = RAccum >> 4
                    g = GAccum >> 4
                    b = BAccum >> 4
                    if (r >= (r1 + SeconThresh)) or (r <= (r1 - SeconThresh)):
                        r = r1
                    if (g >= (g1 + SeconThresh)) or (g <= (g1 - SeconThresh)):
                        g = g1
                    if (b >= (b1 + SeconThresh)) or (b <= (b1 - SeconThresh)):
                        b = b1
                    OutImage.putpixel( (x, y), (r, g, b) )
        
        # 5x5 dynamic subset avg mode with mutual thresholds
        if (ThreshMode == "2") and (AvgMode == "4"):
            while (y < (ysize-1)):
                y = y + 1
                x = -1
                while (x < (xsize-1)):
                    x = x + 1
                    RCount = 0
                    GCount = 0
                    BCount = 0
                    CCount = 0
                    ICount = 0
                    #print(str(x) + " " + str(y))
                    r, g, b = SourceImage.getpixel((x,y))
                    r1 = r
                    g1 = g
                    b1 = b
                    loR = r - RedThresh
                    hiR = r + RedThresh
                    loG = g - GreenThresh
                    hiG = g + GreenThresh
                    loB = b - BlueThresh
                    hiB = b + BlueThresh
                    countx = -3
                    county = -3
                    RAccum = 0
                    GAccum = 0
                    BAccum = 0
                    while (county < 2):
                        county = county + 1
                        countx = -3
                        while (countx < 2):
                            countx = countx + 1
                            sampx = x + countx
                            sampy = y + county
                            #print(str(x) + " " + str(y) + " " + str(sampx) + " " + str(sampy))
                            ICount = ICount + 1
                            if (sampx >= 0) and (sampy >= 0) and (sampx < xsize) and (sampy < ysize):
                                #print(str(sampx) + " " + str(sampy))
                                r, g, b = SourceImage.getpixel((sampx,sampy))
                                if (ICount == 1):
                                    RList = [r]
                                    GList = [g]
                                    BList = [b]
                                else:
                                    RList.append(r)
                                    GList.append(g)
                                    BList.append(b)
                            else:
                                if (ICount == 1):
                                    # these are just arbitrarily high so they're never accidentally used
                                    RList = [1024]
                                    GList = [1024]
                                    BList = [1024]
                                else:
                                    RList.append(1024)
                                    GList.append(1024)
                                    BList.append(1024)
                    ICount = 0
                    while (ICount < 25):
                        #print(ICount)
                        ICount2 = OrderLut.get(ICount)
                        r = RList[ICount2]
                        g = GList[ICount2]
                        b = BList[ICount2]
                        if (CCount < 16):
                            if (r >= loR) and (r <= hiR) and (g >= loG) and (g <= hiG) and (b >= loB) and (b <= hiB):
                                RAccum = RAccum + r
                                GAccum = GAccum + g
                                BAccum = BAccum + b
                                CCount = CCount + 1
                        ICount = ICount + 1
                    RAccum = int(RAccum * MultLut.get(CCount)) + 8
                    GAccum = int(GAccum * MultLut.get(CCount)) + 8
                    BAccum = int(BAccum * MultLut.get(CCount)) + 8
                    r = RAccum >> 4
                    g = GAccum >> 4
                    b = BAccum >> 4
                    if (r >= (r1 + SeconThresh)) or (r <= (r1 - SeconThresh)) or (g >= (g1 + SeconThresh)) or (g <= (g1 - SeconThresh)) or (b >= (b1 + SeconThresh)) or (b <= (b1 - SeconThresh)):
                        r = r1
                        g = g1
                        b = b1
                    OutImage.putpixel( (x, y), (r, g, b) )
        
        if (ImgMode == "1"):
            OutFileName = DestFileName + ".png"
            OutImage.save(OutFileName)
        else:
            OutFileName = (DestFileName + ('0' * (FileDigits - (len(str(FileStart))))) + str(FileStart) + ".png")
            OutImage.save(OutFileName)
            FileStart = FileStart + 1
        print("Exporting " + OutFileName)
        SourceImage.close()
        OutImage.close()
    
    return
    
main()