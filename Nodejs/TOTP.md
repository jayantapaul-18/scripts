To develop a local **TOTP (Time-based One-Time Password)** API for user registration and code generation, you'll need to:

1. Allow users to register and generate a unique secret for each user.
2. Use the secret to generate a TOTP code at the time of request.
3. Validate the TOTP code for authentication.

We'll use Node.js and the `speakeasy` library to handle TOTP generation and validation. You can also use an in-memory database (like a simple JSON object) or a real database (e.g., SQLite, PostgreSQL) to store user secrets. In this example, I'll use a simple in-memory object for demonstration purposes.

### Steps:

1. **Set Up the Project:**
   - Initialize a Node.js project.
   - Install necessary dependencies.

2. **Register API:**
   - Generate a TOTP secret for a user and store it.

3. **Generate TOTP Code API:**
   - Use the stored secret to generate a TOTP code.

4. **Verify TOTP Code API:**
   - Verify if the given TOTP code is correct.

---

### 1. **Set Up the Project**

Create a folder for your project and initialize a Node.js app:

```bash
mkdir totp-api
cd totp-api
npm init -y
```

Install the required packages:

```bash
npm install express speakeasy qrcode
```

- **`express`**: A lightweight web framework for building APIs.
- **`speakeasy`**: Library for generating and verifying TOTP codes.
- **`qrcode`**: Generates a QR code that users can scan with TOTP apps like Google Authenticator.

---

### 2. **Create the API**

Create a file `index.js` for the API:

```javascript
const express = require('express');
const speakeasy = require('speakeasy');
const qrcode = require('qrcode');

const app = express();
app.use(express.json());

// In-memory store for users' TOTP secrets
let userSecrets = {};

// Register a user and generate TOTP secret
app.post('/register', (req, res) => {
  const { username } = req.body;

  if (!username) {
    return res.status(400).json({ message: 'Username is required' });
  }

  // Generate a TOTP secret for the user
  const secret = speakeasy.generateSecret({
    name: `TOTP Demo (${username})`
  });

  // Store the secret in memory (could be stored in a database)
  userSecrets[username] = secret.base32;

  // Generate a QR code for easy setup in authenticator apps
  qrcode.toDataURL(secret.otpauth_url, (err, data) => {
    if (err) {
      return res.status(500).json({ message: 'Error generating QR code' });
    }
    res.json({ message: 'User registered', secret: secret.base32, qrCode: data });
  });
});

// Get TOTP code for a user
app.get('/get-totp/:username', (req, res) => {
  const { username } = req.params;

  if (!userSecrets[username]) {
    return res.status(404).json({ message: 'User not found' });
  }

  // Generate the current TOTP code using the secret
  const token = speakeasy.totp({
    secret: userSecrets[username],
    encoding: 'base32'
  });

  res.json({ username, token });
});

// Verify the TOTP code provided by the user
app.post('/verify-totp', (req, res) => {
  const { username, token } = req.body;

  if (!username || !token) {
    return res.status(400).json({ message: 'Username and token are required' });
  }

  if (!userSecrets[username]) {
    return res.status(404).json({ message: 'User not found' });
  }

  // Verify the provided token
  const isVerified = speakeasy.totp.verify({
    secret: userSecrets[username],
    encoding: 'base32',
    token,
    window: 1 // Allow a small window for time drift
  });

  if (isVerified) {
    res.json({ message: 'Token verified successfully' });
  } else {
    res.status(400).json({ message: 'Invalid token' });
  }
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`TOTP API server running on port ${PORT}`);
});
```

---

### 3. **Explanation of the Code**

- **`/register`**: This endpoint generates a unique TOTP secret for a user and returns it, along with a QR code (which users can scan with an app like Google Authenticator).
  
- **`/get-totp/:username`**: This endpoint generates a TOTP code for a user based on their secret. The code changes every 30 seconds.

- **`/verify-totp`**: This endpoint verifies the TOTP code sent by the user. It uses the secret stored for the user to check if the provided code is valid.

### Example Requests

1. **Register a User**:

```bash
POST /register
Content-Type: application/json

{
  "username": "user1"
}
```

Response:
```json
{
  "message": "User registered",
  "secret": "JBSWY3DPEHPK3PXP",
  "qrCode": "data:image/png;base64,iVBORw..."
}
```

- The `secret` is the base32-encoded TOTP secret.
- The `qrCode` is a base64-encoded image URL that can be scanned with TOTP apps like Google Authenticator.

2. **Get TOTP Code for a User**:

```bash
GET /get-totp/user1
```

Response:

```json
{
  "username": "user1",
  "token": "123456"
}
```

3. **Verify the TOTP Code**:

```bash
POST /verify-totp
Content-Type: application/json

{
  "username": "user1",
  "token": "123456"
}
```

Response if successful:
```json
{
  "message": "Token verified successfully"
}
```

Response if failed:
```json
{
  "message": "Invalid token"
}
```

---

### 4. **Running the Application**

1. Run the application:
   ```bash
   node index.js
   ```

2. The server will start on `http://localhost:3000`.

You can now use tools like Postman, cURL, or your frontend application to register users, generate TOTP codes, and verify them against the stored secrets.

---

### 5. **Advanced Options**

- **Persisting Secrets**: Instead of storing secrets in memory (`userSecrets` object), store them in a database (e.g., SQLite, PostgreSQL) for persistence.
- **Security**: Consider using HTTPS in production to protect API requests that handle sensitive information like the secret and token.
- **Token Expiration Handling**: TOTP tokens expire after a set time (usually 30 seconds), but you can adjust the `window` parameter in `speakeasy` to allow for some time drift.

---

This setup provides a simple, local TOTP API to register users, generate TOTP codes, and verify them using the `speakeasy` library in Node.js.
