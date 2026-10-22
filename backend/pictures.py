"""Bounded, re-encoded pictures for profiles, banners, and folders; preserves animated GIFs."""
import io
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException


def normalize_picture(data, cover=False, banner=False):
    try:
        with Image.open(io.BytesIO(data), formats=['PNG', 'JPEG', 'WEBP', 'GIF']) as source:
            if source.width * source.height > 16_000_000:
                raise HTTPException(400, 'Choose an image with no more than 16 million pixels.')
            source.seek(0)
            
            # Preserve animated or static GIFs as GIF format
            if source.format == 'GIF':
                output = io.BytesIO()
                source.save(output, format='GIF', save_all=True)
                return output.getvalue()
            
            # Convert non-GIF images to WebP with proper sizing
            image = ImageOps.exif_transpose(source).convert('RGB')
            target_size = (960, 320) if banner else ((960, 540) if cover else (256, 256))
            image = ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS)
            output = io.BytesIO()
            image.save(output, format='WEBP', quality=85, exif=b'')
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(400, 'Choose a valid PNG, JPG, WebP or GIF image.')