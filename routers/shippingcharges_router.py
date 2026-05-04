from fastapi import (
 APIRouter,
 HTTPException
)

from math import ceil
from datetime import datetime

from config.collection import shipping_charges

from models.shippingcharges_model import (
 CountryShippingCreate,
 AddStateRequest,
 AddZoneRequest,
 ShippingEstimateRequest
)
from schemas.shippingcharges_schema import individual_shipping_config,serialized_shipping_configs


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
async def create_shipping_rules(
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
async def get_shipping_rules(
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
async def get_available_countries():
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
async def get_available_states(country: str):
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
async def add_state(
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
async def add_zone(
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
# SHIPPING ESTIMATION
###################################################

@shipping_router.post(
"/estimate"
)
async def estimate_shipping(
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

   if (
      payload.order_total
      >=
      matched_zone[
        "free_delivery_min_order_value"
      ]
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