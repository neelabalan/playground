local n = std.parseInt(std.extVar('n'));

// recursive function to compute the Collatz sequence for a number n
local collatz(num) =
  if num == 1 then [1]
  else if num % 2 == 0 then [num] + collatz(num / 2)
  else [num] + collatz(3 * num + 1);

local sequence = collatz(n);

{
  input: n,
  sorted: std.sort(sequence),
  length: std.length(sequence),
  max: std.foldl(function(a, b) std.max(a, b), sequence, 0),
}
