def individual_shipping_config(
 document
):

    return {

      "id":
        str(
          document["_id"]
        ),

      "admin_id":
        document["admin_id"],

      "country":
        document["country"],

      "states":
        document["states"]
    }



def serialized_shipping_configs(
 documents
):
    return [
      individual_shipping_config(
         item
      )
      for item in documents
    ]