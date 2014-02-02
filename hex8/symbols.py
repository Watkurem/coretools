#symbols.py
#Create a list of the symbols in an xc8 *.sym file
#Also allows looking up an address to find the corresponding symbol and
#saving and merging symbol tables

import sys
import json
import bisect
import os.path

class XC8SymbolTable:
	def __init__(self, path):
		ext = os.path.splitext(path)[1]

		if ext == '.sym':
			self._parse_symtab(path)
			self._calc_sizes()
		elif ext == '.stb':
			with open(path, "r") as f:
				self.known_functions = json.load(f)
		else:
			raise ValueError("Invalid symbol file with extension != [sym|stb]: %s" % path)
		
		self._build_lookup()

	def _parse_symtab(self, path):
		print path
		lines = [line.strip() for line in open(path)]

		self.symtab = {}
		self.sects = {}
		self.known_functions = []

		for line in lines:
			if line == "%segments":	
				break

			fields = line.split(' ')

			if len(fields) != 5:
				raise ValueError("File did not have a valid format, too many fields in line:\n%s\n" % line)

			name = fields[0]
			addr = int(fields[1], 16)
			sect = fields[3]

			if name.startswith('__end_of'):
				self.known_functions.append((name[8:], addr))
				continue

			if name.startswith('__size_of'):
				continue

			self.symtab[name] = (addr, sect)

			#Keep track of which symbols are in which sections
			if sect not in self.sects:
				self.sects[sect] = [name]
			else:
				self.sects[sect].append(name)

	def merge(self, path):
		"""
		Merge another symbol table into this one
		"""

		other = XC8SymbolTable(path)

		self.known_functions += other.known_functions
		self._build_lookup()

	def _calc_sizes(self):
		"""
		Calculate the sizes of all known_functions: functions with a 
		symbol defining the end of the function, i.e. __end_of_foo
		
		Converts the known_functions list in 3-tuples with (name, starting_address, size)
		"""

		self.known_functions = map(lambda x: (x[0], self.symtab[x[0]][0], x[1] - self.symtab[x[0]][0]), self.known_functions)
		self.total_size = reduce(lambda x,y: x+y, map(lambda x: x[2], self.known_functions))

	def _build_lookup(self):
		self.known_functions = sorted(self.known_functions, key=lambda x:x[1])
		self.lookup = map(lambda x: x[1], self.known_functions)

	def map_address(self, addr):
		"""
		Given an address, find the function and offset within that function that it belongs to
		"""

		i = bisect.bisect_right(self.lookup, addr)
		i -= 1

		if i < 0:
			return None

		offset = addr - self.known_functions[i][1]

		if offset < self.known_functions[i][2]:
			return (self.known_functions[i][0], offset)

		return None


	def _gen_define(self, func):
		line = '#define %s_address 0x%x\n' % (func[0], func[1])

		return line

	def _gen_c_call(self, func):
		line = '#define c_call%s() asm("call 0x%x")\n' % (func[0], func[1])

		return line 

	def _gen_asm_call(self, func):
		line = '#define asm_call%s() call 0x%x\n' % (func[0], func[1])

		return line 

	def generate_h_file(self, path):
		defs = map(lambda x: self._gen_define(x), self.known_functions)
		c_calls = map(lambda x: self._gen_c_call(x), self.known_functions)
		asm_calls = map(lambda x: self._gen_asm_call(x), self.known_functions)

		with open(path, "w") as f:
			f.writelines(defs)
			f.writelines(c_calls)
			f.writelines(asm_calls)

	def generate_stb_file(self, path):
		with open(path, "w") as f:
			json.dump(self.known_functions, f)
