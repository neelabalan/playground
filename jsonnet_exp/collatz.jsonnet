// recursive function to compute the Collatz sequence for a number n
local collatz(n) =
  if n == 1 then [1]
  else if n % 2 == 0 then [n] + collatz(n / 2)
  else [n] + collatz(3 * n + 1);

{
  for_6: std.sort(collatz(6)),
  for_11: std.sort(collatz(11)),
  for_19: std.sort(collatz(19)),
}
