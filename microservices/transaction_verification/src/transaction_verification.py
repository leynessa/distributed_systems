import grpc
from concurrent import futures
import re

import sys
from datetime import datetime
import calendar

utils_path = "/app/utils/pb/transaction_service"
sys.path.insert(0, utils_path)


import transaction_pb2 as transaction_verification
import transaction_pb2_grpc


def validate_cvv(cvv):
    """Validate that CVV is 3  digits."""
    return bool(re.fullmatch(r"\d{3}", cvv))


def validate_credit_card_number(number):
    """Validate that the credit card number is exactly 16 digits using regex."""
    pattern = r"^\d{16}$"
    return bool(re.match(pattern, number))


def validate_required_fields(request):
    """Check that required fields are present and non-empty."""
    missing = []
    # User fields
    if not request.user.name:
        missing.append("user.name")
    if not request.user.contact:
        missing.append("user.contact")
    # Credit card fields
    if not request.creditCard.number:
        missing.append("creditCard.number")
    if not request.creditCard.expirationDate:
        missing.append("creditCard.expirationDate")
    if not request.creditCard.cvv:
        missing.append("creditCard.cvv")
    # Billing Address
    if (
        not request.billingAddress.street
        or not request.billingAddress.city
        or not request.billingAddress.country
    ):
        missing.append("billingAddress (street/city/country)")

    if len(request.items) == 0:
        missing.append("items (list is empty)")
    return missing


def validate_expiration_date(date_str):
    """Validate the expiration date is in MM/YY format and not expired (using end-of-month)."""
    if not re.fullmatch(r"\d{2}/\d{2}", date_str):
        return False
    try:
        month, year = date_str.split("/")
        month = int(month)
        year = int("20" + year)
        if month < 1 or month > 12:
            return False
        last_day = calendar.monthrange(year, month)[1]
        exp_date = datetime(year, month, last_day)
        # The card is valid if current date is before or on the expiration date.
        return datetime.now() <= exp_date
    except Exception:
        return False


class TransactionService(transaction_pb2_grpc.TransactionServiceServicer):
    def VerifyTransaction(self, request, context):
        """
        Implementation of VerifyTransaction.
        Applies basic validation logic on the incoming transaction request.
        """
        print(f"Received transaction verification request : {request}")
        print(0)
        if not request.items:
            response.isValid = False
            # response.errors = "Items list is empty"
            return response
        # 1. Validate required fields
        print(1)
        missing = validate_required_fields(request)
        if missing:
            response = transaction_verification.TransactionResponse()
            response.isValid = False
            print(missing)
            # response.errors = "Missing required fields: " + ", ".join(missing)
            return response
        print(2)
        # 2. Validate credit card number format
        if not validate_credit_card_number(request.creditCard.number):
            response = transaction_verification.TransactionResponse()
            response.isValid = False
            # response.errors = "Invalid credit card number."
            return response
        print(3)
        # 3. Validate expiration date format and check if card is expired
        if not validate_expiration_date(request.creditCard.expirationDate):
            response = transaction_verification.TransactionVerificationResponse()
            response.isValid = False
            # response.errors = "Invalid or expired credit card expiration date."
            return response
        print(4)
        # 4. Validate CVV
        if not validate_cvv(request.creditCard.cvv):
            response = transaction_verification.TransactionResponse()
            response.isValid = False
            # response.errors = "Invalid CVV. It must be 3 digits."
            return response
        response = transaction_verification.TransactionResponse()
        response.isValid = True
        print (response)
        return response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    transaction_pb2_grpc.add_TransactionServiceServicer_to_server(
        TransactionService(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server is running on port 50051...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
