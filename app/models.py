from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, backref
from .database import Base, engine
from .process_handler import *
import os


class Jobs(Base):
    __tablename__ = 'jobs'

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    db_host = Column(String(16), nullable=False)
    db_port = Column(Integer, nullable=False)
    db_username = Column(String(16), nullable=False)
    db_password = Column(String(255), nullable=False)
    db_name = Column(String(64), nullable=False)
    ssh_needed = Column(Boolean, nullable=False)
    operation_type = Column(String(6), nullable=False)
    __downloaded_file_path = None
    __uploaded_file_path = None

    def get_job_id(self):
        return self.job_id

    def get_db_host(self):
        return self.db_host

    def get_db_port(self):
        return self.db_port

    def get_db_username(self):
        return self.db_username

    def get_db_password(self):
        return self.db_password

    def get_db_name(self):
        return self.db_name

    def get_ssh_needed(self):
        return self.ssh_needed

    def get_operation_type(self):
        return self.operation_type

    def get_ssh_credential(self):
        return self.ssh_credential

    def _run_ssh(self, command):
        ssh_credential = self.get_ssh_credential()
        username = ssh_credential.get_username()
        host = ssh_credential.get_host()
        port = ssh_credential.get_port()

        if ssh_credential.get_auth_method() == 'ssh-key-path':
            ssh_key_path = ssh_credential.get_ssh_key_path().get_path()
            cmd = get_ssh_private_key_command(host, port, username, ssh_key_path) + [
                ' '.join(command)]
        else:
            ssh_password = ssh_credential.get_ssh_password().get_password()
            cmd = get_ssh_password_command(host, port, username, ssh_password) + [' '.join(command)]

        run_bash_command(cmd)

    def __run_scp(self, remote_path, local_path, operation):
        ssh_credential = self.get_ssh_credential()
        username = ssh_credential.get_username()
        host = ssh_credential.get_host()
        port = ssh_credential.get_port()
        cmd = None

        if ssh_credential.get_auth_method() == 'ssh-key-path':
            ssh_key_path = ssh_credential.get_ssh_key_path().get_path()

            if operation == 'download':
                cmd = get_scp_private_key_command(
                    host, port, username, ssh_key_path, local_path, remote_path, 'download'
                )
            elif operation == 'upload':
                cmd = get_scp_private_key_command(host, port, username, ssh_key_path, local_path, remote_path, 'upload')
        else:
            ssh_password = ssh_credential.get_ssh_password().get_password()

            if operation == 'download':
                cmd = get_scp_password_command(host, port, username, ssh_password, local_path, remote_path, 'download')
            elif operation == 'upload':
                cmd = get_scp_password_command(host, port, username, ssh_password, local_path, remote_path, 'upload')

        run_bash_command(cmd)

    def download_file_on_local(self, remote_file_path, download_path):
        self.__run_scp(remote_file_path, download_path, 'download')
        self.__downloaded_file_path = download_path + remote_file_path.split('/')[-1]

        return self

    def upload_file_on_remote(self, local_file_path, destination_file_path):
        self.__run_scp(destination_file_path, local_file_path, 'upload')
        self.__uploaded_file_path = destination_file_path + local_file_path.split('/')[-1]

        return self

    def get_downloaded_file_path(self):
        return self.__downloaded_file_path

    def get_uploaded_file_path(self):
        return self.__uploaded_file_path

    def unzip_file(self, file_path, ssh=False):
        if ssh is True:
            self._run_ssh(get_unzip_command(file_path))
        else:
            run_bash_command(get_unzip_command(file_path))

        return self


