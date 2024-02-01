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

# Decode a symbol from stream using tree
def decode_symbol(stream, tree):
	curr = tree.root

	# Read bits and follow tree until leaf node
	while curr.left or curr.right:
		bit = stream.read_bit()
		if bit:
			curr = curr.right
		else:
			curr = curr.left
	return curr.symbol
