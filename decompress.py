from stream import *
from huffman import *

# Inflate block where BTYPE == 0b00
def inflate_block_no_compression(stream, out_data):
	# read_bytes will discard remaining bits after BTYPE until next byte boundary
	LEN = stream.read_bytes(2)
	NLEN = stream.read_bytes(2)

	for i in range(LEN):
		out_data.append(stream.read_byte())

# Write n bits from coded_bits into bytes according to DEFLATE specification
def huffman_coded_bits_to_bytes(coded_bits, n):
	result = []
	result.append(0)
	bit_index = 0

	for i in range(n-1, -1, -1):
		if bit_index > 7:
			result.append(0)
			bit_index = 0
		result[-1] |= ((coded_bits >> i) & 1) << bit_index
		bit_index += 1
	
	return bytes(result)

# Code length order table
CodeLengthCodesOrder = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]

# Create literal/length and distance trees by creating and using code length tree
def decode_trees(stream):
	# Number of literal/length codes
	HLIT = stream.read_bits(5) + 257

	# Number of distance codes
	HDIST = stream.read_bits(5) + 1

	# Number of code length codes
	HCLEN = stream.read_bits(4) + 4

	# Read code lengths for the code length alphabet
	code_length_bl_list = [0] * 19
	for i in range(HCLEN):
		code_length_bl_list[CodeLengthCodesOrder[i]] = stream.read_bits(3)

	# Construct code length tree
	code_length_tree = huffman_tree_from_alphabet_and_bl_list(range(19), code_length_bl_list)

	# Read literal/length + distance code length list
	bl_list = []
	while len(bl_list) < HLIT + HDIST:
		symbol = decode_symbol(stream, code_length_tree)
		assert(0 <= symbol <= 18), "Invalid symbol"

		if symbol < 16: # literal value
			bl_list.append(symbol)
		elif symbol == 16:
			# Copy previous code length 3 to 6 times
			prev_code_length = bl_list[-1]
			repeat_length = stream.read_bits(2) + 3
			for i in range(repeat_length):
				bl_list.append(prev_code_length)
		elif symbol == 17:
			# Repeat code length 0 3 to 10 times
			repeat_length = stream.read_bits(3) + 3
			for i in range(repeat_length):
				bl_list.append(0)
		else: # symbol == 18
			# Repeat code length 0 11 to 138 times
			repeat_length = stream.read_bits(7) + 11
			for i in range(repeat_length):
				bl_list.append(0)

	# Construct trees
	literal_length_tree = huffman_tree_from_alphabet_and_bl_list(range(286), bl_list[:HLIT])
	distance_tree = huffman_tree_from_alphabet_and_bl_list(range(30), bl_list[HLIT:])
	return literal_length_tree, distance_tree

# LZ77 tables
LengthBase = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258]
LengthExtraBits = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0]
DistanceBase = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577]
DistanceExtraBits = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13]

# Inflate compressed block using provided literal/length and distance trees
def inflate_compressed_block(stream, literal_length_tree, distance_tree, out_data):
	while True:
		symbol = decode_symbol(stream, literal_length_tree)
		# Handle literals
		if symbol < 256:
			out_data.append(symbol)

		# Handle end of block
		elif symbol == 256:
			return

		# Handle <length, distance> pair
		else:
			# Get index into LZ77 tables
			i = symbol - 257
			length = LengthBase[i] + stream.read_bits(LengthExtraBits[i])
			symbol = decode_symbol(stream, distance_tree)
			distance = DistanceBase[symbol] + stream.read_bits(DistanceExtraBits[symbol])
			# Copy bytes indicated by <length, distance> pair
			for i in range(length):
				out_data.append(out_data[-distance])

# Inflate block where BTYPE == 0b01
def inflate_block_fixed_huffman(stream, out_data):
	# Construct fixed literal/length tree
	bl_list = []
	for i in range(144):
		bl_list.append(8)
	for i in range(144, 256):
		bl_list.append(9) 
	for i in range(256, 280):
		bl_list.append(7)
	for i in range(280, 286):
		bl_list.append(8) 
	literal_length_tree = huffman_tree_from_alphabet_and_bl_list(range(286), bl_list)

	# Construct fixed distance tree
	bl_list = [5] * 30
	distance_tree = huffman_tree_from_alphabet_and_bl_list(range(30), bl_list)

	inflate_compressed_block(stream, literal_length_tree, distance_tree, out_data)

# Inflate block where BTYPE == 0b10
def inflate_block_dynamic_huffman(stream, out_data):
	# Construct literal/length and distance trees encoded in stream
	literal_length_tree, distance_tree = decode_trees(stream)
	inflate_compressed_block(stream, literal_length_tree, distance_tree, out_data)

def inflate(stream):
	# BFINAL indicates final block in DEFLATE stream
	BFINAL = 0
	inflated_data = []

	while not BFINAL:
		BFINAL = stream.read_bit()
		BTYPE = stream.read_bits(2)
		assert(BTYPE != 0b11), "BTYPE == 3 invalid"

		if BTYPE == 0b00:
			inflate_block_no_compression(stream, inflated_data)
		elif BTYPE == 0b01:
			inflate_block_fixed_huffman(stream, inflated_data)
		elif BTYPE == 0b10:
			inflate_block_dynamic_huffman(stream, inflated_data)

	return bytes(inflated_data)

# Main user-facing function
def decompress(memory):
	stream = Stream(memory)

	CMF = stream.read_byte()
	# Compression method
	CM = CMF & 0b1111
	# CM == 8 means DEFLATE compression
	assert(CM == 8), "CM != 8 invalid"

	# Compression info
	CINFO = CMF >> 4
	# CINFO > 7 means LZ77 window size would exceed maximum in specification
	assert(CINFO <= 7), "CINFO > 7 invalid"

	FLG = stream.read_byte()
	assert((CMF * 256 + FLG) % 31 == 0), "CMF and FLG checksum failed"

	# Preset dictionary
	FDICT = (FLG >> 5) & 1
	assert(FDICT == 0), "FDICT == 1 not supported"

	# Decompress DEFLATE data
	data = inflate(stream)

	# ALDER32 checksum
	ALDER32 = stream.read_bytes(4)

	return data
