
for d in Examples/* ; do
    for f in "$d"/*.py; do 
        echo  "$f"
        python "$f"; 
    done
done