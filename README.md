# Description
This is my homework, a microservice-based API using rabbitmq, postgres and redis. 
The goal of the service is to provide easy-to-use APi for collecting activity on your website.  
Features:
  * API is using tokens. separate tokens for *append* (collecting data) and *read* (getting report) rights.
  * collect data on your user's activity:
     * total visits
     * unique users
     * amount of visits for each page
  * request report on your domain, it will arrive to provided address in form of email.

# Setup (\#TODO)
Figure out :)

# Test
There are several scripts that make it easier to test the api from command line. 
If you have sufficient skill with linux bash/shell you can open them and try changing some values yourself.  
  
Available scripts:
* `test.sh` - calls root of the API, simple message response is expected.
* `append_test.sh` - sends bunch of requests with several unique ids.
* `email_test.sh` - sends request with some email (input argument) to retrieve report.
