#!/usr/bin/env python2

from PIL import Image
import math
import StringIO
import os
import sys

class FileReader(object):
    def __init__(self, path):
        if isinstance(path, file):
            if path.name == "<stdin>":
                infile = sys.stdin.read()
                self.length = len(infile)
                self.file = StringIO.StringIO(infile)
            else:
                self.length = os.path.getsize(path.name)
                self.file = path
        else:
            self.length = os.path.getsize(path)
            self.file = open(path)
    def __len__(self):
        return self.length
    def __getattr__(self, attr):
        return getattr(self.file, attr)
    def __iter__(self):
        return iter(self.file)

def choose_file_dimensions(infile, input_dimensions = None):
    if input_dimensions is not None and len(input_dimensions) >= 2 and input_dimensions[0] is not None and input_dimensions[1] is not None:
        # the dimensions were already fully specified
        return input_dimensions
    if not isinstance(infile, FileReader):
        infile = FileReader(infile)
    num_bytes = len(infile)
    num_pixels = int(math.ceil(float(num_bytes)))
    sqrt = math.sqrt(num_pixels)
    sqrt = int(math.ceil(sqrt))

    if input_dimensions is not None and len(input_dimensions) >= 1:
        if input_dimensions[0] is not None:
            # the width is specified but the height is not
            if num_pixels % input_dimensions[0] == 0:
                return (input_dimensions[0], num_pixels / input_dimensions[0])
            else:
                return (input_dimensions[0], num_pixels / input_dimensions[0] + 1)
        else:
            # the height is specified but the width is not
            if num_pixels % input_dimensions[1] == 0:
                return (num_pixels / input_dimensions[1], input_dimensions[1])
            else:
                return (num_pixels / input_dimensions[1] + 1, input_dimensions[1])

    if num_pixels % sqrt == 0:
        dimensions = (sqrt, num_pixels / sqrt)
    else:
        dimensions = (sqrt, num_pixels / sqrt + 1)

    return dimensions

def file_to_png(infile, outfile, dimensions = None):
    dimensions = choose_file_dimensions(infile, dimensions)
    img = Image.new('RGB', dimensions)
    pixels = img.load()
    row = 0
    column = -1
    while True:
        b = infile.read(1)
        if not b:
            break
        b = ord(b[0])

        column += 1
        if column >= img.size[0]:
            column = 0
            row += 1
            if row >= img.size[1]:
                raise Exception("TODO: Write exception!")
                
        b_hi = b / 16
        b_lo = b % 16
        parity = (b_hi * 13 + b_lo * 7 + 3) % 16
        color = [b_hi * 16 + 8, b_lo * 16 + 8, parity * 16 + 8]

        pixels[column,row] = tuple(color)

    img.save(outfile, format="PNG")

def png_to_file(infile, outfile):
    img = Image.open(infile)
    rgb_im = img.convert('RGB')
    for row in range(img.size[1]):
        for col in range(img.size[0]):
            b_hi, b_lo, parity = rgb_im.getpixel((col, row))
            b_hi = b_hi / 16
            b_lo = b_lo / 16
            parity = parity / 16

            if (b_hi, b_lo, parity) == (0, 0, 0):
                # End of File
                break

            if (b_hi * 13 + b_lo * 7 + 3) % 16 != parity:
                sys.stderr.write("wrong parity, (%d, %d, %d)", b_hi, b_lo, parity)
            outfile.write(chr(b_hi * 16 + b_lo))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="A simple cross-platform script for encoding any binary file into a lossless PNG.", prog="bin2png")

    parser.add_argument('file', type=argparse.FileType('r'), default=sys.stdin, help="the file to encode as a PNG (defaults to '-', which is stdin)")
    parser.add_argument("-o", "--outfile", type=argparse.FileType('w'), default=sys.stdout, help="the output file (defaults to '-', which is stdout)")
    parser.add_argument("-d", "--decode", action="store_true", default=False, help="decodes the input PNG back to a file")
    parser.add_argument("-w", "--width", type=int, default=None, help="constrain the output PNG to a specific width")
    parser.add_argument("-v", "--height", type=int, default=None, help="constrain the output PNG to a specific height")

    args = parser.parse_args()

    if args.decode:
        png_to_file(args.file, args.outfile)
    else:
        dimensions = None
        if args.height is not None or args.width is not None:
            dimensions = (args.width, args.height)
        file_to_png(args.file, args.outfile, dimensions=dimensions)
