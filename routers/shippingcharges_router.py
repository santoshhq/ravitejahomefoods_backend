from fastapi import (
 APIRouter,
 HTTPException,
 Request
)

from math import ceil
from datetime import datetime

from config.collection import shipping_charges

from models.shippingcharges_model import (
 CountryShippingCreate,
 AddStateRequest,
 AddZoneRequest,
 UpdateZoneRequest,
 DeleteZoneRequest,
 DeleteStateRequest,
 DeleteCountryRequest,
 ShippingEstimateRequest
)
from schemas.shippingcharges_schema import individual_shipping_config,serialized_shipping_configs
from config.rate_limiter import limiter, RATE_LIMITS


shipping_router=APIRouter(
 prefix="/shipping",
 tags=["Shipping"]
)



###################################################
# CREATE SHIPPING CONFIG
###################################################

@shipping_router.post(
"/admin/{admin_id}/rules"
)
@limiter.limit(RATE_LIMITS["shipping_write"])
async def create_shipping_rules(
 request: Request,
 admin_id:str,
 payload:
 CountryShippingCreate
):


    existing=await shipping_charges.find_one({

      "admin_id":
         admin_id,

      "country":
         payload.country
    })


    if existing:
       raise HTTPException(
         status_code=400,
         detail=
         "Country already configured"
       )


    document=payload.dict()

    document[
      "admin_id"
    ]=admin_id

    document[
      "created_at"
    ]=datetime.utcnow()

    document[
      "updated_at"
    ]=datetime.utcnow()


    result=await shipping_charges.insert_one(
      document
    )


    created=await shipping_charges.find_one(
      {
        "_id":
         result.inserted_id
      }
    )


    return {

      "message":
        "Shipping rules created",

      "data":
        individual_shipping_config(
          created
        )
    }



###################################################
# GET ADMIN RULES
###################################################

@shipping_router.get(
"/admin/{admin_id}/rules"
)
@limiter.limit(RATE_LIMITS["shipping_read"])
async def get_shipping_rules(
 request: Request,
 admin_id:str
):


    data=await shipping_charges.find({

       "admin_id":
         admin_id

    }).to_list(
      None
    )


    return serialized_shipping_configs(
       data
    )



###################################################
# GET AVAILABLE COUNTRIES
###################################################

@shipping_router.get(
"/countries"
)
@limiter.limit(RATE_LIMITS["shipping_public"])
async def get_available_countries(request: Request):
   countries = await shipping_charges.distinct("country")
   return {
      "countries": sorted(countries)
   }



###################################################
# GET AVAILABLE STATES BY COUNTRY
###################################################

@shipping_router.get(
"/countries/{country}/states"
)
@limiter.limit(RATE_LIMITS["shipping_public"])
async def get_available_states(request: Request, country: str):
   doc = await shipping_charges.find_one({
      "country": country
   })

   if not doc:
      raise HTTPException(
         404,
         "Country config not found"
      )

   states = [
      state.get("state_name")
      for state in doc.get("states", [])
   ]

   return {
      "country": country,
      "states": states
   }



###################################################
# ADD STATE
###################################################

@shipping_router.post(
"/admin/{admin_id}/add-state"
)
@limiter.limit(RATE_LIMITS["shipping_write"])
async def add_state(
 request: Request,
 admin_id:str,
 payload:AddStateRequest
):


   doc=await shipping_charges.find_one({

      "admin_id":
         admin_id,

      "country":
         payload.country
   })


   if not doc:
      raise HTTPException(
         404,
         "Country config not found"
      )


   for s in doc["states"]:

      if (
       s["state_name"].lower()
       ==
       payload.state.state_name.lower()
      ):
          raise HTTPException(
             400,
             "State already exists"
          )


   await shipping_charges.update_one(

      {
       "admin_id":
          admin_id,

       "country":
          payload.country
      },

      {

       "$push":{
         "states":
          payload.state.dict()
       },

       "$set":{
         "updated_at":
           datetime.utcnow()
       }

      }
   )


   return {
      "message":
         "State added successfully"
   }



###################################################
# ADD ZONE
###################################################

@shipping_router.post(
"/admin/{admin_id}/add-zone"
)
@limiter.limit(RATE_LIMITS["shipping_write"])
async def add_zone(
 request: Request,
 admin_id:str,
 payload:AddZoneRequest
):


   doc=await shipping_charges.find_one({

      "admin_id":
         admin_id,

      "country":
         payload.country
   })


   if not doc:
      raise HTTPException(
        404,
        "Country config missing"
      )


   states=doc["states"]

   found=False


   for state in states:

      if (
        state["state_name"].lower()
        ==
        payload.state_name.lower()
      ):

         found=True


         for zone in state["zones"]:

            overlap=(
              payload.zone.start_zipcode
              <=zone["end_zipcode"]

              and

              payload.zone.end_zipcode
              >=zone["start_zipcode"]
            )


            if overlap:

                raise HTTPException(
                   400,
                   "Overlapping zipcode range"
                )


         state["zones"].append(
             payload.zone.dict()
         )


   if not found:
      raise HTTPException(
         404,
         "State not found"
      )



   await shipping_charges.update_one(

      {
        "_id":
          doc["_id"]
      },

      {
       "$set":{
         "states":states,

         "updated_at":
             datetime.utcnow()
       }
      }
   )


   return {

      "message":
         "Zone added successfully"
   }


