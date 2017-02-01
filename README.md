# Shop Around - Pick the best laptop within your budget!

Android (4.1 or higher) dowload here: https://drive.google.com/open?id=0B4Qpy_c-QbUwbThNUUtOU3NDWUk. Sorry, no iOS yet!

###How the app was built?
On server side, I establish an Amazon EC2 instance to run a daily script to get all available laptops on Best Buy, then store the general information on a NoSQL DynamoDB, also an Amazon database service. 

The reason I chose DynamoDB one is for my learning purpose, two I think it supports schema-less database, so I just need to update price only if it’s changed on a specific date and it’s also scalable if I want to scrape info from other sources such as amazon, dell.com, … in the future.

This reposition contains python and php script running on an EC2 instance. The instance has been installed LAMP stack to execute php scripts
- Python script run daily to scrape Bestbuy.ca website to get the most updated info. The data then will append and store in DynamoDB to keep track laptop prices.
- Another Python script to read data from DynamoDB and store it in MySQL

- Php scripts installed in PHPAdmin to executes users' queries.

###Enviroments and technologies
- Android studio (Android front end)
- PHP, MySQL
- Sypder 3.0 on Anacoda (Python)
- EC2, DynamoDB

Mindmap: https://app.mindmup.com/map/_free/e4e0f420dc2411e6bdae49d573dbebce
