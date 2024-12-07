from utils.split import split

# Example usage
try:
    result = split("hello world this is a test", " ")
    print(result)  # Output: ['hello', 'world', 'this', 'is', 'a', 'test']
except ValueError as e:
    print(f"Error: {e}")