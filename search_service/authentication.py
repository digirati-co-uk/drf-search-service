
import base64
import json
import logging
from rest_framework import authentication
from rest_framework import exceptions

logger = logging.getLogger(__name__)

class ContextsHeaderAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        """ Authenticates if the x-context header is present, 
            and sets this as the auth contexts for 
        """
        auth_data = {}
        if context:=request.headers.get("x-context"): 
            auth_data["contexts"] = [context] 
            return (True, auth_data)
        else:
            msg = "x-context header not present on request."
            logger.debug(msg)
            raise exceptions.AuthenticationFailed(msg)
