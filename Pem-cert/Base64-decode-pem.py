import base64

def decode_pem(pem_cert):
  """Decodes a PEM certificate by removing beginning/end markers and newline characters.

  Args:
    pem_cert: A string containing the PEM certificate.

  Returns:
    The decoded base64 content of the PEM certificate.
  """
  # Remove the beginning and end markers (-----BEGIN CERTIFICATE----- and -----END CERTIFICATE-----)
  pem_cert = pem_cert.strip().replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '')
  # Remove newline characters
  pem_cert = pem_cert.replace('\n', '')

  # Decode the base64 encoded certificate
  return base64.b64decode(pem_cert)

# Example usage
pem_cert = """-----BEGIN CERTIFICATE-----
MIICsjCCAjEwDQYJKoZIhvcNAQEFBQAwgcoxCzAJBgNVBAYTAlVTMRMwEQYKCZIxEi
iAiBCTAfpIGcjMA0GCSqGSIb3DQEBAQUAA4IGCSqGSIb3DQEBAQADggEBAKUCPqI
... (certificate content) ...
sXtqSA/zDGrI=
-----END CERTIFICATE-----"""

decoded_cert = decode_pem(pem_cert)
print(decoded_cert)
