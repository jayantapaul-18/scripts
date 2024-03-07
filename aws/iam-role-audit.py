import boto3

def audit_iam_roles():
    # Create IAM client
    iam = boto3.client('iam')

    # List all IAM roles
    response = iam.list_roles()

    # Print information about each role
    for role in response['Roles']:
        role_name = role['RoleName']
        print(f"Role Name: {role_name}")

        # Get attached policies
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
        if attached_policies:
            print("Attached Policies:")
            for policy in attached_policies:
                print(f"- {policy['PolicyName']}")

        # Get inline policies
        inline_policies = iam.list_role_policies(RoleName=role_name)['PolicyNames']
        if inline_policies:
            print("Inline Policies:")
            for policy_name in inline_policies:
                inline_policy = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                print(f"- {policy_name}: {inline_policy['PolicyDocument']}")

        print("\n")

if __name__ == "__main__":
    audit_iam_roles()
