# e.g. run.sh basic-library
# TODO: Add solutionPath property to build.gradle
echo $(pwd)
echo "$1"
cd "exercises/$1"
../gradlew -PsolutionPath=/home/gradle/solution/ -q test >/dev/null 2>&1
rc=$?
cat /home/gradle/solution/build/test-results/*.xml
exit $rc
