def s1SetupRequest(**kwargs):
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
         "globalEnbId": kwargs["globalEnbId"],  # for the sake of simplicity assume that there is no macro/home eNB distinction
         "enbName": kwargs["enbName"],
         "supportedTas": kwargs["supportedTas"], # eg. ((43415, "00101", "00102"), (43788, "00101", "00102"))
         "csgIdList": kwargs["csgIdList"],
         "defaultPagingDrx": kwargs["defaultPagingDrx"],
        }
    )

def s1SetupFailure(**kwargs):
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
         "cause": kwargs["cause"],
         "timeToWait": kwargs["timeToWait"],
         "criticalityDiagnostics": kwargs["criticalityDiagnostics"],
        }
    )