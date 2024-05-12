#!/usr/bin/env python3

import sys, os
from io import BytesIO
from PIL import Image
from getopt import gnu_getopt as getopt

_cli_help = """
Usage: dticket-convert [OPTION]... [INPUT-FILE]

Options:
    -o FILE,                Write output to FILE instead of stdout.
        --output FILE
    -f FORMAT,              Specify which input format to process. Valid
        --format FORMAT     values are 'binary', 'png', 'pdf', 'pkpass',
                            and 'auto' where 'auto' uses some heuristics
                            to detect the input format automatically.
                            Default: auto.
    --dump-binary           Write the binary contents to stdout.
    --dump-signature        Write the signature header to stdout.
    --dump-data             Write the uncompressed data to stdout.
    -h, --help              Print this help message and exit.
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

def pdf_extract_aztec_code(input_pdf: bytes) -> bytes:
    import fitz
    d = fitz.open('pdf', input_pdf)
    pno, imgno = 0, -1      # This is where the aztec code is usually located
                            # in the pdf: The last image on the first page.
    aztec_code = d.extract_image(d.get_page_images(pno)[imgno][0])['image']
    return aztec_code

def encode_aztec_code(binary: bytes) -> bytes:
    from zxingcpp import write_barcode, Aztec
    barcode = Image.fromarray(write_barcode(Aztec,
        binary.decode('ISO-8859-1'), width=256, height=256))
    png = BytesIO(); barcode.save(png, format='png'); png.seek(0)
    return png.read()

def pkpass_extract_aztec_code(input_pkpass: bytes) -> bytes:
    from zipfile import ZipFile
    import json
    with ZipFile(BytesIO(input_pkpass)).open('pass.json') as f:
        data = json.loads(f.read())['barcodes'][0]['message']
    return encode_aztec_code(data.encode('ISO-8859-1'))

def decode_aztec_code(image: bytes) -> tuple[bytes,bytes,bytes]:
    from zxingcpp import read_barcode
    binary = read_barcode(Image.open(BytesIO(aztec_code))).bytes
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
        cleaned = str(binary)[2:-1].replace(' ', '·')
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
    opts, args = getopt(sys.argv[1:], 'ho:f:', ['help', 'output=', 'format=',
                        'dump-signature', 'dump-data', 'dump-binary'])
    outfile = sys.stdout.buffer; input_format = 'auto'; dump = None
    for k, v in opts:
        if k in ['-h', '--help']:
            print(_cli_help); exit(0)
        elif k in ['-o', '--output']:
            if v == '-': outfile = sys.stdout.buffer
            else: outfile = open(os.path.expanduser(v), 'wb')
        elif k in ['-f', '--format']:
            if v not in ['binary', 'png', 'pdf', 'pkpass', 'auto']:
                exit(f'Invalid input format: {v}')
            input_format = v
        elif k == '--dump-binary':
            if dump and dump != 'binary':
                exit('The dump commands are mutually exclusive')
            dump = 'binary'
        elif k == '--dump-signature':
            if dump and dump != 'signature':
                exit('The dump commands are mutually exclusive')
            dump = 'signature'
        elif k == '--dump-data':
            if dump and dump != 'data':
                exit('The dump commands are mutually exclusive')
            dump = 'data'
    if len(args) == 0: args = ['-']
    if len(args) != 1: exit(_cli_help)

    if args[0] == '-':
        input_data = sys.stdin.buffer.read()
    else:
        with open(args[0], 'rb') as f:
            input_data = f.read()
    if input_format == 'auto':
        if     input_data.startswith(b'#UT01'):     input_format = 'binary'
        elif   input_data.startswith(b'\x89PNG'):   input_format = 'png'
        elif   input_data.startswith(b'%PDF-'):     input_format = 'pdf'
        elif   input_data.startswith(b'PK'):        input_format = 'pkpass'
        else:  exit('Failed to determine input format automatically')
    if input_format == 'binary':
        aztec_code = encode_aztec_code(input_data)
    elif input_format == 'png':
        aztec_code = input_data
    elif input_format == 'pdf':
        aztec_code = pdf_extract_aztec_code(input_data)
    elif input_format == 'pkpass':
        aztec_code = pkpass_extract_aztec_code(input_data)
    binary, signature, data = decode_aztec_code(aztec_code)
    if dump:
        if dump == 'binary':        outfile.write(binary)
        elif dump == 'signature':   outfile.write(signature)
        elif dump == 'data':        outfile.write(data)
    else:
        aztec_info = interpret_aztec_data(signature, data)
        write_pdf(aztec_code, aztec_info, outfile)
