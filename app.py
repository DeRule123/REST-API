#Imports from standard and non-standard python packages. imports from offers_service_calls are
#imports from another .py file that is part of the application which handles the requests to the
#offers api provided by applifiting that are then used in the main application code for product
#registering and getting the offers for the products.
import os
from flask import Flask, json, jsonify, request, redirect
from flasgger import Swagger
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import uuid
import requests
from dotenv import load_dotenv, dotenv_values
from apscheduler.schedulers.background import BackgroundScheduler
from offers_service_calls import get_new_access_token, register_product

#Testing mode is configured via environment variable and is used to determine weather the application
#running for the purpose of tests using pytest or running for live use. If in testing mode, then requests
#for the local database are used only and then these function are tested using a seperate .py file
#(tests.py). The tests are done using an in-memory database so a new database doesn't have to be created
#just for tests, once the testing is done, the in-memory database is then dumped
#When not in testing mode, the database uri is set to the main database that is used for the application
#When not in testing mode, the variables for the access_token are configured and then the header variable
#is initialised using the access token in a dictionary format so it can be attatched to the request as a
#header using the requests package.

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Product catalogue',  # Customize the API title
    'description': 'An API for browsing a catalogue of product-offers',  # Customize the API description
    'template': {
        'withExtensions': True,
        'swagger': 'custom_swagger_template.html',  # Specify the custom template file
        'tags_sorter': 'alpha',
        'operations_sorter': 'alpha',
    },
}

swagger = Swagger(app)
load_dotenv()
testing_mode = os.getenv("TESTING_MODE")
if testing_mode == "true": 
    print("in testing mode")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:" 
else:
    print("Not in testing mode")
    global access_token
    global header
    access_token = get_new_access_token()
    header = {"Bearer": f"{access_token}"}
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"

#if a multiple of 5 minutes has passed, in which case the access_token has expired, a new token will
#then be requested and the header variabled wil be updated with the new access_token
db = SQLAlchemy(app)
local_database_url = 'http://localhost:5000/'

#This is the class for all the products that are added to the database that defines the database model
#along with the parameters each product has that define it. The ID being the primaary key that will
#define each unique product in UUID format
class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(120))

    def __repr__(self):
        return f"{self.name} - {self.description}"
    

#The localhost root with welcome message
@app.route('/')
def home():

     return redirect('/apidocs/')

#The products page which performs a get request to local database and retreives all of the product
#and then formats the list into a nested dictionary of all the products names, ids and descriptions
@app.route('/products')
def get_products():
    """
    Get a list of all products
    ---
    responses:
      200:
        description: List of products
        schema:
          type: object
          properties:
            products:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  description:
                    type: string
      500:
        description: Failed to retrieve products
    """
    products = Product.query.all()

    output = []
    for product in products:
        product_data = {"id":product.id, "name":product.name, "description":product.description}

        output.append(product_data)

    return {"products": output}

#Gets a product by id defined
@app.route('/products/<string:id>')
def get_product(id):
    """
    Get a product by ID
    ---
    parameters:
      - name: id
        in: path
        type: string
        format: uuid
        required: true
        description: The UUID of the product
    responses:
      200:
        description: Product details
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
      404:
        description: Product not found
    """
    product = Product.query.get_or_404(id)

    return jsonify({"name": product.name, "description": product.description})

#Defines a products parameters and sets the id to a new UUID, will check if a new token is required if
#not in testing mode. The products is then added to the local database but before any return, a post
#request is sent to the offers microservice to register the product, if the product was not able to be
#registered then the database is rolled back an status code 500 is returned with a message which will
#tell you the product could only not be added to the offers microservice
#if the external post request was successful then an appropriate message is sent with status code 201
#if both requests were unsuccessful then status code 500 is returned with an error message which tells
#you the product could not be added to either.
@app.route('/products', methods=['POST'])
def add_product():
    """
    Add a new product
    ---
    parameters:
      - name: product
        in: body
        description: The name and description of the product
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
            description:
              type: string
    responses:
      201:
        description: Product added successfully
        schema:
          type: object
          properties:
            Added product:
              type: string
            id:
              type: string
      400:
        description: Bad request - Invalid input data
      500:
        description: Failed to add the product
    """
    try:
        product = Product(name=request.json['name'], description = request.json['description'])
        product.id = str(uuid.uuid4())
        db.session.add(product)
        db.session.commit()


        if not app.config["TESTING"]:
            new_product_data = {"id": product.id, "name": product.name, "description": product.description}

            response = register_product(os.getenv("OFFERS_MICROSERVICE_URI") + 'products/register', json_data=new_product_data, 
                                 prod_header=header)
        
            if response.status_code == 201:
                return jsonify({"Added product": product.name, "id": product.id}), 201
            else:
                product = Product.query.get(product.id)
                if product is not None:
                    db.session.delete(product)
                    db.session.commit()
                return jsonify({"Error": "Failed to register product to applifiting service"}), 500
        else:
            return jsonify({"Added product": product.name, "id": product.id}), 201
    except SQLAlchemyError as e:
        return jsonify({"Error": "Failed to add product"}), 500
    
