# Product catalogue API
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
---

## Project Description
1. This application is a python JSON REST API that allows the user to browse a catalogue of products and product offers that are provided by the applifting offers microservice.
2. This application supports CRUD for products, allowing you to:
   1. Add a product to the catalogue.
   2. View all the products.
   3. View one specific product.
   4. Update either the name or description of an exsisting product.
   5. Delete a product.
3. The product offers are read only so you can:
   1. View all the offers for one specific product.
   2. View all the offers for every product in the catalogue.
4. There is also an updater component than ensures all the offers listed are kept up to date by making requests every minute on the offers for each product.

## Setup
### Base Set up
1. You will need to have the latest version of python installed and all the packages listed in the requirements.txt file. This file also specifies the version of each package that is used in the project.
   1. Due to the number of packages it is recommended that you create a virtual environment first. I used Anaconda as my python interperater and visual studio code to create the virtual environment.
   2. By doing it this way all the packages, and the correct versions, can be installed all at once using the requirements.txt file.

2. Ensure the project is in the same base directory as the created virtual environment. Once this is done you can begin to set up the project with the following steps:
   1. (This may not be required) Enter the command: Set-ExecutionPolicy Unrestricted -Scope Process in order to be able to activate the virtual environment.
   2. Activate the virtual environment  in windows using: venv\Scripts\Activate.ps1 (or source venv/bin/activate for mac).
   3. Once in the virtual environment enter the python terminal and run the following:
      1. from app import app, db
      2. app.app_context().push()
      3. db.create_all()

    This will create and initialise the database with the mode defined in app.py file and you can now exit out of the python terminal.

### Environment variables
In the .env file, there are the following environment variables that are used and can be configured:
1. The refresh token: the token used for obtaining access tokens required for authenticating requests from the offers microservice.
2. The offers microservice URI: this specifies the root address for the offers microservice.
3. Testing mode: this tells the application whether it is running for the purpose of running tests or for production use. If TESTING_MODE is set to true, then the background updater will not be started, and the application will run in local mode only. This then allows you to run tests using pytest (basic tests provided in the tests.py file). Otherwise, the application will start up and run all the code defined.

## Starting the application
### Production
(Ensure the TESTING_MODE environment variable in the .env file is set to false)

The application can either be started by using python app.py in the terminal or, you can use flask run to start the application using flask.

On start up, the application will send a post request to obtain the access token and a message will be displayed in the console telling you if it has obtained the token or not.

You can either use an application like postman to handle and view responses from requests or you can use ctrl and click the localhost link displayed in the terminal and you will be taken to the API homepage that uses a basic swagger UI. From there you can use the requests listed.

### Testing
(Set the TESTING_MODE environment variable in the .env file to true)
Start the application the same way (either using python app.py or flask run) and the application will start in testing mode.

From there, your own tests can be created and run from a separate file or the tests in the tests.py file provided can be used (see included tests section below).

## Included Tests
The project folder includes several basic tests which can be run using pytest by following the steps below:
1. Start the application in testing mode.
2. Open a new terminal once the application is running and run the commands to enter the virtual environment.
3. In the new terminal run: pytest tests.py

The results of the tests (pass or fail) will be listed after the code has been fully executed.

## Credits
### Applifting
I would like to thank Applifting for not only providing the offers microservice in order for the Product catalogue API to be used but also for giving me the opportunity to take on this task/challenge. It has been an amazing learning experience that expanded my programming and computer science knowledge greatly.
