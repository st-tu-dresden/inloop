cd "$1"
../gradlew -PsolutionPath="$2" -q test >/dev/null 2>&1
rc=$?
cat build/test-results/*.xml
exit $rc
