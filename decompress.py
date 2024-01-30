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

# Inflate block where BTYPE == 0b00
def inflate_block_no_compression(streamer, out_data):
	# read_bytes will discard remaining bits after BTYPE until next byte boundary
	LEN = streamer.read_bytes(2)
	NLEN = streamer.read_bytes(2)

	for i in range(LEN):
		out_data.append(streamer.read_byte())

#Inflate block where BTYPE == 0b01
def inflate_block_fixed_huffman(streamer, out_data):
	return

#Inflate block where BTYPE == 0b10
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
