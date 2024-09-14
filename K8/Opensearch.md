const k8s = require('@kubernetes/client-node');
const axios = require('axios');
const Buffer = require('buffer').Buffer;

async function getSecretAndMakeOpenSearchRequest(secretName, namespace, opensearchUrl) {
  try {
    // Load the Kubernetes config
    const kc = new k8s.KubeConfig();
    kc.loadFromDefault();

    // Create the CoreV1 API client
    const k8sApi = kc.makeApiClient(k8s.CoreV1Api);

    // Retrieve the secret from Kubernetes
    const secretResponse = await k8sApi.readNamespacedSecret(secretName, namespace);
    const secretData = secretResponse.body.data;

    // Decode the base64-encoded secret value (assuming the secret key is "opensearch-password")
    const openSearchPassword = Buffer.from(secretData['opensearch-password'], 'base64').toString('utf8');
    
    // Make the OpenSearch request with the secret value
    const response = await axios.get(`${opensearchUrl}/_search`, {
      auth: {
        username: 'admin',  // replace with your username
        password: openSearchPassword
      },
      params: {
        q: 'status:200'
      }
    });

    // Log the OpenSearch response
    console.log('OpenSearch Response:', response.data);

  } catch (err) {
    console.error('Error:', err);
  }
}

// Example usage
const secretName = 'opensearch-secret';
const namespace = 'default';
const opensearchUrl = 'https://your-opensearch-domain.com';
getSecretAndMakeOpenSearchRequest(secretName, namespace, opensearchUrl);
