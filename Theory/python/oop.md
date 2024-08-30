To learn Python Object-Oriented Programming (OOP) and advanced functions, I'll provide a structured approach with explanations, examples, and key concepts.

### **Part 1: Python Object-Oriented Programming (OOP)**

OOP is a programming paradigm that uses "objects" — data structures consisting of fields and methods — to design software. The main concepts in OOP are **classes**, **objects**, **inheritance**, **encapsulation**, **polymorphism**, and **abstraction**.

#### **1.1 Basics of Classes and Objects**

- **Class**: A blueprint for creating objects (a specific data structure). It defines properties and behaviors.
- **Object**: An instance of a class. It represents a specific entity created using the blueprint.

##### **Example: Creating a Class and an Object**

```python
class Car:
    def __init__(self, brand, model, year):
        # Constructor method, initializes the object with given attributes
        self.brand = brand
        self.model = model
        self.year = year

    def display_info(self):
        # Method to display car information
        print(f"Car: {self.brand} {self.model} ({self.year})")


# Creating an object of the Car class
my_car = Car("Toyota", "Camry", 2020)

# Accessing object methods
my_car.display_info()
```

#### **1.2 Key OOP Concepts**

- **Encapsulation**: Restricting access to certain components (attributes/methods) of an object.
  
  ```python
  class BankAccount:
      def __init__(self, balance):
          self.__balance = balance  # Private attribute

      def deposit(self, amount):
          if amount > 0:
              self.__balance += amount
          return self.__balance

      def __str__(self):
          return f"Account balance: {self.__balance}"

  account = BankAccount(100)
  print(account.deposit(50))  # Output: 150
  print(account.__balance)  # Raises AttributeError
  ```

- **Inheritance**: Creating a new class from an existing class, inheriting its attributes and methods.

  ```python
  class Vehicle:
      def __init__(self, brand):
          self.brand = brand

      def start(self):
          print("Vehicle started")

  class Car(Vehicle):  # Car class inherits from Vehicle
      def __init__(self, brand, model):
          super().__init__(brand)  # Call the parent class constructor
          self.model = model

      def honk(self):
          print("Honk! Honk!")

  my_car = Car("Toyota", "Corolla")
  my_car.start()  # Inherited method
  my_car.honk()   # Method specific to Car
  ```

- **Polymorphism**: Methods in different classes can have the same name, but behave differently.

  ```python
  class Animal:
      def speak(self):
          print("Animal speaks")

  class Dog(Animal):
      def speak(self):
          print("Woof! Woof!")

  class Cat(Animal):
      def speak(self):
          print("Meow!")

  animals = [Dog(), Cat()]
  for animal in animals:
      animal.speak()  # Calls the appropriate speak method
  ```

- **Abstraction**: Hiding complex implementation details and exposing only the essential parts. Typically achieved using abstract classes or interfaces.

  ```python
  from abc import ABC, abstractmethod

  class Shape(ABC):
      @abstractmethod
      def area(self):
          pass

  class Circle(Shape):
      def __init__(self, radius):
          self.radius = radius

      def area(self):
          return 3.14 * self.radius ** 2

  c = Circle(5)
  print(c.area())  # Output: 78.5
  ```

### **Part 2: Advanced Functions in Python**

#### **2.1 Lambda Functions**

- **Lambda functions** are small anonymous functions that can have any number of arguments but only one expression.

  ```python
  add = lambda x, y: x + y
  print(add(3, 5))  # Output: 8
  ```

- **Use Case**: Commonly used for short, throwaway functions or when a full `def` function definition would be unnecessary.

#### **2.2 Decorators**

- **Decorators** are functions that modify the functionality of other functions. They are a powerful tool for extending or wrapping existing functions.

  ```python
  def my_decorator(func):
      def wrapper():
          print("Something is happening before the function is called.")
          func()
          print("Something is happening after the function is called.")
      return wrapper

  @my_decorator
  def say_hello():
      print("Hello!")

  say_hello()
  ```

#### **2.3 Generators**

- **Generators** are functions that return an iterator that yields values one at a time. They are created using `yield` instead of `return`.

  ```python
  def fibonacci(n):
      a, b = 0, 1
      for _ in range(n):
          yield a
          a, b = b, a + b

  for num in fibonacci(5):
      print(num)  # Output: 0, 1, 1, 2, 3
  ```

#### **2.4 Higher-Order Functions**

- **Higher-Order Functions** take other functions as arguments or return functions as results. Examples include `map()`, `filter()`, and `reduce()`.

  ```python
  numbers = [1, 2, 3, 4, 5]

  # Using map to apply a lambda function to each element
  squared = list(map(lambda x: x ** 2, numbers))
  print(squared)  # Output: [1, 4, 9, 16, 25]

  # Using filter to keep only even numbers
  evens = list(filter(lambda x: x % 2 == 0, numbers))
  print(evens)  # Output: [2, 4]
  ```

#### **2.5 Function Annotations**

- **Function annotations** provide a way of attaching metadata to function arguments and return values, though they have no runtime effect.

  ```python
  def greet(name: str) -> str:
      return f"Hello, {name}!"

  print(greet("Alice"))  # Output: Hello, Alice!
  ```

### **Next Steps**

To master these concepts:
1. **Practice Regularly**: Implement small projects or code challenges to apply what you've learned.
2. **Read Books/Documentation**: "Fluent Python" by Luciano Ramalho and the [Python documentation](https://docs.python.org/3/tutorial/) are excellent resources.
3. **Explore Libraries and Frameworks**: Experiment with Python libraries like `numpy`, `pandas`, and `flask` to understand how they utilize OOP and advanced functions.

Would you like more details or examples on any specific topic?
