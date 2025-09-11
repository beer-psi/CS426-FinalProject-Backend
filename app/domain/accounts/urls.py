ACCOUNT_LOGIN = "/api/v1/auth/login"
ACCOUNT_LOGOUT = "/api/v1/auth/logout"
ACCOUNT_REGISTER = "/api/v1/auth/register"

ACCOUNT_OAUTH_LOGIN = "/api/v1/oauth/login"
ACCOUNT_OAUTH_VIEW_PROVIDERS = "/api/v1/oauth/providers"
ACCOUNT_OAUTH_LOGIN_WITH_PROVIDER = "/api/v1/oauth/{provider:str}/login"
ACCOUNT_OAUTH_AUTHORIZE_WITH_PROVIDER = "/api/v1/oauth/{provider:str}/authorize"

ACCOUNT_PROFILE = "/api/v1/users/me"

GET_USER_BY_USERNAME = "/api/v1/users/{username:str}"
