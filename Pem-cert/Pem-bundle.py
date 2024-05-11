from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import ssl


def load_pem_cert_bundle(pem_path):
  """Loads certificates from a PEM file and returns a list.

  Args:
    pem_path: Path to the PEM file.

  Returns:
    A list of loaded X.509 certificates.
  """
  with open(pem_path, 'rb') as pem_file:
    pem_data = pem_file.read()
  certs = []
  for cert_data in pem_data.split('-----BEGIN CERTIFICATE-----'):
    if cert_data.strip():
      certs.append(load_pem_x509_certificate(cert_data, default_backend()))
  return certs


# Example usage (assuming server-side SSL context creation)
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.load_cert_chain(pem_path, password=None)  # Optional password for encrypted PEM files
