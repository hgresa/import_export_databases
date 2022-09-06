import subprocess
from subprocess import PIPE
from datetime import date
import random
import string


def run_bash_command(command, _input=None):
    subprocess.run(command, input=_input)


def generate_random_string():
    letters = string.ascii_lowercase

    return ''.join(random.choice(letters) for i in range(10))


def generate_file_name():
    today = date.today().strftime('%d-%m-%Y')

    return f'{today}_{generate_random_string()}.sql.gz'


def get_unzip_command(file_path):
    return ['gunzip', file_path]


def get_export_command(db_host, db_port, db_username, db_password, db_name, destination_path, file_name):
    return [
        'mysqldump', '-h', db_host, '-P', str(db_port), '-u', db_username, f'--password={db_password}', db_name,
        '|', 'gzip', '>', f'{destination_path}{file_name}'
    ]


def get_import_command(db_host, db_port, db_username, db_password, db_name, file):
    return [
        'mysql', '-h', db_host, '-P', str(db_port), '-u', db_username, "-p%s" % db_password, db_name, '<', file
    ]


def imp(db_host, db_port, db_username, db_password, db_name):
    return [
        'mysql', '-h', db_host, '-P', str(db_port), '-u', db_username, "-p%s" % db_password, db_name
    ]


def get_ssh_password_command(host, port, username, password):
    return ['sshpass', '-p', password, 'ssh', '-p', str(port), f'{username}@{host}']


def get_ssh_private_key_command(host, port, username, key_path):
    return ['ssh', '-i', key_path, '-p', str(port), f'{username}@{host}']


def get_scp_private_key_command(host, port, username, key_path, local_file_path, remote_file_path, operation):
    port = str(port)

    if operation == 'upload':
        return ['scp', '-i', key_path, '-P', port, local_file_path, f'{username}@{host}:{remote_file_path}']
    elif operation == 'download':
        return ['scp', '-i', key_path, '-P', port,  f'{username}@{host}:{remote_file_path}', local_file_path]


def get_scp_password_command(host, port, username, password, local_file_path, remote_file_path, operation):
    port = str(port)

    if operation == 'upload':
        return ['sshpass', '-p', password, 'scp', '-P', port, local_file_path, f'{username}@{host}:{remote_file_path}']
    elif operation == 'download':
        return ['sshpass', '-p', password, 'scp', '-P', port, f'{username}@{host}:{remote_file_path}', local_file_path]
