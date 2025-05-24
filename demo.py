from attachments import Attachment, attach, load, modify, present, adapt, loader, modifier

@loader(lambda att: att.path.lower().endswith(('.heic', '.heif'))) #matcher
def heic_to_pillow(att: Attachment) -> Attachment:
    """Load HEIC files with pillow-heif support."""
    from pillow_heif import register_heif_opener; register_heif_opener()
    from PIL import Image
    att._obj = Image.open(att.path)
    return att

@modifier  
def crop(att: Attachment, img: 'PIL.Image.Image') -> Attachment:
    """Crop: [crop:x,y,w,h]"""
    if 'crop' not in att.commands: return att
    # Support only box format "x1,y1,x2,y2"
    att._obj = img.crop(att.commands['crop'])
    return att

@modifier
def rotate(att: Attachment, img: 'PIL.Image.Image') -> Attachment:
    """Rotate: [rotate:degrees] (positive = clockwise)"""
    if 'rotate' in att.commands:
        att._obj = img.rotate(-float(att.commands['rotate']), expand=True)
    return att

###################################################################################################
# Demo: Multiple approaches work seamlessly
# 1. Direct usage of the functions to get claude ready messages
result1 = (attach("IMG_2160.HEIC")
          | load.heic_to_pillow 
          | modify.crop("100,100,400,300") 
          | modify.rotate(90) 
          | present.images
          | adapt.claude("What do you see?"))

# 2. Define a function with the verbs and call it with the path
image_processor = load.heic_to_pillow | modify.crop | modify.rotate | present.images
image_processor("IMG_2160.HEIC[crop:50,50,200,200][rotate:45]").claude("What do you see?")

# 3. Universal image processor - handles any format via loader chaining
image_processor = (load.heic_to_pillow | load.image_to_pil  # HEIC then fallback
                  | modify.crop | modify.rotate | present.images)

# Works with HEIC and regular images  
r3 = image_processor("IMG_2160.HEIC[rotate:45]").claude("What's in this photo?")
r4 = image_processor("Figure_1.png").openai_chat("Describe the chart")

