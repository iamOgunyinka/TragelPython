function show_products(url)
{
	$("#product_elem").hide();
	$("#staff_elem").hide();
	if( url === '' ) return;
	var json_request = new XMLHttpRequest();
	json_request.open("GET", url, true);
	function create_thead(table){
		$("#product_table tr").remove();
		var header = table.createTHead();	
		var row = header.insertRow(0);
		var cell_sn = row.insertCell(0);
		var cell_name = row.insertCell(1);
		var cell_price = row.insertCell(2);
		var cell_status = row.insertCell(3);
		cell_sn.innerHTML = "S/N";
		cell_name.innerHTML = "Name";
		cell_price.innerHTML = "Price(₦)";
		cell_status.innerHTML = "Status";
	}
	json_request.onreadystatechange = function()
	{
		if( json_request.readyState === 4 && json_request.status === 200 ){
			var products = JSON.parse(json_request.responseText);
			var product_table = document.getElementById('product_table');
			create_thead(product_table);
			for( var index = 0; index != products.length; index = index + 1 )
			{
				var new_row = product_table.insertRow(index+1);
				var product = products[index];
				var sn = new_row.insertCell(0);
				var name = new_row.insertCell(1);
				var price = new_row.insertCell(2);
				var is_deleted = new_row.insertCell(3);

				sn.innerHTML = index + 1;
				name.innerHTML = product.name;
				price.innerHTML = product.price;
				if( product.deleted === true ){
					is_deleted.innerHTML = "Deleted";
				} else {
					is_deleted.innerHTML = "Active";
				}
			}
			$("#product_elem").show();
		}
	};
	json_request.send();
}

function show_staffs(url)
{
	$("#product_elem").hide();
	$("#staff_elem").hide();
	if( url === '' ) return;
	var json_request = new XMLHttpRequest();
	json_request.open("GET", url, true );
	function create_thead(table){
		$("#staff_table tr").remove();
		var header = table.createTHead();
		var row = header.insertRow(0);
		var cell_sn = row.insertCell(0);
		var cell_staff_id = row.insertCell(1);
		var cell_name = row.insertCell(2);
		var cell_email = row.insertCell(3);
		var cell_role = row.insertCell(4);
		var cell_status = row.insertCell(5);
		cell_sn.innerHTML = "S/N";
		cell_staff_id.innerHTML = "Staff ID";
		cell_name.innerHTML = "Name";
		cell_email.innerHTML = "Email";
		cell_role.innerHTML = "Role";
		cell_status.innerHTML = "Status";
	}
	
	json_request.onreadystatechange = function ()
	{
		if( json_request.readyState === 4 && json_request.status === 200 ){
			var staff_table = document.getElementById('staff_table');
			create_thead(staff_table);
			var staffs = JSON.parse(json_request.responseText);
			for( var index = 0; index != staffs.length; index = index + 1 )
			{
				var new_row = staff_table.insertRow(index+1);
				var staff = staffs[index];

				var sn = new_row.insertCell(0);
				var company_id = new_row.insertCell(1);
				var name = new_row.insertCell(2);
				var email = new_row.insertCell(3);
				var role = new_row.insertCell(4);
				var deleted = new_row.insertCell(5);

				sn.innerHTML = index + 1;
				company_id.innerHTML = staff.id;
				name.innerHTML = staff.name;
				email.innerHTML = staff.email;
				role.innerHTML = staff.role_name;
				deleted.innerHTML = staff.is_deleted ? "Deleted": "Active";
			}
			$("#staff_elem").show();
		}
	};
	json_request.send();
}