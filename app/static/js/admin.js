function clear_rows(table)
{
    for( var index = 1; index < table.rows.length; ++index )
    {
        table.deleteRow(-1);
    }
}

function show_products(url)
{
        $("#product_elem").hide();
        $("#staff_elem").hide();
        if( url === '' ) return;
        var json_request = new XMLHttpRequest();
        json_request.open("GET", url, true );
        json_request.onreadystatechange = function ()
        {
            if( json_request.readyState === 4 && json_request.status === 200 ){
                var products = JSON.parse(json_request.responseText);
                var product_table = document.getElementById('product_table');
                clear_rows(product_table);
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
        json_request.onreadystatechange = function ()
        {
            if( json_request.readyState === 4 && json_request.status === 200 ){
                var staffs = JSON.parse(json_request.responseText);
                var staff_table = document.getElementById('staff_table');
                clear_rows(staff_table);
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
                    role = staff.role_name;
                    deleted = staff.is_deleted;
                }
                $("#staff_elem").show();
            }
        };
        json_request.send();
    }