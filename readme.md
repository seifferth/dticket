# DTicket Wallet Tools

DTicket Wallet Tools are a set of tools (mainly one tool so far) for
managing digital Deutschland-Ticket public transport passes issued as
UIC-Barcodes. This set of tools includes support for a number of input
formats including PNG, PDF, and PKPASS. Since UIC is a European standard
for railway ticketing, these tools will probably also work for a number
of other digital tickets. They have not yet been tested with anything
beside the Deutschland-Ticket, however.


## Context

The Deutschland-Ticket is subscription-based monthly pass for public
transport that is valid in most trains (except for IC, ICE, and a few
others) and all (I believe) metropolitan public transport networks
throughout Germany. On a technical level, this ticket can take a number
of forms which seem to be based on the different ticketing systems of
the various public transport networks.

The most sensible implementation for digital ticketing seems to be the
on based on the UIC standard developed by the European Union Agency
for Railways (ERA). According to the UIC standard, a railway ticket is
a sequence of bytes that follows a certain format (which includes a DSA
signature by the issuer) and that is supposed to be presented as a barcode
(usually Aztec) for verification. The binary format consists of two parts:

1. an uncompressed header which contains the signature and a few further
   details, such as the magic number `#UT`, a version number, a numeric ID
   identifying the ticket's issuer, and the length of the compressed data
2. a single zlib-compressed block of ticket data which, in turn, is
   further divided into multiple sections. Currently, these sections
   seem to be:
    a) U_HEAD, containing, among others, another copy of the issuer's
       numeric ID
    b) U_TLAY, a "layout-based" description of the ticketing data (i. e.
       a number of commands for printing individual monospace letters
       into specified columns and rows of a grid, which might conceivably
       be overlaid onto a ticketing form)
    c) U_FLEX, an ASN.1 encoded representation of the ticketing data
       which can be decoded into key-value pairs

It looks like the inclusion of U_TLAY in the Deutschland-Ticket will be
deprecated from January 2025 on.


## Installing

DTicket consists of two tools: dticket-convert and dticket-insert. Both of
these should be copied to any one of the directories mentioned in PATH and
marked as executable. The filename extensions (.py and .sh respectively)
should be removed as part of this process. Furthermore, dticket-insert
depends on dticket-convert being available via PATH with that exact name.

Also make sure that python3 and the following python3 libraries are
available on your system:

* PIL (package 'python3-pil' on debian)
* weasyprint (package 'weasyprint' on debian)
* fitz (package 'python3-fitz' on debian)
* zxingcpp (package 'python3-zxing-cpp' on debian)


## Usage

The dticket-convert command can be used to convert tickets between
multiple representations. It supports the following formats:

Input: PDF (containing a PNG-formatted image of the barcode), PNG,
PKPASS (basically zipped json purposed for the apple wallet), BINARY
(the full sequence of bytes to be displayed in the barcode)

Output: PDF (containing a PNG-formatted image of the barcode), BINARY
(the full sequence of bytes displayed in the barcode), some partial
binary representations

For more information, see `dticket-convert -h`.


The dticket-insert command is a small wrapper around dticket-convert that
can be used to quickly insert a ticket (in pdf format) into the user's
personal wallet at ~/tickets/. The first argument to dticket-insert
specifies part of the filename, the second argument specifies the input
file, which can be in any of the supported input formats (also see
`dticket-insert -h`). The wallet at ~/tickets/ can then, for example,
be synchronized to a portable device such as a smartphone or e-reader
where the ticket can be presented with regular pdf viewing applications.


## Disclaimer

While these tools provide a technically feasible way to manage
UIC-Tickets, there is no guarantee that the tickets converted with
dticket-convert will be accepted by transport agents. This is especially
true for some of the metropolitan transport networks that have still not
equipped their agents with smartphones running the appropriate ticket
verification apps. Instead, some networks seem to rely on their agents'
ability to verify DSA signatures by looking very closely at the barcode
and by running their fingers across the screen. As can be imagined,
this "manual" signature verification method is rather error-prone and
data that are entirely unrelated to the ticket itself (such as fonts
displayed above, below, and beside the barcode) can greatly increase
the risk of producing false negatives.

Also note that Deutschland-Tickets printed on paper are explicitly stated
to be invalid, regardless of the outcome of DSA signature verification.
Displaying barcodes in smartphone applications and digital wallets
is explicitly allowed, however, and there seems to be no further
specification of what constitutes a digital wallet and what kind of
digital wallet can be used. I have not found any mention of tickets
printed on any other material than paper.

Conclusion: Use these tools at your own risk. Software freedom might
depend on winning court cases.


## License

All code in this repository is licensed under the terms of the GNU
General Public License version 3 or later. See also `license.txt`.


## Further Reading

Deutschlandtarifverbund GmbH (Ed.) 2022. Ergebnisdokument
Deutschlandticket UIC. Schaffung einer einheitlichen Barcodeausgabe
nach UIC und einer Barcodekontrolle nach UIC und VDV-KA. [German] URL:
<https://www.kcd-nrw.de/fileadmin/user_upload/01_Ergebnisdokument_Deutschlandticket_UIC__V1.02.pdf>

European Union Agency for Railways (Ed.) 2023. Digital
Security Elements for Rail Passenger Ticketing. [English] URL:
<https://www.era.europa.eu/system/files/2023-06/ERA-OPI-2023-4%20-%20ERA_Technical_Document_TAP_B_12.pdf>
