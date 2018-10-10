#!/usr/bin/python

import itertools, random
import solver

class Builder:
	def __init__(self):
		self.counter = 0
		self.clauses = []
		self.vars = set()
		self.var_names = {}
		# Adding true and false variables is almost free, because the first unit propagation pass fully eliminates these.
		self.false = self.new_var("false")
		self.true = self.new_var("true")
		self.add_clause([], [self.false])
		self.add_clause([self.true], [])
		self.bools = {0: self.false, 1: self.true}

	def new_var(self, name):
		self.counter += 1
		var = self.counter
		self.vars.add(var)
		self.var_names[var] = name
		return var

	def make_instance(self):
		return solver.Instance(self.clauses, {})

	def make_assignment_total(self, assignment):
		assignment = assignment.copy()
		for var in self.vars:
			if var not in assignment:
				assignment[var] = False
		return assignment

	def iterate_totality(self, assignment):
		missing_vars = [var for var in self.vars if var not in assignment]
		for missing_assignment in itertools.product((False, True), repeat=len(missing_vars)):
			sub_assign = assignment.copy()
			for var, truth in zip(missing_vars, missing_assignment):
				sub_assign[var] = truth
			yield sub_assign

	def add_clause(self, positive, negative):
		self.clauses.append(solver.Clause(set(positive), set(negative)))

	def equate(self, var1, var2):
		# TODO: Rewrite all the current clauses under this equality, rather than simply adding new clauses.
		self.add_clause([var1], [var2])
		self.add_clause([var2], [var1])

class Integer:
	def __init__(self, builder, bit_length):
		self.bit_length = bit_length
		self.bits = [builder.new_var("i%i" % i) for i in xrange(bit_length)]

	def __getitem__(self, i):
		return self.bits[i]

	def to_list(self):
		return [self[i] for i in xrange(self.bit_length)]

	def decode(self, total_assignment):
		return sum(total_assignment[var] << i for i, var in enumerate(self.bits))

class BitRotation(Integer):
	def __init__(self, builder, x, rotation_amount):
		self.bit_length = x.bit_length
		rotation_amount %= self.bit_length
		self.bits = x.bits[-rotation_amount:] + x.bits[:-rotation_amount]
		assert len(self.bits) == self.bit_length

class Xor(Integer):
	def __init__(self, builder, x, y):
		assert x.bit_length == y.bit_length
		Integer.__init__(self, builder, x.bit_length)
		for i in xrange(self.bit_length):
			xor_gate(builder, x[i], y[i], self[i])

class Addition(Integer):
	def __init__(self, builder, x, y):
		assert isinstance(x, Integer)
		assert isinstance(y, Integer)
		assert x.bit_length == y.bit_length
		self.bit_length = x.bit_length
		self.carries = Integer(builder, self.bit_length)
		self.bits = Integer(builder, self.bit_length)

		previous_carry = builder.false
		for i in xrange(self.bit_length):
			current_carry = self.carries[i]
			# We now want to add x[i], y[i], and previous_carry to generate self.bits[i], current_carry.
			full_adder(builder, x[i], y[i], previous_carry, self.bits[i], current_carry)
			previous_carry = current_carry

		self.overflow_bit = current_carry

class Comparison:
	def __init__(self, builder, x, y):
		negative_y = integer_negate(builder, y)
		self.subtraction = Addition(builder, x, negative_y)
		self.greater_than_or_equal = builder.new_var("cmp.ge")
		or_gate(builder, self.subtraction.overflow_bit, negative_y.overflow_bit, self.greater_than_or_equal)

		self.equal = integer_equals_zero(builder, self.subtraction)

		# Compute less_than as (less_than_or_equal XOR equal)
		self.greater_than = builder.new_var("cmp.gt")
		xor_gate(builder, self.greater_than_or_equal, self.equal, self.greater_than)

		# Compute greater_than as (not less_than_or_equal)
		self.less_than = builder.new_var("cmp.lt")
		not_gate(builder, self.greater_than_or_equal, self.less_than)

def bit_inverse(builder, x):
	result = Integer(builder, x.bit_length)
	for i in xrange(x.bit_length):
		not_gate(builder, x[i], result[i])
	return result

