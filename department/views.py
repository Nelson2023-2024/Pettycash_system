from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from utils.decorators.login_required import login_required
from utils.decorators.allowed_http_methods import allowed_http_methods
from utils.response_provider import ResponseProvider
from .services.department_services import DepartmentController

# Create your views here.
@csrf_exempt
@allowed_http_methods('POST')
@login_required('ADM')
def create_department_view(request):
    try:
        department = DepartmentController().create_department(request)
        return department 
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


@csrf_exempt
@allowed_http_methods('GET')
@login_required()
def get_departments_view(request):
    try:
        departments = DepartmentController().get_departments(request)
        return departments
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)
    

@csrf_exempt
@allowed_http_methods('GET')
@login_required()
def get_department_view(request,department_id):
    try:
        department = DepartmentController().get_department(request, department_id)
        return department
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)
    
@csrf_exempt
@allowed_http_methods('PATCH')
@login_required('ADM')
def update_department_view(request, department_id):
    try:
        return DepartmentController.update_department(request, department_id)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


@csrf_exempt
@allowed_http_methods('DELETE')
@login_required('ADM')
def deactivate_department_view(request, department_id):
    try:
        return DepartmentController.deactivate_department(request, department_id)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


@csrf_exempt
@allowed_http_methods('PATCH')
@login_required('ADM')
def assign_line_manager_view(request, department_id):
    try:
        return DepartmentController.assign_line_manager(request, department_id)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)