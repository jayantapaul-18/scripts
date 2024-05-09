import pem

def extract_pem_info(filename):
  """
  Extracts certificates and basic information from a PEM file.

  Args:
    filename: The path to the PEM file.

  Returns:
    A list of dictionaries, where each dictionary contains information
    about a certificate found in the file. The dictionary may include:
      - type: The type of PEM object (e.g., "Certificate").
      - data: The PEM encoded data.
      - subject: The subject (owner) of the certificate (if applicable).
      - issuer: The issuer (authority that issued the certificate) (if applicable).
      - validity: A tuple containing the (not before, not after) validity dates (if applicable).
  """
  certs = []
  with open(filename, 'rb') as pem_file:
    for cert in pem.parse(pem_file.read()):
      cert_info = {}
      cert_info['type'] = cert.type
      cert_info['data'] = str(cert)  # PEM encoded data

      # Additional information extraction (limited for certificates)
      if cert.type == pem.Certificate:
        try:
          from cryptography.x509 import load_pem_x509_certificate
          certificate = load_pem_x509_certificate(cert.data, cryptography.x509.default_backend())
          cert_info['subject'] = certificate.subject.get_attributes_for_oid(cryptography.x509.NameOID.COMMON_NAME)[0].value
          cert_info['issuer'] = certificate.issuer.get_attributes_for_oid(cryptography.x509.NameOID.COMMON_NAME)[0].value
          cert_info['validity'] = (certificate.not_valid_before, certificate.not_valid_after)
        except Exception as e:
          # Handle potential errors during certificate parsing
          print(f"Error extracting details for certificate: {e}")

      certs.append(cert_info)
  return certs

# Example usage
pem_file = "certificates.pem"
cert_info_list = extract_pem_info(pem_file)

for cert_info in cert_info_list:
  print(f"Type: {cert_info['type']}")
  print(f"Data:\n{cert_info['data']}")
  if 'subject' in cert_info:
    print(f"Subject: {cert_info['subject']}")
  if 'issuer' in cert_info:
    print(f"Issuer: {cert_info['issuer']}")
  if 'validity' in cert_info:
    print(f"Validity: {cert_info['validity'][0]} - {cert_info['validity'][1]}")
  print("-"*20)