def integer_negate(builder, x):
	x = bit_inverse(builder, x)
	const = Integer(builder, x.bit_length)
	integer_constant_constraint(builder, const, 1)
	return Addition(builder, x, const)

def integer_equals_zero(builder, x):
	result = builder.new_var("allz")
	# Constrain that at least one bit must be 1, or the result bit must be 1.
	builder.add_clause(x.bits.to_list() + [result], [])
	# Further constrain that if any x[i] is 1 then the result must be 0.
	for i in xrange(x.bit_length):
		builder.add_clause([], [x[i], result])
	return result

def not_gate(builder, a, out):
	builder.add_clause([a, out], [])
	builder.add_clause([], [a, out])

def and_gate(builder, a, b, out):
	builder.add_clause([a], [out])
	builder.add_clause([b], [out])
	builder.add_clause([out], [a, b])

def xor_gate(builder, a, b, out):
	# If a and b are (0, 0) then out can't be 1.
	builder.add_clause([a, b], [out])
	# If a and b are (0, 1) then out can't be 0.
	builder.add_clause([a, out], [b])
	# If a and b are (1, 0) then out can't be 0.
	builder.add_clause([b, out], [a])
	# We can't have all three bits true.
	builder.add_clause([], [a, b, out])

def or_gate(builder, a, b, out):
	builder.add_clause([out], [a])
	builder.add_clause([out], [b])
	builder.add_clause([a, b], [out])

def full_adder(builder, a, b, c, out, carry_out):
	fa0 = builder.new_var("fa.0")
	xor_gate(builder, a, b, fa0)
	xor_gate(builder, c, fa0, out)
	fa1 = builder.new_var("fa.1")
	fa2 = builder.new_var("fa.2")
	and_gate(builder, a, b, fa1)
	and_gate(builder, c, fa0, fa2)
	or_gate(builder, fa1, fa2, carry_out)

def integer_constant_constraint(builder, x, const):
	assert isinstance(x, Integer)
	for i in xrange(x.bit_length):
		bit = (const >> i) & 1
		builder.equate(x[i], builder.bools[bit])

if False:
	builder = Builder()
	x = builder.new_var("x")
	y = builder.new_var("y")
	z = builder.new_var("z")
	and_gate(builder, x, y, z)
	instance = builder.make_instance()
	for assignment in solver.solve(instance):
		for assignment in builder.iterate_totality(assignment):
			print int(assignment[x]), "op", int(assignment[y]), "=", int(assignment[z])
	exit()

def test_comparator(bit_length):
	builder = Builder()
	x = Integer(builder, bit_length)
	y = Integer(builder, bit_length)
	comparison = Comparison(builder, x, y)
	instance = builder.make_instance()
	for assignment in solver.solve(instance):
		for total_assignment in builder.iterate_totality(assignment):
			X, Y = [i.decode(total_assignment) for i in (x, y)]
			lt = total_assignment[comparison.less_than]
			eq = total_assignment[comparison.equal]
			gt = total_assignment[comparison.greater_than]
			message = ""
			if lt != (X < Y):
				message += " BAD LT"
			if eq != (X == Y):
				message += " BAD EQ"
			if gt != (X > Y):
				message += " BAD GT"
			print "x = %3i, y = %3i -> %i %i %i%s" % (X, Y, lt, eq, gt, message)

if __name__ == "__main__":
	bit_length = 3
	modulus = 2**bit_length
#	x_value = random.getrandbits(bit_length)
#	y_value = random.getrandbits(bit_length)

	builder = Builder()
	x = Integer(builder, bit_length)
	y = Integer(builder, bit_length)
	integer_constant_constraint(builder, x, 2)
#	integer_constant_constraint(builder, y, y_value)
	z = Addition(builder, x, y)
	w = Integer(builder, bit_length)
	integer_constant_constraint(builder, w, 3)
	comparison = Comparison(builder, z, w)
	builder.equate(comparison.less_than, builder.bools[True])
	instance = builder.make_instance()

	print "Enumerating solutions:"
	for assignment in solver.solve(instance):
		print "Base solution over:", len(assignment)
		for total_assignment in builder.iterate_totality(assignment):
			x_v, y_v, z_v = [v.decode(total_assignment) for v in (x, y, z)]
			print "x =", x_v
			print "y =", y_v
			print "z =", z_v
			r = (x_v + y_v) % modulus
			assert r == z_v

