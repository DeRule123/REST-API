#modules required for testing
import pytest
from app import app, db, Product
from unittest.mock import patch
import uuid
#Define the pytest fixture for the application
#Use an in-memory database so once testing is done, no storage is taken up by the database
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_add_product(client):
    #Set up test data to testing making a post request to the database
    data = {
        "id": str(uuid.uuid4()),
        "name": "Testing product",
        "description": "This product was added using pytest in the in-memory db"
    }

    response = client.post('/products', json=data) #make the post request

    assert response.status_code == 201 #Assert successful request
    assert b"Added product" in response.data #Assert the correct return data

    product = Product.query.filter_by(name="Testing product").first()
    assert product is not None #Check the product is in the database
    assert product.description == "This product was added using pytest in the in-memory db"

def test_get_product(client):
    #Create a product to post to the database to then test the get request
    test_product = Product(id=str(uuid.uuid4()), name="Another test product", description="another one")
    db.session.add(test_product)
    db.session.commit() #Add test product to the database
    retreived_product = db.session.get(Product, test_product.id) #get request for the product just added
    assert retreived_product is not None #assert product data was returned
    assert retreived_product.id == test_product.id #assert the id is correct
    assert retreived_product.name == test_product.name #assert the name is correct
    assert retreived_product.description == test_product.description #assert the correct description
    db.session.delete(test_product) #once product has been successfully retreived using a get request
    db.session.commit() #we can remove it

def test_delete_product(client):
    #Create a product to add to then test deleting it
    test_product = Product(id=str(uuid.uuid4()), name="Test product to delete", description="This product is made to test the delete request")
    db.session.add(test_product)
    db.session.commit()
    #Get the product's id
    product_id = test_product.id
    
    #Send a delete rquest
    response = client.delete(f'/products/{product_id}')

    #assert the response for testing
    assert response.status_code == 200

    #check the product has been removed from the database
    deleted_product = db.session.get(Product, product_id)
    assert deleted_product is None

    