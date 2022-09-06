from app import app
from flask import render_template, request
from app.models import Jobs, SSHPasswords, SSHCredentials, SSHKeyPaths, ImportExportJobs, AdditionalSQL, ExportJob, ImportJob
from .database import SessionLocal
import os


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/save_job', methods=['POST'])
def save_job():
    objects_to_save = {'export': {}, 'import': {}}
    form_data = request.form

    for operation in ['export', 'import']:
        database_host = form_data.get(f'{operation}-database-host')
        database_port = form_data.get(f'{operation}-database-port')
        database_username = form_data.get(f'{operation}-database-username')
        database_password = form_data.get(f'{operation}-database-password')
        database_name = form_data.get(f'{operation}-database-name')
        ssh_needed = True if form_data.get(f'{operation}-ssh-needed') == f'{operation}-ssh-yes' else False
        job_name = form_data.get('job-name')

        job = Jobs(
            db_host=database_host,
            db_port=int(database_port),
            db_username=database_username,
            db_password=database_password,
            db_name=database_name,
            ssh_needed=ssh_needed,
            operation_type=operation
        )

        objects_to_save[f'{operation}']['job'] = job

        if ssh_needed:
            ssh_username = form_data.get(f'{operation}-ssh-username')
            ssh_host = form_data.get(f'{operation}-ssh-host')
            ssh_port = form_data.get(f'{operation}-ssh-port')
            ssh_auth_method = form_data.get(f'{operation}-ssh-auth-method')

            ssh_credential = SSHCredentials(
                username=ssh_username,
                host=ssh_host,
                port=int(ssh_port),
                auth_method=ssh_auth_method[7:],
                job=job
            )

            objects_to_save[f'{operation}']['ssh_credential'] = ssh_credential

            if ssh_auth_method == f'{operation}-ssh-password':
                ssh_password = form_data.get(f'{operation}-ssh-password')

                ssh_password = SSHPasswords(
                    password=ssh_password,
                    ssh_credential=ssh_credential
                )

                objects_to_save[f'{operation}']['ssh_password'] = ssh_password
            else:
                ssh_key_path = form_data.get(f'{operation}-ssh-key-path')

                ssh_key_path = SSHKeyPaths(
                    path=ssh_key_path,
                    ssh_credential=ssh_credential
                )

                objects_to_save[f'{operation}']['ssh_key_path'] = ssh_key_path

    import_export = ImportExportJobs(
        name=job_name,
        export_file_path=form_data.get('export-file-path'),
        import_ssh_home_dir_path=form_data.get('import-ssh-home-directory'),
        export_job=objects_to_save['export']['job'],
        import_job=objects_to_save['import']['job']
    )

    additional_sql = AdditionalSQL(
        command=form_data.get('import-additional-sql'),
        job=objects_to_save['import']['job']
    )

    with SessionLocal() as session:
        session.add(import_export)
        session.add(additional_sql)

        for operation in ['export', 'import']:
            for key, obj in objects_to_save[operation].items():
                session.add(obj)

        session.commit()

    return ''


@app.route('/edit_job', methods=['GET', 'POST'])
def edit_job():
    pass


@app.route('/job_list', methods=['GET'])
def job_list():
    with SessionLocal() as session:
        import_export_jobs = session.query(ImportExportJobs).all()

    return render_template('job_list.html', jobs=import_export_jobs)


@app.route('/run_job', methods=['POST'])
def start_process():
    import_export_job_id = request.form.get('import_export_job_id')

    with SessionLocal() as session:
        import_export_job = session.query(ImportExportJobs).get(import_export_job_id)

    export_job = session.query(ExportJob).get(import_export_job.get_export_job_id())
    import_job = session.query(ImportJob).get(import_export_job.get_import_job_id())

    if export_job.get_ssh_needed() is True:
        export_job\
            .start_export_job(destination_path=import_export_job.get_export_file_path(), ssh=True)\
            .download_file_on_local(remote_file_path=export_job.get_exported_file_path(), download_path=os.path.expanduser('~') + '/')

        if import_job.get_ssh_needed() is True:
            import_job\
                .upload_file_on_remote(local_file_path=export_job.get_downloaded_file_path(), destination_file_path=import_export_job.get_ssh_home_dir_path())\
                .unzip_file(file_path=import_job.get_uploaded_file_path(), ssh=True)\
                # .start_import_job(file_path=import_job.get_uploaded_file_path(), ssh=True)
        else:
            # localhost or remote
            export_job.unzip_file(file_path=export_job.get_downloaded_file_path(), ssh=False)
            # import_job.start_import_job(file_path=export_job.get_downloaded_file_path())
    else:
        export_job.start_export_job(destination_path='/home/hgresa')

        if import_job.get_ssh_needed() is True:
            import_job\
                .upload_file_on_remote(local_file_path=export_job.get_exported_file_path(), destination_file_path=import_export_job.get_ssh_home_dir_path())\
                .unzip_file(file_path=import_job.get_uploaded_file_path(), ssh=True)\
                .start_import_job(file_path=import_job.get_uploaded_file_path(), ssh=True)
        else:
            # localhost or remote
            import_job.start_import_job(file_path=export_job.get_exported_file_path())

    return ''
