# bit-blasting-SAT

*Disclaimer:* This SAT solver is so hilariously non-competitive compared to real SAT solvers that it's only worth looking at if you're interested pedagogically.

## Introduction

This repo contains some experiments of mine with [DPLL](https://en.wikipedia.org/wiki/DPLL_algorithm) and bit-blasting a theory of fixed-width integers into SAT instances.
The file `solver.py` contains a simple DPLL implementation in Python2.

If imported you can create a SAT instance via `solver.Clause(positive_variables, negative_variables)` which creates a disjunctive clause.
For example:
```
import solver

# Represents the clause (x ∨ y ∨ ¬z)
clause1 = solver.Clause(["x", "y"], ["z"])

# Represents the clause (¬x ∨ ¬y)
clause2 = solver.Clause([], ["x", "y"])

# Represents the problem (x ∨ y ∨ ¬z) ∧ (¬x ∨ ¬y)
instance = solver.Instance([clause1, clause2])

print "All satisfying assignments:"
for assignment in solver.solve(instance):
	print assignment
```
The above will print the only satisfying assignment, namely `{'x': False, 'y': False, 'z': False}`.

The `solver.solve` function will iterate over all solutions in turn, and produces them dynamically one at a time, so it's safe to iterate over even if there are potentially exponentially many solutions.
The assignments it returns might not include assignments for all variables if the instance is satisfied regardless of the assignment of the remaining variables.

## Bit Blasting for Cryptanalysis

Bit blasting refers to decomposing arithmetic operations into SAT instances.
The file `bit_blasting.py` implements an interface for bit blasting various arithmetic operations on fixed-width integers into SAT instances, suitable for passing into `solver.py`.

We use this to do some very basic cryptanalysis on a toy "block cipher" based on the design of Threefish, which I'll be calling Toyfish here.
Diagrammed below:

![Toyfish](/docs/diagram1.png?raw=true | width=600)

Here each line carries 16 bits, yielding a 64-bit block cipher with a 64-bit key.
One round of this cipher consists of applying a Threefish-style mix operation on the left two words and right two words, then permuting the words.
(The permutation after the last pass of mix operations is suppressed, because it clearly adds no security.)
Finally, the block is whitened with the key by XOR at the beginning and by addition at the end of the cipher.
The innards of this cipher obviously don't provide anything even remotely resembling enough diffusion at just two rounds, as depicted above.
It's really a disgustingly terrible design, but it'll suffice as a test case for our SAT solver.

Now, at two rounds, one can trivially break Toyfish, but we'll break it automatically using our SAT solver.
We will perform a known-plaintext attack where we solve for every key that is consistent with our known plaintext/ciphertext pair.
This is implemented in `toyfish_invert.py`.

Specifically, `toyfish_invert.py` picks a random 64-bit key, generates a random plaintext/ciphertext pair under this key, then uses `bit_blast.py` to build a bit-blasted implementation of Toyfish as a SAT instance, and equates the inputs and outputs to the known plaintext/ciphertext pair.
Then it runs `solver.py` on the SAT instance to enumerate every possible 64-bit key that is consistent with the known pair.

### Random SAT

If you run `solver.py` it will do a test solve on a randomly generated 3SAT instance with 100 variables and 4.2 clauses per variable (which is approximately the right number of clauses to make a random 3SAT instance as hard as possible).

An example invocation with 80 variables:

```
Performing a test solve on a random 3SAT instance with 80 variables and 336 clauses.
SAT instance:

[61:24,41] [64:4,9] [3,52:28] [61,63:62] [:12,69,33] [32,3:29] [6,51,46:] [69:52,27] [6,29:23] [59,72:34] [39:70,39] [31,65,23:] [72,58,46:] [75,73:27] [:76,70,37] [69,56:74] [69,57:79] [32:75,46] [42:31,63] [3:47,54] [74:49] [68:21,60] [67,41:11] [54:79,28] [14:76,70] [29,11:67] [23,37:34] [63:55,61] [:25,59,10] [:59,28,16] [17:73,74] [31,73:10] [42,63:9] [63,4,30:] [59,68:65] [36:32,57] [14:75,57] [23:54,1] [15:17,45] [48:57,56] [:1,17,67] [42:61,72] [54,35,0:] [38,69:50] [43,5:58] [71:33,78] [:21,27,50] [47,53:2] [4,49:44] [77,23:31] [48,18:63] [9,26:29] [61,29:51] [9,78:28] [59,79:61] [35:25,35] [:4,56,51] [53,64:59] [:75,35,6] [38,45,13:] [:59,27,74] [73,44,12:] [38:44,23] [38,33,15:] [10,71:65] [14,21:72] [49,36:5] [19:53,60] [77,62:41] [9,61:67] [47,48,70:] [52,64:43] [10,39:41] [:6,14,49] [78,23:77] [58,26:55] [37:25,72] [21,71,8:] [17,49:41] [22,62:16] [17,28:23] [31:19,8] [16:13,10] [70,3:11] [57,11:31] [67,37:48] [:71,6,14] [25:46,26] [70:15,12] [25,47:21] [24:49,35] [:71,57,54] [21:59,20] [3,75:77] [27:59,74] [70,63:14] [20,34:54] [74:67,73] [50:50,54] [16:56,69] [15:21,56] [42:39,2] [56,55:12] [18:37,9] [61,34,47:] [:75,39,41] [69,71:26] [4:29] [45,50:15] [32:31,5] [23:34,76] [23,6:22] [51,20:54] [:52,78,43] [14,3:77] [69,2:36] [34:32,39] [66,1:79] [47:11,49] [48:49,1] [:0,60,45] [:12,30,33] [73,11:72] [56,55:31] [:44,70,71] [66,19:66] [60,62:1] [74,49:35] [58,23:64] [73,2:67] [48:77,68] [14,36:34] [:8,27,18] [29,79:12] [39,6,42:] [74,69:71] [20,23:49] [10,41:35] [1,35:46] [6,54:12] [24,59:59] [25:20,76] [76,10,79:] [32:17,36] [44:19,29] [34,56:36] [23,73:24] [48:66,77] [13,78:23] [36,20:58] [35:59,65] [44,28:66] [2:33,41] [66,78,75:] [70,68:47] [28:67,47] [8,9,4:] [62,1:61] [5,44,48:] [60:34,16] [68,61,65:] [42:9,54] [55:42,52] [11:39] [66:27,23] [59,60:62] [28,4:66] [16:77,60] [51,50:36] [76,1:9] [53:0,30] [14,22,33:] [35,43:18] [66,53,59:] [63:57,70] [65,38:64] [36,65:51] [18,60:41] [46,51:16] [41:2,45] [:18,68,43] [27,55,59:] [14,71:38] [78:20,29] [27:22,71] [23:51,50] [18,58:29] [22,14:50] [23:78,76] [61:47,19] [76,59:49] [70:8,25] [67:41,25] [72,36:] [32:54,49] [36:14,21] [53,36:76] [39:78,15] [79,77,74:] [20,34,39:] [74,36:74] [21,78:41] [44:45,46] [72,34:13] [79,12:64] [26,39:13] [40:30,0] [33:3,67] [73,63:28] [14:51,18] [:25,6,61] [75,67,79:] [6,79:2] [8,33:72] [78,59:64] [61,32:53] [70:73,71] [8,37:19] [64:20,8] [8,43,15:] [49,9,11:] [22,30:58] [:31,17,15] [47,65:32] [46,42:51] [70,16:63] [0,35:1] [40:40,33] [43,60:13] [79,54,11:] [3:66,30] [:49,17,18] [26,38,10:] [13,44,39:] [5:55,25] [26,68:16] [:27,26,23] [:12,47,4] [7,59:38] [21:77,49] [6:62,51] [25,46,28:] [59,54:75] [55:61,31] [55,75:49] [59,19:37] [43:55,22] [32,7,38:] [34:28,58] [55,68:76] [33:6,47] [:49,29,36] [51,60,50:] [44:76,29] [37,36:65] [38,24:60] [52,64:44] [4:46,0] [3:58,36] [49,63:72] [66,64,53:] [3,29,41:] [68,26:61] [57:3,55] [58:74,30] [69,79:29] [1,35,36:] [:24,28,27] [20:40,24] [:67,49,24] [63:47,33] [:75,2,78] [14,10,47:] [14:3,38] [:56,54,22] [67,43:35] [:77,52,2] [1,14:8] [70,73,51:] [33:70,62] [64:30,75] [79:47,44] [4,34:23] [1:47,79] [23:75,47] [34:75,47] [21:12,5] [71,16:1] [54:29,39] [8,11:27] [44:12,48] [48:67,49] [65:57,36] [:13,27,72] [57:2,33] [8,26,55:] [44:57,54] [26,34:71] [73,23,5:] [15:22,24] [22:38,66] [16,62:74] [68,16:52] [:53,70,43] [55:73,69] [30,13:59] [13:14,38] [41,3:8] [57,63:1] [12,67:20] [:23,20,42] [7,9:49] [:75,68,35] [:69,17,51] [25,65:51] [40,8:58] [41,22,28:] [6,50:8] [54:65,10] [55:43,73] [61,74:65] [1,34:60] [35,13:67] [23:46,26] [70:56,2] [33,78,29:] [51:27,65] [66:69,73] [20,51:66] [10,32:30] [41:52,69] [32,4,5:] [62,59,69:] [:61,54,52] [39,60,31:] [73:28,26]

Solving up to first satisfying assignment...

7=1 61=0 24=0 40=1 64=0 4=1 9=0 67=0 3=1 63=1 12=0 20=0 6=0 51=0 46=1 54=0 66=0 53=1 32=1 69=0 52=0 43=0 42=1 44=0 73=1 45=0 0=1 35=0 1=1 18=0 48=1 68=1 37=1 29=0 23=0 22=0 49=0 11=1 41=1 28=0 17=1 60=1 19=1 47=0 34=1 76=0 25=0 26=0 21=0 78=1 65=1 59=0 72=1 14=1 75=0 39=1 79=1 57=1 36=1 5=1 2=1 50=1 38=1 13=1 27=0 55=1 58=1 30=1 10=0 71=1 33=1 74=1 62=1 70=1 56=1 16=1 77=1 31=0 8=0 15=1

Completed in 0.255 seconds.
```

