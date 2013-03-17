randomAccessPreamble = lambda raRnti, rapid: (
    "uu",
    {
     "physicalChannel" :"prach",
     "transportChannel": "rach",
     "logicalChannel": None,
     "raRnti" : raRnti  # between 1 and 10 (the subframe in which the message is xmitted)
    },
    {
     "messageName": "randomAccessPreamble",
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

contentionResolutionIdentity = \
    lambda cRnti, messageContent: (
        "uu",
        {
         "physicalChannel" :"pdsch",
         "transportChannel": "dl-sch",
         "logicalChannel": "none",
         "C-RNTI": cRnti  # the PDCCH CRC bits are scrambled by the temporary CRNTI
        },
        {
         "messageName" : "contentionResolutionIdentity",
         "echoedMessage": messageContent
        }
)