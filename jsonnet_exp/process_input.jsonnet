local input = std.parseJson(importstr 'input.json');

local collatz(num) =
  if num == 1 then [1]
  else if num % 2 == 0 then [num] + collatz(num / 2)
  else [num] + collatz(3 * num + 1);

{
  metadata: {
    title: input.title,
    description: input.description,
  },
  results: [
    {
      number: n,
      sequence: collatz(n),
      length: std.length(collatz(n)),
      max: std.foldl(function(a, b) std.max(a, b), collatz(n), 0),
    }
    for n in input.numbers
  ],
}
