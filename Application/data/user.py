from dotenv import dotenv_values


class User:
    MAIN_TOKEN = dotenv_values('secrets.env').get('MAIN_TOKEN', '')
    TEST_TOKEN = dotenv_values('secrets.env').get('TEST_TOKEN', '')

if __name__ == '__main__':
    print(User.MAIN_TOKEN, '\n', User.TEST_TOKEN)