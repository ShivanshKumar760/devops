from flask import Blueprint,request,jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api import db
from api.models.models import Account,Customer

auth_bp = Blueprint('auth', __name__)

# def issue_seller_token(mobile:str):
#     """ Issues a JWT token for a seller account. """
#     account = Account.query.filter_by(mobile=mobile).first()
#     if not account:
#         #create a new account if it doesn't exist
#         account = Account(mobile=mobile)
#         db.session.add(account)
#         db.session.commit()
#         token = create_access_token(identity={
#             "id": str(account.id),
#             "role": "seller"
#         })

#         return account,token
    

def issue_seller_token(mobile: str):
    account = Account.query.filter_by(mobile=mobile).first()

    if not account:
        account = Account(mobile=mobile)
        db.session.add(account)
        db.session.commit()

    token = create_access_token(
        identity=str(account.id),
        additional_claims={
            "role": "seller"
        }
    )

    return account, token


def issue_buyer_token(mobile: str):
    """Create customer record if not exists and return JWT."""
    customer = Customer.query.filter_by(mobile=mobile).first()
    if not customer:
        customer = Customer(mobile=mobile)
        db.session.add(customer)
        db.session.commit()
    

    token = create_access_token(
        identity=str(customer.id),
        additional_claims={
            "role": "buyer"
        }
    )
    return customer, token