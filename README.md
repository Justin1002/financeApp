# financeApp Project

CS50 Finance is a full stack web application built with Flask that allows users to buy and sell stocks with real time tracking capabilities.


## Final Product

!["Screenshot of Account Page"](https://raw.githubusercontent.com/Justin1002/financeApp/main/docs/Screenshot_2021-02-17%20C%2450%20Finance%20Account.png)
!["screenshot of Buy page"](https://raw.githubusercontent.com/Justin1002/financeApp/main/docs/Screenshot_2021-02-17%20C%2450%20Finance%20Buy.png)
!["Screenshot of History Page"](https://raw.githubusercontent.com/Justin1002/financeApp/main/docs/Screenshot_2021-02-17%20C%2450%20Finance%20History.png)

## Dependencies

Main Dependencies include:
- cs50
- Flask
- Flask-Session
- requests

Full list can be found in requirements.txt

## Getting Started

- Install all dependencies  using the following command:
  ```
  pip3 install requirements.txt
  ```
- Register for an API key to query IEX data
  - iexcloud.io/cloud-login#/register/
  - Create an account and copy the key under the Token column (begins with pk_)
  - In a terminal window in the project folder, execute
  ```
  $ export API_KEY=copiedKey
  ```
- start the web server
  ```
  flask run --port XXXX
  ```
  where XXXX is the designated port.

## Extras

Added Extras include:

1. Added account page to change password if requested
