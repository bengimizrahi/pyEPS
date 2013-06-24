authenticationInformationRequest = lambda imsi, visitedPlmnId, endToEndId: (
    "s6a",
    {
     "endToEndId": endToEndId
    },
    {
     "imsi": imsi,
     "supportedFeatures": None,
     "requestedEutranAuthenticationInfo": None,
     "requestedUtranGeranAuthenticationInfo": None,
     "visitedPlmnId": visitedPlmnId,
    }
)

authenticationInformationAnswer = lambda resultCode, authenticationInfo, endToEndId: (
    "s6a",
    {
     "endToEndId": endToEndId
    },
    {
     "resultCode": resultCode,
     "errorDiagnostic": None,
     "supportedFeatures": None,
     "authenticationInfo": authenticationInfo,
    }
)

