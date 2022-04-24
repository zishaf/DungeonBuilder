import numpy as np
import re
import os


# convert an rle file to a 2d numpy array of 1s and 0s
def conway_array_from_rle(filename: str) -> np.ndarray:

    with open(filename) as f:

        line = f.readline()

        # RLE files sometimes start with '#' for comment lines.  ignore these and go to next line
        while line[0] == '#':
            line = f.readline()

        # The first line after that is the header, split on '= ' and ',' to seperate the x and y values
        header_line = re.split(r'= |,', line)
        width, height = header_line[3], header_line[1]

        # Initialize an array of with 2 extra width and height for a bounding box, all false
        arr = np.zeros((int(width)+2, int(height)+2), dtype=bool, order='F')

        # read the last lines that describe the pattern
        line = f.readline()
        continuation = f.readline()
        while continuation:
            line += continuation
            continuation = f.readline()

        # remove the \n (next line) characters and ! (end of file) character from the string and leave the pattern
        line = line.replace('\n]', '')
        line = line.replace('!', '')

        rows = line.split('$')

        for x, row in enumerate(rows):
            # track x_index of the array and how many live cells to draw (string default 0 if there is no number)
            number_string = '0'
            y_index = 1

            for c in row:
                if c.isdigit():
                    number_string += c
                # b denotes dead cells, they remain 0 and x_index is updated
                elif c == 'b':
                    y_index += max(1, int(number_string))
                    number_string = '0'
                # o denotes live cells, make 1s starting from x_index to our number
                elif c == 'o':
                    arr[x+1, y_index:max(y_index+int(number_string), y_index+1)] = True
                    y_index += max(1, int(number_string))
                    number_string = '0'

    return arr


def make_arrays_from_rle():
    arrays = np.ndarray(len(os.listdir('resources/rle')), dtype=np.ndarray)
    for i, file in enumerate(os.listdir('resources/rle')):
        arrays[i] = conway_array_from_rle('resources/rle/' + file)
    np.savez_compressed('resources/life/nparrays', arrays)
