public class Fibonacci {
    // Iterative solution, slightly changed
    public static int fib(final int x) {
        if (x < 0) throw new IllegalArgumentException();
        long a = 0;
        long b = 1;
        for (long i = 0; i < x; i++) {
            long sum = a + b;
            a = b;
            b = sum;
        }
        return a;
    }

    private static void nothing() {
        for (;;) {int a = 0;}
    }
}
