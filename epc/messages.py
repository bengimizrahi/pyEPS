randomAccessRequest = lambda raRnti, rapid: (
    "uu",
    {
     "physicalChannel" :"prach",
     "transportChannel": "rach",
     "logicalChannel": None,
     "raRnti" : raRnti  # between 1 and 10 (the subframe in which the message is xmitted)
    },
    {
     "messageName": "randomAccessRequest",
     "rapid": rapid
    }
) 

rrcConnectionRequest = \
    lambda cRnti, ueIdentityType, ueIdentityValue, establishmentCause: (
        "uu",
        {
         "physicalChannel" :"pusch",    
         "transportChannel": "ul-sch",  
         "logicalChannel": "ccch",
         "C-RNTI": cRnti #When using CCCH (RRC Establishment), the C-RNTI is used as input
# when scrambling the PUSCH prior to modulation. When using DCCH (RRC Connection
# re-establishment, the C-RNTI is included as part of the MAC header. 
        },
        {
         "messageName": "rrcConnectionRequest",
         "ueIdentity" : {
          "type": ueIdentityType,
          "randomValue": ueIdentityValue
         },
         "establishmentCause": establishmentCause # mo-signalling used for Attach
        }
)

contentionResolutionIdentity = \
    lambda cRnti, ueIdentityType, ueIdentityValue, establishmentCause: (
        "uu",
        {
         "physicalChannel" :"pdsch",    
         "transportChannel": "dl-sch",  
         "logicalChannel": "none",
         "C-RNTI": cRnti  # the PDCCH CRC bits are scrambled by the temporary CRNTI 
        },
        {
         "messageName": "contentionResolutionIdentity",  # this is a mirror of the L3 message sent by the UE
         "ueIdentity" : {
          "type": ueIdentityType,
          "randomValue": ueIdentityValue
         },
         "establishmentCause": establishmentCause # mo-signalling used for Attach
        }
)

rrcConnectionSetupComplete = \
    lambda rrcTransactionIdentifier, selectedPlmnIdentity, dedicatedInfoNas: (
        "uu",
        {
         "physicalChannel" : "pusch",    
         "transportChannel": "ul-sch",  
         "logicalChannel": "dcch",
         "lcid":  "srb1"
        },
        {
         "messageName": "rrcConnectionSetupComplete",
         "rrcTransactionIdentifier" : rrcTransactionIdentifier,
         "selectedPlmnIdentity":  selectedPlmnIdentity,
         "dedicatedInfoNas": dedicatedInfoNas
        }
)