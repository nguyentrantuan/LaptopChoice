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
if (isset($_GET["high"])) {
    
	$high = $_GET['high'];
	$low = 0;
	if (isset($_GET["low"]))
		$low = $_GET['low'];
    // get a laptop from laptops table
    $result = mysql_query("SELECT *FROM laptops WHERE CurrentPrice > $low AND CurrentPrice < $high ORDER BY Bestmatch LIMIT 10");
 
    if (!empty($result)) {
        // check for empty result
        if (mysql_num_rows($result) > 0) {
			// success
            $response["success"] = 1;
 
            // user node
            $response["laptop"] = array();
			while ($row = mysql_fetch_array($result)) 
			{
 
            $laptop = array();
            $laptop["index"] = $row["index"];
            $laptop["Video Memory Configuration"] = $row["Video Memory Configuration"];
            $laptop["rating"] = $row["rating"];
            $laptop["NoRaters"] = $row["NoRaters"];
            $laptop["SKU"] = $row["SKU"];
            $laptop["seller"] = $row["seller"];
			$laptop["link"] = $row["link"];
            $laptop["Screen Size"] = $row["Screen Size"];
			$laptop["Touchscreen Display"] = $row["Touchscreen Display"];
			$laptop["Processor Type"] = $row["Processor Type"];
			$laptop["Hard Drive Capacity"] = $row["Hard Drive Capacity"];
			$laptop["RAM Size"] = $row["RAM Size"];
			$laptop["Dedicated Video Memory Size"] = $row["Dedicated Video Memory Size"];
			$laptop["SSD Function"] = $row["SSD Function"];
			$laptop["imgsrc"] = $row["imgsrc"];
			$laptop["ProductName"] = $row["ProductName"];
			$laptop["CurrentPrice"] = $row["CurrentPrice"];
			$laptop["TotalPoint"] = $row["TotalPoint"];
			$laptop["HDD point"] = $row["HDD point"];
			$laptop["RAM point "] = $row["RAM point"];
			$laptop["CPU point"] = $row["CPU point"];
			$laptop["Review point"] = $row["Review point"];
			$laptop["Bestmatch"] = $row["Bestmatch"];
			
 
            array_push($response["laptop"], $laptop);
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