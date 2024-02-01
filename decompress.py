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

# Construct canonical Huffman tree from alphabet and bit length list
def huffman_tree_from_alphabet_and_bl_list(alphabet, bl_list):
	max_bits = max(bl_list)

	# Get number of codes for each bit length
	bl_count = [0] * len(bl_list)
	for i in range(max_bits + 1):
		for bl in bl_list:
			if bl == i and i != 0:
				bl_count[i] += 1

	# Compute smallest code for each bit length
	next_code = [0, 0]
	for bit_length in range(2, max_bits + 1):
		next_code.append((next_code[bit_length - 1] + bl_count[bit_length - 1]) << 1)

	# Construct canonical tree
	tree = HuffmanTree()
	for symbol, bit_length in zip(alphabet, bl_list):
		if bit_length != 0:
			tree.insert(next_code[bit_length], bit_length, symbol)
			next_code[bit_length] += 1
	return tree

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

# Code length order table
CodeLengthCodesOrder = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]

# Create literal/length and distance trees by creating and using code length tree
def decode_trees(streamer):
	# Number of literal/length codes
	HLIT = streamer.read_bits(5) + 257

	# Number of distance codes
	HDIST = streamer.read_bits(5) + 1

	# Number of code length codes
	HCLEN = streamer.read_bits(4) + 4

	# Read code lengths for the code length alphabet
	code_length_bl_list = [0] * 19
	for i in range(HCLEN):
		code_length_bl_list[CodeLengthCodesOrder[i]] = r.read_bits(3)

	# Construct code length tree
	code_length_tree = huffman_tree_from_alphabet_and_bl_list(range(19), code_length_bl_list)

	# Read literal/length + distance code length list
	bl_list = []
	while len(bl_list) < HLIT + HDIST:
		symbol = decode_symbol(r, code_length_tree)
		assert(0 <= symbol <= 18), "Invalid symbol"

		if symbol < 16: # literal value
			bl_list.append(symbol)
		elif symbol == 16:
			# Copy previous code length 3 to 6 times
			prev_code_length = bl_list[-1]
			repeat_length = r.read_bits(2) + 3
			for i in range(repeat_length):
				bl_list.append(prev_code_length)
		elif symbol == 17:
			# Repeat code length 0 3 to 10 times
			repeat_length = r.read_bits(3) + 3
			for i in range(repeat_length):
				bl_list.append(0)
		else: # symbol == 18
			# Repeat code length 0 11 to 138 times
			repeat_length = r.read_bits(7) + 11
			for i in range(repeat_length):
				bl_list.append(0)

	# Construct trees
	literal_length_tree = huffman_tree_from_alphabet_and_bl_list(range(286), bl_list[:HLIT])
	distance_tree = huffman_tree_from_alphabet_and_bl_list(range(30), bl_list[HLIT:])
	return literal_length_tree, distance_tree

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
