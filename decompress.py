class ByteStreamer:
	def __init__(self, memory):
		self.memory = memory # Stream of bytes
		self.byte_index = 0 # Index of next byte in stream
		self.bit_index = 0 # Index of current bit in current byte

	# Read next byte from stream starting from next byte boundary
	def read_byte(self):
		# Advance to next byte boundary
		if (self.bit_index > 0):
			self.bit_index = 0
			self.byte_index += 1

		# Read next byte and advance index
		byte = self.memory[self.byte_index]
		self.byte_index += 1
		return byte

	# Read next n bytes from stream starting from next byte boundary
	def read_bytes(self, n):
		bytes = 0
		for i in range(n):
			bytes |= self.read_byte() << (8 * i)
		return bytes

	# Read next bit from stream
	def read_bit(self):
		# Read bit and increment bit index
		bit = (self.memory[self.byte_index] >> self.bit_index) & 1
		self.bit_index += 1

		# Ensure incremented bit index isn't out of bounds
		if self.bit_index > 7:
			self.bit_index = 0
			self.byte_index += 1

		return bit

	# Read next n bits from stream
	def read_bits(self, n):
		bits = 0
		for i in range(n):
			bits |= self.read_bit() << i
		return bits

# Inflate block where BTYPE == 0b00
def inflate_block_no_compression(streamer, out_data):
	# read_bytes will discard remaining bits after BTYPE until next byte boundary
	LEN = streamer.read_bytes(2)
	NLEN = streamer.read_bytes(2)

	for i in range(LEN):
		out_data.append(streamer.read_byte())

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

class HuffmanTreeNode:
	def __init__(self):
		self.left = None
		self.right = None
		self.symbol = ""

class HuffmanTree:
	def __init__(self):
		self.root = HuffmanTreeNode()

	# Insert huffman_code of length n associated with symbol into tree
	def insert(self, huffman_code, n, symbol):
		curr = self.root
		for i in range(n):
			bit = (huffman_code >> (n - i - 1)) & 1

			# Follow right branch
			if bit:
				nxt = curr.right
				if nxt == None:
					curr.right = HuffmanTreeNode()
					nxt = curr.right

			# Follow left branch
			else:
				nxt = curr.left
				if nxt == None:
					curr.left = HuffmanTreeNode()
					nxt = curr.left

			curr = nxt

		# Assign symbol at leaf node
		curr.symbol = symbol

# Decode a symbol from streamer using tree
def decode_symbol(streamer, tree):
	curr = tree.root

	# Read bits and follow tree until leaf node
	while curr.left or curr.right:
		bit = streamer.read_bit()
		if bit:
			curr = curr.right
		else:
			curr = curr.left
	return curr.symbol

# LZ77 tables
LengthBase = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258]
LengthExtraBits = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0]
DistanceBase = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577]
DistanceExtraBits = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13]

def inflate_compressed_block(streamer, literal_length_tree, distance_tree, out_data):
	while True:
		symbol = decode_symbol(streamer, literal_length_tree)
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
			length = LengthBase[i] + streamer.read_bits(LengthExtraBits[i])
			symbol = decode_symbol(streamer, distance_tree)
			distance = DistanceBase[i] + streamer.read_bits(DistanceExtraBits[i])
			# Copy bytes indicated by <length, distance> pair
			for i in range(length):
				out_data.append(out[-distance])

# Inflate block where BTYPE == 0b01
def inflate_block_fixed_huffman(streamer, out_data):
	return

# Inflate block where BTYPE == 0b10
def inflate_block_dynamic_huffman(streamer, out_data):
	return

def inflate(streamer):
	# BFINAL indicates final block in DEFLATE stream
	BFINAL = 0
	inflated_data = []

	while not BFINAL:
		BFINAL = streamer.read_bit()
		BTYPE = streamer.read_bits(2)
		assert(BTYPE != 0b11), "BTYPE == 3 invalid"

		if BTYPE == 0b00:
			inflate_block_no_compression(streamer, inflated_data)
		elif BTYPE == 0b01:
			inflate_block_fixed_huffman(streamer, inflated_data)
		elif BTYPE == 0b10:
			inflate_block_dynamic_huffman(streamer, inflated_data)

	return bytes(inflated_data)

# Main user-facing function
def decompress(memory):
	streamer = ByteStreamer(memory)

	CMF = streamer.read_byte()
	# Compression method
	CM = CMF & 0b1111
	# CM == 8 means DEFLATE compression
	assert(CM == 8), "CM != 8 invalid"

	# Compression info
	CINFO = CMF >> 4
	# CINFO > 7 means LZ77 window size would exceed maximum in specification
	assert(CINFO <= 7), "CINFO > 7 invalid"

	FLG = streamer.read_byte()
	assert((CMF * 256 + FLG) % 31 == 0), "CMF and FLG checksum failed"

	# Preset dictionary
	FDICT = (FLG >> 5) & 1
	assert(FDICT == 0), "FDICT == 1 not supported"

	# Decompress DEFLATE data
	data = inflate(streamer)

	# ALDER32 checksum
	ALDER32 = streamer.read_bytes(4)

	return data

import zlib
x = zlib.compress(b'The quick brown fox jumped over the lazy dog', level = 0)
print(decompress(x))
