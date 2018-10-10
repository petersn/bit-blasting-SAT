#!/usr/bin/python

import random
import solver
import bit_blast

bit_size = 9
modulus = 2**bit_size

def mix(builder, x, y, rotation):
	r1 = bit_blast.Addition(builder, x, y)
	r2 = bit_blast.BitRotation(builder, y, rotation)
	r3 = bit_blast.Xor(builder, r1, r2)
	return r1, r3

def concrete_mix(x, y, rotation):
	rotation %= bit_size
	r1 = (x + y) % modulus
	r2 = ((y << rotation) | (y >> (bit_size - rotation))) % modulus
	r3 = r1 ^ r2
	return r1, r3

def execute(regs, key):
	regs = list(regs)
	key = list(key)
	for i in xrange(len(regs)):
		regs[i] ^= key[i]
	regs[0], regs[1] = concrete_mix(regs[0], regs[1], 17)
	regs[2], regs[3] = concrete_mix(regs[2], regs[3], 20)
	regs = [regs[1], regs[3], regs[0], regs[2]]
	regs[0], regs[1] = concrete_mix(regs[0], regs[1], 9)
	regs[2], regs[3] = concrete_mix(regs[2], regs[3], 30)
	for i in xrange(len(regs)):
		regs[i] ^= key[i]
	return regs

def fmt(values):
	return " ".join("%03x" % v for v in values)

if __name__ == "__main__":
	n = 4
	random.seed(1234)
	builder = bit_blast.Builder()
	plaintext_values = [random.getrandbits(bit_size) for _ in xrange(n)]
	secret_key = [random.getrandbits(bit_size) for _ in xrange(len(plaintext_values))]
	ciphertext_values = execute(plaintext_values, secret_key)
	print "Plaintext: ", fmt(plaintext_values)
	print "Secret Key:", fmt(secret_key)
	print "Ciphertext:", fmt(ciphertext_values)
	print "==== Solving"

	registers = [bit_blast.Integer(builder, bit_size) for _ in xrange(len(plaintext_values))]
	key = [bit_blast.Integer(builder, bit_size) for _ in xrange(len(plaintext_values))]

	def add_key():
		for i in xrange(len(registers)):
			registers[i] = bit_blast.Xor(builder, registers[i], key[i])

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
	apply_mix(2, 20)
	registers = [registers[1], registers[3], registers[0], registers[2]]
	apply_mix(0, 9)
	apply_mix(2, 30)
	add_key()

	# Fix the the ciphertext values.
	for var, value in zip(registers, ciphertext_values):
		bit_blast.integer_constant_constraint(builder, var, value)

	# Solve for the key from our plaintext + ciphertext pair.
	instance = builder.make_instance()
	print "=== Base instance stats:"
	print "Variables:", len(instance.get_all_variables())
	print "Clauses:", len(instance.clauses)
	instance.propagate()
	print "=== After simplification:"
	print "Variables:", len(instance.get_all_variables())
	print "Clauses:", len(instance.clauses)

	key_values = None
	for assignment in solver.solve(instance):
		for total_assignment in builder.iterate_totality(assignment):
			key_values = [k.decode(total_assignment) for k in key]
			print ">>> KEY SOLUTION FOUND:", fmt(key_values)
			# Assert that the solution is valid.
			assert execute(plaintext_values, key_values) == ciphertext_values
			if key_values == secret_key:
				print "Correct key found!"
				exit()
#			break
#		if key_values != None:
#			break
	if key_values == None:
		print "No solution exists; impossible plaintext + ciphertext pair."
		exit()

