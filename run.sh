# e.g. run.sh basic-library
cd "exercises/$1"
../gradlew -PsolutionPath=/home/gradle/solution/ -q test >/dev/null 2>&1
rc=$?
cat build/test-results/*.xml
if [ "$?" -ne 0 ]
  then
    # Test reports don't exist. Assume a compiler error
    # happened and call javac manually for error output
    # cd into directory to hide path in stdout error report
    cd /home/gradle/solution/ && javac *
    rc=42
fi
exit $rc
