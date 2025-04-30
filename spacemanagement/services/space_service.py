import copy
from core.config import settings
from services.azure_cosmosdb_service import CosmosService
from datetime import datetime
import uuid
from util.constants import AUTH, DB_QUERY, MSG
import json
from fastapi import status
from util.logger import Logger

logger = Logger()


class SpaceService():

    def __init__(self):
        self.cosmosdb_service = None
        self.container_name = 'space'

    def establish_cosmosdb_connection(self, container_name = 'space'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService()
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)

    def get_space(self, space_id, user):
        # Hit cosmos db and get space
        self.establish_cosmosdb_connection()
        space = self.cosmosdb_service.get_item(user, str(space_id), partition_key = space_id)
        #
        return space
    
    def create_space(self, space, user):
        # convert pydantic object to a dictionary
        space = dict(space)
        # Create unique space ID
        space_id = str(uuid.uuid4())
        # Update space ids
        space['id'] = space_id
        space['spaceId'] = space_id
        # Add email to assignedUsers field
        space['assignedUsers'] = [user.email]
        # Create assigned user details
        space['assignedUserDetails'] = [
            {
                'name': user.name,
                'email': user.email,
                'userType': 'admin', # when space is created, the type will be changed to admin
                'isContact': False
            }
        ]
        # Update space history
        self.update_space_history(space, user)

        self.establish_cosmosdb_connection(container_name = 'space')
        check_duplicate = self.cosmosdb_service.check_duplicate_space(space['spaceName'])

        if not check_duplicate:
            # Establish cosmosDB connection
            self.establish_cosmosdb_connection()
            # Upsert new space item
            self.cosmosdb_container.upsert_item(space)
        #
        return space,check_duplicate

    def update_space_publish(self, space_id, new_space, user):
        # Update user details
        if not isinstance(new_space, dict):
            user_details = [dict(user_detail) for user_detail in new_space.assignedUserDetails]
            new_space.assignedUserDetails = user_details
            assigned_group_details = [dict(group_detail) for group_detail in new_space.assignedGroupDetails]
            new_space.assignedGroupDetails = assigned_group_details
        # convert pydantic object to a dictionary
        new_space = dict(new_space)
        # Update history
        new_space = self.update_space_history(new_space, user)
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Update space
        updated_space = self.cosmosdb_service.update_item(space_id, new_space)      
        return updated_space

    def is_admin(self, space_id, user, group_names): 
        admin = False 
        if self._is_super_admin(user):
            admin = True 
        else:
            space = self.get_space(space_id, user)
            admin = self._is_user_admin_in_space(space, user) or self._is_group_admin_in_space(space, group_names)        
        return admin

    def _is_super_admin(self, user):
        return AUTH.SUPER_ADMIN_ROLE in user.roles

    def _is_user_admin_in_space(self, space, user):
        assigned_user_details = space.get("assignedUserDetails", [])
        for user_detail in assigned_user_details:
            if user_detail['name'].lower() == user.name.lower() and user_detail['userType'].lower() == 'admin':
                return True
        return False

    def _is_group_admin_in_space(self, space, group_names):
        assigned_group_details = space.get("assignedGroupDetails", [])
        for group_detail in assigned_group_details:
            if group_detail['userType'].lower() == 'admin' and group_detail['displayname'].lower() in [group.lower() for group in group_names]:
                return True
        return False


    def update_space(self, space_id, new_space, user):
            # Update user details
            if not isinstance(new_space, dict):
                user_details = [dict(user_detail) for user_detail in new_space.assignedUserDetails]
                new_space.assignedUserDetails = user_details
                assigned_group_details = [dict(group_detail) for group_detail in new_space.assignedGroupDetails]
                new_space.assignedGroupDetails = assigned_group_details
            # convert pydantic object to a dictionary
            new_space = dict(new_space)
            self.establish_cosmosdb_connection(container_name = 'space')
            check_duplicate = self.cosmosdb_service.check_duplicate_space_update(space_id,new_space['spaceName'])
            updated_space = new_space
            if not check_duplicate:
                # Update history
                new_space = self.update_space_history(new_space, user)
                # Establish cosmosDB connection
                self.establish_cosmosdb_connection()
                # Update space
                updated_space = self.cosmosdb_service.update_item(space_id, new_space)      
            return updated_space,check_duplicate


    def update_space_history(self, space, user, clone=False):

        space['lastUpdatedBy'] = user.email
        space['lastUpdatedOn'] = datetime.now().isoformat()
        # update created by, on
        if space['createdBy'] == "" or space['createdOn'] is None or clone:
            space['createdOn'] = datetime.now().isoformat()
            space['createdBy'] = user.email
        elif not isinstance(space['createdOn'], str):
            space['createdOn'] = space['createdOn'].isoformat() 

        return space

    def delete_space(self, space_id):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Delete space
        self.cosmosdb_service.delete_item(space_id, partition_key = space_id)

    def get_all_spaces(self, user):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Get the space item
        space_list = self.cosmosdb_service.get_all_items(user)
        #
        return space_list

    def get_space_by_id(self, space_id, user):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Get the space leveraging cosmosdb service
        space = self.cosmosdb_service.get_item_by_id(space_id, partition_key = space_id)
        #
        return space

    def publish_space(self, space_id, user,publishFlag):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # get space
        space = self.get_space(space_id, user)
        errorList =[]
        if publishFlag:
            # check optimum prompt list validation to publish space
            self.establish_cosmosdb_connection(container_name = 'prompt')
            optimum_prompt_list = self.cosmosdb_service.get_items_for_optimum_flag(space_id)
            if not optimum_prompt_list:
                errorList.append(MSG.ERROR_MSG_OPTIMUM_PROMPT_LIST_CHECK)

            # check is any Response template validation to publish space
            self.establish_cosmosdb_connection(container_name = 'document')
            all_documents = self.cosmosdb_service.get_all_items_with_filter(space_id)
            if not all_documents:
                errorList.append(MSG.ERROR_MSG_RESPONSE_TEMPLATE_CHECK)

            self.establish_cosmosdb_connection(container_name = 'document')
            default_documents = self.cosmosdb_service.get_all_default_items_with_filter(space_id)
            if not default_documents:
                errorList.append(MSG.ERROR_MSG_DEFAULT_RESPONSE_TEMPLATE_CHECK)

            if errorList:
                response = {
                'published' : False,
                'message' : errorList,
                'status_code' : status.HTTP_400_BAD_REQUEST,
                'space' : space
            }
            else:
                space['published'] = publishFlag
                published_space = self.update_space_publish(space_id, space, user)
                response= {
                'published' : publishFlag,
                'message' : "Assistant published successfully",
                'status_code' : status.HTTP_200_OK,
                'space' : published_space,
                }
        else:
            # Update space to unpublish
            space['published'] = publishFlag
            unpublished_space = self.update_space_publish(space_id, space, user)
            response= {
                'published' : publishFlag,
                'message' : "Assistant has been unpublished successfully",
                'status_code' : status.HTTP_200_OK,
                'space' : unpublished_space,
            }
        return response

    def get_published_spaces(self):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Build query
        query = DB_QUERY.ALL_PUBLISHED_SPACES.format(container_name = 'space', published_field = 'published')
        # Get the space item
        space_list = self.cosmosdb_service.get_items_for_query(query)
        #
        return space_list
    
    def get_published_space_spaceid(self,spaceid):
        published_space = {}
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Build query
        query = DB_QUERY.GET_QUERY_PUBLISHED_SPACES_BY_SPACEID.format(container_name = 'space', published_field = 'published',space_id_field='spaceId',space_id=spaceid)
        # Get the space item
        space_list = self.cosmosdb_service.get_items_for_query(query)
        # Extract the first item from the list
        if space_list:
            published_space = space_list[0]
        
        return published_space
    
    def get_published_spaces_all_with_groups_user(self,user,group_names):
        
        # Get the space item
        space_list = self.get_published_spaces()
        space_list_user = copy.deepcopy(space_list)
        space_list_group = copy.deepcopy(space_list)
        if AUTH.SUPER_ADMIN_ROLE in user.roles:
            return space_list
        else :
            spaces_with_user_permissions = self.get_space_with_user(space_list_user,user.email)
            spaces_with_group_permissions = self.get_space_with_groups(space_list_group,group_names)               
            space_list = self.merge_by_priority(spaces_with_user_permissions,spaces_with_group_permissions)
            return space_list
        
    def get_spaces_all_with_groups_user(self,user,group_names):
        
        self.establish_cosmosdb_connection()
        # Get the space item
        space_list = self.cosmosdb_service.get_all_items(user)
        space_list_user = copy.deepcopy(space_list)
        space_list_group = copy.deepcopy(space_list)
        spaces_with_user_permissions = []
        spaces_with_group_permissions = []
        if AUTH.SUPER_ADMIN_ROLE in user.roles:
            return space_list
        else :
            spaces_with_user_permissions = self.get_space_with_user(space_list_user,user.email)
            if group_names:
                spaces_with_group_permissions = self.get_space_with_groups(space_list_group,group_names)
            space_list = self.merge_by_priority(spaces_with_user_permissions,spaces_with_group_permissions)
            return space_list

    def process_email_info(self, assigned_user):
        email_id = ''
        try:
            if isinstance(assigned_user, dict):
                email_id = assigned_user['emailId'].lower()
            else:
                email_id = assigned_user.lower()
        except Exception as error:
            logger.log('Error in extracting email from assigned users')

        return email_id
        

    def get_space_with_user(self,spaces_user,email):
        # Iterate over each item in the list of spaces
        for space_user in spaces_user:
            # Get assigned user email in lower case
            assigned_users_email_list = [self.process_email_info(assigned_user) for assigned_user in space_user.get("assignedUsers", [])]
            # Check if the email is in the assignedUsers list for the current space
            if email.lower() in assigned_users_email_list:  # Use .get() to avoid KeyError
                # Find the user's details in assignedUserDetails
                for user_detail in space_user.get("assignedUserDetails", []):  # Use .get() to avoid KeyError
                    if user_detail.get("email") == email:  # Using .get() to avoid KeyError
                        # Assign the user permission type to the temporary variable
                        space_user["user_permission"] = user_detail.get("userType", None)  # Default to None if no userType
                        space_user["accessMedium"] ="User"
                        break
        spaces_with_permissions=[]
        for space_user in spaces_user:
            # Check if the space has a 'user_permission' field and it is not None
            if space_user.get("user_permission") is not None:
                spaces_with_permissions.append(space_user)
        return spaces_with_permissions

    def get_space_with_groups(self,spaces_group, group_names):
        group_names = [name.lower() for name in group_names]
        user_type_priority = ['admin', 'contributor', 'viewer']
        for space in spaces_group:
            if 'assignedGroups' in space:
                # Find matching groups
                matching_groups = self.get_matching_groups(space['assignedGroups'], group_names)
                if not matching_groups:
                    continue
                
                # Get assigned group with the highest priority and its permission
                assigned_group, assigned_permission = self.get_assigned_permission_and_groups(space, matching_groups, user_type_priority)
                
                if assigned_permission:
                    self.assign_permission_to_space(space, assigned_group, assigned_permission)

        # Filter out spaces with no user_permission assigned
        return self.filter_spaces_with_permission(spaces_group)

    def get_matching_groups(self,assigned_groups, group_names):
            """Returns the matching groups from the assigned groups."""
            return [group.lower() for group in assigned_groups if group.lower() in group_names]

    def get_assigned_permission_and_groups(self,space, matching_groups, user_type_priority):
        """Returns the group with the highest priority permission."""
        assigned_group = None
        assigned_permission = None

        for group in space['assignedGroupDetails']:
            # Check if the group's displayname matches the requested groups
            if group['displayname'].lower() in matching_groups:
                # Determine the current user's permission priority
                current_permission = group['userType'].lower()
                
                # Compare it with the currently assigned permission
                if assigned_permission is None or user_type_priority.index(current_permission) < user_type_priority.index(assigned_permission):
                    assigned_group = group['displayname']  # Store the group displayname as a string
                    assigned_permission = current_permission

        return assigned_group, assigned_permission

    def assign_permission_to_space(self,space, assigned_group, assigned_permission):
        """Assigns the permission and the group to the space."""
        space['user_permission'] = assigned_permission
        space['accessMedium'] = 'Group'
        space['accessGroup'] = assigned_group  # Just the highest priority group as a string

    def filter_spaces_with_permission(self,spaces):
        """Filters spaces that have user_permission assigned."""
        return [space for space in spaces if 'user_permission' in space]


    # def merge_by_priority(self,spaces_with_user_permissions, spaces_with_group_permissions):
    #     # Dictionary to store the merged records based on 'id'
    #     merged_dict = {}
    #     priority_map = {'admin': 3, 'contributor': 2, 'viewer': 1}
    #     # Process 'user' list
    #     for item in spaces_with_user_permissions:
    #         merged_dict[item['id']] = item

    #     # Process 'group' list and merge with higher priority
    #     for item in spaces_with_group_permissions:
    #         if item['id'] in merged_dict:
    #             existing_item = merged_dict[item['id']]
    #             # Get priority of current item and existing item
    #             current_priority = priority_map.get(item.get('priority', 'viewer'), 1)  # Default to 'viewer' priority (1)
    #             existing_priority = priority_map.get(existing_item.get('priority', 'viewer'), 1)
                
    #             # Keep the record with higher priority
    #             if current_priority > existing_priority:
    #                 merged_dict[item['id']] = item
    #         else:
    #             merged_dict[item['id']] = item

    #     # Convert merged dictionary back to a list and return it
    #     return list(merged_dict.values())

    def merge_by_priority(self,spaces_with_user_permissions, spaces_with_group_permissions):
        # Priority mapping for user types
        priority_map = {'admin': 3, 'contributor': 2, 'viewer': 1}

        # Step 1: Create a dictionary for faster lookup of existing ids in both lists
        final_output = {}

        # Step 2: Process the group_output list
        for entry in spaces_with_user_permissions:
            id = entry['id']
            # Store the entry with the user_permission and its priority for comparison
            final_output[id] = {'data': entry, 'priority': priority_map[entry['user_permission']]}

        # Step 3: Process the user_output list
        for entry in spaces_with_group_permissions:
            id = entry['id']
            # If the id is already in the final_output, compare the priority
            if id in final_output:
                current_priority = final_output[id]['priority']
                new_priority = priority_map[entry['user_permission']]
                
                # If the new entry has higher priority, update the final_output
                if new_priority > current_priority:
                    final_output[id] = {'data': entry, 'priority': new_priority}
            else:
                # If the id is not in the final_output, add it directly
                final_output[id] = {'data': entry, 'priority': priority_map[entry['user_permission']]}

        # Step 4: Collect the final results by extracting the 'data' from final_output
        result = [value['data'] for value in final_output.values()]

        return result
