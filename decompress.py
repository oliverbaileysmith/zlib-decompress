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

def decompress(memory):
	streamer = ByteStreamer(memory)

	CMF = streamer.read_byte()
	# Compression method
	CM = CMF & 0b1111
	# CM == 8 means DEFLATE compression
	assert(CM == 8), "Invalid CM: CM != 8 not supported"

	# Compression info
	CINFO = CMF >> 4
	# CINFO > 7 means LZ77 window size would exceed maximum in specification
	assert(CINFO <= 7), "Invalid CINFO: CINFO > 7 not supported"

	FLG = streamer.read_byte()
	assert((CMF * 256 + FLG) % 31 == 0), "CMF and FLG checksum failed"

	# Preset dictionary
	FDICT = (FLG >> 5) & 1
	assert(FDICT == 0), "Preset dictionary not supported"

	# Decompress DEFLATE data
	# data = inflate(streamer)

	# ALDER32 checksum
	ALDER32 = streamer.read_bytes(4)

	# return data

import zlib
x = zlib.compress(b'Hello World!')
print(decompress(x))
