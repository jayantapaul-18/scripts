To create an AWS Lambda function that sends HTTP requests using `urllib` and loops through `n` times, you can follow these steps. AWS Lambda functions in Python are typically written in a file named `lambda_function.py` and are deployed using the AWS Lambda console or AWS CLI.

Here’s how you can structure the AWS Lambda function:

1. **Set up the Lambda function** in AWS.
2. **Use `urllib` to make HTTP requests**.
3. **Loop through `n` requests** and print the status codes.

### Example Lambda Function Code

```python
import urllib.request
import json

def lambda_handler(event, context):
    url = event.get('url', 'http://example.com')  # Default URL if not provided
    n = event.get('n', 1)  # Default to 1 if n is not provided

    def get_status_code(url):
        """Lambda function to request a URL and return the status code."""
        return urllib.request.urlopen(url).getcode()

    result = []

    for i in range(n):
        try:
            status_code = get_status_code(url)
            result.append(f"Request {i + 1}: Status code {status_code}")
        except Exception as e:
            result.append(f"Request {i + 1}: Failed with error {e}")

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

### Explanation:

1. **Input through `event`**:
    - The Lambda function takes an event object, which can contain the URL and the number `n` to specify how many requests to make.
    - If the `url` or `n` is not provided in the event, it defaults to `'http://example.com'` and 1, respectively.

2. **`get_status_code` function**:
    - This function is a simple helper that makes an HTTP request to a URL and returns the status code.

3. **Loop through `n`**:
    - A `for` loop makes `n` requests and stores the results (either the status code or the error message) in a `result` list.

4. **Return structure**:
    - The function returns an HTTP response (with status code 200) and a JSON body containing the list of results for each request.

### Deploying to AWS Lambda

1. **Create Lambda Function**:
    - Go to the AWS Lambda console, create a new function, and choose "Author from scratch."
    - Select Python 3.x as the runtime.

2. **Copy and paste the code**:
    - Paste the above code into the Lambda function editor under `lambda_function.py`.

3. **Set IAM Role**:
    - Ensure that the Lambda function has an appropriate IAM role, though for basic outbound HTTP requests, no specific permissions are required.

4. **Test the Function**:
    - Use the "Test" feature in the AWS Lambda console to invoke the function. Here’s an example input:

    ```json
    {
      "url": "http://example.com",
      "n": 5
    }
    ```

5. **Invoke via API Gateway (Optional)**:
    - You can expose this Lambda function via an API Gateway endpoint if you want to call it externally.

### Testing and Example Output

For a test where `n=3` and the URL is `http://example.com`, you might get the following output:

```json
{
  "statusCode": 200,
  "body": [
    "Request 1: Status code 200",
    "Request 2: Status code 200",
    "Request 3: Status code 200"
  ]
}
``` 

This method loops through the specified number of requests and reports the HTTP status for each, returning it in a structured JSON response.
