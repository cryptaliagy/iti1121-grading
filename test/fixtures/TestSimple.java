// Simple test file for integration testing
public class TestSimple {
    public static void main(String[] args) {
        System.out.println("Running test suite...");
        
        // Test 1
        boolean test1Passed = testAddition();
        if (test1Passed) {
            System.out.println("Grade for Test1 (out of a possible 10): 10");
        } else {
            System.out.println("Grade for Test1 (out of a possible 10): 0");
        }
        
        // Test 2
        boolean test2Passed = testSubtraction();
        if (test2Passed) {
            System.out.println("Grade for Test2 (out of a possible 5): 5");
        } else {
            System.out.println("Grade for Test2 (out of a possible 5): 0");
        }
        
        System.out.println("Test suite complete!");
    }
    
    private static boolean testAddition() {
        return (2 + 2) == 4;
    }
    
    private static boolean testSubtraction() {
        return (5 - 3) == 2;
    }
}
