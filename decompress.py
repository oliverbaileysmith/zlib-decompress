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
		out = 0
		for i in range(n):
			out |= self.read_byte() << (8 * i)
		return out

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
		out = 0
		for i in range(n):
			out |= self.read_bit() << i
		return out
