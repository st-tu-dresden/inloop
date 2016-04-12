# e.g. run.sh BasicLibrary

# NOTE
# this stuff and the ol' checker will be removed soon, but until the new
# one gets deployed we have to fix the most annoying bugs here.

set -o pipefail

# yes, the only return code that will mark a solution as not passed is 42
cd "exercises/$1" || exit 42

solution_path=/home/gradle/solution

# try to show a friendly message if students use the package statement
if grep -q '^package ' $solution_path/*.java; then
    echo 'You are using the `package` statement, but our checker expects'
    echo 'all classes to be in the default package. In other words, please'
    echo 'remove the `package` statement and upload your solution again.'
    exit 42
fi

# compile separately while redirecting compiler errors to stdout, disguise internal path in output
../gradlew -q --console=plain -PsolutionPath=$solution_path compileTestJava 2>&1 \
    | sed "s|$solution_path|/sandbox|g"

# compiler error -> return 42
if [ $? -ne 0 ]; then
    echo "NOT PASSED - COMPILATION FAILED."
    exit 42
fi

# execute the tests & ignore output ...
../gradlew -q -PsolutionPath=$solution_path test >/dev/null 2>&1
rc=$?

# ... because we use the XML results
cat build/test-results/*.xml 2>/dev/null

if [ $? -ne 0 ] && [ $rc -ne 0 ]; then
    echo "Your solution failed the test, but I can't find any test reports "
    echo "that would assist you while debugging the problem :-("
    # ensure passed will be set to False:
    exit 42
fi
