#!/usr/bin/env -S sed -nEf


/###START_INPUT_AUTOMATION###/ {
  # [p]rint the start-marker line.
  p

  # Next, we'll read lines (using `n`) in a loop, so mark this point in
  # the script as the beginning of the loop using a label called `loop`.
  :loop

  # Read the next line.
  n

  # If the last read line doesn't match the pattern for the end marker,
  # just continue looping by [b]ranching to the `:loop` label.
  /^###END_INPUT_AUTOMATION###/! {
    b loop
  }

  # If the last read line matches the end marker pattern, then just insert
  # the text we want and print the last read line. The net effect is that
  # all the previous read lines will be replaced by the inserted text.
  /^###END_INPUT_AUTOMATION###/ {
    # Insert the replacement text
    i\
$REPLACEMENT

    # [print] the end-marker line
    p
  }

  # Exit the script, so that we don't hit the [p]rint command below.
  b
}

# Print all other lines.
p
