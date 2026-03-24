import io

from PIL import Image

MAX_WIDTH = 1920
QUALITY = 85
IMAGE_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'image/tiff'}


def is_image(content_type: str) -> bool:
    return content_type in IMAGE_MIME_TYPES


def compress_image(file) -> io.BytesIO:
    """Ridimensiona e comprime un'immagine in JPEG.

    - Larghezza massima: 1920px (mantiene le proporzioni)
    - Qualità JPEG: 85
    - Converte RGBA/palette → RGB (JPEG non supporta trasparenza)
    - Restituisce un BytesIO pronto per essere assegnato a InMemoryUploadedFile
    """
    img = Image.open(file)

    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=QUALITY, optimize=True)
    output.seek(0)
    return output
