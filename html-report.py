import json

# Sample JSON array
json_array = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]

# Generate HTML table
html_table = "<table border='1'>\n"
html_table += "<tr><th>Name</th><th>Age</th></tr>\n"

for item in json_array:
    html_table += "<tr>"
    html_table += f"<td>{item['name']}</td>"
    html_table += f"<td>{item['age']}</td>"
    html_table += "</tr>\n"

html_table += "</table>"

# Print or save the HTML table
print(html_table)
