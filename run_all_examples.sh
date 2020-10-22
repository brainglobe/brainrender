for entry in "examples"/*
do
  for f in $entry/*
  do
    echo "running $f"
    python $f
  done
done