@app.route('/products/<string:id>', methods=['PUT'])
def update_product(id):
    """
    Update an exsisting product
    ---
    parameters:
      - name: id
        in: path
        type: string
        format: uuid
        required: true
        description: The UUID of the product
      - name: product
        in: body
        description: The name and description of the product
        schema:
          type: object
          required:
            - name
          properties:
            description:
              type: string
            name:
              type: string
    responses:
      200:
        description: Product updated successfully
        schema:
          type: object
          properties:
            Added product:
              type: string
            id:
              type: string
      404:
        Error: Product not found
      400:
        description: Bad request - Invalid input data
      500:
        Error: Failed to update the product
    """
    try:
        product = Product.query.get(id)
        if product is None:
            return jsonify({"Error": "Product not found"}), 404
        data = request.get_json()
        updated_name = data.get('name')
        updated_description = data.get('description')

        product.name = updated_name
        product.description = updated_description

        db.session.commit()
        return jsonify({"messsage": "Product updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to update product", "details": str(e)}), 500


#Makes an external get request to the offers microservce and returns the status code and appropriate
#data/message
@app.route('/products/<id>/offers')
def get_offers(id):
    """
    Get product-offers by product ID
    ---
    parameters:
      - name: id
        in: path
        type: string
        format: uuid
        required: true
        description: The UUID of the product
    responses:
      200:
        description: Product offers
        schema:
          type: object
          properties:
            id:
              type: string
            items_in_stock:
              type: integer
            price:
              type: integer
      404:
        description: Product not found
      500:
        Error: Failed to retreive product offers
    """
    json_data = {"product_id": id}
    response = requests.get(os.getenv("OFFERS_MICROSERVICE_URI") + 'products/' + id + '/offers', json=json_data, 
                            headers=header)
    if response.status_code == 200:
        product_offers = response.json()

        return product_offers
    
    else:
        return jsonify({"Error": "Failed to retreive product offers"}), 500

#Allows the user to delete a specfic product by providing an id corresponding to a registered product
@app.route('/products/<string:id>', methods=['DELETE'])
def delete_Product(id):
    """
    Delete a product by ID
    ---
    parameters:
      - name: id
        in: path
        type: string
        required: true
        description: The UUID of the product to delete
    responses:
      200:
        description: Product deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Product not found
      500:
        description: Failed to delete the product
    """
    product = Product.query.get(id)
    if product is None:
        return({"error": "not found"})
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message":"Product be gone!"}), 200

#Returns all the offers for every product in the database
@app.route('/products/offers')
def update_offers_endpoint():
    """
    View all offers for all products
    ---
    responses:
      200:
        description: List of product offers
        schema:
          type: object
          properties:
            product_id:
              type: string
            id:
              type: string
            items_in_stock:
              type: integer
            price:
              type: integer
      400:
        description: Failed request
        schema:
          type: object
          properties:
            Error_message:
              type: string
    """
    all_offers = get_all_offers() #The function that also makes periodic calls to the offers microservice
    if all_offers is not None:
      return jsonify(all_offers), 200
    else:
        return jsonify({"Error": "Unable to retreive product offers"}), 500

#Gets all the products then creates a list of all the IDs to then be used to get all of the offers
def get_all_product_IDs():
    with app.app_context():
        productIDs = []
        all_products = get_products()["products"]

        for product in all_products:
            productIDs.append(product["id"])

        return productIDs

#Gets all the offers for each product ID and creates a nested dictionary
def get_all_offers():
    with app.app_context():
        all_offers = {}
        product_ids = get_all_product_IDs()
        for productID in product_ids:
            print("Updating offers for product with ID: " + productID)
            offers = get_offers(productID)
            all_offers[productID] = offers
        print("Updated product offers")
        return all_offers

#Function for using the refresh token every five minutes to update the access token
def refresh_access_token_header():
  global access_token
  access_token = get_new_access_token()
  global header
  header = {"Bearer": f"{access_token}"}


if not app.config["TESTING"]:
    scheduler = BackgroundScheduler() #Create instance of BackgroundScheduler object
    scheduler.add_job(get_all_offers, 'interval', minutes=1) #Schedule the function to be run and set the interval
    scheduler.add_job(refresh_access_token_header, 'interval', minutes=5)
    scheduler.start() #Start the background periodic calls

#main program
#runs all the code and sets up the background process to run using BackgroundScheduler from the
#apscheduler package
if __name__ == "__main__":
    app.run(debug=True)
