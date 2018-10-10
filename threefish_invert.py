#!/usr/bin/python

import solver
import bit_blast

def mix(builder, x, y, rotation):
	r1 = bit_blast.Addition(builder, x, y)
	r2 = bit_blast.BitRotation(builder, y, rotation)
	r3 = bit_blast.Xor(builder, r1, r2)
	return r1, r3

if __name__ == "__main__":
	bit_size = 10 #32
	builder = bit_blast.Builder()
#	plaintext_values = [1, 2, 3, 4]
#	ciphertext_values = [5, 6, 7, 8]
	plaintext_values = [1, 2]
	ciphertext_values = [5, 6]

	registers = [bit_blast.Integer(builder, bit_size) for _ in xrange(len(plaintext_values))]
	key = [bit_blast.Integer(builder, bit_size) for _ in xrange(len(plaintext_values))]

	def add_key():
		for i in xrange(len(registers)):
			registers[i] = bit_blast.Addition(builder, registers[i], key[i])

	def apply_mix(offset, r):
		x, y = mix(builder, registers[offset], registers[offset + 1], r)
		registers[offset], registers[offset + 1] = x, y

	# Start by fixing the plaintext values.
	for var, value in zip(registers, plaintext_values):
		bit_blast.integer_constant_constraint(builder, var, value)

	# Implement two rounds of mini-Threefish-128.
	# This is a fictious "block cipher" based on Threefish designed to be a test problem.
	add_key()
	apply_mix(0, 17)
#	apply_mix(2, 21)
#	registers = [registers[1], registers[3], registers[0], registers[2]]
	apply_mix(0, 9)
#	apply_mix(2, 30)
	add_key()

	# Fix the the ciphertext values.
	for var, value in zip(registers, ciphertext_values):
		bit_blast.integer_constant_constraint(builder, var, value)

	# Solve for the key from our plaintext + ciphertext pair.
	instance = builder.make_instance()
	print "Instance stats:"
	print "Variables:", len(builder.var_names)
	print "Clauses:", len(instance.clauses)
	key_values = None
	for assignment in solver.solve(instance):
		print "Assignment over:", len(assignment)
		for total_assignment in builder.iterate_totality(assignment):
			key_values = [k.decode(total_assignment) for k in key]
			break
		if key_values != None:
			break
	if key_values == None:
		print "No solution exists; impossible plaintext + ciphertext pair."
		exit()

	print "Key values:", " ".join("%x" % k for k in key_values)

