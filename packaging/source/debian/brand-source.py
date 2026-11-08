#!/usr/bin/env python3
"""Replace application marks with original NullWire artwork before compilation."""
import ctypes as c
from pathlib import Path
import struct
import sys

class Rectangle(c.Structure):
    _fields_=[(name,c.c_double) for name in ('x','y','width','height')]


def renderer():
    svg=c.CDLL('librsvg-2.so.2');cairo=c.CDLL('libcairo.so.2');obj=c.CDLL('libgobject-2.0.so.0')
    svg.rsvg_handle_new_from_file.argtypes=[c.c_char_p,c.c_void_p];svg.rsvg_handle_new_from_file.restype=c.c_void_p
    svg.rsvg_handle_render_document.argtypes=[c.c_void_p,c.c_void_p,c.POINTER(Rectangle),c.c_void_p];svg.rsvg_handle_render_document.restype=c.c_int
    cairo.cairo_image_surface_create.argtypes=[c.c_int,c.c_int,c.c_int];cairo.cairo_image_surface_create.restype=c.c_void_p
    cairo.cairo_create.argtypes=[c.c_void_p];cairo.cairo_create.restype=c.c_void_p
    cairo.cairo_surface_write_to_png.argtypes=[c.c_void_p,c.c_char_p];cairo.cairo_surface_write_to_png.restype=c.c_int
    cairo.cairo_destroy.argtypes=[c.c_void_p];cairo.cairo_surface_destroy.argtypes=[c.c_void_p];obj.g_object_unref.argtypes=[c.c_void_p]
    return svg,cairo,obj


def render(asset,target,width,height):
    svg,cairo,obj=renderer()
    handle=svg.rsvg_handle_new_from_file(bytes(asset),None)
    if not handle:raise ValueError('cannot load original NullWire artwork')
    surface=cairo.cairo_image_surface_create(0,width,height);context=cairo.cairo_create(surface)
    try:
        if not svg.rsvg_handle_render_document(handle,context,c.byref(Rectangle(0,0,width,height)),None):raise ValueError('SVG rendering failed')
        if cairo.cairo_surface_write_to_png(surface,bytes(target)):raise ValueError('PNG writing failed')
    finally:
        cairo.cairo_destroy(context);cairo.cairo_surface_destroy(surface);obj.g_object_unref(handle)


def brand(root):
    root=Path(root).resolve(strict=True);asset=Path(__file__).resolve().with_name('nullwire.svg')
    art=root/'Telegram/Resources/art'
    targets=sorted(set(art.glob('icon*.png'))|set(art.glob('logo_*.png')))
    if not targets:raise ValueError('application icon resources are missing')
    for path in targets:
        if not path.resolve(strict=True).is_relative_to(root):raise ValueError('icon path escapes source tree')
        with path.open('rb') as f:header=f.read(24)
        if header[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('unexpected icon format')
        width,height=struct.unpack('>II',header[16:24])
        if not (0<width<=2048 and 0<height<=2048):raise ValueError('unexpected icon dimensions')
        render(asset,path,width,height)
    tray=root/'Telegram/Resources/icons'
    symbolic='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="M110 80h292v272H235l-93 66v-66h-32Z" fill="none" stroke="#000" stroke-width="36" stroke-linejoin="round"/><path d="m165 165 55 55-55 55m97 0h60" fill="none" stroke="#000" stroke-width="28" stroke-linecap="round"/></svg>'''
    for name in ['tray_monochrome.svg','tray_monochrome_attention.svg','tray_monochrome_mute.svg']:
        path=tray/name
        if path.is_file():
            text=symbolic
            if name.endswith('_attention.svg'):text=text.replace('</svg>','<circle cx="405" cy="88" r="55" fill="#000"/></svg>')
            elif name.endswith('_mute.svg'):text=text.replace('</svg>','<path d="m78 65 360 360" stroke="#000" stroke-width="35"/></svg>')
            path.write_text(text)
    print(f'Installed original NullWire artwork in {len(targets)} application resources')

if __name__=='__main__':brand(sys.argv[1])
