<?php
 
/*
 * Following code will get single product details
 * A product is identified by product id (pid)
 */
 
// array for JSON response
$response = array();
 
// include db connect class
require_once __DIR__ . '/db_connect.php';
 
// connecting to db
$db = new DB_CONNECT();
 
// check for post data
if (isset($_GET["sku"])) {
    
	$sku = $_GET['sku'];
    // get data from prices table
    $result = mysql_query("SELECT * FROM prices WHERE SKU = $sku ORDER BY Date ASC");
 
    if (!empty($result)) {
        // check for empty result
        if (mysql_num_rows($result) > 0) {
			// success
            $response["success"] = 1;
 
            // user node
            $response["points"] = array();
			while ($row = mysql_fetch_array($result)) 
			{
 
            $point = array();
            $point["Date"] = $row["Date"];
			$point["Price"] = $row["Price"];
			
 
            array_push($response["points"], $point);
			}
 
            // echoing JSON response
            echo json_encode($response);
        } else {
            // no product found
            $response["success"] = 0;
            $response["message"] = "No product found";
 
            // echo no users JSON
            echo json_encode($response);
        }
    } else {
        // no product found
        $response["success"] = 0;
        $response["message"] = "No product found";
 
        // echo no users JSON
        echo json_encode($response);
    }
} else {
    // required field is missing
    $response["success"] = 0;
    $response["message"] = "Required field(s) is missing";
 
    // echoing JSON response
    echo json_encode($response);
}
?>