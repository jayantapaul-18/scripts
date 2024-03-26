import boto3
import json

def get_iam_roles(iam_client):
  """
  Gets all IAM roles starting with the specified prefix.
  """
  paginator = iam_client.get_paginator('list_roles')
  roles = []
  for page in paginator.paginate(Prefix='isp'):
    roles.extend(page['Roles'])
  return roles

def get_role_info(iam_client, role):
  """
  Gets information about a specific IAM role, including tags.
  """
  role_data = iam_client.get_role(RoleName=role['RoleName'])
  role_info = {
    'RoleName': role_data['Role']['RoleName'],
    'Arn': role_data['Role']['Arn'],
  }
  if 'Tags' in role_data['Role']:
    role_info['Tags'] = {tag['Key']: tag['Value'] for tag in role_data['Role']['Tags']}
  return role_info

def generate_json_report(roles):
  """
  Generates a JSON file containing selected information about the roles.
  """
  role_data = [get_role_info(iam_client, role) for role in roles]
  with open('iam_roles.json', 'w') as f:
    json.dump(role_data, f, indent=4)

def generate_html_report(roles):
  """
  Generates an HTML report with a table summarizing the roles.
  """
  html_content = """
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>IAM Role Audit Report</title>
    <style>
      table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
        padding: 5px;
      }
    </style>
  </head>
  <body>
    <h1>IAM Role Audit Report</h1>
    <table>
      <tr>
        <th>Role Name</th>
        <th>Arn</th>
        <th>Tags</th>
      </tr>
  """
  for role in roles:
    tags = ', '.join(f"{k}:{v}" for k, v in role.get('Tags', {}).items())
    html_content += f"""
      <tr>
        <td>{role['RoleName']}</td>
        <td>{role['Arn']}</td>
        <td>{tags}</td>
      </tr>
    """
  html_content += """
    </table>
  </body>
  </html>
  """
  with open('iam_roles_report.html', 'w') as f:
    f.write(html_content)

if __name__ == '__main__':
  iam_client = boto3.client('iam')
  roles = get_iam_roles(iam_client)

  generate_json_report(roles)
  generate_html_report(roles)

  print("IAM role information saved to iam_roles.json and iam_roles_report.html")
