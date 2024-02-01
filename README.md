# zlib-decompress
**Disclaimer: This project is for learning purposes only and is not a specification-compliant ZLIB decompressor.**<br/><br/>
A Python implementation of decompression of [ZLIB](https://www.ietf.org/rfc/rfc1950.txt) compressed data.<br/><br/>
`decompress.py` contains the user-facing function `decompress` which takes in data compressed by `zlib.compress` and returns the decompressed data.<br/><br/>
Running `py main.py` shows an example of compressing input data using `zlib.compress` and decompressing using `decompress`.

## ZLIB format
The ZLIB format has a header that contains details about the compression algorithm used. The only defined compression method is DEFLATE meaning that ZLIB is essentially an extension of the [DEFLATE](https://www.ietf.org/rfc/rfc1951.txt) format. The ZLIB format also adds the option for a "preset dictionary", none of which are defined in the specification, so this implementation does not handle those. Additionally, the ZLIB format includes an Adler-32 checksum to verify data integrity, which this implementation does not calculate.<br/><br/>
DEFLATE uses Huffman coding to convert bytes (each composed of 8 bits) into a string of bits in which the most frequently occurring characters use fewer bits and less frequently occurring characters use more bits. This coding significantly reduces the size of data, especially in written English where some characters are much more common than others.<br/><br/>
DEFLATE also uses LZ77 to compress repeated strings of data by replacing a repeated string with a <length, backward distance> pair referring to a copy of the same string in the decompressed data.
