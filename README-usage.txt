NOTE: IF YOU ARE USING THIS SCRIPT FOR THE REMOVAL OR SOFTENING OF DITHERING, you will get the BEST results/only ACCEPTABLE results by feeding it the NATIVE framebuffer resolution of the game. This Script MAY still produce ACCEPTABLE results as a denoiser if fed non-native resolutions

how to use this program:


option 1: sequence mode:

this asks if you will be processing a single image or a sequence of images
if processing a single image you must enter the file name

if processing a sequence, you must enter the file name in parts:
the filename prefix, the number of digits in the file number, the starting number, the ending number and the file extension
for instance, if you want to process a sequence of images labeled "abcdf0013.png" to "abcdf0123.png", you would enter:
abcdf
4
13
123
.png


option 2: output file name:

this asks the filename of the output image, whatever you enter will have ".png" appended onto the end.
if you are processing a sequence rather than an individual image, the number will be copied from the input images and applied between the entered filename and the ".png"


option 3: red, green, and blue thresholds:

these are asking how much difference is allowed from the pixel you're currently processing when looking for similar pixels to blend with

sane thresholds to try first are: 24 for 4bpc, 12 for 5bpc, 6 for 6bpc


option 4: Secondary Threshold:

after the pixel has been processed, it will be compared against the original value of the pixel.
if the difference exceeds this threshold, then the processing shall be reverted.
this option helps preserve intentional 1x1 details when using higher blend thresholds or when using a modified LUT which makes use of values that would normally be discarded, it can be effectively disabled by using a number above 239


option 5: Threshold mode:

"independent mode" processes each color channel independently, with no influence from the other channels, may produce slightly softer gradients in some cases
"mutual mode" requires any potential pixel to pass the thresholds of all 3 channels before it can contribute to the current pixel, this may improve edge sharpness in some cases


option 6: averaging modes:

3x3 average: this mode simply searches a 3x3 window centered on the pixel being processed, then averages all pixels that pass the threshold together. produces a faint "stippled" pattern when processing a 2x2 or 4x4 bayer matrix due to a mismatch in window size

3x3 averaged lut: this mode is similar to 3x3 average, but rather than simply blend the pixels that pass, it instead sends a list of all pixels that match to a 256-entry LUT, which then returns a list of which pixels to blend with
this feature can potentially be used to search for and blur certain patterns. details on how to read and modify this LUT are in another document

3x3 bit-shift lut: this mode is similar to 3x3 averaged lut, but in addition to the LUT providing a list of which pixels to average with, it also gives a list of weights for those pixel values in the form of bit shifts, allowing more control over the final output
this mode is unique in that it performs no multiplication or division, relying entirely on bit shifts, while the other modes all require a single multiply per color channel

5x5 dynamic subset: this mode is very similar to 3x3 average, but rather than using only a 3x3 window, it uses an up-to-16-sample subset of a 5x5 window, checking near the original sample first, then expanding its range if it cannot find 16 slots
this mode fixes the "stippling" of the 3x3 average mode, but has slightly worse locality, potentially utilizing unwanted samples from disconnected features