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

randomAccessResponse = \
    lambda raRnti, rapid, temporaryCrnti, uplinkGrant: (
        "uu",
        {
         "physicalChannel" :"pdcch/pdsch",   #RA-RNTI is in the PDCCH. 
         "transportChannel": "dl-sch",  # RAPID and UL Grant and Temp-CRNTI are in PDSCH
         "logicalChannel": "None",
         "raRnti" : raRnti   # the crc bits of pdcch are scrambled by raRnti
         },
         {
          "messageName": "randomAccessResponse",
          "rapid": rapid,  # number between 1 and 64
          "uplinkGrant": uplinkGrant,
          "temporaryCrnti": temporaryCrnti
         } 
) 

rrcConnectionRequest = \
    lambda cRnti, ueIdentityType, ueIdentityValue, rrcEstablishmentCause: (
        "uu",
        {
         "physicalChannel" :"pusch",    
         "transportChannel": "ul-sch",  
         "logicalChannel": "ccch",
         "cRnti": cRnti #When using CCCH (RRC Establishment), the C-RNTI is used as input
                        # when scrambling the PUSCH prior to modulation. When using DCCH (RRC Connection
                        # re-establishment, the C-RNTI is included as part of the MAC header. 
        },
        {
         "messageName": "rrcConnectionRequest",
         "ueIdentity" : {
          "type": ueIdentityType,
          "value": ueIdentityValue
         },
         "rrcEstablishmentCause": rrcEstablishmentCause # mo-signalling used for Attach
        }
)

contentionResolutionIdentity = \
    lambda cRnti, messageContent: (
        "uu",
        {
         "physicalChannel" :"pdsch",    
         "transportChannel": "dl-sch",  
         "logicalChannel": "none",
         "C-RNTI": cRnti  # the PDCCH CRC bits are scrambled by the temporary CRNTI 
        },
        messageContent
)

rrcConnectionSetup =  \
    lambda cRnti, rrcTransactionIdentifier : (
        "uu",
        {
         "physicalChannel" :"pusch",    
         "transportChannel": "ul-sch",  
         "logicalChannel": "ccch",
         "puschScramblingInput": cRnti,  # The crnti scambles the pusch channel
         "lcid": "SRB0"   # The MAC header contains the Logical ID                                                
         },
         {
          "messageName": "rrcConnectionSetup",
          "rrcTransactionIdentifier" : rrcTransactionIdentifier
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