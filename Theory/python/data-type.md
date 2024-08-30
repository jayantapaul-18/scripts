Here’s a Python script that demonstrates the use of different data types (e.g., strings, lists, dictionaries, sets, tuples) and various methods associated with each type. This script is a good starting point to understand how these data types and methods work together.

### **Python Example Script with Different Data Types and Methods**

```python
# String Data Type and Methods
text = "Hello, World!"

# String methods
print(text.lower())  # Output: "hello, world!" (Convert to lowercase)
print(text.upper())  # Output: "HELLO, WORLD!" (Convert to uppercase)
print(text.replace("World", "Python"))  # Output: "Hello, Python!" (Replace substring)
print(text.split(", "))  # Output: ['Hello', 'World!'] (Split into a list)

# List Data Type and Methods
fruits = ["apple", "banana", "cherry"]

# List methods
fruits.append("orange")  # Add item to end
print(fruits)  # Output: ['apple', 'banana', 'cherry', 'orange']
fruits.remove("banana")  # Remove item by value
print(fruits)  # Output: ['apple', 'cherry', 'orange']
fruits.insert(1, "mango")  # Insert at specific index
print(fruits)  # Output: ['apple', 'mango', 'cherry', 'orange']
print(fruits.pop())  # Output: 'orange' (Remove and return last item)
print(fruits)  # Output: ['apple', 'mango', 'cherry']
fruits.sort()  # Sort list alphabetically
print(fruits)  # Output: ['apple', 'cherry', 'mango']

# Tuple Data Type and Methods
numbers = (1, 2, 3, 4, 5)

# Tuple methods
print(numbers.count(2))  # Output: 1 (Count occurrences of an element)
print(numbers.index(3))  # Output: 2 (Find the index of an element)

# Dictionary Data Type and Methods
student = {"name": "John", "age": 21, "courses": ["Math", "Science"]}

# Dictionary methods
print(student.keys())  # Output: dict_keys(['name', 'age', 'courses']) (Get all keys)
print(student.values())  # Output: dict_values(['John', 21, ['Math', 'Science']]) (Get all values)
print(student.items())  # Output: dict_items([('name', 'John'), ('age', 21), ('courses', ['Math', 'Science'])]) (Get all key-value pairs)
student.update({"age": 22, "city": "New York"})  # Update multiple values
print(student)  # Output: {'name': 'John', 'age': 22, 'courses': ['Math', 'Science'], 'city': 'New York'}
print(student.get("name"))  # Output: 'John' (Get value of a key)
student.pop("age")  # Remove key-value pair
print(student)  # Output: {'name': 'John', 'courses': ['Math', 'Science'], 'city': 'New York'}

# Set Data Type and Methods
numbers_set = {1, 2, 3, 4, 5}
even_numbers = {2, 4, 6}

# Set methods
numbers_set.add(6)  # Add an element
print(numbers_set)  # Output: {1, 2, 3, 4, 5, 6}
numbers_set.remove(3)  # Remove an element
print(numbers_set)  # Output: {1, 2, 4, 5, 6}
print(numbers_set.union(even_numbers))  # Output: {1, 2, 4, 5, 6} (Union of two sets)
print(numbers_set.intersection(even_numbers))  # Output: {2, 4, 6} (Intersection of two sets)
print(numbers_set.difference(even_numbers))  # Output: {1, 5} (Difference between two sets)

# Boolean Data Type and Methods
x = True
y = False

# Boolean expressions and methods
print(x and y)  # Output: False (Logical AND)
print(x or y)  # Output: True (Logical OR)
print(not x)  # Output: False (Logical NOT)

# None Data Type
empty_value = None

# Checking for None
if empty_value is None:
    print("The variable is None.")  # Output: The variable is None.
else:
    print("The variable is not None.")

# Examples of Type Conversion
num_str = "100"
converted_int = int(num_str)  # Convert string to integer
print(converted_int)  # Output: 100
num_float = float(converted_int)  # Convert integer to float
print(num_float)  # Output: 100.0

# Complex Numbers
complex_num = 3 + 4j  # Complex number
print(complex_num.real)  # Output: 3.0 (Real part)
print(complex_num.imag)  # Output: 4.0 (Imaginary part)

# Byte Data Type and Methods
byte_data = b"Hello"
print(byte_data.decode("utf-8"))  # Output: "Hello" (Convert byte to string)
```

### **Explanation of Each Data Type and Methods**

1. **String**: A sequence of characters used to store text. Common methods include `.lower()`, `.upper()`, `.replace()`, and `.split()`.
   
2. **List**: An ordered collection of items, which is mutable. Common methods include `.append()`, `.remove()`, `.insert()`, `.pop()`, and `.sort()`.

3. **Tuple**: An ordered collection of items, which is immutable. Common methods include `.count()` and `.index()`.

4. **Dictionary**: A collection of key-value pairs. Common methods include `.keys()`, `.values()`, `.items()`, `.update()`, `.get()`, and `.pop()`.

5. **Set**: An unordered collection of unique elements. Common methods include `.add()`, `.remove()`, `.union()`, `.intersection()`, and `.difference()`.

6. **Boolean**: A data type with two possible values: `True` or `False`. Logical operations include `and`, `or`, and `not`.

7. **None**: Represents the absence of a value or a null value. Checking if a variable is `None` is commonly done using `is None`.

8. **Type Conversion**: Changing data types using functions like `int()`, `float()`, `str()`, etc.

9. **Complex Numbers**: Numbers with a real and an imaginary part. Access real and imaginary parts using `.real` and `.imag`.

10. **Bytes**: Represents immutable sequences of bytes. Can be converted to strings using `.decode()`.

This script covers various data types and their methods, illustrating how you can manipulate and utilize different types of data in Python. Let me know if you would like to explore any specific data type or method in more detail!
