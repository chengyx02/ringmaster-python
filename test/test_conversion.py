from utils.conversion import strict_stoi, strict_stoll, double_to_string, narrow_cast

# Example usage
try:
    print(strict_stoi("123"))  # Output: 123
    print(strict_stoll("123456789012345"))  # Output: 123456789012345
    print(double_to_string(123.456, 2))  # Output: 123.46
    print(narrow_cast(int, 123))  # Output: 123
except Exception as e:
    print(f"Error: {e}")