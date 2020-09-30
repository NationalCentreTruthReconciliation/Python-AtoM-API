import getpass

def prompt_for_username_password(prompt: str):
    print(prompt)
    username = ''
    while username == '':
        username = input('Username: ').strip()
    password = getpass.getpass()
    return {
        'username': username,
        'password': password,
    }
