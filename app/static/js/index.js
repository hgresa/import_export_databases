for (const operation of ['export', 'import']) {
    $(`#${operation}-ssh-needed`).on('change', function (event) {
        let option = event.target.value
        let ssh_credentials_element = $(`.${operation}-ssh-credentials`)

        if (option === `${operation}-ssh-yes`) {
            ssh_credentials_element.show()
        } else if (option === `${operation}-ssh-no`) {
            ssh_credentials_element.hide()
        }
    })

    $(`#${operation}-ssh-auth-method`).on('change', function (event) {
        let option = event.target.value
        let ssh_password_element = $(`#${operation}-ssh-password`)
        let ssh_key_path_element = $(`#${operation}-ssh-key-path`)

        if (option === `${operation}-ssh-password`) {
            ssh_key_path_element.parent().hide()
            ssh_password_element.parent().show()
        } else if (option === `${operation}-ssh-key-path`) {
            ssh_password_element.parent().hide()
            ssh_key_path_element.parent().show()
        }
    })
}

$('.btn-success').on('click', function (event) {
    let import_export_job_id = event.target.value
    $.post({
        async: false,
        url: '/run_job',
        data: {'import_export_job_id': import_export_job_id}
    })
})

$('#submit').on('click', function () {
    let form_data = $('form')
    let fd = new FormData(form_data[0])
    $.post({
            async: false,
            url: '/save_job',
            contentType: false,
            processData: false,
            data: fd
        }
    )
})
