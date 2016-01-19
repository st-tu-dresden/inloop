# e.g. run.sh basic-library
echo $(pwd)
echo "$1"
cd "exercises/$1"
../gradlew -PsolutionPath=/home/gradle/solution/ -q test >/dev/null 2>&1
rc=$?
cat build/test-results/*.xml
exit $rc
