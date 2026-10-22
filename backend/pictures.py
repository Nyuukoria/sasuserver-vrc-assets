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
            
            target_size = (960, 320) if banner else ((960, 540) if cover else (256, 256))
            # Keep GIF animation while applying the same size/metadata rules as other pictures.
            if source.format == 'GIF':
                count = getattr(source, 'n_frames', 1)
                if count > 120 or source.width * source.height * count > 64_000_000:
                    raise HTTPException(400, 'This animation is too large. Use at most 120 frames and 64 million total pixels.')
                frames, durations = [], []
                loop = source.info.get('loop')
                for index in range(count):
                    source.seek(index)
                    frame = ImageOps.fit(source.convert('RGBA'), target_size, method=Image.Resampling.LANCZOS)
                    frame.info.clear()
                    frames.append(frame)
                    durations.append(max(20, int(source.info.get('duration', 100))))
                output = io.BytesIO()
                options = {'loop': loop} if loop is not None else {}
                frames[0].save(output, format='GIF', save_all=True, append_images=frames[1:], duration=durations, disposal=2, **options)
                if output.tell() > 8 * 1024 * 1024:
                    raise HTTPException(400, 'The resized animation is too large. Choose a shorter GIF.')
                return output.getvalue()
            
            # Convert non-GIF images to WebP with proper sizing
            image = ImageOps.exif_transpose(source).convert('RGB')
            image = ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS)
            output = io.BytesIO()
            image.save(output, format='WEBP', quality=85, exif=b'')
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(400, 'Choose a valid PNG, JPG, WebP or GIF image.')
