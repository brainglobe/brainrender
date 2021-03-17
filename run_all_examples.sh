for entry in "examples"/*
do
  for f in $entry/*
  do
    python $f
  done
done