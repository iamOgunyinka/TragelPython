$(function(){
        var drop_down = {
            create_key: $('#create_sub'),
            company: $('#select_company')
        };
        var sub_field = {
            last_sub: $('#last_sub'),
            key_field: $('#key_field'),
            start_date: $('#date_from'),
            end_date: $('#date_to')
        };

        update_companies();

        function update_companies()
        {
	        var send = {
		        company_id: drop_down.company.val()
	        };
	        sub_field.last_sub.attr('disabled', 'disabled');
	        $.getJSON("{{url_for('admin._get_subscriptions')}}", send, function
	        (data)
	        {
	            $('#last_sub').val(data.last);
            });
        }

        function get_key()
        {
            $('#key_field').val('');
            var send = {
		        company_id: drop_down.company.val(),
		        start: sub_field.start_date.val(),
		        end: sub_field.end_date.val()
	        };
	        sub_field.key_field.attr('disabled', 'disabled');
	        $.getJSON("{{url_for('admin._get_key')}}", send, function
	        (data)
	        {
	            console.log(data);
	            if( data.error === undefined ){
	                $('#key_field').val(data.key);
	                sub_field.key_field.removeAttr('disabled');;
	            } else {
	                alert(data.error);
	            }
            });
        }
        sub_field.key_field.attr('disabled', 'disabled');
        drop_down.company.on('change', function(){
            update_companies();
        });
        drop_down.create_key.on('click', function(){
            get_key();
        });
        $( "#date_from" ).datepicker();
        $( "#date_to" ).datepicker();
    });