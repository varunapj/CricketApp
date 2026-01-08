from pathlib import Path
svg = Path('static/images/architecture.svg')
png = Path('static/images/architecture.png')

if not svg.exists():
    raise SystemExit('SVG not found: ' + str(svg))

out = {'created': False, 'method': None, 'errors': []}

try:
    import cairosvg
    cairosvg.svg2png(url=str(svg), write_to=str(png))
    out['created'] = True
    out['method'] = 'cairosvg'
except Exception as e:
    out['errors'].append(('cairosvg', repr(e)))
    try:
        from PIL import Image, ImageDraw, ImageFont
        w,h = 1200,720
        img = Image.new('RGB',(w,h),(255,255,255))
        draw = ImageDraw.Draw(img)
        text = 'Architecture Diagram (raster fallback)\nSee architecture.svg for the vector version.'
        try:
            font = ImageFont.truetype('DejaVuSans.ttf',24)
        except Exception:
            font = ImageFont.load_default()
        draw.multiline_text((40,40), text, fill=(0,0,0), font=font)
        img.save(str(png))
        out['created'] = True
        out['method'] = 'Pillow'
    except Exception as e2:
        out['errors'].append(('pillow', repr(e2)))

print(out)
