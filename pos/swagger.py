import os
import json
from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema

# Load schema map
SCHEMA_MAP_PATH = os.path.join(os.path.dirname(__file__), 'schema_map.json')
try:
    with open(SCHEMA_MAP_PATH, 'r') as f:
        VIEW_SCHEMA_MAP = json.load(f)
except Exception as e:
    VIEW_SCHEMA_MAP = {}

class CustomSwaggerAutoSchema(SwaggerAutoSchema):
    def get_operation_id(self, operation_keys=None):
        if hasattr(self.view, 'func'):
            name = self.view.func.__name__
            return name.replace('_', ' ').title()
        elif hasattr(self.view, 'action') and self.view.action:
            return self.view.action.replace('_', ' ').title()
        
        operation_id = super().get_operation_id(operation_keys)
        if operation_id:
            return operation_id.replace('_', ' ').title()
        return operation_id

    def get_tags(self, operation_keys=None):
        tags = super().get_tags(operation_keys)
        
        if hasattr(self.view, '__module__'):
            module = self.view.__module__
            app_name = module.split('.')[0]
            
            tag_map = {
                'counterapi': 'Counter',
                'v1': 'V1 Core',
                'kot': 'KOT',
                'qr': 'QR',
                'userauth': 'UserAuth',
                'subscriptions': 'Subscriptions',
                'users': 'Users',
                'helpdesk': 'Helpdesk',
                'adminpanel': 'AdminPanel',
            }
            
            if app_name in tag_map:
                return [tag_map[app_name]]
            else:
                return [app_name.title()]
                
        return tags

    def get_summary_and_description(self):
        summary, description = super().get_summary_and_description()
        if not summary:
            # Fallback to operation_id if no explicit summary is set
            operation_id = self.get_operation_id()
            if operation_id:
                summary = operation_id
        return summary, description

    def get_responses(self):
        responses = super().get_responses()
        
        view_name = None
        if hasattr(self.view, 'func'):
            view_name = self.view.func.__name__
        elif hasattr(self.view, 'action') and self.view.action:
            view_name = self.view.action
            
        if not view_name or view_name not in VIEW_SCHEMA_MAP:
            return responses
            
        expected_keys = VIEW_SCHEMA_MAP[view_name]
        metadata_keys = {'error', 'detail', 'details', 'message'}
        
        wrapped_responses = {}
        for status_code, response in responses.items():
            if int(status_code) >= 200 and int(status_code) < 300:
                if isinstance(response, openapi.Response):
                    original_schema = response.schema
                    description = response.description
                else:
                    original_schema = response
                    description = "Successful response"
                
                properties = {}
                data_key_assigned = False
                
                # Check if the original schema is already wrapped to prevent double wrapping
                if hasattr(original_schema, 'properties') and 'error' in (original_schema.properties or {}):
                    wrapped_responses[status_code] = response
                    continue
                
                for key in expected_keys:
                    if key in {'error', 'is_logged_in', 'is_active'}:
                        properties[key] = openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False)
                    elif key in metadata_keys:
                        properties[key] = openapi.Schema(type=openapi.TYPE_STRING)
                    elif key in {'total_count', 'sequence', 'total_pages', 'current_page', 'count'}:
                        properties[key] = openapi.Schema(type=openapi.TYPE_INTEGER)
                    else:
                        # Data keys like 'ticket', 'categories', 'user_details', 'products'
                        if original_schema and not data_key_assigned and getattr(original_schema, 'type', '') != openapi.TYPE_STRING:
                            properties[key] = original_schema
                            data_key_assigned = True
                        else:
                            # Fallback for extra keys
                            properties[key] = openapi.Schema(type=openapi.TYPE_STRING)
                
                if not properties:
                    # If we somehow failed to map, return original
                    wrapped_responses[status_code] = response
                    continue
                    
                wrapped_schema = openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties=properties
                )
                wrapped_responses[status_code] = openapi.Response(description, wrapped_schema)
            else:
                wrapped_responses[status_code] = response
                
        return wrapped_responses
