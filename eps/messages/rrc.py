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
         "messageType": "rrcConnectionRequest",
         "ueIdentity" : {
          "type": ueIdentityType,
          "value": ueIdentityValue
         },
         "rrcEstablishmentCause": rrcEstablishmentCause # mo-signalling used for Attach
        }
)

rrcConnectionSetup =  \
    lambda cRnti, rrcTransactionIdentifier : (
        "uu",
        {
         "physicalChannel" :"pusch",    
         "transportChannel": "ul-sch",  
         "logicalChannel": "ccch",
         "puschScramblingInput": cRnti,  # The crnti scambles the pusch channel
         "lcid": "srb0"   # The MAC header contains the Logical ID
         },
         {
          "messageType": "rrcConnectionSetup",
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
         "messageType": "rrcConnectionSetupComplete",
         "rrcTransactionIdentifier" : rrcTransactionIdentifier,
         "selectedPlmnIdentity":  selectedPlmnIdentity,
         "dedicatedInfoNas": dedicatedInfoNas
        }
)


rrcUlInformationTransfer = lambda dedicatedInfoNas: (
    "uu",
    {
     "physicalChannel" : "pusch",
     "transportChannel": "ul-sch",
     "logicalChannel": "dcch",
     "lcid":  "srb1"
    },
    {
     "messageType": "rrcUlInformationTransfer",
     "dedicatedInfoNas": dedicatedInfoNas
    }
)

rrcDlInformationTransfer = lambda dedicatedInfoNas: (
    "uu",
    {
     "physicalChannel" : "pusch",
     "transportChannel": "ul-sch",
     "logicalChannel": "dcch",
     "lcid":  "srb1"
    },
    {
     "messageType": "rrcDlInformationTransfer",
     "dedicatedInfoNas": dedicatedInfoNas
    }
)

securityModeCommand = \
    lambda rrcTransactionIdentifier, cipheringAlgorithm, integrityProtAlgorithm: (
    "uu",
    {
     "physicalChannel": "pusch",
     "transportChannel": "ul-sch",
     "logicalChannel": "dcch",
     "lcid": "srb1"
    },
    {
     "messageType": "securityModeCommand",
     "rrcTransactionIdentifier": rrcTransactionIdentifier,
     "cipheringAlgorithm": cipheringAlgorithm,
     "integrityProtAlgorithm": integrityProtAlgorithm
    }
)

securityModeComplete = lambda rrcTransactionIdentifier: (
    "uu",
    {
     "physicalChannel": "pusch",
     "transportChannel": "ul-sch",
     "logicalChannel": "dcch",
     "lcid": "srb1"
    },
    {
     "messageType": "securityModeComplete",
     "rrcTransactionIdentifier": rrcTransactionIdentifier,
    }
)

securityModeFailure = lambda rrcTransactionIdentifier: (
    "uu",
    {
     "physicalChannel": "pusch",
     "transportChannel": "ul-sch",
     "logicalChannel": "dcch",
     "lcid": "srb1"
    },
    {
     "messageType": "securityModeFailure",
     "rrcTransactionIdentifier": rrcTransactionIdentifier,
    }
)