###################################################
# EDIT ZONE
###################################################

@shipping_router.patch(
"/admin/{admin_id}/edit-zone"
)
@limiter.limit(RATE_LIMITS["shipping_write"])
async def edit_zone(
 request: Request,
 admin_id: str,
 payload: UpdateZoneRequest
):
   """
   Edit/Update an existing zone in a state
   Admin can update any combination of fields (charge_per_kg, free_delivery_min_order_value)
   
   Parameters:
   - admin_id: Admin ID
   - payload: UpdateZoneRequest with old zipcode ranges to identify zone
             and optional new values to update
   """
   
   doc = await shipping_charges.find_one({
      "admin_id": admin_id,
      "country": payload.country
   })

   if not doc:
      raise HTTPException(
         404,
         "Country config not found"
      )

   states = doc["states"]
   found_state = False
   updated_fields = {}

   for state in states:
      if state["state_name"].lower() == payload.state_name.lower():
         found_state = True
         found_zone = False

         for zone in state["zones"]:
            if (
               zone["start_zipcode"] == payload.old_start_zipcode
               and
               zone["end_zipcode"] == payload.old_end_zipcode
            ):
               found_zone = True
               
               # Store old values for response
               updated_fields["previous_values"] = {
                  "charge_per_kg": zone["charge_per_kg"],
                  "free_delivery_min_order_value": zone["free_delivery_min_order_value"]
               }
               
               # Update only provided fields
               if payload.new_charge_per_kg is not None:
                  zone["charge_per_kg"] = payload.new_charge_per_kg
                  
               if payload.new_free_delivery_min_order_value is not None:
                  zone["free_delivery_min_order_value"] = payload.new_free_delivery_min_order_value
               
               # Store new values for response
               updated_fields["updated_values"] = {
                  "charge_per_kg": zone["charge_per_kg"],
                  "free_delivery_min_order_value": zone["free_delivery_min_order_value"]
               }
               break

         if not found_zone:
            raise HTTPException(
               404,
               "Zone not found with those zipcode ranges"
            )
         break

   if not found_state:
      raise HTTPException(
         404,
         "State not found"
      )

   await shipping_charges.update_one(
      {"_id": doc["_id"]},
      {
         "$set": {
            "states": states,
            "updated_at": datetime.utcnow()
         }
      }
   )

   return {
      "message": "Zone updated successfully",
      "country": payload.country,
      "state": payload.state_name,
      "zone_identified_by": {
         "start_zipcode": payload.old_start_zipcode,
         "end_zipcode": payload.old_end_zipcode
      },
      "previous_values": updated_fields.get("previous_values"),
      "updated_values": updated_fields.get("updated_values")
   }


###################################################
# DELETE ZONE
###################################################

@shipping_router.delete(
"/admin/{admin_id}/delete-zone"
)
@limiter.limit(RATE_LIMITS["shipping_write"])
async def delete_zone(
 request: Request,
 admin_id: str,
 payload: DeleteZoneRequest
):
   """
   Delete a zone from a state
   
   Parameters:
   - admin_id: Admin ID
   - payload: DeleteZoneRequest with country, state_name, and zipcode ranges
   """
   
   doc = await shipping_charges.find_one({
      "admin_id": admin_id,
      "country": payload.country
   })

   if not doc:
      raise HTTPException(
         404,
         "Country config not found"
      )

   states = doc["states"]
   found_state = False
   zone_found = False

   for state in states:
      if state["state_name"].lower() == payload.state_name.lower():
         found_state = True
         # Filter out the zone to delete
         original_count = len(state["zones"])
         state["zones"] = [
            zone for zone in state["zones"]
            if not (
               zone["start_zipcode"] == payload.start_zipcode
               and
               zone["end_zipcode"] == payload.end_zipcode
            )
         ]
         if len(state["zones"]) < original_count:
            zone_found = True
         break

   if not found_state:
      raise HTTPException(
         404,
         "State not found"
      )

   if not zone_found:
      raise HTTPException(
         404,
         "Zone not found with those zipcode ranges"
      )

   await shipping_charges.update_one(
      {"_id": doc["_id"]},
      {
         "$set": {
            "states": states,
            "updated_at": datetime.utcnow()
         }
      }
   )

   return {
      "message": "Zone deleted successfully",
      "country": payload.country,
      "state": payload.state_name,
      "deleted_zone": {
         "start_zipcode": payload.start_zipcode,
         "end_zipcode": payload.end_zipcode
      }
   }


###################################################
# DELETE STATE
###################################################

