sed -i '/- k =/d' */aims.out
sed -i '/- k =/d' */aims.out

sed -i '/| k-string \*\*\*\* :/d' wo_spline/*/aims.out
sed -i '/| k-string \*\*\*\* :/d' w_spline/*/aims.out

sed -i '/| k-string/d' wo_spline/*/aims.out
sed -i '/| k-string/d' w_spline/*/aims.out

sed -i '/term along reciprocal/d' wo_spline/*/aims.out
sed -i '/term along reciprocal/d' w_spline/*/aims.out

sed -i '/Treating all/d' wo_spline/*/aims.out
sed -i '/Treating all/d' w_spline/*/aims.out

sed -i '/|-> Computing Wannier center evolution at k-point number:/d' wo_spline/*/aims.out
sed -i '/|-> Computing Wannier center evolution at k-point number:/d' w_spline/*/aims.out

sed -i '/Using pol_lapack_version/d' wo_spline/*/aims.out
sed -i '/Using pol_lapack_version/d' w_spline/*/aims.out

sed -i '/Sampling over :/d' wo_spline/*/aims.out
sed -i '/Sampling over :/d' w_spline/*/aims.out

sed -i '/from k_start =/d' wo_spline/*/aims.out
sed -i '/from k_start =/d' w_spline/*/aims.out

for f in wo_spline/*/aims.out; do
    awk 'NF {n=0; print; next} n++ < 3 {print}' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done

for f in w_spline/*/aims.out; do
    awk 'NF {n=0; print; next} n++ < 3 {print}' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done
