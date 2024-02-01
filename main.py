import zlib
from decompress import *

# Test decompress on zlib compressed data

input_data = b'As noted above, encoded data blocks in the "deflate" format consist of sequences of symbols drawn from three conceptually distinct alphabets: either literal bytes, from the alphabet of byte values (0..255), or <length, backward distance> pairs, where the length is drawn from (3..258) and the distance is drawn from (1..32,768). In fact, the literal and length alphabets are merged into a single alphabet (0..285), where values 0..255 represent literal bytes, the value 256 indicates end-of-block, and values 257..285 represent length codes (possibly in conjunction with extra bits following the symbol code) as follows:'

print("INPUT DATA:")
print(input_data, "\n")

compressed_data = zlib.compress(input_data)
output_data = decompress(compressed_data)

print("OUTPUT DATA:")
print(output_data)
