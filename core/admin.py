from django.contrib import admin
from django.utils.html import format_html
from .models import Campus, College, School, Department, Class, Student
import nfc
from django.contrib import messages

# Campus Admin
@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# College Admin
@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name', 'campus')
    search_fields = ('name', 'campus__name')


# School Admin
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'college')
    search_fields = ('name', 'college__name')


# Department Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    search_fields = ('name', 'school__name')


# Class Admin
@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    search_fields = ('name', 'department__name')


# Student Admin

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'campus', 'college', 'school', 'department', 'student_class', 'nfc_url_link','laptop_model', 'laptop_serial')
    list_filter = ('payment_status',) 
    search_fields = ('student_id', 'first_name', 'last_name', 'campus__name', 'college__name', 'school__name', 'department__name', 'student_class__name')
    actions = ['write_to_nfc_card']

    def nfc_url_link(self, obj):
        """
        Display the NFC URL as a clickable link in the admin panel.
        """
        if obj.nfc_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.nfc_url, obj.nfc_url)
        return "No URL"
    nfc_url_link.short_description = "NFC URL"

    def save_model(self, request, obj, form, change):
        """
        Override save_model to pass the request object to the Student model
        so the NFC URL can be dynamically generated with the correct host.
        """
        obj.save(request=request)  # Pass the request object to the save method
        super().save_model(request, obj, form, change)

    def write_to_nfc_card(self, request, queryset):
        """
        Custom admin action to write the NFC URL to an NFC card.
        """
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one student to write to an NFC card.", level=messages.ERROR)
            return

        student = queryset.first()
        if not student.nfc_url:
            self.message_user(request, "The selected student does not have an NFC URL.", level=messages.ERROR)
            return

        try:
            # Check if an NFC reader is connected
            clf = nfc.ContactlessFrontend('usb')
            if not clf:
                self.message_user(request, "No NFC reader found. Please connect an NFC reader.", level=messages.ERROR)
                return

            # Write the NFC URL to the NFC card
            def write_tag(tag):
                tag.ndef.message = nfc.ndef.TextRecord(student.nfc_url)
                return True

            clf.connect(rdwr={'on-connect': write_tag})
            clf.close()

            self.message_user(request, f"NFC URL successfully written to the NFC card for student {student.first_name} {student.last_name}.", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"An error occurred while writing to the NFC card: {e}", level=messages.ERROR)

    write_to_nfc_card.short_description = "Write NFC URL to NFC Card"