#!/usr/bin/python

import random, itertools

class Unsatisfiable(Exception):
	pass

class Clause(object):
	__slots__ = ["positive", "negative"]

	def __init__(self, positive, negative):
		self.positive = set(positive)
		self.negative = set(negative)

	def __repr__(self):
		return "[%s:%s]" % (
			",".join(repr(pos) for pos in self.positive),
			",".join(repr(neg) for neg in self.negative),
		)

	def copy(self):
		return Clause(self.positive, self.negative)

	def is_unit(self):
		return len(self.positive) + len(self.negative) == 1

	def is_empty(self):
		return (not self.positive) and (not self.negative)

	def apply_subst(self, var, truth):
		"""apply_subst(self, var, truth) -> bool

		Returns True if the clause is now satisfied by the assignment.
		"""
		if truth:
			self.negative.discard(var)
			if self.is_empty():
				raise Unsatisfiable()
			return var in self.positive
		else:
			self.positive.discard(var)
			if self.is_empty():
				raise Unsatisfiable()
			return var in self.negative

class Instance(object):
	__slots__ = ["clauses", "assignments"]

	def __init__(self, clauses, assignments=None):
		assignments = assignments or {}
		self.clauses = clauses
		self.assignments = assignments

	def __repr__(self):
		return " ".join(repr(clause) for clause in self.clauses)

	def copy(self):
		return Instance(
			[clause.copy() for clause in self.clauses],
			self.assignments.copy(),
		)

	def apply_subst(self, var, truth):
		assert var not in self.assignments
		self.assignments[var] = truth
		i = 0
		while i < len(self.clauses):
			is_satisfied = self.clauses[i].apply_subst(var, truth)
			if is_satisfied:
				self.clauses.pop(i)
				continue
			i += 1

	def unit_propagate_once(self):
		for clause in self.clauses:
			if clause.is_unit():
				if clause.positive:
					self.apply_subst(iter(clause.positive).next(), True)
				else:
					self.apply_subst(iter(clause.negative).next(), False)
				return True
		return False

	def pure_literal_eliminate_once(self):
		positive_literals = set()
		negative_literals = set()
		for clause in self.clauses:
			positive_literals |= clause.positive
			negative_literals |= clause.negative
		only_positive = positive_literals - negative_literals
		only_negative = negative_literals - positive_literals
		for var in only_positive:
			self.apply_subst(var, True)
		for var in only_negative:
			self.apply_subst(var, False)
		return bool(only_positive) or bool(only_negative)

	def propagate(self):
		while True:
			made_progress = False
			made_progress |= self.unit_propagate_once()
			made_progress |= self.pure_literal_eliminate_once()
			if not made_progress:
				break

	def verify_against(self, assignment):
		by_truth = {
			truth_value: set(var for var in assignment if assignment[var] == truth_value)
			for truth_value in (False, True)
		}
		for clause in self.clauses:
			if clause.positive & by_truth[True]:
				continue
			if clause.negative & by_truth[False]:
				continue
			return False
		return True

def pick_branch_assignment(state):
	# Chose literally just the first variable we encounter.
	first_clause = state.clauses[0]
	# Select an arbitrary variable from the first clause.
	# Note that it is impossible for this clause to be empty, or
	# we would already have rejected the state as unsatisfiable.
	var = iter(first_clause.positive | first_clause.negative).next()
	# For now always just explore the "var = False" path first.
	truth = False
	return var, truth

def solve_inner(state):
	# Propagate the state.
	try:
		state.propagate()
	except Unsatisfiable:
		return
	# Check if there are no more clauses, which indicates a satisfied instance.
	if not state.clauses:
		yield state.assignments
		return
	# Check if the state has an empty clause, which indicates unsatisfiability.
	if any(clause.is_empty() for clause in state.clauses):
		assert False, "We should already have caught this when the assignment happened!"
	# Branch the solver on a variable.
	var, truth = pick_branch_assignment(state)
	state_copy = state.copy()
	state.apply_subst(var, truth)
	state_copy.apply_subst(var, not truth)
	for assignment in solve_inner(state):
		yield assignment
	for assignment in solve_inner(state_copy):
		yield assignment

def solve(original_state):
	# Make a copy of the state to avoid mutating what was passed in.
	state = original_state.copy()
	# Eliminate any clauses that contain a variable in both positive
	# and negative position, as these clauses are trivially satisifed.
	# We don't need to repeat this later, because DPLL will never generate
	# such clauses if they don't exist to start with.
	state.clauses = [
		clause for clause in state.clauses
		if not (clause.positive & clause.negative)
	]
	# Launch our inner solve loop.
	for assignment in solve_inner(state):
		assert original_state.verify_against(assignment)
		yield assignment

def solve_brute_force(state):
	all_vars = set()
	for clause in state.clauses:
		all_vars |= clause.positive | clause.negative
	all_vars = list(all_vars)
	for truths in itertools.product((False, True), repeat=len(all_vars)):
		assignment = dict(zip(all_vars, truths))
		if state.verify_against(assignment):
			yield assignment

def random_instance(var_count, clause_count, valid_clause_lengths):
	clauses = []
	for _ in xrange(clause_count):
		positive, negative = set(), set()
		for _ in xrange(random.choice(valid_clause_lengths)):
			random.choice((positive, negative)).add(random.randrange(var_count))
		clauses.append(Clause(positive, negative))
	return Instance(clauses, {})

if __name__ == "__main__":
	import time

	var_count = 80
	clause_count = int(4.2 * var_count)
	instance = random_instance(var_count, clause_count, [3])

	print "Performing a test solve on a random 3SAT instance with %i variables and %i clauses." % (var_count, clause_count)
	print "SAT instance:"
	print
	print instance
	print
	print "Solving up to first satisfying assignment..."

	start_time = time.time()
	for assignment in solve(instance):
		print
		print " ".join("%i=%i" % (var, truth) for var, truth in assignment.iteritems())
		print
		break
	else:
		print "No solution."
	print "Completed in %.3f seconds." % (time.time() - start_time,)

