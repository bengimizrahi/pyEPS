def s1SetupRequest(globalEnbId, enbName, supportedTas, csgIdList, defaultPagingDrx):
    return (
        "s1",
        {
         "streamId": 0
        },
        {
         "messageType": {
          "procedureCode": "s1Setup",
          "typeOfMessage": "initiatingMessage"
         },
         "globalEnbId": globalEnbId, # for the sake of simplicity assume that there is no macro/home eNB distinction
         "enbName": enbName,
         "supportedTas": supportedTas, # eg. ((43415, "00101", "00102"), (43788, "00101", "00102"))
         "csgIdList": csgIdList,
         "defaultPagingDrx": defaultPagingDrx,
        }
    )

def s1SetupResponse(mmeName, servedGummeis, relativeMmeCapacity, criticalityDiagnostics):
    return (
        "s1",
        {
         "streamId": 0
        },
        {
         "messageType": {
          "procedureCode": "s1Setup",
          "typeOfMessage": "successfulOutcome"
         },
         "mmeName": mmeName,
         "servedGummeis": servedGummeis,
         "relativeMmeCapacity": relativeMmeCapacity,
         "criticalityDiagnostics": criticalityDiagnostics,
        }
    )

def s1SetupFailure(cause, timeToWait, criticalityDiagnostics):
    return (
        "s1",
        {
         "streamId": 0
        },
        {
         "messageType": {
          "procedureCode": "s1Setup",
          "typeOfMessage": "unsuccessfulOutcome"
         },
         "cause": cause,
         "timeToWait": timeToWait,
         "criticalityDiagnostics": criticalityDiagnostics,
        }
    )

def initialUeMessage(enbUeS1apId, nasPdu, tai, eUtranCgi, rrcEstablishmentCause,
    sTmsi, csgId, gummei, cellAccessMode):
    return (
        "s1",
        {
         "streamId": 1
        },
        {
         "messageType": {
          "procedureCode": "initialUeMessage",
          "typeOfMessage": "initiatingMessage"
         },
         "enbUeS1apId": enbUeS1apId,
         "nasPdu": nasPdu,
         "tai": tai,
         "eUtranCgi": eUtranCgi,
         "rrcEstablishmentCause": rrcEstablishmentCause,
         "sTmsi": sTmsi,
         "csgId": csgId,
         "gummei": gummei,
         "cellAccessMode": cellAccessMode
        }
    )

def uplinkNasTransport(enbUeS1apId, mmeUeS1apId, nasPdu, tai):
    return (
        "s1",
        {
         "streamId": 1
        },
        {
         "messageType": {
          "procedureCode": "downlinkNasTransport",
          "typeOfMessage": "initiatingMessage"
         },
         "enbUeS1apId": enbUeS1apId,
         "mmeUeS1apId": enbUeS1apId,
         "nasPdu": nasPdu,
         "tai": tai,
        }
    )

def downlinkNasTransport(enbUeS1apId, mmeUeS1apId, nasPdu):
    return (
        "s1",
        {
         "streamId": 1
        },
        {
         "messageType": {
          "procedureCode": "downlinkNasTransport",
          "typeOfMessage": "initiatingMessage"
         },
         "enbUeS1apId": enbUeS1apId,
         "mmeUeS1apId": enbUeS1apId,
         "nasPdu": nasPdu,
        }
    )
