const fs = require('fs');

// Read JSON file
fs.readFile('data.json', 'utf8', (err, data) => {
  if (err) {
    console.error('Error reading JSON file:', err);
    return;
  }

  // Parse JSON data
  const jsonData = JSON.parse(data);

  // Create HTML template
  const htmlTemplate = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>JSON to HTML Report</title>
    </head>
    <body>
      <h1>Report</h1>
      <ul>
        <% jsonData.forEach(item => { %>
          <li><strong>Name:</strong> <%= item.name %>, <strong>Age:</strong> <%= item.age %></li>
        <% }); %>
      </ul>
    </body>
    </html>
  `;

  // Populate HTML template with data
  const populatedHtml = htmlTemplate.replace(/<%([^%>]+)?%>/g, (match, p1) => {
    return eval(p1);
  });

  // Write HTML to file
  fs.writeFile('report.html', populatedHtml, (err) => {
    if (err) {
      console.error('Error writing HTML file:', err);
      return;
    }
    console.log('HTML report generated successfully!');
  });
});
