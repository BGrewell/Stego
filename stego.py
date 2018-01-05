import os
import argparse
from PIL import Image

class BitmapEncoder():

    image = None

    def __init__(self, cover_image):
        self.image = Image.open(cover_image)

    def encode_simple_raw_message(self, message, output):
        '''

        :param message:
        :return:
        '''
        rgb_source = self.image.convert('RGB') # convert image to rgb
        pixels = rgb_source.load() # load the pixel map
        width, height = rgb_source.size # get the size of the image
        max_cover_message_length = width * height # calculate the maximum amount of information we can hide
        total_message_length = len(message) + 4 # store the total length of the message
        if (total_message_length > max_cover_message_length | total_message_length > 4294967295): # make sure the message is smaller then the cover medium and our 32 bit value
            raise Exception('Message length must be smaller or the cover image must be larger.')
        msg_len_a = total_message_length >> 24 # split the message length into 4 bytes
        msg_len_b = (total_message_length & 0xFF0000) >> 16
        msg_len_c = (total_message_length & 0xFF00) >> 8
        msg_len_d = (total_message_length & 0xFF)
        msg_len = [msg_len_a, msg_len_b, msg_len_c, msg_len_d] # Place the bytes into a list
        for idx in range(0, total_message_length):
            y = int(idx / width)
            x = idx % width
            if (idx < 4):
                working_byte = msg_len[idx]
            else:
                working_byte = ord(message[idx-4])
            r_bits = working_byte >> 5  # get the 3 bits we will hide in the red component
            g_bits = (working_byte & 0b00011100) >> 2  # get the 3 bits we will hide in the green component
            b_bits = (working_byte & 0b00000011)  # get the 2 bits we will hide in the blue component
            r, g, b = rgb_source.getpixel((x, y))  # get the current r,g,b values
            mod_r, mod_g, mod_b = (r & 0b11111000) + r_bits, (g & 0b11111000) + g_bits, (b & 0b11111100) + b_bits  # hide the message bits in the r,g,b channels
            pixels[x, y] = (mod_r, mod_g, mod_b)  # set the pixel to the modified values
        rgb_source.save(output) # save the image out

    @staticmethod
    def decode_simple_raw_message(image):
        rgb_source = Image.open(image).convert('RGB')
        width, height = rgb_source.size
        embedded_message_length = 0
        for idx in range(0,4):
            r, g, b = rgb_source.getpixel((idx,0))
            original_byte = ((r & 0x7) << 5) + ((g & 0x7) << 2) + (b & 3)
            embedded_message_length += original_byte << (8 * (3 - idx))
        message = ''
        for idx in range(4, embedded_message_length):
            y = int(idx / width)
            x = idx % width
            r, g, b = rgb_source.getpixel((x, y))
            original_byte = ((r & 0x7) << 5) + ((g & 0x7) << 2) + (b & 3)
            message += chr(original_byte)
        return message




if __name__ == '__main__':
    '''
    Modes:
        -h Hide
        -x Extract
    -i Input Image (always required)
    -o Output Image (required on -h)
    -a Algorithm (defaults to simple))
    Message
    '''
    parser = argparse.ArgumentParser('Stego is a steganography tool used to hide messages inside of BMP and PNG files.')
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True
    hide_parser = subparsers.add_parser('hide', help='command to hide message inside of a cover image')
    hide_parser.add_argument('-c', dest='cover', required=True, help='location of cover image to hide message inside')
    hide_parser.add_argument('-o', dest='output', required=True, help='location to place the output image')
    hide_parser.add_argument('message', help='message to hide in cover image')
    extract_parser = subparsers.add_parser('extract', help='command to extract message from a cover image')
    extract_parser.add_argument('-i', dest='input', required=True, help="path to image containing message")
    args = parser.parse_args()

    if args.cmd == 'hide':
        print('[+] Stego - Hiding message inside of cover image')
        if not os.path.isfile(args.cover) and os.access(args.cover, os.R_OK):
            print('[-] Error: Cover file is not accessible.')
            exit(-1)
        filename, extension = os.path.splitext(args.cover)
        if (not extension == '.bmp') and (not extension == '.png'):
            print('[-] Error: Cover file must be a .bmp or .png file.')
            exit(-1)
        encoder = BitmapEncoder(args.cover)
        encoder.encode_simple_raw_message(args.message, args.output)
        print('\tMessage has been hidden.')
        print('\tSaved to', args.output)
    elif args.cmd == 'extract':
        print('[+] Stego - Extracting hidden message inside of cover image')
        message = BitmapEncoder.decode_simple_raw_message(args.input)
        print('\t', message)
    else:
        print(parser.print_help())