import datetime
import hashlib
import random

DEBUG = 0
INFO = 1
WARN = 2
ERROR  = 3
FATAL = 4

def generate_text_color(text):
    # Use hashlib to generate a hash value from the input text
    hash_value = hashlib.sha256(text.encode()).hexdigest()
    
    # Take the first 6 characters of the hash value to represent the RGB color
    color_hex = hash_value[:6]
    
    # Convert the hexadecimal color code to an RGB tuple
    r = int(color_hex[0:2], 16)
    g = int(color_hex[2:4], 16)
    b = int(color_hex[4:6], 16)
    
    return r, g, b

def colorize_text(text, r, g, b):
    color_code = f"\x1b[38;2;{r};{g};{b}m"  # ANSI escape code for 24-bit color
    reset_code = "\x1b[0m"  # Reset color to default
    return f"{color_code}{text}{reset_code}"

def apply_color(text):
    r,g,b = generate_text_color(text)
    return colorize_text(text, r, g, b)

def form_header(router, state):
    return "[" + colorize_text(state, 255,0,0) + ":" + colorize_text(router.tags[0],0,245,0) + ":" + colorize_text(datetime.datetime.now().isoformat()[2:-5],0,0,245) + "]:"

def debug(router, *args):
    try:
        if (router.verbosity <= DEBUG): 
            print(form_header(router, "DEBUG"), *args)
    except:
        print(form_header(router, "DEBUG"), *args)
def info(router, *args):
    try:
        if (router.verbosity <= INFO): 
            print(form_header(router, "INFO"), *args)
    except:
        print(form_header(router, "DEBUG"), *args)
def error(router, *args):
    if (router.verbosity <= ERROR): 
        print(form_header(router, "ERROR"), *args)

def fatal(router, *args):
    print(form_header(router, "FATAL"), args)

