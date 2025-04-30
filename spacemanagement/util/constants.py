class DB_QUERY:

    ALL_SPACES_FOR_USER_QUERY = '''
        Select * from {container_name} 
        where ARRAY_CONTAINS({container_name}.{assigned_users_field},"{users_and_groups}", true)
    '''

    GET_ALL_SPACES = '''
        Select * from {container_name}
    '''

    GET_SPACE_BY_SPACE_ID  = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}"
    '''

    SPACE_FOR_USER_QUERY = '''
        Select * from {container_name} 
        where ARRAY_CONTAINS({container_name}.{assigned_users_field},"{users_and_groups}", true) 
        AND {container_name}.{space_id_field} = "{space_id}"
    '''

    GET_VARIABLE_SET_QUERY = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}"
        AND {container_name}.{is_instance_variableSet_field} = false
    '''

    ALL_PUBLISHED_SPACES = '''
        Select * from {container_name} 
        where {container_name}.{published_field} = true 
    '''

    GET_QUERY_PUBLISHED_SPACES_BY_SPACEID = '''
        Select * from {container_name} 
        where {container_name}.{published_field} = true 
        AND {container_name}.{space_id_field} = "{space_id}"
    '''

    ALL_ITEMS_FOR_OPTIMUM_FLAG = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}" and {container_name}.{flag_field} = true
    '''

    ALL_ITEMS_WITH_FILTER_BY_RESPONSE_TEMPLATE = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}" and {container_name}.{is_response_template} = true
    '''

    ALL_ITEMS_WITH_FILTER_BY_DEFAULT_TEMPLATE = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}" and {container_name}.{is_default_response_template} = true
    '''

    CHECK_DUPLICATE_INSTANCE_QUERY = '''
        Select * from {container_name} 
        where ARRAY_CONTAINS({container_name}.{assigned_users_field},"{users_and_groups}", true)
        AND {container_name}.{space_instance_name_field} = "{space_instance_name}"
        AND {container_name}.{space_id_field} = "{space_id}"
    '''
    CHECK_UPDATE_DUPLICATE_INSTANCE_QUERY = '''
        Select * from {container_name} 
        where ARRAY_CONTAINS({container_name}.{assigned_users_field},"{users_and_groups}", true)
        AND {container_name}.{space_instance_name_field} = "{space_instance_name}"
        AND {container_name}.{space_instance_id_field} <> "{instance_id}"
    '''
    CHECK_DUPLICATE_SPACE_UPDATE_QUERY = '''
        Select * from {container_name} 
        where {container_name}.{space_name_field} = "{space_name}"
        AND {container_name}.{space_id_field} <> "{space_id}"
    '''

    CHECK_DUPLICATE_SPACE_QUERY = '''
        Select * from {container_name} 
        where {container_name}.{space_name_field} = "{space_name}"
    '''
class MSG:
    ERROR_MSG_OPTIMUM_PROMPT_LIST_CHECK = '''Failed to publish assistant. Please select at least 1 prompt list as Optimum prompt list.'''
    ERROR_MSG_RESPONSE_TEMPLATE_CHECK = '''Failed to publish assistant. Please upload at least 1 response template.'''
    ERROR_MSG_DEFAULT_RESPONSE_TEMPLATE_CHECK = '''Failed to publish assistant. Please select at least 1 response template as default response template.'''

class ENV_SWITCH:
    # LOG_STORE = 'LOCAL'
    LOG_STORE = 'AZURE_APP_INSIGHTS'

class URL:
    OAUTH2_AUTH = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize'
    OAUTH2_TOKEN = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    JWKS_URI = 'https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys'

class SECRETS:
    KEYS = ['COSMOSDB_KEY']

class TIME:
    INSTANCE_EXPIRY = 15

class AUTH:
    SUPER_ADMIN_ROLE = 'IFC-chatifc-studio-superadmin'