@shipping_router.delete(
"/admin/{admin_id}/delete-state"
)
@limiter.limit(RATE_LIMITS["shipping_write"])
async def delete_state(
 request: Request,
 admin_id: str,
 payload: DeleteStateRequest
):
   """
   Delete a complete state and all its zones
   
   Parameters:
   - admin_id: Admin ID
   - payload: DeleteStateRequest with country and state_name
   """
   
   doc = await shipping_charges.find_one({
      "admin_id": admin_id,
      "country": payload.country
   })

   if not doc:
      raise HTTPException(
         404,
         "Country config not found"
      )

   original_states_count = len(doc["states"])
   
   # Filter out the state to delete
   doc["states"] = [
      state for state in doc["states"]
      if state["state_name"].lower() != payload.state_name.lower()
   ]

   if len(doc["states"]) >= original_states_count:
      raise HTTPException(
         404,
         "State not found"
      )

   await shipping_charges.update_one(
      {"_id": doc["_id"]},
      {
         "$set": {
            "states": doc["states"],
            "updated_at": datetime.utcnow()
         }
      }
   )

   return {
      "message": "State and all its zones deleted successfully",
      "country": payload.country,
      "deleted_state": payload.state_name
   }


###################################################
# DELETE COUNTRY
###################################################

@shipping_router.delete(
"/admin/{admin_id}/delete-country"
)
@limiter.limit(RATE_LIMITS["shipping_write"])
async def delete_country(
 request: Request,
 admin_id: str,
 payload: DeleteCountryRequest
):
   """
   Delete a complete country and all its states/zones
   
   Parameters:
   - admin_id: Admin ID
   - payload: DeleteCountryRequest with country name
   """
   
   doc = await shipping_charges.find_one({
      "admin_id": admin_id,
      "country": payload.country
   })

   if not doc:
      raise HTTPException(
         404,
         "Country config not found"
      )

   result = await shipping_charges.delete_one({
      "admin_id": admin_id,
      "country": payload.country
   })

   if result.deleted_count == 0:
      raise HTTPException(
         404,
         "Country config not found"
      )

   return {
      "message": "Country and all its states/zones deleted successfully",
      "deleted_country": payload.country,
      "admin_id": admin_id
   }


###################################################
# SHIPPING ESTIMATION
###################################################

@shipping_router.post(
"/estimate"
)
@limiter.limit(RATE_LIMITS["shipping_read"])
async def estimate_shipping(
 request: Request,
 payload:
 ShippingEstimateRequest
):

   
   doc=await shipping_charges.find_one({



      "country":
         payload.country
   })


   if not doc:
      raise HTTPException(
        404,
        "Shipping config not found"
      )


   matched_zone=None


   for state in doc["states"]:

      if (
       state["state_name"].lower()
       ==
       payload.state.lower()
      ):

        for zone in state["zones"]:

            if (
              zone["start_zipcode"]
              <=
              payload.zipcode
              <=
              zone["end_zipcode"]
            ):

                matched_zone=zone
                break



   if not matched_zone:

      raise HTTPException(
        404,
        "No delivery available"
      )



   ##################################
   # FREE SHIPPING
   ##################################

   free_delivery_threshold = matched_zone.get(
      "free_delivery_min_order_value"
   )

   if (
      free_delivery_threshold is not None
      and
      payload.order_total
      >=
      free_delivery_threshold
   ):

       return {

         "shipping_charge":0,

         "free_delivery":True,

         "message":
           "Free delivery applied"
       }



   ##################################
   # WEIGHT BILLING
   ##################################

   weight_kg=(
      payload.cart_weight_grams
      /1000
   )


   billable_weight=ceil(
      weight_kg
   )


   shipping_charge=(
      billable_weight
      *
      matched_zone[
         "charge_per_kg"
      ]
   )



   return {

      "country":
         payload.country,

      "state":
         payload.state,

      "zipcode":
         payload.zipcode,

      "actual_weight_kg":
         weight_kg,

      "billable_weight_kg":
         billable_weight,

      "charge_per_kg":
         matched_zone[
            "charge_per_kg"
         ],

      "shipping_charge":
         shipping_charge,

      "free_delivery":
         False
   }


###################################################
# DELETE COUNTRY
###################################################

@shipping_router.delete(
"/admin/{admin_id}/delete-country"
)
@limiter.limit(RATE_LIMITS["shipping_write"])
async def delete_country(
 request: Request,
 admin_id: str,
 country: str
):
   """
   Delete a complete country configuration and all its states and zones
   
   Parameters:
   - admin_id: Admin ID
   - country: Country name to delete (query parameter)
   """
   
   doc = await shipping_charges.find_one({
      "admin_id": admin_id,
      "country": country
   })

   if not doc:
      raise HTTPException(
         status_code=404,
         detail="Country configuration not found"
      )

   result = await shipping_charges.delete_one({
      "admin_id": admin_id,
      "country": country
   })

   if result.deleted_count == 0:
      raise HTTPException(
         status_code=500,
         detail="Failed to delete country configuration"
      )

   return {
      "message": "Country configuration deleted successfully",
      "deleted_country": country,
      "admin_id": admin_id,
      "states_deleted": len(doc.get("states", []))
   }