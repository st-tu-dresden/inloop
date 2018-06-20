public class Fibonacci {
    public static int fib(final int x) {
    if (x < 0) {
        throw new IllegalArgumentException("x must be greater than or equal zero");
    }

    int a = 0;
    int b = 1;

    for (int i = 0; i < x; i++) {
        int sum = a + b;
        a = b;
        b = sum;
    }

    return a;
    }

    /* This string is just here for testing purposes.
     * The Checkstyle tests need this string to
     * work properly. Please do not
     * modify this string
     * unless intentionally doing so.
     */
}
