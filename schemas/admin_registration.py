def indiviual_data(register)->dict:
    return {
        "id":str(register["_id"]),
        "fullname":register.get("fullname"),
        "email":register.get("email"),
        "mobile":register.get("mobile"),
    }
    
def all_data(registrations)->list:
    return[indiviual_data(register) for register in registrations ]