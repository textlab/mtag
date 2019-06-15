# The Oslo-Bergen Multitagger for Norwegian Bokmål and Nynorsk

The Python version has been written by Michał Kosek (Text Laboratory,
University of Oslo).

The code is partially based on the Perl Multitagger written by Lars Jørgen
Tvedt (Dokumentasjonsprosjektet, University of Oslo).

The output of the multitagger reproduces the format used by the Lisp
Multitagger written by Paul Meurer, University of Bergen. To produce an output
that most resembles the Lisp version, use -compat in the command line.

The compound analyser has been written by Michał Kosek, using rules formulated
by Janne Bondi Johannessen and Helge Hauglin (1998).

The code is freely available under the MIT licence. The associated grammatical
information comes from Norsk Ordbank, National Library of Norway, and is
available under the CC-BY licence.

Bug reports and comments can be directed to tekstlab-post@iln.uio.no.

Johannessen, J. B., & Hauglin, H. (1998). *An automatic analysis of Norwegian compounds.*

## Troubleshooting
The multitagger will refuse to process invalid UTF-8:

    $ ./mtag.py textfile
    Traceback (most recent call last):
    [...]
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf8 in position 1252: invalid start byte

It usually means that the input file has different encoding, and needs to be converted
to UTF-8 before processing. However, if you are sure you want to process the file with
invalid UTF-8 as it is, call the tagger as follows:

    $ PYTHONIOENCODING=utf-8:surrogateescape ./mtag.py < textfile

Note that this requires Python 3, and that the input needs to be provided by
redirecting stdin with <.
