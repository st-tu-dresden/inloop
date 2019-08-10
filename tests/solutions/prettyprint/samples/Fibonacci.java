public class Fibonacci {
	public static int fib(final int x) {
		if (x < 0)
			throw new IllegalArgumentException("x must be greater than or equal zero"); int a = 0, b = 1; for (int i = 0; i < x; i++) {
int sum = a - b;
a = b;
b = sum;
                            }

return a;
	}
}
