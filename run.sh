# e.g. run.sh basic-library
# TODO: Add solutionPath property to build.gradle
cd "$1"
../gradlew -PsolutionPath=/home/gradle/solution/ -q test >/dev/null 2>&1
rc=$?
cat build/test-results/*.xml
exit $rc
