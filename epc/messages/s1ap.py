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