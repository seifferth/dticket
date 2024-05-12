#!/usr/bin/env python3

import sys, os
from getopt import gnu_getopt as getopt

_cli_help = """
Usage: dticket-convert [-h|-o FILE] FILE

Further Options:
    --dump-binary
    --dump-signature
    --dump-data
""".lstrip()

_css_style = """
.left, .right {
    font-family: Noto Sans, Sans Serif;
    display: block;
    float: left;
}
.left {
    margin-left: 2.4cm;
    padding-right: 1.8cm;
}
.left > h1 {
    padding-top: 1.2cm;
    padding-bottom: .5cm;
}
.left > img {
    width: 7.7cm;
}
.binary {
    font-size: 91%;
    color: #777777;
}
@page {
    size: a5 landscape;
    margin: -.7cm;
}
"""
_new_html = """
<style>{stylesheet}</style>

<div class="left">
<h1>Deutschlandticket</h1>
<img src="data:image/png;base64,{aztec_code_base64}" />
<p>{validity}</p>
</div>

<div class="right binary">
<pre>{signature}</pre>
<pre>{full_data}</pre>
</div>
</p>
"""
def write_pdf(aztec_code: bytes, aztec_info: dict, outfile) -> None:
    import weasyprint, base64
    newdoc = weasyprint.HTML(string = _new_html.format(
        aztec_code_base64 = base64.b64encode(aztec_code).decode('ascii'),
        stylesheet = _css_style, **aztec_info,
    ))
    newdoc.write_pdf(outfile)

def extract_aztec_code(input_pdf) -> bytes:
    import fitz
    d = fitz.open(input_pdf)
    pno, imgno = 0, -1      # This is where the aztec code is usually located
                            # in the pdf: The last image on the first page.
    aztec_code = d.extract_image(d.get_page_images(pno)[imgno][0])['image']
    return aztec_code

def decode_aztec_code(image: bytes) -> tuple[bytes,bytes,bytes]:
    import zxingcpp
    from PIL import Image
    from io import BytesIO
    binary = zxingcpp.read_barcodes(Image.open(BytesIO(aztec_code)))[0].bytes
    # See <https://stackoverflow.com/questions/34423303> for what follows
    import zlib
    signature = binary[:68]             # Apparently a DSA signature
    data = zlib.decompress(binary[68:])
    return binary, signature, data

def interpret_aztec_data(signature: bytes, data: bytes) -> dict:
    # For more info also see <https://github.com/pbock/ticket-parser> and
    # <https://github.com/rumpeltux/onlineticket/blob/master/onlineticket.py>
    # which I did not yet incorporate here.
    import textwrap
    def display_binary(binary: bytes) -> str:
        cleaned = str(binary)[2:-1] \
                        .replace('\n', '↵') \
                        .replace('\t', '›') \
                        .replace(' ', '·')
        return textwrap.fill(cleaned, width=40, break_on_hyphens=False)
    d = dict()
    # Ticket validity
    i = data.find(b'Gueltig ')
    d['validity'] = 'Gültig '+data[i+8:i+37].decode('ascii')
    # Full data decoded using an 8-bit decoding
    d['signature'] = display_binary(signature)
    d['full_data'] = display_binary(data)
    return d

if __name__ == "__main__":
    opts, args = getopt(sys.argv[1:], 'ho:', ['help', 'output=',
                        'dump-signature', 'dump-data', 'dump-binary'])
    outfile = sys.stdout.buffer
    dump_binary, dump_signature, dump_data = False, False, False
    for k, v in opts:
        if k in ['-h', '--help']:
            print(_cli_help); exit(0)
        elif k in ['-o', '--output']:
            outfile = open(os.path.expanduser(v), 'wb')
        elif k == '--dump-binary':
            dump_binary = True
        elif k == '--dump-signature':
            dump_signature = True
        elif k == '--dump-data':
            dump_data = True
    if len(args) != 1:
        print(_cli_help, file=sys.stderr); exit(1)

    with open(args[0], 'rb') as f:
        aztec_code = extract_aztec_code(f)
    binary, signature, data = decode_aztec_code(aztec_code)
    if dump_binary or dump_signature or dump_data:
        if dump_signature: sys.stdout.buffer.write(signature)
        if dump_data: sys.stdout.buffer.write(data)
        if dump_binary: sys.stdout.buffer.write(binary)
        exit(0)
    aztec_info = interpret_aztec_data(signature, data)
    write_pdf(aztec_code, aztec_info, outfile)
