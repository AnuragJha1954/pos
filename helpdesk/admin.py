from django.contrib import admin
from .models import Ticket

# Register your models here.

class TicketAdmin(admin.ModelAdmin):
    # Display fields in the list view
    list_display = ('id', 'title', 'outlet', 'raised_by', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'outlet')  # Add filter options for status and outlet
    search_fields = ('title', 'description')  # Enable search by title and description
    ordering = ('-created_at',)  # Order by creation date, newest first
    readonly_fields = ('created_at', 'updated_at')  # Make created_at and updated_at readonly

    # Define fields for the detail view form
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'outlet', 'raised_by', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Make the timestamp section collapsible
        }),
    )

# Register the Ticket model with the custom admin class
admin.site.register(Ticket, TicketAdmin)