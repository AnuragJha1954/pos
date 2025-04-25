from django.contrib import admin
from .models import Ticket
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Register your models here.

class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'outlet', 'raised_by', 'status', 'media_preview', 'created_at', 'updated_at')
    list_filter = ('status', 'outlet')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'media_preview')

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'media', 'media_preview', 'outlet', 'raised_by', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def media_preview(self, obj):
        if obj.media:
            file_url = obj.media.url
            if obj.media.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                return format_html('<img src="{}" width="150" style="border:1px solid #ccc;" />', file_url)
            elif obj.media.name.lower().endswith('.pdf'):
                return format_html('<a href="{}" target="_blank">View PDF</a>', file_url)
            else:
                return format_html('<a href="{}" target="_blank">Download File</a>', file_url)
        return "No media attached"
    media_preview.short_description = "Media Preview"

# Register the admin
admin.site.register(Ticket, TicketAdmin)