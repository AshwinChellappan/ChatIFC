class DB_QUERY:

    ALL_ITEMS_WITH_FILTER = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}"
    '''

    ALL_ITEMS_WITH_FILTER_INSTANCEID = '''
                Select * from {container_name} 
                where {container_name}.{instance_id_field} = "{instance_id}"
                and {container_name}.{is_instance_doc_field} = true
            '''
    
    ALL_ITEMS_WITH_FILTER_SPACEID = '''
                Select * from {container_name} 
                where {container_name}.{space_id_field} = "{space_id}"
                and {container_name}.{is_default_template_field} = true
            '''

    ALL_DOCUMENTS = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}"
        and {container_name}.{is_instance_doc_field} = {is_instance_doc}
        and {container_name}.{is_response_template_field} = {is_response_template}
        and {container_name}.{is_response_doc_field} = {is_response_doc}
    '''
    
    ALL_DOCS_FOR_RAG = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}" 
        and {container_name}.{is_instance_doc_field} = false
        and {container_name}.{rag_flag_field} = true
    '''

    INSTANCE_DOCS_FOR_TYPE = '''
        Select * from {container_name} 
        where {container_name}.{doc_type_id_field} = "{doc_type_id}"
        and {container_name}.{instance_id_field} = "{instance_id}"
    '''
    
    REMAINING_INSTANCE_DOCS_FOR_TYPE = '''
        Select * from {container_name} 
        where {container_name}.{ingested_field} = false
        and {container_name}.{instance_id_field} = "{instance_id}"
        and {container_name}.{doc_type_id_field} = "{doc_type_id}"
    '''

    DOCS_FOR_TYPE = '''
        Select * from {container_name} 
        where {container_name}.{doc_type_id_field} = "{doc_type_id}"
        and {container_name}.{is_instance_doc_field} = false
    '''

    UNINGESTED_DOCS_FOR_TYPE = '''
        Select * from {container_name} 
        where {container_name}.{doc_type_id_field} = "{doc_type_id}"
        and {container_name}.{is_instance_doc_field} = false
        and {container_name}.{ingested_field} = false
    '''

    ALL_ITEMS_WITH_INSTANCE_FILTER = '''
        Select * from {container_name} 
        where {container_name}.{instance_field} = "{instance_id}" 
        and {container_name}.{is_instance_doc_field} = true
    '''

    GET_PROMPT_FOR_DOCTYPE = '''
    SELECT *  FROM {container_name} c
    WHERE EXISTS ( SELECT VALUE p FROM p IN c.prompts WHERE ARRAY_CONTAINS(p.{docTypes_id_field}, "{doctype_id}"))
    '''
    GET_ALL_FAILED_DOCS = '''
        Select * from {container_name} 
        where {container_name}.{docTypes_id_field} = "{doctype_id}" 
        and {container_name}.{uploadStatus} = false
    '''

    CHECK_PROMPT_FOR_DOCTYPE = '''
        SELECT * 
        FROM  c 
        WHERE EXISTS (
            SELECT VALUE p 
            FROM p IN c.prompts 
            WHERE ARRAY_CONTAINS(p.{docTypes_id_field}, "{doctype_id}")
        ) 
        AND c.{space_id_field} = "{space_id}" 
        AND c.isInstanceList = false
        '''

    ALL_ITEMS_WITH_SPACE_FILTER = '''
        Select * from {container_name} 
        where {container_name}.{space_field} = "{space_id}" 
    '''

    ALL_ITEMS_WITH_INSTANCEID_FILTER = '''
        Select * from {container_name} 
        where {container_name}.{instance_id_field} = "{instance_id}" 
    '''
    
    ITEMS_WITH_INGESTION_PROGRESS = '''
        Select * from {container_name} 
        where {container_name}.{doc_type_field} = "{doc_type_id}"
        and {container_name}.{is_instance_doc_field} = false
        and {container_name}.{ingestion_in_progress} = true
    '''
    
    STUDIO_LEVEL_DOC_TYPES = '''
        Select * from {container_name} 
        where {container_name}.{doc_type_level_field} = 0
    '''

    DOC_TYPES_FOR_SPACE = '''
        Select * from {container_name} 
        where ({container_name}.{doc_type_level_field} = 0 AND ARRAY_CONTAINS({container_name}.{linked_assistants_field},"{space_id}", true) )
        OR ({container_name}.{space_id_field} = "{space_id}")    
    '''
    
    DOCS_FOR_TYPES = '''
        Select * from {container_name} 
        where ({pd_filter} AND {container_name}.{doc_type_field} IN ({persistent_doc_types}))
    '''

    DOCS_FOR_TYPES_IU = '''
        Select * from {container_name} 
        where ({pd_filter} AND {container_name}.{doc_type_field} IN ({persistent_doc_types}))
        OR (
            {npd_filter} AND {container_name}.{doc_type_field} IN ({non_persistent_doc_types})
            AND {container_name}.{is_instance_doc_field} = {is_instance_doc}
            AND {container_name}.{is_response_template_field} = {is_response_template}
            AND {container_name}.{is_response_doc_field} = {is_response_doc}
        )
    '''

    DOCS_FOR_TYPES_BU = '''
        Select * from {container_name} 
        where ({pd_filter} AND {container_name}.{doc_type_field} IN ({persistent_doc_types}))
        OR (
            {npd_filter} AND {container_name}.{doc_type_field} IN ({non_persistent_doc_types})
            AND {container_name}.{is_instance_doc_field} = {is_instance_doc}
            AND {container_name}.{instance_id_field} = "{instance_id}"
        )
    '''

    GET_VARIABLE_SET_ITEM = '''
        Select * from {container_name} 
        where {container_name}.{space_id_field} = "{space_id}"
    '''

    INSTANCE_PROMPT_LIST = '''
        Select * from {container_name} 
        where {container_name}.{instance_flag_field} = true
        and {container_name}.{instance_id_field} = "{instance_id}" 
    '''

class GRAPH_API:
    GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0/users/'

class AI_SEARCH:
    INDEX_NAME = 'chatifc-aistudio-1'

class ENV_SWITCH:
    # LOG_STORE = 'LOCAL'
    LOG_STORE = 'AZURE_APP_INSIGHTS'

class URL:
    OAUTH2_AUTH = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize'
    OAUTH2_TOKEN = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    JWKS_URI = 'https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys'

class SECRETS:
    KEYS = ['COSMOSDB_KEY', 'AZURE_AISEARCH_KEY', 'AZURE_OPENAI_API_KEY', 'AZURE_ADI_KEY']

class STATUS_MSG:
    IN_PROGRESS = 'Document upload and ingestion is in progress.'
    COMPLETED = 'Document upload and ingestion completed.'

class MISC:
    RT_AI_DISCLAIMER = "<AI-generated content will be displayed here.>"
    RT_AI_DISCLAIMER_RBG = (128,128,128)
    DOC_TYPE_LEVEL_MAP = {
        0: 'studio',
        1: 'assistant',
        2: 'user-defined'
    }
class AUTH:
    SUPER_ADMIN_ROLE = 'IFC-chatifc-studio-superadmin'
class AI_SEARCH:
    INDEX_NAME = 'chatifc-aistudio-1'
    MODEL_TOKEN_LIMIT = 128000