class ImportJob(Jobs):
    def start_import_job(self, file_path, ssh: bool = False):
        db_creds = [
            self.get_db_host(),
            self.get_db_port(),
            self.get_db_username(),
            self.get_db_password(),
            self.get_db_name(),
        ]

        import_cmd = imp(
            *db_creds
        )

        additional_sql = self.get_additional_sql()

        with open('additional_sql.sql', 'w') as sql_file:
            sql_file.write(additional_sql.get_command())

        with open('additional_sql.sql', 'r') as sql_file:
            raw_sql = sql_file.read()

        additional_sql_cmd = imp(
            *db_creds
        )

        if ssh is True:
            self._run_ssh(import_cmd)
            self._run_ssh(additional_sql_cmd)
        else:
            # print(test(import_cmd, file_path))
            # print(test(additional_sql_cmd, raw_sql.encode('utf-8')))
            run_bash_command(import_cmd, raw_sql.encode('utf-8'))
            # run_bash_command(additional_sql_cmd)

        return self

    def get_additional_sql(self):
        return self.additional_sql


class ExportJob(Jobs):
    __exported_file_name = None
    __exported_file_path = None

    def start_export_job(self, destination_path, ssh: bool = False):
        file_name = generate_file_name()
        export_cmd = get_export_command(
            self.get_db_host(),
            self.get_db_port(),
            self.get_db_username(),
            self.get_db_password(),
            self.get_db_name(),
            destination_path,
            file_name
        )

        self.__exported_file_path = destination_path + file_name

        if ssh is True:
            self._run_ssh(export_cmd)
        else:
            run_bash_command(export_cmd)

        return self

    def get_exported_file_path(self):
        return self.__exported_file_path


class SSHCredentials(Base):
    __tablename__ = 'ssh_credentials'

    credential_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    auth_method = Column(String(11), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.job_id'))
    job = relationship('Jobs', lazy='subquery', backref=backref('ssh_credential', uselist=False))

    def get_credential_id(self):
        return self.credential_id

    def get_username(self):
        return self.username

    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    def get_auth_method(self):
        return self.auth_method

    def get_ssh_key_path(self):
        return self.ssh_key_path

    def get_ssh_password(self):
        return self.ssh_password


class SSHPasswords(Base):
    __tablename__ = 'ssh_passwords'

    password_id = Column(Integer, primary_key=True, autoincrement=True)
    password = Column(String(255), nullable=False)
    credential_id = Column(Integer, ForeignKey('ssh_credentials.credential_id'))
    ssh_credential = relationship('SSHCredentials', lazy='subquery', backref=backref('ssh_password', uselist=False))

    def get_password_id(self):
        return self.password_id

    def get_password(self):
        return self.password


class SSHKeyPaths(Base):
    __tablename__ = 'ssh_key_paths'

    key_path_id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(255), nullable=False)
    credential_id = Column(Integer, ForeignKey('ssh_credentials.credential_id'))
    ssh_credential = relationship('SSHCredentials', lazy='subquery', backref=backref('ssh_key_path', uselist=False))

    def get_ket_path_id(self):
        return self.key_path_id

    def get_path(self):
        return self.path


class ImportExportJobs(Base):
    __tablename__ = 'import_export_jobs'

    import_export_job_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    export_file_path = Column(String(255), nullable=False)
    import_ssh_home_dir_path = Column(String(255), nullable=True)
    export_job_id = Column(Integer, ForeignKey('jobs.job_id'))
    import_job_id = Column(Integer, ForeignKey('jobs.job_id'))
    export_job = relationship('Jobs', lazy='subquery', foreign_keys=[export_job_id],
                              backref=backref('export_job', uselist=False))
    import_job = relationship('Jobs', lazy='subquery', foreign_keys=[import_job_id],
                              backref=backref('import_job', uselist=False))

    def get_id(self):
        return self.import_export_job_id

    def get_name(self):
        return self.name

    def get_export_job_id(self):
        return self.export_job_id

    def get_import_job_id(self):
        return self.import_job_id

    def get_export_file_path(self):
        return self.export_file_path

    def get_ssh_home_dir_path(self):
        return self.import_ssh_home_dir_path


class AdditionalSQL(Base):
    __tablename__ = 'additional_sql'

    id = Column(Integer, primary_key=True, autoincrement=True)
    command = Column(Text, nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.job_id'))
    job = relationship('Jobs', lazy='subquery', backref=backref('additional_sql', uselist=False))

    def get_id(self):
        return self.id

    def get_command(self):
        return self.command


Base.metadata.create_all(bind=engine)
