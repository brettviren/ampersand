'''
Set X11 background.
'''

import click

# fixme: put a layer of indirection to allow swapping different image loaders
from sh import feh as set_bkg_cmd

from pathlib import Path
import os
from PIL import Image
import random
import time
import tempfile
import socket
from Xlib.display import Display

hostname = socket.gethostname()

def get_screen_size():
    display = Display(os.environ.get("DISPLAY",":0.0"))
    root = display.screen().root
    w = root.get_geometry().width
    h = root.get_geometry().height
    return (w,h)
#screen_size = get_screen_size()
#print (screen_size)

def do_crop(image):
    sw,sh = get_screen_size()
    sratio = float(sw)/float(sh)

    iw,ih = image.size
    iratio = float(iw)/float(ih)
    #print sratio,iratio

    if sratio > iratio:             # image is portrait
        crop_width = iw
        crop_height = int(iw/sratio)
        x = 0
        y = random.randint(0,ih-crop_height)
        return image.crop((x,y,x+crop_width,y+crop_height)).resize((sw,sh))

    elif sratio < iratio:         # image is landscape
        crop_width = int(ih*sratio)
        crop_height = ih
        x = random.randint(0,iw-crop_width)
        y = 0
        return image.crop((x,y,x+crop_width,y+crop_height)).resize((sw,sh))

    return image.resize((sw,sh))


def shape_background(infile, outfile):
    '''
    Take infile and optimally shape it to fit the root window saving
    it to outfile.
    '''
    with open(infile, 'rb') as infp:
        image  = Image.open(infp)
        crop = do_crop(image)
        crop.save(outfile,quality=95)

        del(crop)
        del(image)
    return

def set_background(fname):
    set_bkg_cmd(["--bg-fill", fname])

def get_file(dname):
    picdir = os.path.expandvars(dname)
    for path,subdir,files in os.walk(picdir):
        touse = list()
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext.lower() in ['.png','.jpg','.jpeg']:
                touse.append(f)
        files = touse
        while True:
            fname = random.choice(files)
            if fname[0] != '.':
                fname = os.path.join(path,fname)
                if os.path.exists(fname):
                    return fname
            continue
        continue
    print ('No files found in "%s"' % picdir)
    return None


@click.group("ampersand")
@click.pass_context
def cli(ctx):
    '''
    Set display backgrounds.
    '''
    pass


def do_one(directory):
    infile = get_file(directory)
    orig,ext = os.path.splitext(infile)
    fp,outfile = tempfile.mkstemp(ext)
    try:
        shape_background(infile,outfile)
    except Exception as msg:
        warn("failed to shape pic: %s" % infile)
        return
    set_background(outfile)
    if os.path.exists(outfile):
        os.close(fp)        # without this it will leak open files
        os.remove(outfile)

    
@cli.command("once")
@click.option("-d", "--directory",
              default = Path.home() / "Desktop" / "bkg",
              help="The directory from which images are sampled")
def cmd_once(directory):
    '''
    Load a random image from the directory to the display background
    '''
    do_one(directory)

@cli.command("cycle")
@click.option("-d", "--directory",
              default = Path.home() / "Desktop" / "bkg",
              help="The directory from which images are sampled")
@click.option("-p","--period",
              default = 300,
              help="The cycle period in seconds")
def cmd_cycle(directory, period):
    '''
    Cycle through files in given directory and display them for given delay
    '''
    while True:
        do_one(directory)
        time.sleep(period)
    return

def main():
    cli(obj=dict())

if '__main__' == __name__:
    main()

 

